# -*- coding: utf-8 -*-
'''
Execute a job on the targeted minions by using a moving window of fixed size `batch`.
'''

# Import python libs
from __future__ import absolute_import, print_function, unicode_literals
import gc
import salt.ext.tornado

# Import salt libs
import salt.client

# pylint: enable=import-error,no-name-in-module,redefined-builtin
import logging

log = logging.getLogger(__name__)

from salt.cli.batch import get_bnum, batch_get_opts, batch_get_eauth


class BatchAsync(object):
    '''
    Run a job on the targeted minions by using a moving window of fixed size `batch`.

    ``BatchAsync`` is used to execute a job on the targeted minions by keeping
    the number of concurrent running minions to the size of `batch` parameter.

    The control parameters are:
        - batch: number/percentage of concurrent running minions
        - batch_delay: minimum wait time between batches
        - batch_presence_ping_timeout: time to wait for presence pings before starting the batch
        - gather_job_timeout: `find_job` timeout
        - timeout: time to wait before firing a `find_job`

    When the batch stars, a `start` event is fired:
         - tag: salt/batch/<batch-jid>/start
         - data: {
             "available_minions": self.minions,
             "down_minions": targeted_minions - presence_ping_minions
           }

    When the batch ends, an `done` event is fired:
        - tag: salt/batch/<batch-jid>/done
        - data: {
             "available_minions": self.minions,
             "down_minions": targeted_minions - presence_ping_minions
             "done_minions": self.done_minions,
             "timedout_minions": self.timedout_minions
         }
    '''
    def __init__(self, parent_opts, jid_gen, clear_load):
        ioloop = salt.ext.tornado.ioloop.IOLoop.current()
        self.local = salt.client.get_local_client(parent_opts['conf_file'], io_loop=ioloop)
        if 'gather_job_timeout' in clear_load['kwargs']:
            clear_load['gather_job_timeout'] = clear_load['kwargs'].pop('gather_job_timeout')
        else:
            clear_load['gather_job_timeout'] = self.local.opts['gather_job_timeout']
        self.batch_presence_ping_timeout = clear_load['kwargs'].get('batch_presence_ping_timeout', None)
        self.batch_delay = clear_load['kwargs'].get('batch_delay', 1)
        self.opts = batch_get_opts(
            clear_load.pop('tgt'),
            clear_load.pop('fun'),
            clear_load['kwargs'].pop('batch'),
            self.local.opts,
            **clear_load)
        self.eauth = batch_get_eauth(clear_load['kwargs'])
        self.metadata = clear_load['kwargs'].get('metadata', {})
        self.minions = set()
        self.targeted_minions = set()
        self.timedout_minions = set()
        self.done_minions = set()
        self.active = set()
        self.initialized = False
        self.jid_gen = jid_gen
        self.ping_jid = jid_gen()
        self.batch_jid = jid_gen()
        self.find_job_jid = jid_gen()
        self.find_job_returned = set()
        self.ended = False
        self.event = salt.utils.event.get_event(
            'master',
            self.opts['sock_dir'],
            self.opts['transport'],
            opts=self.opts,
            listen=True,
            io_loop=ioloop,
            keep_loop=True)
        self.scheduled = False
        self.patterns = set()

    def __set_event_handler(self):
        ping_return_pattern = 'salt/job/{0}/ret/*'.format(self.ping_jid)
        batch_return_pattern = 'salt/job/{0}/ret/*'.format(self.batch_jid)
        self.event.subscribe(ping_return_pattern, match_type='glob')
        self.event.subscribe(batch_return_pattern, match_type='glob')
        self.patterns = {
            (ping_return_pattern, 'ping_return'),
            (batch_return_pattern, 'batch_run'),
        }
        self.event.set_event_handler(self.__event_handler)

    def __event_handler(self, raw):
        if not self.event:
            return
        try:
            mtag, data = self.event.unpack(raw, self.event.serial)
            for (pattern, op) in self.patterns:
                if mtag.startswith(pattern[:-1]):
                    minion = data['id']
                    if op == 'ping_return':
                        self.minions.add(minion)
                        if self.targeted_minions == self.minions:
                            self.event.io_loop.spawn_callback(self.start_batch)
                    elif op == 'find_job_return':
                        if data.get("return", None):
                            self.find_job_returned.add(minion)
                    elif op == 'batch_run':
                        if minion in self.active:
                            self.active.remove(minion)
                            self.done_minions.add(minion)
                            self.event.io_loop.spawn_callback(self.schedule_next)
        except Exception as ex:
           log.error("Exception occured while processing event: {}".format(ex))

    def _get_next(self):
        to_run = self.minions.difference(
            self.done_minions).difference(
            self.active).difference(
            self.timedout_minions)
        next_batch_size = min(
            len(to_run),                   # partial batch (all left)
            self.batch_size - len(self.active)  # full batch or available slots
        )
        return set(list(to_run)[:next_batch_size])

    def check_find_job(self, batch_minions, jid):
        if self.event:
            find_job_return_pattern = 'salt/job/{0}/ret/*'.format(jid)
            self.event.unsubscribe(find_job_return_pattern, match_type='glob')
            self.patterns.remove((find_job_return_pattern, "find_job_return"))

            timedout_minions = batch_minions.difference(self.find_job_returned).difference(self.done_minions)
            self.timedout_minions = self.timedout_minions.union(timedout_minions)
            self.active = self.active.difference(self.timedout_minions)
            running = batch_minions.difference(self.done_minions).difference(self.timedout_minions)

            if timedout_minions:
                self.schedule_next()

            if self.event and running:
                self.find_job_returned = self.find_job_returned.difference(running)
                self.event.io_loop.spawn_callback(self.find_job, running)

    @salt.ext.tornado.gen.coroutine
    def find_job(self, minions):
        if self.event:
            not_done = minions.difference(self.done_minions).difference(self.timedout_minions)
            try:
                if not_done:
                    jid = self.jid_gen()
                    find_job_return_pattern = 'salt/job/{0}/ret/*'.format(jid)
                    self.patterns.add((find_job_return_pattern, "find_job_return"))
                    self.event.subscribe(find_job_return_pattern, match_type='glob')
                    ret = yield self.local.run_job_async(
                        not_done,
                        'saltutil.find_job',
                        [self.batch_jid],
                        'list',
                        gather_job_timeout=self.opts['gather_job_timeout'],
                        jid=jid,
                        **self.eauth)
                    yield salt.ext.tornado.gen.sleep(self.opts['gather_job_timeout'])
                    if self.event:
                        self.event.io_loop.spawn_callback(
                            self.check_find_job,
                            not_done,
                            jid)
            except Exception as ex:
                log.error("Exception occured handling batch async: {}. Aborting execution.".format(ex))
                self.close_safe()

    @salt.ext.tornado.gen.coroutine
    def start(self):
        if self.event:
            self.__set_event_handler()
            ping_return = yield self.local.run_job_async(
                self.opts['tgt'],
                'test.ping',
                [],
                self.opts.get(
                    'selected_target_option',
                    self.opts.get('tgt_type', 'glob')
                ),
                gather_job_timeout=self.opts['gather_job_timeout'],
                jid=self.ping_jid,
                metadata=self.metadata,
                **self.eauth)
            self.targeted_minions = set(ping_return['minions'])
            #start batching even if not all minions respond to ping
            yield salt.ext.tornado.gen.sleep(self.batch_presence_ping_timeout or self.opts['gather_job_timeout'])
            if self.event:
                self.event.io_loop.spawn_callback(self.start_batch)

    @salt.ext.tornado.gen.coroutine
    def start_batch(self):
        if not self.initialized:
            self.batch_size = get_bnum(self.opts, self.minions, True)
            self.initialized = True
            data = {
                "available_minions": self.minions,
                "down_minions": self.targeted_minions.difference(self.minions),
                "metadata": self.metadata
            }
            ret = self.event.fire_event(data, "salt/batch/{0}/start".format(self.batch_jid))
            if self.event:
                self.event.io_loop.spawn_callback(self.run_next)

    @salt.ext.tornado.gen.coroutine
    def end_batch(self):
        left = self.minions.symmetric_difference(self.done_minions.union(self.timedout_minions))
        if not left and not self.ended:
            self.ended = True
            data = {
                "available_minions": self.minions,
                "down_minions": self.targeted_minions.difference(self.minions),
                "done_minions": self.done_minions,
                "timedout_minions": self.timedout_minions,
                "metadata": self.metadata
            }
            self.event.fire_event(data, "salt/batch/{0}/done".format(self.batch_jid))

            # release to the IOLoop to allow the event to be published
            # before closing batch async execution
            yield salt.ext.tornado.gen.sleep(1)
            self.close_safe()

    def close_safe(self):
       for (pattern, label) in self.patterns:
           self.event.unsubscribe(pattern, match_type='glob')
       self.event.remove_event_handler(self.__event_handler)
       self.event = None
       self.local = None
       self.ioloop = None
       del self
       gc.collect()

    @salt.ext.tornado.gen.coroutine
    def schedule_next(self):
        if not self.scheduled:
            self.scheduled = True
            # call later so that we maybe gather more returns
            yield salt.ext.tornado.gen.sleep(self.batch_delay)
            if self.event:
                self.event.io_loop.spawn_callback(self.run_next)

    @salt.ext.tornado.gen.coroutine
    def run_next(self):
        self.scheduled = False
        next_batch = self._get_next()
        if next_batch:
            self.active = self.active.union(next_batch)
            try:
                ret = yield self.local.run_job_async(
                    next_batch,
                    self.opts['fun'],
                    self.opts['arg'],
                    'list',
                    raw=self.opts.get('raw', False),
                    ret=self.opts.get('return', ''),
                    gather_job_timeout=self.opts['gather_job_timeout'],
                    jid=self.batch_jid,
                    metadata=self.metadata)

                yield salt.ext.tornado.gen.sleep(self.opts['timeout'])

                # The batch can be done already at this point, which means no self.event
                if self.event:
                    self.event.io_loop.spawn_callback(self.find_job, set(next_batch))
            except Exception as ex:
                log.error("Error in scheduling next batch: %s. Aborting execution", ex)
                self.active = self.active.difference(next_batch)
                self.close_safe()
        else:
            yield self.end_batch()
        gc.collect()

    def __del__(self):
        self.local = None
        self.event = None
        self.ioloop = None
        gc.collect()

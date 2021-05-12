# -*- coding: utf-8 -*-
'''
    :codeauthor: Nicole Thomas <nicole@saltstack.com>
'''

# Import python libs
from __future__ import absolute_import, print_function, unicode_literals

# Import Salt Libs
from salt.cli.batch import Batch

# Import Salt Testing Libs
from tests.support.unit import TestCase
from tests.support.mock import MagicMock, patch

from salt.cli.batch import batch_get_opts


class BatchTestCase(TestCase):
    '''
    Unit Tests for the salt.cli.batch module
    '''

    def setUp(self):
        opts = {'batch': '',
                'conf_file': {},
                'tgt': '',
                'transport': '',
                'timeout': 5,
                'gather_job_timeout': 5}

        mock_client = MagicMock()
        with patch('salt.client.get_local_client', MagicMock(return_value=mock_client)):
            with patch('salt.client.LocalClient.cmd_iter', MagicMock(return_value=[])):
                self.batch = Batch(opts, quiet='quiet')

    # get_bnum tests

    def test_get_bnum_str(self):
        '''
        Tests passing batch value as a number(str)
        '''
        self.batch.opts = {'batch': '2', 'timeout': 5}
        self.batch.minions = ['foo', 'bar']
        self.assertEqual(Batch.get_bnum(self.batch), 2)

    def test_get_bnum_int(self):
        '''
        Tests passing batch value as a number(int)
        '''
        self.batch.opts = {'batch': 2, 'timeout': 5}
        self.batch.minions = ['foo', 'bar']
        self.assertEqual(Batch.get_bnum(self.batch), 2)

    def test_get_bnum_percentage(self):
        '''
        Tests passing batch value as percentage
        '''
        self.batch.opts = {'batch': '50%', 'timeout': 5}
        self.batch.minions = ['foo']
        self.assertEqual(Batch.get_bnum(self.batch), 1)

    def test_get_bnum_high_percentage(self):
        '''
        Tests passing batch value as percentage over 100%
        '''
        self.batch.opts = {'batch': '160%', 'timeout': 5}
        self.batch.minions = ['foo', 'bar', 'baz']
        self.assertEqual(Batch.get_bnum(self.batch), 4)

    def test_get_bnum_invalid_batch_data(self):
        '''
        Tests when an invalid batch value is passed
        '''
        ret = Batch.get_bnum(self.batch)
        self.assertEqual(ret, None)

    def test_return_value_in_run_for_ret(self):
        """
        cmd_iter_no_block should have been called with a return no matter if
        the return value was in ret or return.
        """
        self.batch.opts = {
            "batch": "100%",
            "timeout": 5,
            "fun": "test",
            "arg": "foo",
            "gather_job_timeout": 5,
            "ret": "my_return",
        }
        self.batch.minions = ["foo", "bar", "baz"]
        self.batch.local.cmd_iter_no_block = MagicMock(return_value=iter([]))
        ret = Batch.run(self.batch)
        # We need to fetch at least one object to trigger the relevant code path.
        x = next(ret)
        self.batch.local.cmd_iter_no_block.assert_called_with(
            ["baz", "bar", "foo"],
            "test",
            "foo",
            5,
            "list",
            raw=False,
            ret="my_return",
            show_jid=False,
            verbose=False,
            gather_job_timeout=5,
        )

    def test_return_value_in_run_for_return(self):
        """
        cmd_iter_no_block should have been called with a return no matter if
        the return value was in ret or return.
        """
        self.batch.opts = {
            "batch": "100%",
            "timeout": 5,
            "fun": "test",
            "arg": "foo",
            "gather_job_timeout": 5,
            "return": "my_return",
        }
        self.batch.minions = ["foo", "bar", "baz"]
        self.batch.local.cmd_iter_no_block = MagicMock(return_value=iter([]))
        ret = Batch.run(self.batch)
        # We need to fetch at least one object to trigger the relevant code path.
        x = next(ret)
        self.batch.local.cmd_iter_no_block.assert_called_with(
            ["baz", "bar", "foo"],
            "test",
            "foo",
            5,
            "list",
            raw=False,
            ret="my_return",
            show_jid=False,
            verbose=False,
            gather_job_timeout=5,
        )

    def test_batch_presence_ping(self):
        '''
        Tests passing batch_presence_ping_timeout and batch_presence_ping_gather_job_timeout
        '''
        ret = batch_get_opts('', 'test.ping', '2', {},
                             timeout=20, gather_job_timeout=120)
        self.assertEqual(ret['batch_presence_ping_timeout'], 20)
        self.assertEqual(ret['batch_presence_ping_gather_job_timeout'], 120)
        ret = batch_get_opts('', 'test.ping', '2', {},
                             timeout=20, gather_job_timeout=120,
                             batch_presence_ping_timeout=4,
                             batch_presence_ping_gather_job_timeout=360)
        self.assertEqual(ret['batch_presence_ping_timeout'], 4)
        self.assertEqual(ret['batch_presence_ping_gather_job_timeout'], 360)

    def test_gather_minions_with_batch_presence_ping(self):
        '''
        Tests __gather_minions with batch_presence_ping options
        '''
        opts_no_pp   = {'batch': '2',
                        'conf_file': {},
                        'tgt': '',
                        'transport': '',
                        'timeout': 5,
                        'gather_job_timeout': 20}
        opts_with_pp = {'batch': '2',
                        'conf_file': {},
                        'tgt': '',
                        'transport': '',
                        'timeout': 5,
                        'gather_job_timeout': 20,
                        'batch_presence_ping_timeout': 3,
                        'batch_presence_ping_gather_job_timeout': 4}
        mock_client = MagicMock()
        with patch('salt.client.get_local_client', MagicMock(return_value=mock_client)):
            with patch('salt.client.LocalClient.cmd_iter', MagicMock(return_value=[])):
                Batch(opts_no_pp)
                Batch(opts_with_pp)
        self.assertEqual(mock_client.mock_calls[0][1][3],
                         opts_no_pp['timeout'])
        self.assertEqual(mock_client.mock_calls[0][2]['gather_job_timeout'],
                         opts_no_pp['gather_job_timeout'])
        self.assertEqual(mock_client.mock_calls[2][1][3],
                         opts_with_pp['batch_presence_ping_timeout'])
        self.assertEqual(mock_client.mock_calls[2][2]['gather_job_timeout'],
                         opts_with_pp['batch_presence_ping_gather_job_timeout'])

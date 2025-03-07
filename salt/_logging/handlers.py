"""
    salt._logging.handlers
    ~~~~~~~~~~~~~~~~~~~~~~

    Salt's logging handlers
"""

import copy
import logging
import logging.handlers
import queue as _queue
import sys
from collections import deque

from salt._logging.mixins import ExcInfoOnLogLevelFormatMixin
from salt.utils.versions import warn_until_date

log = logging.getLogger(__name__)


class TemporaryLoggingHandler(logging.NullHandler):
    """
    This logging handler will store all the log records up to its maximum
    queue size at which stage the first messages stored will be dropped.

    Should only be used as a temporary logging handler, while the logging
    system is not fully configured.

    Once configured, pass any logging handlers that should have received the
    initial log messages to the function
    :func:`TemporaryLoggingHandler.sync_with_handlers` and all stored log
    records will be dispatched to the provided handlers.

    .. versionadded:: 0.17.0
    """

    def __init__(self, level=logging.NOTSET, max_queue_size=10000):
        warn_until_date(
            "20260101",
            "Please stop using '{name}.TemporaryLoggingHandler'. "
            "'{name}.TemporaryLoggingHandler' will go away after "
            "{{date}}.".format(name=__name__),
        )
        super().__init__(level=level)
        self.__messages = deque(maxlen=max_queue_size)

    def handle(self, record):
        self.acquire()
        self.__messages.append(record)
        self.release()

    def sync_with_handlers(self, handlers=()):
        """
        Sync the stored log records to the provided log handlers.
        """
        if not handlers:
            return

        while self.__messages:
            record = self.__messages.popleft()
            for handler in handlers:
                if handler.level > record.levelno:
                    # If the handler's level is higher than the log record one,
                    # it should not handle the log record
                    continue
                handler.handle(record)


class StreamHandler(ExcInfoOnLogLevelFormatMixin, logging.StreamHandler):
    """
    Stream handler which properly handles exc_info on a per handler basis
    """


class DeferredStreamHandler(StreamHandler):
    """
    This logging handler will store all the log records up to its maximum
    queue size at which stage the first messages stored will be dropped.

    Should only be used as a temporary logging handler, while the logging
    system is not fully configured.

    Once configured, pass any logging handlers that should have received the
    initial log messages to the function
    :func:`DeferredStreamHandler.sync_with_handlers` and all stored log
    records will be dispatched to the provided handlers.

    If anything goes wrong before logging is properly setup, all stored messages
    will be flushed to the handler's stream, ie, written to console.

    .. versionadded:: 3005.0
    """

    def __init__(self, stream, max_queue_size=10000):
        super().__init__(stream)
        self.__messages = deque(maxlen=max_queue_size)
        self.__emitting = False
        import traceback

        self.stack = "".join(traceback.format_stack())

    def handle(self, record):
        self.acquire()
        self.__messages.append(record)
        self.release()

    def flush(self):
        if self.__emitting:
            # We set the flushing flag because the stream handler actually calls flush when
            # emitting a log record and we don't want to cause a RecursionError
            return
        while self.__messages:
            try:
                self.__emitting = True
                record = self.__messages.popleft()
                # We call the parent's class handle method so it's actually
                # handled and not queued back
                # However, temporarily
                super().handle(record)
            finally:
                self.__emitting = False
        # This will raise a ValueError if the file handle has been closed.
        super().flush()

    def sync_with_handlers(self, handlers=()):
        """
        Sync the stored log records to the provided log handlers.
        """
        while self.__messages:
            record = self.__messages.popleft()
            for handler in handlers:
                if handler is self:
                    continue
                handler.handle(record)


class FileHandler(ExcInfoOnLogLevelFormatMixin, logging.FileHandler):
    """
    File handler which properly handles exc_info on a per handler basis
    """


class SysLogHandler(ExcInfoOnLogLevelFormatMixin, logging.handlers.SysLogHandler):
    """
    Syslog handler which properly handles exc_info on a per handler basis
    """

    def handleError(self, record):
        """
        Override the default error handling mechanism for py3
        Deal with syslog os errors when the log file does not exist
        """
        handled = False
        if sys.stderr and sys.version_info >= (3, 5, 4):
            exc_type, exc, exc_traceback = sys.exc_info()
            try:
                if exc_type.__name__ in "FileNotFoundError":
                    sys.stderr.write(
                        "[WARNING ] The log_file does not exist. Logging not "
                        "setup correctly or syslog service not started.\n"
                    )
                    handled = True
            finally:
                # 'del' recommended. See documentation of
                # 'sys.exc_info()' for details.
                del exc_type, exc, exc_traceback

        if not handled:
            super().handleError(record)


class RotatingFileHandler(
    ExcInfoOnLogLevelFormatMixin, logging.handlers.RotatingFileHandler
):
    """
    Rotating file handler which properly handles exc_info on a per handler basis
    """

    def handleError(self, record):
        """
        Override the default error handling mechanism

        Deal with log file rotation errors due to log file in use
        more softly.
        """
        handled = False

        # Can't use "salt.utils.platform.is_windows()" in this file
        if (
            sys.platform.startswith("win") and logging.raiseExceptions and sys.stderr
        ):  # see Python issue 13807
            exc_type, exc, exc_traceback = sys.exc_info()
            try:
                # PermissionError is used since Python 3.3.
                # OSError is used for previous versions of Python.
                if (
                    exc_type.__name__ in ("PermissionError", "OSError")
                    and exc.winerror == 32
                ):
                    if self.level <= logging.WARNING:
                        sys.stderr.write(
                            '[WARNING ] Unable to rotate the log file "{}" '
                            "because it is in use\n".format(self.baseFilename)
                        )
                    handled = True
            finally:
                # 'del' recommended. See documentation of
                # 'sys.exc_info()' for details.
                del exc_type, exc, exc_traceback

        if not handled:
            super().handleError(record)


class WatchedFileHandler(
    ExcInfoOnLogLevelFormatMixin, logging.handlers.WatchedFileHandler
):
    """
    Watched file handler which properly handles exc_info on a per handler basis
    """


if sys.version_info < (3, 7):
    # On python versions lower than 3.7, we sill subclass and overwrite prepare to include the fix for:
    #  https://bugs.python.org/issue35726
    class QueueHandler(
        ExcInfoOnLogLevelFormatMixin, logging.handlers.QueueHandler
    ):  # pylint: disable=no-member,inconsistent-mro
        def __init__(self, queue):  # pylint: disable=useless-super-delegation
            super().__init__(queue)
            warn_until_date(
                "20260101",
                "Please stop using '{name}.QueueHandler' and instead "
                "use 'logging.handlers.QueueHandler'. "
                "'{name}.QueueHandler' will go away after "
                "{{date}}.".format(name=__name__),
            )

        def enqueue(self, record):
            """
            Enqueue a record.

            The base implementation uses put_nowait. You may want to override
            this method if you want to use blocking, timeouts or custom queue
            implementations.
            """
            try:
                self.queue.put_nowait(record)
            except _queue.Full:
                sys.stderr.write(
                    "[WARNING ] Message queue is full, "
                    'unable to write "{}" to log.\n'.format(record)
                )

        def prepare(self, record):
            """
            Prepares a record for queuing. The object returned by this method is
            enqueued.
            The base implementation formats the record to merge the message
            and arguments, and removes unpickleable items from the record
            in-place.
            You might want to override this method if you want to convert
            the record to a dict or JSON string, or send a modified copy
            of the record while leaving the original intact.
            """
            # The format operation gets traceback text into record.exc_text
            # (if there's exception data), and also returns the formatted
            # message. We can then use this to replace the original
            # msg + args, as these might be unpickleable. We also zap the
            # exc_info and exc_text attributes, as they are no longer
            # needed and, if not None, will typically not be pickleable.
            msg = self.format(record)
            # bpo-35726: make copy of record to avoid affecting other handlers in the chain.
            record = copy.copy(record)
            record.message = msg
            record.msg = msg
            record.args = None
            record.exc_info = None
            record.exc_text = None
            return record

else:

    class QueueHandler(
        ExcInfoOnLogLevelFormatMixin, logging.handlers.QueueHandler
    ):  # pylint: disable=no-member,inconsistent-mro
        def __init__(self, queue):  # pylint: disable=useless-super-delegation
            super().__init__(queue)
            warn_until_date(
                "20260101",
                "Please stop using '{name}.QueueHandler' and instead "
                "use 'logging.handlers.QueueHandler'. "
                "'{name}.QueueHandler' will go away after "
                "{{date}}.".format(name=__name__),
            )

        def enqueue(self, record):
            """
            Enqueue a record.

            The base implementation uses put_nowait. You may want to override
            this method if you want to use blocking, timeouts or custom queue
            implementations.
            """
            try:
                self.queue.put_nowait(record)
            except _queue.Full:
                sys.stderr.write(
                    "[WARNING ] Message queue is full, "
                    'unable to write "{}" to log.\n'.format(record)
                )

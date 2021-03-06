# coding: utf-8

import errno
import re
import socket
import sys
import threading
import time
from pdb import Pdb
import xbmc
from xbmcgui import DialogProgressBG

__version__ = "1.2.0"

PY3 = sys.version_info[0] == 3


def cry(message):
    xbmc.log('remote-pdb: {0}'.format(message), xbmc.LOGNOTICE)


class LF2CRLF_FileWrapper(object):
    def __init__(self, fh):
        self.stream = fh
        self.read = fh.read
        self.readline = fh.readline
        self.readlines = fh.readlines
        self.close = fh.close
        self.flush = fh.flush
        self.fileno = fh.fileno

    @property
    def encoding(self):
        return self.stream.encoding

    def __iter__(self):
        return self.stream.__iter__()

    def write(self, data, nl_rex=re.compile("\r?\n")):
        self.stream.write(nl_rex.sub("\r\n", data))
        # we have to explicitly flush, and unfortunately we cannot just disable buffering because on Python 3 text
        # streams line buffering seems the minimum and on Windows line buffering doesn't work properly because we
        # write unix-style line endings
        self.stream.flush()

    def writelines(self, lines, nl_rex=re.compile("\r?\n")):
        self.stream.writelines(nl_rex.sub("\r\n", line) for line in lines)
        self.stream.flush()


class RemotePdb(Pdb):
    """
    This will run pdb as a ephemeral telnet service. Once you connect no one
    else can connect. On construction this object will block execution till a
    client has connected.

    Based on https://github.com/tamentis/rpdb I think ...

    To use this::

        RemotePdb(host='0.0.0.0', port=4444).set_trace()

    Then run: telnet 127.0.0.1 4444
    """
    active_instance = None
    has_quit = False

    def __init__(self, host, port, patch_stdstreams=False):
        cry('listen socket')
        self._listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listen_socket.settimeout(None)
        cry('setsokcport')
        self._listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        cry('bind')
        self._listen_socket.bind((host, port))
        self._stop_monitor = threading.Event()
        self._monitor_thread = threading.Thread(target=self._monitor_abort)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        if not host:
            host = socket.gethostname()
        port = self._listen_socket.getsockname()[1]
        cry("RemotePdb session open at %s:%s, waiting for connection ..." % (host, port))
        self._dialog = DialogProgressBG()
        self._dialog.create('remote-pdb',
                            'Waiting for connection at [COLOR=yellow]%s:%s[/COLOR]' % (host, port)
                            )
        self._listen_socket.listen(1)
        self._connection, address = self._listen_socket.accept()
        self._connection.settimeout(None)
        self._dialog.update(100, heading='remote-pdb', message='Connection from %s active' % address[0])
        cry("RemotePdb accepted connection from %s." % repr(address))
        if PY3:
            self.handle = LF2CRLF_FileWrapper(self._connection.makefile('rw'))
        else:
            self.handle = LF2CRLF_FileWrapper(self._connection.makefile())
        Pdb.__init__(self, completekey='tab', stdin=self.handle, stdout=self.handle)
        self.backup = []
        if patch_stdstreams:
            for name in (
                    'stderr',
                    'stdout',
                    '__stderr__',
                    '__stdout__',
                    'stdin',
                    '__stdin__',
            ):
                self.backup.append((name, getattr(sys, name)))
                setattr(sys, name, self.handle)
        RemotePdb.active_instance = self

    def _monitor_abort(self):
        while not (xbmc.abortRequested or self._stop_monitor.is_set()):
            time.sleep(0.1)
        if not self._stop_monitor.is_set():
            self.do_quit(None)

    def __restore(self):
        if self.backup:
            cry('Restoring streams: %s ...' % self.backup)
        for name, fh in self.backup:
            setattr(sys, name, fh)
        self.handle.close()
        RemotePdb.active_instance = None

    def do_quit(self, arg):
        self._dialog.close()
        self._stop_monitor.set()
        try:
            self._connection.shutdown(socket.SHUT_WR)
            self._connection.close()
        except AttributeError:
            pass
        self._listen_socket.close()
        try:
            self.__restore()
        except AttributeError:
            pass
        self.set_quit()
        RemotePdb.has_quit = True
        return 1

    do_q = do_exit = do_quit

    def set_trace(self, frame=None):
        if frame is None:
            frame = sys._getframe().f_back
        try:
            Pdb.set_trace(self, frame)
        except IOError as exc:
            if exc.errno != errno.ECONNRESET:
                raise

    def set_quit(self):
        sys.settrace(None)


def set_trace(host='127.0.0.1', port=0, patch_stdstreams=False):
    """
    Opens a remote PDB on first available port.
    """
    if not RemotePdb.has_quit:
        rdb = RemotePdb.active_instance
        if rdb is None:
            rdb = RemotePdb(host=host, port=port, patch_stdstreams=patch_stdstreams)
        rdb.set_trace(frame=sys._getframe().f_back)

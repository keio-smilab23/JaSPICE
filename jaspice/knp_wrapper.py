import subprocess
import pexpect
import re
import socket
from pyknp import KNP
from pyknp import Juman
from pyknp.utils.analyzer import Analyzer
from pyknp.utils.process import Subprocess


class ServerKNP(KNP):
    def __init__(self,
                 command='knp',
                 server="localhost",
                 port=31000,
                 timeout=60,
                 option='-tab',
                 rcfile='',
                 pattern=r'EOS',
                 jumancommand='jumanpp',
                 jumanrcfile='',
                 jumanoption='',
                 jumanpp=True,
                 multithreading=False,
                 ):
        super().__init__(command, server, port, timeout, option, rcfile, pattern, jumancommand, jumanrcfile, jumanoption, jumanpp, multithreading)
        self._open_server(port)
        self.analyzer = SocketAnalyzer(backend='socket', timeout=timeout, server=server, port=port,
                                 socket_option=b'RUN -tab -normal\n')

    def _open_server(self, knp_port):
        try:
            proc = subprocess.Popen(f"knp -tab -S -N {knp_port}".split(" "))
            import time
            time.sleep(1)
        except:
            proc = None
        
        self.proc = proc


    def __del__(self):
        if self.proc is not None:
            self.proc.terminate()
            print("del")



class PexpectKNP(KNP):
    def __init__(self,
                 command='knp',
                 server=None,
                 port=31000,
                 timeout=60,
                 option='-tab',
                 rcfile='',
                 pattern=r'EOS',
                 jumancommand='jumanpp',
                 jumanrcfile='',
                 jumanoption='',
                 jumanpp=True,
                 multithreading=False):
        super().__init__(command, server, port, timeout, option, rcfile, pattern, jumancommand, jumanrcfile, jumanoption, jumanpp, multithreading)
        knp_command = self.analyzer.command
        juman_command = self.juman.command
        self.analyzer = _Analyzer(backend='subprocess', multithreading=multithreading, timeout=timeout, command=knp_command)
        self.juman.analyzer = PexpectAnalyzer(backend='subprocess', multithreading=multithreading, timeout=timeout, command=juman_command)


class ServerKNP2(KNP):
    def __init__(self,
                 command='knp',
                 server='localhost',
                 port=31000,
                 timeout=60,
                 option='-tab',
                 rcfile='',
                 pattern=r'EOS',
                 jumancommand='jumanpp',
                 jumanrcfile='',
                 jumanoption='',
                 jumanpp=True,
                 multithreading=False):
        super().__init__(command, server, port, timeout, option, rcfile, pattern, jumancommand, jumanrcfile, jumanoption, jumanpp, multithreading)
        juman_command = self.juman.command
        self.analyzer = SocketAnalyzer(backend='subprocess', server=server, port=port, timeout=timeout, socket_option="RUN -tab -normal")
        self.juman.analyzer = PexpectAnalyzer(backend='subprocess', multithreading=multithreading, timeout=timeout, command=juman_command)


class SocketAnalyzer(Analyzer):
    def __init__(self,
                 backend,
                 multithreading=False,
                 server=None,
                 port=None,
                 socket_option=None,
                 command=None,
                 timeout=180,
                 ):
        super().__init__(backend, multithreading, server, port, socket_option, command, timeout)
        self.socket = Socket(self.server, self.port, self.socket_option)

    def query(self, input_str, pattern):
        assert self.socket
        res = super().query(input_str, pattern)
        return res


class Socket(object):
    def __init__(self, hostname, port, option=None):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((hostname, port))
        except:
            raise
        if option is not None:
            self.sock.send(option)
        data = ""
        while "OK" not in data:
            data = self.sock.recv(1024)
            data = str(data, 'utf-8')

    def __del__(self):
        if self.sock:
            self.sock.close()

    def _decode(self, x):
        try:
            s = x.decode('utf-8')
            return s
        except:
            return ""

    def query(self, sentence, pattern):
        sentence = sentence.strip() + '\n'  # ensure sentence ends with '\n'
        self.sock.sendall(sentence.encode('utf-8'))
        data = self.sock.recv(1024)
        recv = data
        pattern = "EOS\n$"
        while not re.search(pattern, self._decode(recv)):
            data = self.sock.recv(1024)
            recv = recv + data
        return recv.strip().decode('utf-8')


class PexpectAnalyzer(Analyzer):
    def __init__(self,
                 backend,
                 multithreading=False,
                 server=None,
                 port=None,
                 socket_option=None,
                 command=None,
                 timeout=180,
                 ):
        super().__init__(backend, multithreading, server, port, socket_option, command, timeout)
        if isinstance(self.command, list):
            command = ' '.join(self.command)
        elif isinstance(self.command, str):
            command = self.command
        else:
            assert False, "'command' should be list or str."
        self.subprocess = pexpect.spawnu(command)

    def query(self, input_str, pattern):
        assert self.subprocess
        self.subprocess.sendline(input_str)
        buffer, line = "", ""
        while True:
            line = self.subprocess.readline()
            if re.match(pattern, line.strip()):
                break
            if line.strip() != input_str:
                buffer += line.rstrip() + "\n"

        return buffer


class _Analyzer(Analyzer):
    def __init__(self,
                 backend,
                 multithreading=False,
                 server=None,
                 port=None,
                 socket_option=None,
                 command=None,
                 timeout=180,
                 ):
        super().__init__(backend, multithreading, server, port, socket_option, command, timeout)
        self.subprocess = _Subprocess(self.command, timeout=self.timeout)

    def query(self, input_str, pattern):
        assert self.subprocess
        res = super().query(input_str, pattern)
        return res


class _Subprocess(Subprocess):
    def __init__(self, command, timeout=180):
        super().__init__(command, timeout)

    def query(self, sentence, pattern):
        sentence = sentence.strip() + '\n'  # ensure sentence ends with '\n'
        result = ''
        try:
            self.process.stdin.write(sentence.encode('utf-8'))
            self.process.stdin.flush()
            while True:
                line = self.process.stdout.readline().decode('utf-8').rstrip()
                if re.search(pattern, line):
                    break
                result += line + '\n'
        except BaseException:
            pass

        self.process.stdout.flush()
        return result

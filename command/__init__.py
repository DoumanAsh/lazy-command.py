from os import environ, path
from subprocess import Popen, DEVNULL, TimeoutExpired, PIPE
from shlex import split as shell_split
from collections import namedtuple


Output = namedtuple('Output', 'status stdout stderr')


class Command(object):
    """ Command class wrapper over subprocess.Popen

        To customize command use method chaining.
        Each method returns self except otherwise stated.

        Args:
            command: String with command to run.
    """
    def __init__(self, command):
        """ Initializer.
        """
        self._args = shell_split(command, posix=False)
        self._env = environ.copy()
        self._stderr = None
        self._stdout = None
        self._stdin = None
        self._shell = False
        self._cwd = None
        self._universal_newlines = True

        self._inner = None

    def arg(self, arg):
        """ Adds argument to command.

            Args:
                arg: String with argument.

            Returns:
                self
        """
        self._args.append(arg)

        return self

    def args(self, args):
        """ Adds multiple arguments.

            Args:
                command: Iterable with arguments.

            Returns:
                self
        """
        self._args.extend(args)

        return self

    def binary_mode(self):
        """ Sets binary mode to underlying Popen.

            It means that stdout/stderr/stdin are treated as binary streams
        """
        self._universal_newlines = False

        return self

    def shell(self):
        """ Enables shell mode.

            Command will be passed as single string.
            and shell=True will be passed to underlying Popen

            Returns:
                self
        """
        self._shell = True

        return self

    def cwd(self, cwd):
        """ Sets cwd of command.

            Args:
                cwd: Valid path to existing directory

            Returns:
                self

            Raises:
                ValueError: If cwd is path to non-existing directory.
        """
        if not path.isdir(cwd):
            raise ValueError

        self._cwd = cwd
        return self

    def env(self, **kwargs):
        """ Add environ variables to system environ.

           Args:
               kwargs: Variables to add to command's environment.

           Returns:
               self
        """
        self._env = dict(self._env, **kwargs)
        return self

    def all_pipe(self):
        """ Sets all streams redirection to subprocess.PIPE.
        """
        self.stderr_pipe()
        self.stdout_pipe()
        self.stdin_pipe()
        return self

    def stderr_pipe(self):
        """ Sets stderr redirection to subprocess.PIPE.
        """
        return self.stderr(PIPE)

    def stdout_pipe(self):
        """ Sets stdout redirection to subprocess.PIPE.
        """
        return self.stdout(PIPE)

    def stdin_pipe(self):
        """ Sets stdin redirection to subprocess.PIPE.
        """
        return self.stdin(PIPE)

    def all_null(self):
        """ Sets all streams redirection to NULL.
        """
        self.stderr_null()
        self.stdout_null()
        self.stdin_null()
        return self

    def stderr_null(self):
        """ Sets stderr redirection to NULL.
        """
        return self.stderr(DEVNULL)

    def stdout_null(self):
        """ Sets stdout redirection to NULL.
        """
        return self.stdout(DEVNULL)

    def stdin_null(self):
        """ Sets stdin redirection to NULL.
        """
        return self.stdin(DEVNULL)

    def stderr(self, stderr):
        """ Sets stderr redirection.

            Args:
                stderr: PIPE, DEVNULL,
                        an existing file descriptor (a positive integer),
                        an existing file object, and None.

            Returns:
                self
        """
        self._stderr = stderr
        return self

    def stdout(self, stdout):
        """ Sets stdout redirection.

            Args:
                stdout: PIPE, DEVNULL,
                        an existing file descriptor (a positive integer),
                        an existing file object, and None.

            Returns:
                self
        """
        self._stdout = stdout
        return self

    def stdin(self, stdin):
        """ Sets stdin redirection.

            Args:
                stdin: PIPE, DEVNULL,
                       an existing file descriptor (a positive integer),
                       an existing file object, and None.

            Returns:
                self
        """
        self._stdin = stdin
        return self

    def start(self):
        """ Starts command.

            Returns:
                self
        """
        if self._inner:
            return self

        if self._shell:
            cmd = " ".join(self._args)
        else:
            cmd = self._args

        self._inner = Popen(cmd,
                            env=self._env,
                            shell=self._shell,
                            stdin=self._stdin,
                            stdout=self._stdout,
                            stderr=self._stderr,
                            universal_newlines=self._universal_newlines,
                            cwd=self._cwd)

        return self

    def status(self, timeout=None):
        """ Waits for command to terminate and returns status code.

            Args:
                timeout: Timeout in seconds. Optional. Default None

            Returns:
                None: On timeout.
                int: Return code.

        """
        self.start()
        try:
            return_code = self._inner.wait(timeout)
            self._inner = None
            return return_code
        except TimeoutExpired:
            return None

    def output(self, timeout=None):
        """ Waite for command to finish and collects its output.

            Args:
                timeout: Timeout in seconds. Optional. Default None

            Note:
                In order to return stdout\stderr
                you need to setup PIPE redirection.

            Returns:
                None: On timeout.
                Output: Named tuple with fields status, stdout and stderr.
        """
        self.start()
        try:
            stdout, stderr = self._inner.communicate(timeout=timeout)
            result = Output(self._inner.returncode, stdout, stderr)
            self._inner = None
            return result
        except TimeoutExpired:
            return None

    def poll(self):
        """ Checks if command is running.

            Returns:
                None: Process is not terminated.
                returncode: Return code of command from Popen.

            Note:
                Should be called after start.
        """
        if not self._inner:
            return None

        return self._inner.poll()

    def stop(self):
        """ Terminates command.

            Note:
                Should be called after start.
        """
        if self._inner:
            self._inner.terminate()
            self._inner = None

        return self

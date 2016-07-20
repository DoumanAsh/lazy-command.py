"""
This is a Rust-inspired wrapper over subprocess.Popen

It provides you with Command builder that can be customized via
multiple method chaining.

The Command type acts as a process builder,
providing fine-grained control over how a new process should be spawned.

A default configuration can be generated using Command(program),
where program gives a path to the program or
string with command and its options to run.

Under hood this command is being split by shlex.split()
Additional builder methods allow the configuration to be changed
(for example, by adding arguments) prior to starting it.
"""
from os import environ, path
from subprocess import Popen, DEVNULL, TimeoutExpired, PIPE
from shlex import split as shell_split


class Output(object):
    """ Represents Command's output.

        Note:
            Type of stdout/stderr is determined by command's mode.

        Attributes:
            return_code (int): Return code of Command.
            stdout: Content of stdout. Either bytes or str
            stderr: Content of stdout. Either bytes or str
    """
    def __init__(self, return_code, stdout, stderr):
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr

    def __repr__(self):
        return "Output(code={}, stdout={}, stderr={})".format(
                self.return_code,
                self.stdout.__repr__(),
                self.stderr.__repr__())

    def __str__(self):
        return self.__repr__()

    def __bool__(self):
        return self.is_success()

    def __nonzero__(self):
        return self.is_success()

    def is_success(self):
        """ Returns whether execution of Command has been successful.

            Returns:
                True If return code is zero, False otherwise.
        """
        return self.return_code == 0


class Command(object):
    """ Command class wrapper over subprocess.Popen

        To customize command use method chaining.
        Each method returns self except otherwise stated.

        Args:
            command (str): String with command to run.
                           It is split by shlex.split()
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
                arg (str): String with argument.

            Returns:
                self
        """
        self._args.append(arg)

        return self

    def args(self, args):
        """ Adds multiple arguments.

            Args:
                args (list): Iterable with arguments.

            Returns:
                self
        """
        self._args.extend(args)

        return self

    def binary_mode(self):
        """ Sets binary mode to underlying Popen.

            It means that stdout/stderr/stdin are treated as binary streams

            Returns:
                self
        """
        self._universal_newlines = False

        return self

    def shell(self):
        """ Enables shell mode.

            Command with all arguments is passed as single string.
            and shell=True will be set to underlying Popen

            Returns:
                self
        """
        self._shell = True

        return self

    def cwd(self, cwd):
        """ Sets cwd of command.

            Args:
                cwd (str): Valid path to existing directory

            Returns:
                self

            Raises:
                ValueError: If cwd is path to non-existing directory.
        """
        if not path.isdir(cwd):
            raise ValueError

        self._cwd = cwd
        return self

    def env_clear(self):
        """ Clears all environment variables for command.

            Returns:
                self
        """
        self._env.clear()
        return self

    def env_remove(self, *args):
        """ Remove environ variables from command's environment.

           Args:
               args: List of keys to remove. Should be str.

           Returns:
               self
        """
        for key in args:
            if key in self._env:
                del self._env[key]

        return self

    def env(self, **kwargs):
        """ Add environ variables command's environment.

           Args:
               kwargs: Variables to add to command's environment.

           Returns:
               self
        """
        self._env = dict(self._env, **kwargs)
        return self

    def all_pipe(self):
        """ Sets all streams redirection to subprocess.PIPE.

            Returns:
                self
        """
        return self.stderr_pipe().stdout_pipe().stdin_pipe()

    def stderr_pipe(self):
        """ Sets stderr redirection to subprocess.PIPE.

            Returns:
                self
        """
        return self.stderr(PIPE)

    def stdout_pipe(self):
        """ Sets stdout redirection to subprocess.PIPE.

            Returns:
                self
        """
        return self.stdout(PIPE)

    def stdin_pipe(self):
        """ Sets stdin redirection to subprocess.PIPE.

            Returns:
                self
        """
        return self.stdin(PIPE)

    def all_null(self):
        """ Sets all streams redirection to NULL.

            Returns:
                self
        """
        return self.stderr_null().stdout_null().stdin_null()

    def stderr_null(self):
        """ Sets stderr redirection to NULL.

            Returns:
                self
        """
        return self.stderr(DEVNULL)

    def stdout_null(self):
        """ Sets stdout redirection to NULL.

            Returns:
                self
        """
        return self.stdout(DEVNULL)

    def stdin_null(self):
        """ Sets stdin redirection to NULL.

            Returns:
                self
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

            Note:
                Upon termination underlying Popen is cleared.

            Args:
                timeout (int): Timeout in seconds. Optional. Default None

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
                timeout (int): Timeout in seconds. Optional. Default None

            Note:
                Upon termination underlying Popen is cleared.

            Note:
                By default (i.e. redirection is not set)
                stdin/stdout/stderr are captured.

            Returns:
                None: On timeout.
                Output: Named tuple with fields status, stdout and stderr.
        """
        if self._stderr is None:
            self.stderr_pipe()

        if self._stdout is None:
            self.stdout_pipe()

        if self._stdin is None:
            self.stdin_pipe()

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

        """
        if not self._inner:
            return None

        return self._inner.poll()

    def stop(self):
        """ Terminates command.

            Note:
                Upon termination underlying Popen is cleared.
        """
        if self._inner:
            self._inner.terminate()
            self._inner = None

        return self

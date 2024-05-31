from ctypes import util, cdll, c_char_p, c_int, c_char, c_void_p, c_uint64
import os
import select


MAX_UDP_BULKSIZE = 65535 - 8 - 20


def more_data(pipe_out):
    """Check if there is more data left on the pipe

    :param pipe_out: The os pipe_out
    :rtype: bool
    """
    r, _, _ = select.select([pipe_out], [], [], 0)
    return bool(r)


def read_pipe(pipe_out):
    """Read data on a pipe

    Used to capture stdout data produced by libiperf

    :param pipe_out: The os pipe_out
    :rtype: unicode string
    """
    out = b""
    while more_data(pipe_out):
        out += os.read(pipe_out, 1024)

    return out.decode("utf-8")


def output_to_pipe(pipe_in):
    """Redirects stdout and stderr to a pipe

    :param pipe_out: The pipe to redirect stdout and stderr to
    """
    os.dup2(pipe_in, 1)  # stdout
    # os.dup2(pipe_in, 2)  # stderr


def output_to_screen(stdout_fd, stderr_fd):
    """Redirects stdout and stderr to a pipe

    :param stdout_fd: The stdout file descriptor
    :param stderr_fd: The stderr file descriptor
    """
    os.dup2(stdout_fd, 1)
    # os.dup2(stderr_fd, 2)


class IPerf3(object):
    """The base class used by both the iperf3 :class:`Server` and :class:`Client`

    .. note:: You should not use this class directly
    """

    def __init__(self, role, verbose=True, lib_name=None):
        """Initialise the iperf shared library

        :param role: 'c' = client; 's' = server
        :param verbose: enable verbose output
        :param lib_name: optional name and path for libiperf.so.0 library
        """
        if lib_name is None:
            lib_name = util.find_library("libiperf")
            if lib_name is None:
                # If we still couldn't find it lets try the manual approach
                lib_name = "libiperf.so.0"

        try:
            self.lib = cdll.LoadLibrary(lib_name)
        except OSError:
            raise OSError(
                "Couldn't find shared library {}, is iperf3 installed?".format(lib_name)
            )

        # Set the appropriate C types.
        self.lib.iperf_client_end.restype = c_int
        self.lib.iperf_client_end.argtypes = (c_void_p,)
        self.lib.iperf_free_test.restxpe = None
        self.lib.iperf_free_test.argtypes = (c_void_p,)
        self.lib.iperf_new_test.restype = c_void_p
        self.lib.iperf_new_test.argtypes = None
        self.lib.iperf_defaults.restype = c_int
        self.lib.iperf_defaults.argtypes = (c_void_p,)
        self.lib.iperf_get_test_role.restype = c_char
        self.lib.iperf_get_test_role.argtypes = (c_void_p,)
        self.lib.iperf_set_test_role.restype = None
        self.lib.iperf_set_test_role.argtypes = (
            c_void_p,
            c_char,
        )
        self.lib.iperf_get_test_bind_address.restype = c_char_p
        self.lib.iperf_get_test_bind_address.argtypes = (c_void_p,)
        self.lib.iperf_set_test_bind_address.restype = None
        self.lib.iperf_set_test_bind_address.argtypes = (
            c_void_p,
            c_char_p,
        )
        self.lib.iperf_get_test_server_port.restype = c_int
        self.lib.iperf_get_test_server_port.argtypes = (c_void_p,)
        self.lib.iperf_set_test_server_port.restype = None
        self.lib.iperf_set_test_server_port.argtypes = (
            c_void_p,
            c_int,
        )
        self.lib.iperf_get_test_json_output.restype = c_int
        self.lib.iperf_get_test_json_output.argtypes = (c_void_p,)
        self.lib.iperf_set_test_json_output.restype = None
        self.lib.iperf_set_test_json_output.argtypes = (
            c_void_p,
            c_int,
        )
        self.lib.iperf_get_verbose.restype = c_int
        self.lib.iperf_get_verbose.argtypes = (c_void_p,)
        self.lib.iperf_set_verbose.restype = None
        self.lib.iperf_set_verbose.argtypes = (c_void_p, c_int)
        self.lib.iperf_strerror.restype = c_char_p
        self.lib.iperf_strerror.argtypes = (c_int,)
        self.lib.iperf_get_test_server_hostname.restype = c_char_p
        self.lib.iperf_get_test_server_hostname.argtypes = (c_void_p,)
        self.lib.iperf_set_test_server_hostname.restype = None
        self.lib.iperf_set_test_server_hostname.argtypes = (
            c_void_p,
            c_char_p,
        )
        self.lib.iperf_get_test_protocol_id.restype = c_int
        self.lib.iperf_get_test_protocol_id.argtypes = (c_void_p,)
        self.lib.set_protocol.restype = c_int
        self.lib.set_protocol.argtypes = (
            c_void_p,
            c_int,
        )
        self.lib.iperf_get_test_omit.restype = c_int
        self.lib.iperf_get_test_omit.argtypes = (c_void_p,)
        self.lib.iperf_set_test_omit.restype = None
        self.lib.iperf_set_test_omit.argtypes = (
            c_void_p,
            c_int,
        )
        self.lib.iperf_get_test_duration.restype = c_int
        self.lib.iperf_get_test_duration.argtypes = (c_void_p,)
        self.lib.iperf_set_test_duration.restype = None
        self.lib.iperf_set_test_duration.argtypes = (
            c_void_p,
            c_int,
        )
        self.lib.iperf_get_test_rate.restype = c_uint64
        self.lib.iperf_get_test_rate.argtypes = (c_void_p,)
        self.lib.iperf_set_test_rate.restype = None
        self.lib.iperf_set_test_rate.argtypes = (
            c_void_p,
            c_uint64,
        )
        self.lib.iperf_get_test_blksize.restype = c_int
        self.lib.iperf_get_test_blksize.argtypes = (c_void_p,)
        self.lib.iperf_set_test_blksize.restype = None
        self.lib.iperf_set_test_blksize.argtypes = (
            c_void_p,
            c_int,
        )
        self.lib.iperf_get_test_num_streams.restype = c_int
        self.lib.iperf_get_test_num_streams.argtypes = (c_void_p,)
        self.lib.iperf_set_test_num_streams.restype = None
        self.lib.iperf_set_test_num_streams.argtypes = (
            c_void_p,
            c_int,
        )
        self.lib.iperf_has_zerocopy.restype = c_int
        self.lib.iperf_has_zerocopy.argtypes = None
        self.lib.iperf_set_test_zerocopy.restype = None
        self.lib.iperf_set_test_zerocopy.argtypes = (
            c_void_p,
            c_int,
        )
        self.lib.iperf_get_test_reverse.restype = c_int
        self.lib.iperf_get_test_reverse.argtypes = (c_void_p,)
        self.lib.iperf_set_test_reverse.restype = None
        self.lib.iperf_set_test_reverse.argtypes = (
            c_void_p,
            c_int,
        )
        self.lib.iperf_run_client.restype = c_int
        self.lib.iperf_run_client.argtypes = (c_void_p,)
        self.lib.iperf_run_server.restype = c_int
        self.lib.iperf_run_server.argtypes = (c_void_p,)
        self.lib.iperf_reset_test.restype = None
        self.lib.iperf_reset_test.argtypes = (c_void_p,)

        try:
            # Only available from iperf v3.1 and onwards
            self.lib.iperf_get_test_json_output_string.restype = c_char_p
            self.lib.iperf_get_test_json_output_string.argtypes = (c_void_p,)
        except AttributeError:
            pass

        # The test C struct iperf_test
        self._test = self._new()
        self.defaults()

        # stdout/strerr redirection variables
        self._stdout_fd = os.dup(1)
        self._stderr_fd = os.dup(2)
        self._pipe_out, self._pipe_in = os.pipe()  # no need for pipe write

        # Generic test settings
        self.role = role
        self.json_output = True
        self.verbose = verbose

    def __del__(self):
        """Cleanup the test after the :class:`IPerf3` class is terminated"""
        os.close(self._stdout_fd)
        os.close(self._stderr_fd)
        os.close(self._pipe_out)
        os.close(self._pipe_in)

        try:
            # In the current version of libiperf, the control socket isn't
            # closed on iperf_client_end(), see proposed pull request:
            # https://github.com/esnet/iperf/pull/597
            # Workaround for testing, don't ever do this..:
            #
            # sck=self.lib.iperf_get_control_socket(self._test)
            # os.close(sck)

            self.lib.iperf_client_end(self._test)
            self.lib.iperf_free_test(self._test)
        except AttributeError:
            # self.lib doesn't exist, likely because iperf3 wasn't installed or
            # the shared library libiperf.so.0 could not be found
            pass

    def _new(self):
        """Initialise a new iperf test

        struct iperf_test *iperf_new_test()
        """
        return self.lib.iperf_new_test()

    def defaults(self):
        """Set/reset iperf test defaults."""
        self.lib.iperf_defaults(self._test)

    @property
    def role(self):
        """The iperf3 instance role

        valid roles are 'c'=client and 's'=server

        :rtype: 'c' or 's'
        """
        try:
            self._role = c_char(self.lib.iperf_get_test_role(self._test)).value.decode(
                "utf-8"
            )
        except TypeError:
            self._role = c_char(
                chr(self.lib.iperf_get_test_role(self._test))
            ).value.decode("utf-8")
        return self._role

    @role.setter
    def role(self, role):
        if role.lower() in ["c", "s"]:
            self.lib.iperf_set_test_role(
                self._test, c_char(role.lower().encode("utf-8"))
            )
            self._role = role
        else:
            raise ValueError("Unknown role, accepted values are 'c' and 's'")

    @property
    def bind_address(self):
        """The bind address the iperf3 instance will listen on

        use * to listen on all available IPs
        :rtype: string
        """
        result = c_char_p(self.lib.iperf_get_test_bind_address(self._test)).value
        if result:
            self._bind_address = result.decode("utf-8")
        else:
            self._bind_address = "*"

        return self._bind_address

    @bind_address.setter
    def bind_address(self, address):
        self.lib.iperf_set_test_bind_address(
            self._test, c_char_p(address.encode("utf-8"))
        )
        self._bind_address = address

    @property
    def port(self):
        """The port the iperf3 server is listening on"""
        self._port = self.lib.iperf_get_test_server_port(self._test)
        return self._port

    @port.setter
    def port(self, port):
        self.lib.iperf_set_test_server_port(self._test, int(port))
        self._port = port

    @property
    def json_output(self):
        """Toggles json output of libiperf

        Turning this off will output the iperf3 instance results to
        stdout/stderr

        :rtype: bool
        """
        enabled = self.lib.iperf_get_test_json_output(self._test)

        if enabled:
            self._json_output = True
        else:
            self._json_output = False

        return self._json_output

    @json_output.setter
    def json_output(self, enabled):
        if enabled:
            self.lib.iperf_set_test_json_output(self._test, 1)
        else:
            self.lib.iperf_set_test_json_output(self._test, 0)

        self._json_output = enabled

    @property
    def verbose(self):
        """Toggles verbose output for the iperf3 instance

        :rtype: bool
        """
        enabled = self.lib.iperf_get_verbose(self._test)

        if enabled:
            self._verbose = True
        else:
            self._verbose = False

        return self._verbose

    @verbose.setter
    def verbose(self, enabled):
        if enabled:
            self.lib.iperf_set_verbose(self._test, 1)
        else:
            self.lib.iperf_set_verbose(self._test, 0)
        self._verbose = enabled

    @property
    def _errno(self):
        """Returns the last error ID

        :rtype: int
        """
        return c_int.in_dll(self.lib, "i_errno").value

    @property
    def iperf_version(self):
        """Returns the version of the libiperf library

        :rtype: string
        """
        # TODO: Is there a better way to get the const char than allocating 30?
        VersionType = c_char * 30
        return VersionType.in_dll(self.lib, "version").value.decode("utf-8")

    def _error_to_string(self, error_id):
        """Returns an error string from libiperf

        :param error_id: The error_id produced by libiperf
        :rtype: string
        """
        strerror = self.lib.iperf_strerror
        strerror.restype = c_char_p
        return strerror(error_id).decode("utf-8")

    def run(self):
        """Runs the iperf3 instance.

        This function has to be instantiated by the Client and Server
        instances

        :rtype: NotImplementedError
        """
        raise NotImplementedError

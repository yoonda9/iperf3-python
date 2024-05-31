from iperf.iperf3.test_result import TestResult
from iperf.iperf3._iperf3 import (
    MAX_UDP_BULKSIZE,
    IPerf3,
    output_to_pipe,
    output_to_screen,
    read_pipe,
)


from ctypes import c_char_p
from socket import SOCK_DGRAM, SOCK_STREAM


class Client(IPerf3):
    """An iperf3 client connection.

    This opens up a connection to a running iperf3 server

    Basic Usage::

      >>> import iperf3

      >>> client = iperf3.Client()
      >>> client.duration = 1
      >>> client.server_hostname = '127.0.0.1'
      >>> client.port = 5201
      >>> client.run()
      {'intervals': [{'sum': {...
    """

    def __init__(self, *args, **kwargs):
        """Initialise the iperf shared library"""
        super(Client, self).__init__(role="c", *args, **kwargs)

        # Internal variables
        self._blksize = None
        self._server_hostname = None
        self._port = None
        self._num_streams = None
        self._zerocopy = False
        self._omit = None
        self._duration = None
        self._bandwidth = None
        self._protocol = None

    @property
    def server_hostname(self):
        """The server hostname to connect to.

        Accepts DNS entries or IP addresses.

        :rtype: string
        """
        result = c_char_p(self.lib.iperf_get_test_server_hostname(self._test)).value
        if result:
            self._server_hostname = result.decode("utf-8")
        else:
            self._server_hostname = None
        return self._server_hostname

    @server_hostname.setter
    def server_hostname(self, hostname):
        self.lib.iperf_set_test_server_hostname(
            self._test, c_char_p(hostname.encode("utf-8"))
        )
        self._server_hostname = hostname

    @property
    def protocol(self):
        """The iperf3 instance protocol

        valid protocols are 'tcp' and 'udp'

        :rtype: str
        """
        proto_id = self.lib.iperf_get_test_protocol_id(self._test)

        if proto_id == SOCK_STREAM:
            self._protocol = "tcp"
        elif proto_id == SOCK_DGRAM:
            self._protocol = "udp"

        return self._protocol

    @protocol.setter
    def protocol(self, protocol):
        if protocol == "tcp":
            self.lib.set_protocol(self._test, int(SOCK_STREAM))
        elif protocol == "udp":
            self.lib.set_protocol(self._test, int(SOCK_DGRAM))

            if self.blksize > MAX_UDP_BULKSIZE:
                self.blksize = MAX_UDP_BULKSIZE

        self._protocol = protocol

    @property
    def omit(self):
        """The test startup duration to omit in seconds."""
        self._omit = self.lib.iperf_get_test_omit(self._test)
        return self._omit

    @omit.setter
    def omit(self, omit):
        self.lib.iperf_set_test_omit(self._test, omit)
        self._omit = omit

    @property
    def duration(self):
        """The test duration in seconds."""
        self._duration = self.lib.iperf_get_test_duration(self._test)
        return self._duration

    @duration.setter
    def duration(self, duration):
        self.lib.iperf_set_test_duration(self._test, duration)
        self._duration = duration

    @property
    def bandwidth(self):
        """Target bandwidth in bits/sec"""
        self._bandwidth = self.lib.iperf_get_test_rate(self._test)
        return self._bandwidth

    @bandwidth.setter
    def bandwidth(self, bandwidth):
        self.lib.iperf_set_test_rate(self._test, bandwidth)
        self._bandwidth = bandwidth

    @property
    def blksize(self):
        """The test blksize."""
        self._blksize = self.lib.iperf_get_test_blksize(self._test)
        return self._blksize

    @blksize.setter
    def blksize(self, bulksize):
        # iperf version < 3.1.3 has some weird bugs when bulksize is
        # larger than MAX_UDP_BULKSIZE
        if self.protocol == "udp" and bulksize > MAX_UDP_BULKSIZE:
            bulksize = MAX_UDP_BULKSIZE

        self.lib.iperf_set_test_blksize(self._test, bulksize)
        self._blksize = bulksize

    @property
    def bulksize(self):
        """The test bulksize.

        Deprecated argument, use blksize instead to ensure consistency
        with iperf3 C libary
        """
        # Keeping bulksize argument for backwards compatibility with
        # iperf3-python < 0.1.7
        return self.blksize

    @bulksize.setter
    def bulksize(self, bulksize):
        # Keeping bulksize argument for backwards compatibility with
        # iperf3-python < 0.1.7
        self.blksize = bulksize

    @property
    def num_streams(self):
        """The number of streams to use."""
        self._num_streams = self.lib.iperf_get_test_num_streams(self._test)
        return self._num_streams

    @num_streams.setter
    def num_streams(self, number):
        self.lib.iperf_set_test_num_streams(self._test, number)
        self._num_streams = number

    @property
    def zerocopy(self):
        """Toggle zerocopy.

        Use the sendfile() system call for "Zero Copy" mode. This uses much
        less CPU. This is not supported on all systems.

        **Note** there isn't a hook in the libiperf library for getting the
        current configured value. Relying on zerocopy.setter function

        :rtype: bool
        """
        return self._zerocopy

    @zerocopy.setter
    def zerocopy(self, enabled):
        if enabled and self.lib.iperf_has_zerocopy():
            self.lib.iperf_set_test_zerocopy(self._test, 1)
            self._zerocopy = True
        else:
            self.lib.iperf_set_test_zerocopy(self._test, 0)
            self._zerocopy = False

    @property
    def reverse(self):
        """Toggles direction of test

        :rtype: bool
        """
        enabled = self.lib.iperf_get_test_reverse(self._test)

        if enabled:
            self._reverse = True
        else:
            self._reverse = False

        return self._reverse

    @reverse.setter
    def reverse(self, enabled):
        if enabled:
            self.lib.iperf_set_test_reverse(self._test, 1)
        else:
            self.lib.iperf_set_test_reverse(self._test, 0)

        self._reverse = enabled

    def run(self):
        """Run the current test client.

        :rtype: instance of :class:`TestResult`
        """
        if self.json_output:
            output_to_pipe(self._pipe_in)  # Disable stdout
            error = self.lib.iperf_run_client(self._test)

            if not self.iperf_version.startswith("iperf 3.1"):
                data = read_pipe(self._pipe_out)
                if data.startswith("Control connection"):
                    data = "{" + data.split("{", 1)[1]
            else:
                data = c_char_p(
                    self.lib.iperf_get_test_json_output_string(self._test)
                ).value
                if data:
                    data = data.decode("utf-8")

            output_to_screen(self._stdout_fd, self._stderr_fd)  # enable stdout

            if not data or error:
                data = '{"error": "%s"}' % self._error_to_string(self._errno)

            return TestResult(data)

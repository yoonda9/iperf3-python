import threading
from queue import Queue

from iperf.iperf3._iperf3 import IPerf3, output_to_pipe, output_to_screen, read_pipe
from iperf.iperf3.test_result import TestResult


class Server(IPerf3):
    """An iperf3 server connection.

    This starts an iperf3 server session. The server terminates after each
    succesful client connection so it might be useful to run Server.run()
    in a loop.

    The C function iperf_run_server is called in a seperate thread to make
    sure KeyboardInterrupt(aka ctrl+c) can still be captured

    Basic Usage::

      >>> import iperf3

      >>> server = iperf3.Server()
      >>> server.run()
      {'start': {...
    """

    def __init__(self, *args, **kwargs):
        """Initialise the iperf3 server instance"""
        super(Server, self).__init__(role="s", *args, **kwargs)

    def run(self):
        """Run the iperf3 server instance.

        :rtype: instance of :class:`TestResult`
        """

        def _run_in_thread(self, data_queue):
            """Runs the iperf_run_server

            :param data_queue: thread-safe queue
            """
            output_to_pipe(self._pipe_in)  # disable stdout
            error = self.lib.iperf_run_server(self._test)
            output_to_screen(self._stdout_fd, self._stderr_fd)  # enable stdout

            # TODO json_output_string not available on earlier iperf3 builds
            # have to build in a version check using self.iperf_version
            # The following line should work on later versions:
            # data = c_char_p(
            #    self.lib.iperf_get_test_json_output_string(self._test)
            # ).value
            data = read_pipe(self._pipe_out)

            if not data or error:
                data = '{"error": "%s"}' % self._error_to_string(self._errno)

            self.lib.iperf_reset_test(self._test)
            data_queue.put(data)

        if self.json_output:
            data_queue = Queue()

            t = threading.Thread(target=_run_in_thread, args=[self, data_queue])
            t.daemon = True

            t.start()
            while t.is_alive():
                t.join(0.1)

            return TestResult(data_queue.get())
        else:
            # setting json_output to False will output test to screen only
            self.lib.iperf_run_server(self._test)
            self.lib.iperf_reset_test(self._test)

            return None

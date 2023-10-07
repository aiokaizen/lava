import threading

__all__ = ["AssertNumThreads"]


class AssertNumThreads:
    message = "Actual number of threads ({}) is different than the expected one ({})."

    def __init__(self, expected_threads):
        self.expected_threads = expected_threads

    def __enter__(self):
        self.initial_num_threads = threading.active_count()

    def __exit__(self, exc_type, exc_val, exc_tb):
        actual_num_threads = threading.active_count() - self.initial_num_threads
        assert actual_num_threads == self.expected_threads, self.message.format(
            actual_num_threads, self.expected_threads
        )

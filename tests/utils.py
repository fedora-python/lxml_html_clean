import unittest


def peak_memory_usage(func, *args, **kwargs):
    """
    Monitor the memory usage of a function and return the peak memory used, in MiB.
    """
    try:
        from memory_profiler import memory_usage  # type: ignore
    except ImportError:
        raise unittest.SkipTest("memory-profiler is not available")

    try:
        mem_usage = memory_usage((func, args, kwargs), interval=0.1, timeout=None)
    except MemoryError:
        return float("inf")
    peak_memory = max(mem_usage) - min(mem_usage)
    return peak_memory

"""Bounded prefetch of independent public reads; no change to query contents.

At most two tasks run at once and task launches are spaced by 2.2 seconds.
The existing request helper retains its own post-read pacing and retry backoff.
On any error, stop dispatch, cancel unstarted tasks and let in-flight reads end.
All successful responses use the unchanged raw-cache format and later replay.
"""
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import json
from pathlib import Path
import threading
import time


def prefetch(jobs, invoke, *, workers=2, spacing=2.2, progress_every=20):
    assert 1 <= workers <= 2 and spacing > 0
    jobs = list(jobs)
    pending, completed = set(), 0
    last_launch = float('-inf')
    executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix='public-read')
    def collect(done):
        nonlocal completed
        # Observe every completed error before dispatching another task.
        for future in done:
            future.result()
        pending.difference_update(done)
        completed += len(done)
        if progress_every and done and completed//progress_every > (completed-len(done))//progress_every:
            print('Historical-read prefetch', completed, len(jobs), flush=True)
    try:
        for job in jobs:
            collect({future for future in pending if future.done()})
            while len(pending) >= workers:
                done, _ = wait(pending, return_when=FIRST_COMPLETED)
                collect(done)
            delay = spacing - (time.monotonic() - last_launch)
            if delay > 0:
                time.sleep(delay)
            collect({future for future in pending if future.done()})
            pending.add(executor.submit(invoke, job))
            last_launch = time.monotonic()
        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            collect(done)
    except BaseException:
        for future in pending:
            future.cancel()
        executor.shutdown(wait=True, cancel_futures=True)
        raise
    executor.shutdown(wait=True)
    assert completed == len(jobs)
    return completed


def self_test():
    lock = threading.Lock()
    started, finished = [], []
    active = maximum = 0
    def invoke(job):
        nonlocal active, maximum
        with lock:
            active += 1; maximum = max(maximum, active)
            started.append((job, time.monotonic()))
        time.sleep(.025)
        with lock:
            active -= 1; finished.append(job)
    count = prefetch(range(9), invoke, spacing=.012, progress_every=0)
    assert count == 9 and sorted(finished) == list(range(9))
    assert maximum <= 2 and active == 0
    gaps = [b[1]-a[1] for a,b in zip(started, started[1:])]
    assert min(gaps) >= .010, gaps
    launched = []
    def fail(job):
        launched.append(job)
        if job == 0:
            raise RuntimeError('ARTIFICIAL SOFTWARE TEST FAILURE')
    try:
        prefetch(range(9), fail, spacing=.012, progress_every=0)
    except RuntimeError as error:
        assert str(error) == 'ARTIFICIAL SOFTWARE TEST FAILURE'
    else:
        raise AssertionError('A worker failure was swallowed')
    assert launched == [0], launched
    result = {'status': 'PASS', 'fixture_type': 'ARTIFICIAL SOFTWARE TESTS ONLY',
              'successful_jobs': count, 'maximum_simultaneous_tasks': maximum,
              'minimum_test_launch_spacing_seconds': min(gaps),
              'stop_on_error': True, 'network_requests': 0,
              'production_workers': 2, 'production_task_spacing_seconds': 2.2}
    output = Path(__file__).resolve().parents[1]/'reports/revision6/prefetch_software_tests.json'
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    self_test()

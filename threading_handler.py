import queue
import threading
import traceback


class ThreadingHandler:
    def __init__(self, ui_root, poll_interval_ms=100):
        self.ui_root = ui_root
        self.poll_interval_ms = poll_interval_ms

        self._result_queue = queue.Queue()
        self._polling_active = False
        self._active_workers = 0
        self._lock = threading.Lock()

    def run_task(self, task_func, on_success=None, on_error=None):
        if not callable(task_func):
            raise ValueError("task_func harus callable")

        with self._lock:
            self._active_workers += 1

        worker = threading.Thread(
            target=self._worker,
            args=(task_func, on_success, on_error),
            daemon=True,
        )
        worker.start()

        self._ensure_polling()

    def _worker(self, task_func, on_success, on_error):
        try:
            result = task_func()
            self._result_queue.put(("success", result, on_success))
        except Exception as exc:
            self._result_queue.put(("error", exc, on_error))
        finally:
            with self._lock:
                self._active_workers -= 1

    def _ensure_polling(self):
        if self._polling_active:
            return

        self._polling_active = True
        self.ui_root.after(self.poll_interval_ms, self._poll_results)

    def _poll_results(self):
        while True:
            try:
                status, payload, callback = self._result_queue.get_nowait()
            except queue.Empty:
                break

            if callback is None:
                continue

            try:
                callback(payload)
            except Exception:
                traceback.print_exc()

        with self._lock:
            still_running = self._active_workers > 0

        if still_running or not self._result_queue.empty():
            self.ui_root.after(self.poll_interval_ms, self._poll_results)
            return

        self._polling_active = False

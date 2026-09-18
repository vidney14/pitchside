"""Owns the single active ingestion run and fans its bus events out to
every connected SSE client. One run at a time -- this is a demo, not a
job queue."""
import queue
import threading

from pipeline import bus as B
from pipeline import db
from pipeline.ingest import run_ingestion


class RunManager:
    def __init__(self):
        self.conn = db.connect()
        self.thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self._listeners: list[queue.Queue] = []
        self._lock = threading.Lock()

    def _broadcast(self, msg: dict) -> None:
        for q in list(self._listeners):
            q.put(msg)

    def is_running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def start(self, scenario_ids: list[int], delay: float, provider: str) -> None:
        with self._lock:
            if self.is_running():
                raise RuntimeError("a run is already in progress")
            self.conn.close()
            self.conn = db.connect(fresh=True)
            bus = B.Bus(self.conn)
            bus.subscribe(self._broadcast)
            self.stop_event = threading.Event()
            self.thread = threading.Thread(
                target=run_ingestion,
                args=(self.conn, bus, scenario_ids),
                kwargs={"stop_event": self.stop_event, "delay": delay, "provider": provider},
                daemon=True,
            )
            self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()

    def subscribe(self) -> "queue.Queue":
        q: queue.Queue = queue.Queue()
        self._listeners.append(q)
        return q

    def unsubscribe(self, q: "queue.Queue") -> None:
        if q in self._listeners:
            self._listeners.remove(q)


manager = RunManager()

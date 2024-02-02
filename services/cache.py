import datetime as dt
from threading import Lock


class TimedCache:
    def __init__(self) -> None:
        self.lock = Lock()
        self.cache = {}

    def add(self, key: str, entry) -> None:
        self.lock.acquire()
        current_date = dt.datetime.now()
        self.cache[key] = (entry, current_date)
        self.lock.release()

    def exists(self, key: str) -> bool:
        if key in self.cache:
            self.lock.acquire()
            old_date = self.cache[key][1]
            diff = old_date - dt.datetime.now()
            self.lock.release()
            if diff > dt.timedelta(days=1):
                return False
            else:
                return True

        return False

    def get(self, key: str):
        return self.cache[key][0]

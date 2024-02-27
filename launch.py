import logging
from threading import Thread, Lock
import os
import subprocess
import time
from typing import List, Tuple

logging.basicConfig(
    format='%(asctime)s, %(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO
)


class Assembler:
    def __init__(self) -> None:
        self.filter_threads = None
        self.central_thread = None
        self.wd = os.getcwd()
        self.lock = Lock()
        self.filters: List[Tuple[str, str]] = []

    def launch_central(self):
        self.lock.acquire()
        os.chdir(self.wd)
        os.chdir("central")
        p = subprocess.Popen(["./gradlew clean; ./gradlew build; ./gradlew bootRun --console=plain"], shell=True)
        self.lock.release()
        p.wait()

    def launch_filter(self, path: str, command: str, filename: str):
        self.lock.acquire()
        os.chdir(self.wd)
        os.chdir(path)
        p = subprocess.Popen([command, filename])
        self.lock.release()
        p.wait()

    def run(self):
        self.central_thread = Thread(target=self.launch_central, name="central")
        self.filter_threads = [self.central_thread]
        for f in self.filters:
            filename, lang = f
            match lang:
                case "python":
                    path = "services/"
                    file = filename + ".py"
                    command = "python"
                case _:
                    raise ValueError("Unknown language")
            t = Thread(target=self.launch_filter, args=(path, command, file), name=filename)
            self.filter_threads.append(t)
        for t in self.filter_threads:
            t.start()
            logging.info(f"Starting thread {t.name}")
            time.sleep(2)
        for t in self.filter_threads:
            t.join()


if __name__ == "__main__":
    a = Assembler()
    with open("config.yml", "r") as f:
        reading_filters = False
        for line in f:
            s = line.rstrip()
            if "filters" in s:
                reading_filters = True
                continue
            if reading_filters == True:
                if not s.startswith(" "):
                    reading_filters = False
                    continue
                service_name, lang = s.strip().split(":")
                a.filters.append((service_name, lang))
    try:
        a.run()
    except KeyboardInterrupt:
        logging.info("All services are shutdown")
    except:
        logging.error("Can't launch application")

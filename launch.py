import logging
from threading import Thread, Lock
import os
import subprocess
import time
from typing import Dict, List, Tuple

logging.basicConfig(
    format='%(asctime)s, %(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO
)

class Assembler:
    def __init__(self) -> None:
        self.filter_threads = []
        self.central_thread = None
        self.wd = os.getcwd()
        self.lock = Lock()
        self.filters: List[Tuple[str, str]] = []
        self.threads_started = False
        self.kill = False
        self.process_filter_map: Dict[str, subprocess.Popen] = {}

    def launch_central(self):
        self.lock.acquire()
        os.chdir(self.wd)
        os.chdir("central")
        self.process_filter_map["central"] = subprocess.Popen(["./gradlew clean; ./gradlew build; ./gradlew bootRun --console=plain"], shell=True)
        self.lock.release()
        self.process_filter_map["central"].wait()
        logging.info("Stopped central process")

    def launch_filter(self, path: str, command: str, filename: str):
        self.lock.acquire()
        os.chdir(self.wd)
        os.chdir(path)
        self.process_filter_map[filename] = subprocess.Popen([command, filename])
        self.lock.release()
        self.process_filter_map[filename].wait()
        logging.info(f"Stopped {filename} process")

    def run(self):
        self.central_thread = Thread(target=self.launch_central, name="central")
        self.filter_threads.append(self.central_thread)
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

        logging.info("Started all threads")
        self.threads_started = True

        for t in self.filter_threads:
            t.join()

def check_health(assembler: Assembler):
    while True:
        time.sleep(5)
        if assembler.filter_threads is not None and assembler.threads_started:
            for t in assembler.filter_threads:
                if not t.is_alive():
                    assembler.kill = True
                    logging.info(f"{t.name} thread is dead")
                    return


def main(assembler: Assembler):
    with open("config.yml", "r") as f:
        reading_filters = False
        for line in f:
            s = line.rstrip()
            if "filters" in s:
                reading_filters = True
                continue
            if reading_filters:
                if not s.startswith(" "):
                    reading_filters = False
                    continue
                service_name, lang = s.strip().split(":")
                assembler.filters.append((service_name, lang))

    assembler.run()


if __name__ == "__main__":
    assembler = Assembler()

    main_thread = Thread(target=main, args=(assembler,))
    main_thread.start()

    health_check_thread = Thread(target=check_health, args=(assembler,))
    health_check_thread.start()

    try:
        while True:
            if assembler.kill:
                logging.info("The program is destined to die")
                logging.info("Press ctrl+c to exit...")
                while True:
                    pass

    except KeyboardInterrupt:
        logging.info("All services are shutdown")


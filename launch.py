import logging
from threading import Thread, Lock
import os
import subprocess

class Assembler:
    def __init__(self) -> None:
        pass

        self.wd = os.getcwd()
        self.lock = Lock()
        self.filters = []

    def launch_central(self):
        self.lock.acquire()
        os.chdir(self.wd)
        os.chdir("central")
        p = subprocess.Popen(["./gradlew clean; ./gradlew build; ./gradlew bootRun --console=plain"], shell=True)
        self.lock.release()
        p.wait()

    def launch_filter(self, path: str):
        self.lock.acquire()
        os.chdir(self.wd)
        os.chdir(path)
        p = subprocess.Popen(["python", "main.py"])
        self.lock.release()
        p.wait()


    def run(self):
        self.central_thread = Thread(target=self.launch_central)
        self.filter_threads = [self.central_thread]
        for f in self.filters:
            path = "services/" + f
            t = Thread(target=self.launch_filter, args=(path,))
            self.filter_threads.append(t)
        for t in self.filter_threads:
            t.start()
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
                a.filters.append(s.strip())
    try:
        a.run()
    except KeyboardInterrupt:
        logging.info("All services are shutdown")


from threading import Thread, Lock
from time import sleep
from signal import signal, SIGINT
import os
import subprocess

wd = os.getcwd()
lock = Lock()
filters = []

def launch_central():
    lock.acquire()
    os.chdir(wd)
    os.chdir("central")
    p = subprocess.Popen(["./gradlew clean; ./gradlew build; ./gradlew bootRun --console=plain"], shell=True)
    lock.release()
    p.wait()

def launch_filter(path: str):
    lock.acquire()
    os.chdir(wd)
    os.chdir(path)
    p = subprocess.Popen(["python", "main.py"])
    lock.release()
    p.wait()


def main():
    central_thread = Thread(target=launch_central)
    filter_threads = [central_thread]
    for f in filters:
        path = "filter/" + f
        t = Thread(target=launch_filter, args=(path,))
        filter_threads.append(t)
    for t in filter_threads:
        t.start()
    for t in filter_threads:
        t.join()

if __name__ == "__main__":
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
                filters.append(s.strip())
    main()

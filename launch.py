from threading import Thread
from time import sleep
from signal import signal, SIGINT
import os
import subprocess

wd = os.getcwd()

def launch_central():
    os.chdir("central")
    p = subprocess.Popen(["./gradlew clean; ./gradlew build; ./gradlew bootRun"], shell=True)
    p.wait()



def launch_stock_predict():
    os.chdir(wd)
    os.chdir("filter/stock_predict")
    p = subprocess.Popen(["python", "main.py"])
    p.wait()

def main():
    t1 = Thread(target=launch_central)
    t2 = Thread(target=launch_stock_predict)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

if __name__ == "__main__":
    main()

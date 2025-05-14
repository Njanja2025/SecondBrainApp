import time
from baddy_interface import monitor_tasks

if __name__ == "__main__":
    print("[Baddy] Online and watching for tasks...")
    while True:
        monitor_tasks()
        time.sleep(5)

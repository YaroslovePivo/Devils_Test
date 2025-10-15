
import os
import sys
import subprocess
import time
from datetime import datetime
import shutil
import platform

def install(package):
    try:
        __import__(package)
    except ImportError:
        print(f"📦 Installing missing package: {package} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install("psutil")
import psutil

SYSTEM = platform.system().lower()

if SYSTEM == "windows":
    BASE_LOG_PATH = os.path.expandvars(r"%USERPROFILE%\Desktop")
else:
    BASE_LOG_PATH = "/var/log"

LOG_FILE = os.path.join(BASE_LOG_PATH, "sys_monitor.log")
ALERT_FILE = os.path.join(BASE_LOG_PATH, "sys_alerts.log")
REPORT_FILE = os.path.join(BASE_LOG_PATH, "daily_report.txt")

CPU_THRESHOLD = 80
MEM_THRESHOLD = 90
DISK_THRESHOLD = 85
PACKET_LOSS_THRESHOLD = 0.1
LOG_MAX_SIZE = 1 * 1024 * 1024 * 1024  # 1GB

os.makedirs(BASE_LOG_PATH, exist_ok=True)
for f in [LOG_FILE, ALERT_FILE, REPORT_FILE]:
    if not os.path.exists(f):
        with open(f, "w") as tmp:
            tmp.write(f"Created {f} at {datetime.now()}\n")

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")

def alert(msg):
    print("⚠️ ALERT:", msg)
    with open(ALERT_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")

def rotate_logs():
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > LOG_MAX_SIZE:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive = f"{LOG_FILE}.{ts}"
        shutil.move(LOG_FILE, archive)
        subprocess.run(["gzip", archive])
        log("Rotated log file (>1GB)")

def check_cpu():
    cpu = psutil.cpu_percent(interval=5)
    if cpu > CPU_THRESHOLD:
        alert(f"CPU usage high: {cpu}%")
    return cpu

def check_mem():
    mem = psutil.virtual_memory().percent
    if mem > MEM_THRESHOLD:
        alert(f"Memory usage high: {mem}%")
    return mem

def check_disk():
    disk = psutil.disk_usage("/").percent
    if disk > DISK_THRESHOLD:
        alert(f"Disk usage high: {disk}%")
    return disk

def check_network_loss():
    try:
        if SYSTEM == "windows":
            cmd = ["ping", "-n", "10", "8.8.8.8"]
        else:
            cmd = ["ping", "-c", "10", "8.8.8.8"]

        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.lower()

        import re
        loss = 0.0

        # Чвиндовс
        match = re.search(r"(\d+)%\s*loss", output)
        if match:
            loss = float(match.group(1))
        else:
            # Клинукс
            match = re.search(r"(\d+(?:\.\d+)?)%\s*packet loss", output)
            if match:
                loss = float(match.group(1))

        if loss > PACKET_LOSS_THRESHOLD:
            alert(f"Network packet loss high: {loss}%")

        return loss

    except Exception as e:
        alert(f"Network check failed: {e}")
        return None

def daily_report(cpu, mem, disk, loss):
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} | CPU={cpu}% | MEM={mem}% | DISK={disk}% | LOSS={loss}%\n")

def main():
    rotate_logs()
    cpu = check_cpu()
    mem = check_mem()
    disk = check_disk()
    loss = check_network_loss()
    log(f"CPU={cpu}% | MEM={mem}% | DISK={disk}% | LOSS={loss}%")
    daily_report(cpu, mem, disk, loss)
    print(f"✅ CPU={cpu}% | MEM={mem}% | DISK={disk}% | LOSS={loss}%")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("❌ Stopped by user")
    except Exception as e:
        alert(f"Script error: {e}")

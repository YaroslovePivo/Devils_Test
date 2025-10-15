
import os
import subprocess
from datetime import datetime, timedelta


BASE_BACKUP_DIR = "/home/user/backups"
DB_NAME = "trading_db"
DB_USER = "postgres"
CONFIG_DIR = "/etc/myapp"
LOG_DIR = "/var/log/trading"

# Retention
RETENTION_LOGS = 7      
RETENTION_DB = 30       
RETENTION_MONTHLY = 90  
RETENTION_WAL = 2       

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs(BASE_BACKUP_DIR, exist_ok=True)

full_backup_dir = os.path.join(BASE_BACKUP_DIR, f"db_full_{timestamp}")
print(f"Creating full database backup in {full_backup_dir} ...")
subprocess.run(f"pg_basebackup -U {DB_USER} -D {full_backup_dir} -F tar -z -P", shell=True)

wal_archive_dir = os.path.join(BASE_BACKUP_DIR, "wal_archive")
os.makedirs(wal_archive_dir, exist_ok=True)
print(f"Archiving WAL files to {wal_archive_dir} ...")

config_backup_file = os.path.join(BASE_BACKUP_DIR, f"config_{timestamp}.tar.gz")
print(f"Backing up configs to {config_backup_file} ...")
subprocess.run(f"tar -czf {config_backup_file} -C {CONFIG_DIR} .", shell=True)

log_backup_file = os.path.join(BASE_BACKUP_DIR, f"logs_{timestamp}.tar.gz")
print(f"Backing up logs to {log_backup_file} ...")
subprocess.run(f"tar -czf {log_backup_file} -C {LOG_DIR} .", shell=True)

def rotate_files(pattern, retention_days):
    cutoff = datetime.now() - timedelta(days=retention_days)
    for f in os.listdir(BASE_BACKUP_DIR):
        if f.startswith(pattern):
            full_path = os.path.join(BASE_BACKUP_DIR, f)
            file_time = datetime.fromtimestamp(os.path.getmtime(full_path))
            if file_time < cutoff:
                print(f"Deleting old backup: {full_path}")
                if os.path.isdir(full_path):
                    subprocess.run(f"rm -rf {full_path}", shell=True)
                else:
                    os.remove(full_path)

rotate_files("logs_", RETENTION_LOGS)
rotate_files("db_full_", RETENTION_DB)
rotate_files("config_", RETENTION_DB)
rotate_files("wal_archive", RETENTION_WAL)

print("Backup + WAL archive process completed!")

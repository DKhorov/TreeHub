import os
from datetime import datetime

os.makedirs("log", exist_ok=True)
LOG_FILE = "log/data.log"

def write_log(message: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{now}] {message}\n")

# TreeHub API - Source Code
# This language is Python
# This file is: logapidll.py
# Author: Dmitry Khorov
# GitHub: https://github.com/DKhorov/TreeHub.git

import time
from fastapi import HTTPException
from logapidll import write_log

RATE_LIMIT_WINDOW = 60  
MAX_REQUESTS = 5
request_log = {}

def check_rate_limit(ip: str):
    now = time.time()
    if ip not in request_log:
        request_log[ip] = []
    request_log[ip] = [t for t in request_log[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(request_log[ip]) >= MAX_REQUESTS:
        write_log(f"⚠️ Перегрузка сервера: слишком много регистраций с IP {ip}")
        raise HTTPException(status_code=429, detail="Слишком много запросов, попробуйте позже.")
    request_log[ip].append(now)

# TreeHub API - Source Code
# This language is Python
# This file is: cashdll.py
# Author: Dmitry Khorov
# GitHub: https://github.com/DKhorov/TreeHub.git

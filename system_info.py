import platform
import psutil
from prettytable import PrettyTable

def get_system_info():
    table = PrettyTable()
    table.field_names = ["Параметр", "Значение"]
    table.add_row(["ОС", f"{platform.system()} {platform.release()}"])
    table.add_row(["Версия ОС", platform.version()])
    table.add_row(["Имя устройства", platform.node()])
    table.add_row(["Процессор", platform.processor()])
    table.add_row(["Архитектура", platform.architecture()[0]])
    table.add_row(["Ядер (физических)", psutil.cpu_count(logical=False)])
    table.add_row(["Потоков (логических)", psutil.cpu_count(logical=True)])
    table.add_row(["Использование CPU (%)", psutil.cpu_percent(interval=1)])
    table.add_row(["ОЗУ всего (ГБ)", round(psutil.virtual_memory().total / (1024**3), 2)])
    table.add_row(["ОЗУ доступно (ГБ)", round(psutil.virtual_memory().available / (1024**3), 2)])
    table.add_row(["Диск C всего (ГБ)", round(psutil.disk_usage('/').total / (1024**3), 2)])
    table.add_row(["Диск C свободно (ГБ)", round(psutil.disk_usage('/').free / (1024**3), 2)])
    return table

# TreeHub API - Source Code
# This language is Python
# This file is: system_info.py
# Author: Dmitry Khorov
# GitHub: https://github.com/DKhorov/TreeHub.git

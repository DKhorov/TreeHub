import os
from datetime import datetime
import platform
import psutil
from prettytable import PrettyTable
from art import tprint
from colorama import Fore, Back, Style, init

init(autoreset=True)

from system_info import get_system_info
from shelldll import shell

tprint("TreeHub API")


if os.path.exists("serverdll.py"):

 if os.path.exists("log/data.log"):
    print(Fore.GREEN +"== Файл data.log есть - OK"+Fore.RESET)
    now = datetime.now() 
    with open("log/data.log", "a", encoding="utf-8") as f:
       f.write(f"[{now}] Поиск файла data.log прошла успешно!\n")
 else:
    print(Fore.RED + "Файл data.log есть - NO"+Fore.RESET)
    print(Fore.RED + "Создайте срочно папку log в ней data.log!!!!"+Fore.RESET)
    with open("kernelLog.log", "w", encoding="utf-8") as f:
       f.write("Аварийный лог файл!\n")
       f.write("Поиск файла data.log не нашелся файл! Создайте его в папке log , если папки нет создайте ее\n")


 if os.path.exists("shelldll.py"):
    print(Fore.GREEN +"== Компонент shelldll.py есть - OK"+Fore.RESET)
    now = datetime.now() 
    with open("log/data.log", "a", encoding="utf-8") as f:
       f.write(f"[{now}] Поиск Компонент shelldll.py прошла успешно!\n")
    print("="*20,"="*20)
    print("Операционная система:", platform.system())
    print("Версия ОС:", platform.version())
    print("Архитектура:", platform.architecture())
    print("Имя компьютера:", platform.node())
    print("Процессор:", platform.processor())
    print("Python версия:", platform.python_version())
    print("="*20,"="*20)
    shell()
    
 else:
    print(Fore.RED + "Файл data.log есть - NO"+Fore.RESET)
    print(Fore.RED + "Установите shelldll.py из сайта provinhi.pro/treehub/dll"+Fore.RESET)
   
else:
    print(Fore.RED + "Файл data.log есть - NO"+Fore.RESET)
    print(Fore.RED + "Создайте срочно папку log в ней data.log!!!!"+Fore.RESET)
    with open("kernelLog.log", "w", encoding="utf-8") as f:
       f.write("Аварийный лог файл!\n")
       f.write("Поиск файла data.log не нашелся файл! Создайте его в папке log , если папки нет создайте ее\n")







# TreeHub API - Source Code
# This language is Python
# This file is: server.py
# Author: Dmitry Khorov
# GitHub: https://github.com/DKhorov/TreeHub.git

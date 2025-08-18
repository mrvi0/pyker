#!/usr/bin/env python3
"""
Пример простого бота для демонстрации работы Pyker
"""

import time
import random
import sys
from datetime import datetime

def main():
    print(f"[{datetime.now()}] Бот запущен!")
    print(f"[{datetime.now()}] PID: {os.getpid()}")
    
    counter = 0
    while True:
        try:
            counter += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Имитируем работу бота
            if counter % 10 == 0:
                print(f"[{current_time}] Выполнено {counter} итераций")
            
            # Случайная ошибка для демонстрации
            if random.random() < 0.001:  # 0.1% шанс ошибки
                print(f"[{current_time}] Произошла случайная ошибка!")
                raise Exception("Случайная ошибка для демонстрации")
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            print(f"[{current_time}] Получен сигнал остановки")
            break
        except Exception as e:
            print(f"[{current_time}] Ошибка: {e}")
            time.sleep(5)  # Пауза перед продолжением
    
    print(f"[{datetime.now()}] Бот завершен!")

if __name__ == "__main__":
    import os
    main() 
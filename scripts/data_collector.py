#!/usr/bin/env python3
"""
Пример скрипта для сбора данных
"""

import time
import json
import random
from datetime import datetime
from pathlib import Path

def collect_data():
    """Собирает данные и сохраняет их"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "temperature": random.uniform(20, 30),
        "humidity": random.uniform(40, 80),
        "pressure": random.uniform(1000, 1020)
    }
    return data

def save_data(data, filename="collected_data.json"):
    """Сохраняет данные в файл"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    file_path = data_dir / filename
    
    # Читаем существующие данные
    existing_data = []
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            existing_data = []
    
    # Добавляем новые данные
    existing_data.append(data)
    
    # Сохраняем обратно
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    return len(existing_data)

def main():
    print(f"[{datetime.now()}] Сборщик данных запущен!")
    
    counter = 0
    while True:
        try:
            counter += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Собираем данные
            data = collect_data()
            total_records = save_data(data)
            
            if counter % 5 == 0:
                print(f"[{current_time}] Собрано {counter} записей, всего в файле: {total_records}")
                print(f"[{current_time}] Последние данные: {data}")
            
            time.sleep(2)
            
        except KeyboardInterrupt:
            print(f"[{current_time}] Получен сигнал остановки")
            break
        except Exception as e:
            print(f"[{current_time}] Ошибка: {e}")
            time.sleep(5)
    
    print(f"[{datetime.now()}] Сборщик данных завершен!")

if __name__ == "__main__":
    main() 
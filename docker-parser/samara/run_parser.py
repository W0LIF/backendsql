#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import sys
from universal_parser import UniversalParser
from config_sites import CONFIGURATIONS
from threaded_parser import ThreadedParser

def main(city='piter'):
    print("="*60)
    print(f"ЗАПУСК ПАРСЕРА ДЛЯ {city.upper()}")
    print("="*60)
    
    # Фильтруем конфигурации по городу
    configs_to_parse = {}
    
    if city == 'samara':
        configs_to_parse = {
            name: config for name, config in CONFIGURATIONS.items() 
            if 'samara' in name # Поиск всей самары
        }
    elif city == 'piter':
        configs_to_parse = {
            name: config for name, config in CONFIGURATIONS.items() 
            if name.startswith(('gu_spb', 'gov_spb', 'consultant'))
        }
    elif city == 'moscow':
        # Добавьте конфигурации для Москвы
        pass
    
    if not configs_to_parse:
        print(f"❌ Нет конфигураций для города {city}")
        return
    
    print(f"\nНайдено конфигураций: {len(configs_to_parse)}")
    for name in configs_to_parse:
        print(f"  • {name}")
    
    # Запускаем многопоточный парсинг
    threaded_parser = ThreadedParser(max_workers=3)
    threaded_parser.parse_all_sites(configs_to_parse, city)
    
    print(f"\n{'='*60}")
    print(f"ПАРСИНГ ЗАВЕРШЕН")
    print(f"Данные сохранены в: backend/data/{city}/")
    print(f"{'='*60}")

if __name__ == "__main__":
    # Если передан аргумент, используем его как город
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main('piter')  # По умолчанию Питер
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import sys
from universal_parser import UniversalParser
from config_sites import CONFIGURATIONS

def main(city='moscow'):
    print("="*60)
    print(f"ЗАПУСК ПАРСЕРА ДЛЯ {city.upper()}")
    print("="*60)
    
    # Берем все конфигурации (они уже только для Москвы)
    configs_to_parse = CONFIGURATIONS
    
    if not configs_to_parse:
        print(f"❌ Нет конфигураций для города {city}")
        return
    
    print(f"\nНайдено конфигураций: {len(configs_to_parse)}")
    for name in configs_to_parse:
        print(f"  • {name}")
    
    # Создаем экземпляр парсера
    parser = UniversalParser()
    
    # Парсим каждый сайт последовательно
    for site_name, config in configs_to_parse.items():
        print(f"\n{'='*60}")
        print(f"ПАРСИНГ: {site_name}")
        print(f"{'='*60}")
        
        try:
            parser.parse_site(config, city)
        except Exception as e:
            print(f"❌ Ошибка при парсинге {site_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"ПАРСИНГ ЗАВЕРШЕН")
    print(f"Данные сохранены в: data/{city}/")
    print(f"{'='*60}")

if __name__ == "__main__":
    # Если передан аргумент, используем его как город
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main('moscow')  # По умолчанию Москва
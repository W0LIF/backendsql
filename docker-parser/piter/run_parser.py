#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import json
from universal_parser import UniversalParser
from config_sites import CONFIGURATIONS

def parse_multipage_site(parser, config, city='piter'):
    """Парсит многостраничный сайт"""
    all_items = []
    base_url = config['url']
    base_prefix = config['output_prefix']
    start_page = config.get('start_page', 1)
    end_page = config.get('end_page', 1)
    
    site_name = [name for name, cfg in CONFIGURATIONS.items() if cfg == config][0]
    print(f"\n{'='*60}")
    print(f"Парсинг многостраничного сайта: {site_name}")
    print(f"Страницы: {start_page}-{end_page}")
    print(f"{'='*60}")
    
    for page_num in range(start_page, end_page + 1):
        print(f"\n--- Страница {page_num}/{end_page} ---")
        
        page_config = {
            'url': f"{base_url}{page_num}",
            'output_prefix': f"{base_prefix}_{page_num}",
            'list_selectors': config['list_selectors'],
            'content_selectors': config.get('content_selectors', [])
        }
        
        try:
            items = parser.parse_site(page_config, city=city)
            for item in items:
                item['source_page'] = page_num
                item['site'] = site_name
            all_items.extend(items)
            print(f"✓ Страница {page_num}: {len(items)} элементов")
        except Exception as e:
            print(f"✗ Ошибка на странице {page_num}: {e}")
        
        time.sleep(2)
    
    # Сохраняем все страницы в один общий файл
    if all_items:
        json_filename = f"backend/data/{city}/{base_prefix}_ALL.json"
        os.makedirs(os.path.dirname(json_filename), exist_ok=True)
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(all_items, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Всего спарсено страниц: {len(all_items)}")
        print(f"✅ Общий файл: {json_filename}")
    
    return all_items

def main():
    print("="*60)
    print("ЗАПУСК ПАРСЕРА ДЛЯ САНКТ-ПЕТЕРБУРГА")
    print("="*60)
    
    parser = UniversalParser()
    city = 'piter'  # Фиксированный город
    
    total_sites = 0
    total_items = 0
    
    # Парсим все сайты из конфигурации
    for site_name, config in CONFIGURATIONS.items():
        # Проверяем, многостраничный ли сайт
        if config.get('multiple_pages', False):
            # Обрабатываем многостраничный сайт
            items = parse_multipage_site(parser, config, city)
            total_sites += 1
            total_items += len(items)
        else:
            # Обычный сайт
            print(f"\n{'#'*60}")
            print(f"Сайт: {site_name}")
            print(f"{'#'*60}")
            
            try:
                items = parser.parse_site(config, city=city)
                total_sites += 1
                total_items += len(items)
                print(f"✓ Получено элементов: {len(items)}")
            except Exception as e:
                print(f"✗ ОШИБКА: {e}")
            
            time.sleep(3)
    
    print(f"\n{'='*60}")
    print(f"ПАРСИНГ ЗАВЕРШЕН")
    print(f"Обработано сайтов: {total_sites}")
    print(f"Всего элементов: {total_items}")
    print(f"Данные сохранены в: backend/data/{city}/")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
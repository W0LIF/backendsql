#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import time
import sys
from run_parser import main as run_parser
from threaded_parser import ThreadedParser

def start_background_parsing(interval_seconds: int = 3600, run_once=False, city='piter'):
    """Запускает фоновый поток с парсером"""
    def _target():
        cycle_count = 0
        while True:
            cycle_count += 1
            try:
                print(f"\n[background_parser] === Цикл парсинга #{cycle_count} для города {city} ===")
                start_time = time.time()
                
                # Запускаем парсинг
                if city == 'samara':
                    # Для Самары используем многопоточность
                    from config_sites import CONFIGURATIONS
                    samara_configs = {
                        name: config for name, config in CONFIGURATIONS.items() 
                        if name.startswith('mfc_samara')
                    }
                    threaded_parser = ThreadedParser(max_workers=3)
                    threaded_parser.parse_all_sites(samara_configs, city)
                else:
                    # Для других городов обычный парсинг
                    run_parser()
                
                elapsed = time.time() - start_time
                print(f"[background_parser] Цикл завершен за {elapsed:.1f} секунд")
                
            except Exception as e:
                print(f"[background_parser] Критическая ошибка: {e}")
            
            if run_once:
                break
            
            print(f"[background_parser] Следующий цикл через {interval_seconds} секунд")
            time.sleep(interval_seconds)

    th = threading.Thread(target=_target, daemon=True)
    th.start()
    return th

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Фоновый парсер сайтов')
    parser.add_argument('--interval', type=int, default=3600, 
                       help='Интервал между циклами парсинга в секундах')
    parser.add_argument('--run_once', action='store_true', 
                       help='Запустить один цикл и завершиться')
    parser.add_argument('--city', type=str, default='piter',
                       help='Город для парсинга (piter/samara/moscow)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("ЗАПУСК ФОНОВОГО ПАРСЕРА")
    print(f"Город: {args.city}")
    print(f"Интервал: {args.interval} сек")
    print(f"Режим: {'однократный' if args.run_once else 'постоянный'}")
    print("="*60)
    
    start_background_parsing(
        interval_seconds=args.interval, 
        run_once=args.run_once,
        city=args.city
    )
    
    if not args.run_once:
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n[background_parser] Остановлен пользователем")
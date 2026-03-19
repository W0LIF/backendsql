import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from universal_parser import UniversalParser

class ThreadedParser:
    """Многопоточный парсер для ускорения работы"""
    
    def __init__(self, max_workers=3):
        self.max_workers = max_workers
        self.parser = UniversalParser()
        self.results = {}
        self.errors = {}
        
    def parse_site_task(self, site_name, config, city):
        """Задача для парсинга одного сайта"""
        try:
            print(f"\n[Поток {threading.current_thread().name}] Начинаю: {site_name} для города {city}")
            start_time = time.time()
            
            # Создаем новый экземпляр парсера для каждого потока
            parser = UniversalParser()
            
            # Вызываем основной метод парсинга
            items = parser.parse_site(config, city=city)
            
            elapsed = time.time() - start_time
            print(f"[Поток] ✅ {site_name}: {len(items)} элементов за {elapsed:.1f}с")
            
            return {
                'site_name': site_name,
                'items': items,
                'success': True,
                'count': len(items)
            }
        except Exception as e:
            print(f"[Поток] ❌ {site_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'site_name': site_name,
                'error': str(e),
                'success': False
            }
    
    def parse_all_sites(self, configurations, city='piter'):
        """Парсит все сайты в многопоточном режиме"""
        print(f"\n{'='*60}")
        print(f"МНОГОПОТОЧНЫЙ ПАРСИНГ ДЛЯ {city.upper()}")
        print(f"Потоков: {self.max_workers}")
        print(f"Сайтов: {len(configurations)}")
        print(f"{'='*60}")
        
        # УБРАНА ФИЛЬТРАЦИЯ: Берем все конфигурации, переданные в метод
        sites_to_parse = configurations
        
        if not sites_to_parse:
            print("Нет сайтов для парсинга")
            return {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_site = {}
            for site_name, config in sites_to_parse.items():
                future = executor.submit(
                    self.parse_site_task, 
                    site_name, 
                    config, 
                    city
                )
                future_to_site[future] = site_name
            
            for future in as_completed(future_to_site):
                result = future.result()
                if result['success']:
                    self.results[result['site_name']] = result['items']
                else:
                    self.errors[result['site_name']] = result['error']
        
        self._print_statistics()
        return self.results
    
    def _print_statistics(self):
        """Выводит статистику выполнения"""
        print(f"\n{'='*60}")
        print(f"СТАТИСТИКА ВЫПОЛНЕНИЯ")
        print(f"{'='*60}")
        
        successful = len(self.results)
        failed = len(self.errors)
        total_items = sum(len(items) for items in self.results.values())
        
        print(f"✅ Успешно: {successful} сайтов")
        print(f"❌ Ошибок: {failed} сайтов")
        print(f"📊 Всего элементов: {total_items}")
        
        if self.results:
            print(f"\nСохраненные файлы:")
            for site_name in self.results:
                print(f"  • {site_name}.json")
        
        if self.errors:
            print(f"\nОшибки:")
            for site, error in self.errors.items():
                print(f"  • {site}: {error}")
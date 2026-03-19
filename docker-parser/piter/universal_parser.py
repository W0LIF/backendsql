import requests
from bs4 import BeautifulSoup
import json
import time
import os
from urllib.parse import urljoin

class UniversalParser:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _make_request_with_retry(self, url, max_retries=3):
        """Выполняет запрос с повторными попытками при таймауте"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                return response
            except requests.exceptions.Timeout:
                print(f"Таймаут запроса (попытка {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    raise
            except requests.exceptions.RequestException as e:
                print(f"Ошибка запроса: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    raise
        return None

    def _parse_list(self, url, selectors):
        """Парсит список элементов с главной страницы"""
        try:
            print(f"Загружаем страницу: {url}")
            response = self._make_request_with_retry(url)
            if not response or response.status_code != 200:
                print(f"Ошибка: статус код {getattr(response, 'status_code', 'неизвестен')} для {url}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for selector_config in selectors:
                selector = selector_config['selector']
                elements = soup.select(selector)
                if elements:
                    print(f"Найдено {len(elements)} элементов с селектором: {selector}")
                    items = []
                    for element in elements:
                        item_data = {}
                        
                        for field, field_selector in selector_config['fields'].items():
                            try:
                                if isinstance(field_selector, str) and '@' in field_selector:
                                    if field_selector.startswith('@'):
                                        attr_name = field_selector[1:]
                                        value = element.get(attr_name, '')
                                        item_data[field] = value.strip() if value else ''
                                    else:
                                        sel, attr_name = field_selector.split('@', 1)
                                        target_element = element.select_one(sel)
                                        if target_element:
                                            value = target_element.get(attr_name, '')
                                            item_data[field] = value.strip() if value else ''
                                        else:
                                            item_data[field] = ''
                                else:
                                    if field_selector == '':
                                        value = element.get_text(strip=True)
                                        item_data[field] = value
                                    else:
                                        target_element = element.select_one(field_selector)
                                        if target_element:
                                            value = target_element.get_text(strip=True)
                                            item_data[field] = value
                                        else:
                                            item_data[field] = ''
                            except Exception as e:
                                print(f"Ошибка при извлечении поля {field}: {e}")
                                item_data[field] = ''
                        
                        if 'link' in item_data and item_data['link']:
                            if not item_data['link'].startswith('http'):
                                item_data['link'] = urljoin(url, item_data['link'])
                        
                        if item_data.get('title') and item_data.get('link'):
                            items.append(item_data)
                            print(f"  Добавлен элемент: {item_data['title'][:50]}...")
                    
                    if items:
                        return items
            
            print("Не найдено элементов с указанными селекторами")
            return []
            
        except Exception as e:
            print(f"Ошибка при парсинге списка: {e}")
            return []

    def _parse_content(self, url, selectors):
        """Парсит контент с внутренней страницы"""
        try:
            print(f"  Загружаем контент с: {url}")
            response = self._make_request_with_retry(url)
            if not response or response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join([elem.get_text(strip=True) for elem in elements])
                    if len(content) > 50:
                        return content[:20000]
            
            paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            return content[:20000] if content else None
            
        except Exception as e:
            print(f"  Ошибка при загрузке контента: {str(e)}")
            return None

    def parse_site(self, config, city='piter'):
        """Основной метод парсинга по конфигурации
        Args:
            config: словарь с конфигурацией сайта
            city: название города для сохранения (по умолчанию 'piter')
        """
        url = config['url']
        list_selectors = config['list_selectors']
        content_selectors = config.get('content_selectors', [])
        output_prefix = config['output_prefix']
        
        print(f"\n{'='*60}")
        print(f"Парсинг: {output_prefix}")
        print(f"URL: {url}")
        print(f"Город: {city}")
        print(f"{'='*60}")
        
        # Парсим список элементов
        items = self._parse_list(url, list_selectors)
        
        # Если нужно парсить контент
        if content_selectors and items:
            detailed_items = []
            for i, item in enumerate(items):
                if 'link' in item and item['link']:
                    print(f"  Парсим контент элемента {i+1}/{len(items)}...")
                    content = self._parse_content(item['link'], content_selectors)
                    if content:
                        item['content'] = content
                    time.sleep(1)
                detailed_items.append(item)
            items = detailed_items
        
        # Сохраняем результаты
        if items:
            self._save_results(items, output_prefix, city)
        
        return items

    def _save_results(self, items, prefix, city='piter'):
        if not items:
            print("Нет данных для сохранения")
            return

        script_dir = os.path.dirname(os.path.abspath(__file__)) 
    
        
        project_root = os.path.abspath(os.path.join(script_dir, "..", "..")) 
        target_dir = os.path.join(project_root, "data", city)
        
        json_filename = os.path.join(target_dir, f"{prefix}.json")
        
        os.makedirs(target_dir, exist_ok=True)
        
        print(f"Сохраняем в: {json_filename}")
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Сохранено {len(items)} элементов в {json_filename}")
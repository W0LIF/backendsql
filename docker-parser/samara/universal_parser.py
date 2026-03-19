#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re
import hashlib
from urllib.parse import urljoin, urlparse
from datetime import datetime

class UniversalParser:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.visited_urls = set()
        self.items_count = 0
        self.base_url = "https://www.culture.ru"
        self.site_type = 'unknown'

    def _make_request_with_retry(self, url, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                if response.status_code == 200:
                    return response
                print(f"  Статус код {response.status_code} для {url}")
            except Exception as e:
                print(f"  Ошибка запроса {url}: {e}")
            time.sleep(1)
        return None

    def _should_parse_url(self, url, config):
        parsed = urlparse(url)
        if 'allowed_domains' in config:
            if not any(domain in parsed.netloc for domain in config['allowed_domains']):
                return False
        
        path = parsed.path
        if 'url_patterns' in config:
            if not any(re.search(p, path) for p in config['url_patterns']):
                return False
        if 'ignore_patterns' in config:
            if any(re.search(p, path) for p in config['ignore_patterns']):
                return False
        return True

    def _extract_list_items(self, soup, config, current_url):
        """Извлекает отдельные элементы со страницы списка (для kassy.ru)"""
        items = []
        
        # Специальная обработка для kassy.ru - страницы списков событий
        if 'kassy.ru' in current_url and ('/events/' in current_url or '/range-' in current_url):
            # Ищем все элементы li внутри ul.events
            event_items = soup.select('ul.events > li')
            print(f"  [kassy.ru] Найдено {len(event_items)} событий на странице")
            
            for event_li in event_items:
                try:
                    item = {}
                    
                    # Заголовок и ссылка
                    title_elem = event_li.select_one('h2 a.event_link')
                    if title_elem:
                        item['title'] = title_elem.get_text(strip=True)
                        href = title_elem.get('href')
                        if href:
                            item['link'] = urljoin('https://samara.kassy.ru', href)
                            if hasattr(self, 'urls_to_visit'):
                                self.urls_to_visit.add(item['link'])
                    
                    # Категория
                    category_elem = event_li.select_one('.announce a[href^="/events/"]')
                    if category_elem:
                        item['category'] = category_elem.get_text(strip=True)
                    
                    # Возрастное ограничение
                    age_elem = event_li.select_one('.RARS')
                    if age_elem:
                        item['age_restriction'] = age_elem.get_text(strip=True)
                    
                    # Место проведения и дата
                    venue_elem = event_li.select_one('p.venue')
                    if venue_elem:
                        venue_text = venue_elem.get_text(" ", strip=True)
                        # Парсим место и дату
                        venue_parts = venue_text.split(',')
                        if len(venue_parts) > 0:
                            item['venue'] = venue_parts[0].strip()
                        if len(venue_parts) > 1:
                            date_text = venue_parts[1].strip()
                            # Извлекаем дату и время
                            date_match = re.search(r'(\d+\s+\S+\s+\d{4})\s+(\d{2}:\d{2})', date_text)
                            if date_match:
                                item['event_date'] = date_match.group(1)
                                item['event_time'] = date_match.group(2)
                    
                    # Описание
                    desc_elem = event_li.select_one('p.fw-light')
                    if desc_elem:
                        item['description'] = desc_elem.get_text(strip=True)
                    
                    # Цена
                    price_elem = event_li.select_one('.price_line p')
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        price_match = re.search(r'([\d\s]+)\s*—\s*([\d\s]+)', price_text)
                        if price_match:
                            item['price_from'] = int(price_match.group(1).replace(' ', ''))
                            item['price_to'] = int(price_match.group(2).replace(' ', ''))
                        else:
                            price_single = re.search(r'([\d\s]+)', price_text)
                            if price_single:
                                item['price'] = int(price_single.group(1).replace(' ', ''))
                    
                    # Статус (перенос и т.д.)
                    alert_elem = event_li.select_one('.alert-danger')
                    if alert_elem:
                        item['status'] = alert_elem.get_text(strip=True)
                    
                    if item.get('title'):  # Сохраняем только если есть заголовок
                        items.append(item)
                        
                except Exception as e:
                    print(f"  [kassy.ru] Ошибка парсинга элемента: {e}")
                    continue
        
        return items

    def _extract_content(self, soup, config):
        """Извлечение контента - только для страниц, где нет списков"""
        content = {}
        min_length = config.get('min_content_length', 100)
        
        # Оригинальные селекторы
        for selector in config.get('content_selectors', []):
            try:
                elements = soup.select(selector)
                if elements:
                    all_text = []
                    for element in elements:
                        for tag in element.select('script, style, nav, header, footer, .t282, .t228, .t190, .t381'):
                            tag.decompose()
                        
                        text = element.get_text(" ", strip=True)
                        if len(text) > min_length:
                            all_text.append(text)
                    
                    if all_text:
                        content['main_content'] = '\n\n'.join(all_text)[:100000]
                        print(f"  [DEBUG] Найден контент по селектору '{selector}': {sum(len(t) for t in all_text)} символов")
                        return content
            except Exception as e:
                continue
        
        return content

    def _extract_from_json(self, soup, config, current_url):
        """УНИВЕРСАЛЬНЫЙ метод извлечения данных из JSON для culture.ru"""
        items = []
        
        for selector_config in config.get('list_selectors', []):
            if selector_config.get('type') == 'json':
                
                # ========== ОБРАБОТКА CULTURE.RU (__NEXT_DATA__) ==========
                if 'culture.ru' in current_url:
                    script_tag = soup.select_one('script#__NEXT_DATA__[type="application/json"]')
                    if script_tag and script_tag.string:
                        try:
                            json_data = json.loads(script_tag.string)
                            
                            extract_path = selector_config.get('extract', '')
                            if extract_path:
                                parts = extract_path.split('.')
                                data = json_data
                                for part in parts:
                                    if isinstance(data, dict):
                                        data = data.get(part, {})
                                    elif isinstance(data, list) and part.isdigit():
                                        idx = int(part)
                                        data = data[idx] if idx < len(data) else {}
                                    else:
                                        data = None
                                        break
                            else:
                                data = json_data
                            
                            if isinstance(data, list):
                                print(f"  [culture.ru JSON] Найдено {len(data)} элементов")
                                for item_data in data:
                                    if not isinstance(item_data, dict):
                                        continue
                                        
                                    item = {}
                                    for field_name, field_config in selector_config['fields'].items():
                                        if field_name == 'link' and isinstance(field_config, dict):
                                            if 'template' in field_config and 'fields' in field_config:
                                                template = field_config['template']
                                                field_values = {}
                                                for f in field_config['fields']:
                                                    if f in item_data:
                                                        val = item_data[f]
                                                        field_values[f] = val if val is not None else ''
                                                try:
                                                    relative_link = template.format(**field_values)
                                                    item['link'] = urljoin(self.base_url, relative_link)
                                                    if hasattr(self, 'urls_to_visit'):
                                                        self.urls_to_visit.add(item['link'])
                                                except:
                                                    item['link'] = ''
                                        elif isinstance(field_config, str):
                                            if field_config in item_data:
                                                item[field_name] = item_data[field_config]
                                            elif '.' in field_config:
                                                value = item_data
                                                for key in field_config.split('.'):
                                                    if isinstance(value, dict):
                                                        value = value.get(key, '')
                                                    elif isinstance(value, list) and key.isdigit():
                                                        idx = int(key)
                                                        value = value[idx] if idx < len(value) else ''
                                                    else:
                                                        value = ''
                                                        break
                                                item[field_name] = value
                                    
                                    if item and item.get('title'):
                                        items.append(item)
                                
                                return items
                                
                        except Exception as e:
                            print(f"  [culture.ru WARN] Ошибка парсинга JSON: {e}")
        
        return items

    def _extract_event_details_culture(self, soup, url):
        """СПЕЦИАЛЬНО для culture.ru - извлекает детали со страницы события"""
        if 'culture.ru' not in url:
            return {}
            
        details = {
            'description': '',
            'start_date': '',
            'end_date': '',
            'display_date': '',
            'age_restriction': '',
            'contact_info': {}
        }
        
        # Пробуем из JSON
        script_tag = soup.select_one('script#__NEXT_DATA__[type="application/json"]')
        if script_tag and script_tag.string:
            try:
                json_data = json.loads(script_tag.string)
                if 'props' in json_data and 'pageProps' in json_data['props']:
                    props = json_data['props']['pageProps']
                    
                    if 'description' in props and props['description']:
                        details['description'] = props['description']
                    elif 'text' in props and props['text']:
                        details['description'] = props['text']
                    
                    if 'age_restriction' in props:
                        details['age_restriction'] = props['age_restriction']
                        
            except Exception:
                pass
        
        return details

    def _save_item_to_file(self, item, config, city):
        """Сохранение элемента в файл"""
        # Поднимаемся на уровень вверх (из папки samara в docker-parser) и затем в data/город
        base_dir = os.path.join("..", "data", city)
        
        # Создаем папку, если её нет
        os.makedirs(base_dir, exist_ok=True)
        
        # Создаем ID для файла
        if 'link' in item and item['link']:
            url_id = hashlib.md5(item['link'].encode()).hexdigest()[:8]
        elif 'url' in item:
            url_id = hashlib.md5(item['url'].encode()).hexdigest()[:8]
        else:
            url_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        
        # Очищаем заголовок для имени файла
        title = item.get('title', 'untitled')
        if isinstance(title, str):
            clean_title = re.sub(r'[^\w\s-]', '', title)[:30].strip().replace(' ', '_')
        else:
            clean_title = 'untitled'
        
        # Добавляем дату если есть для уникальности
        date_suffix = ''
        if 'event_date' in item:
            date_suffix = '_' + re.sub(r'\s+', '_', item['event_date'])
        
        filename = os.path.join(base_dir, f"{config['output_prefix']}_{clean_title}{date_suffix}_{url_id}.json")
        
        # Добавляем метаданные
        item['city'] = city
        item['site'] = config.get('output_prefix', 'unknown')
        item['parsed_timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(item, f, ensure_ascii=False, indent=2)
            self.items_count += 1
            print(f"  [SAVE] ✓ Сохранено: {filename}")
        except Exception as e:
            print(f"  [ERROR] Не удалось сохранить файл: {e}")

    def parse_site_recursive(self, url, config, city='piter', depth=0):
        if depth > config.get('max_depth', 2) or url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        print(f"{'  ' * depth}[Глубина {depth}] Анализ: {url}")
        
        response = self._make_request_with_retry(url)
        if not response:
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ========== СПЕЦИАЛЬНАЯ ОБРАБОТКА ДЛЯ KASSY.RU ==========
        if 'kassy.ru' in url:
            # Извлекаем отдельные события со страницы списка
            list_items = self._extract_list_items(soup, config, url)
            
            if list_items:
                print(f"  [kassy.ru] Сохраняю {len(list_items)} отдельных событий")
                for item in list_items:
                    self._save_item_to_file(item, config, city)
                
                # Не сохраняем основную страницу как контент
                return
            
            # Если это не страница списка (детальная страница события)
            elif re.search(r'/events/[^/]+/\d+-[^/]+/$', url):
                # Извлекаем детальную информацию о событии
                title_elem = soup.select_one('h1') or soup.select_one('title')
                title = title_elem.get_text(strip=True) if title_elem else url
                
                # Извлекаем описание
                desc_elem = soup.select_one('p.fw-light')
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                
                # Извлекаем возраст
                age_elem = soup.select_one('.RARS')
                age = age_elem.get_text(strip=True) if age_elem else ''
                
                # Извлекаем venue и дату
                venue_elem = soup.select_one('p.venue')
                venue = ''
                event_date = ''
                event_time = ''
                if venue_elem:
                    venue_text = venue_elem.get_text(" ", strip=True)
                    venue_parts = venue_text.split(',')
                    if len(venue_parts) > 0:
                        venue = venue_parts[0].strip()
                    if len(venue_parts) > 1:
                        date_text = venue_parts[1].strip()
                        date_match = re.search(r'(\d+\s+\S+\s+\d{4})\s+(\d{2}:\d{2})', date_text)
                        if date_match:
                            event_date = date_match.group(1)
                            event_time = date_match.group(2)
                
                # Извлекаем цену
                price_elem = soup.select_one('.price_line p')
                price_from = None
                price_to = None
                price = None
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price_match = re.search(r'([\d\s]+)\s*—\s*([\d\s]+)', price_text)
                    if price_match:
                        price_from = int(price_match.group(1).replace(' ', ''))
                        price_to = int(price_match.group(2).replace(' ', ''))
                    else:
                        price_single = re.search(r'([\d\s]+)', price_text)
                        if price_single:
                            price = int(price_single.group(1).replace(' ', ''))
                
                item = {
                    'url': url,
                    'title': title,
                    'description': description,
                    'age_restriction': age,
                    'venue': venue,
                    'event_date': event_date,
                    'event_time': event_time,
                }
                
                if price_from and price_to:
                    item['price_from'] = price_from
                    item['price_to'] = price_to
                elif price:
                    item['price'] = price
                
                self._save_item_to_file(item, config, city)
                return
        
        # ========== ОБРАБОТКА CULTURE.RU (JSON) ==========
        json_items = self._extract_from_json(soup, config, url)
        if json_items:
            for item in json_items:
                self._save_item_to_file(item, config, city)
            return
        
        # ========== ОБРАБОТКА ДРУГИХ САЙТОВ (оригинальная логика) ==========
        content = self._extract_content(soup, config)
        if content:
            title_elem = soup.select_one('h1') or soup.select_one('title')
            title = title_elem.get_text(strip=True) if title_elem else url
            
            item = {
                'url': url,
                'title': title,
                'main_content': content.get('main_content', '')
            }
            
            # Дополнительно для culture.ru
            if 'culture.ru' in url and '/events/' in url:
                details = self._extract_event_details_culture(soup, url)
                item.update(details)
            
            self._save_item_to_file(item, config, city)

        # Рекурсивный обход ссылок
        if depth < config.get('max_depth', 2):
            links = set()
            
            for sel in config.get('list_selectors', []):
                if sel.get('type') == 'json':
                    continue
                    
                for element in soup.select(sel['selector']):
                    href = element.get('href') if element.name == 'a' else (element.find('a').get('href') if element.find('a') else None)
                    if href:
                        full_url = urljoin(url, href)
                        if self._should_parse_url(full_url, config):
                            links.add(full_url)
            
            if hasattr(self, 'urls_to_visit') and self.urls_to_visit:
                links.update(self.urls_to_visit)
                self.urls_to_visit.clear()
            
            for link in links:
                time.sleep(0.3)
                self.parse_site_recursive(link, config, city, depth + 1)

    def parse_site(self, config, city='piter'):
        self.visited_urls.clear()
        self.items_count = 0
        
        if 'culture.ru' in config.get('url', ''):
            self.urls_to_visit = set()
        
        if config.get('recursive', False):
            start_urls = config.get('start_urls', [config['url']])
            for start_url in start_urls:
                self.parse_site_recursive(start_url, config, city)
            return [None] * self.items_count
        else:
            response = self._make_request_with_retry(config['url'])
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                content = self._extract_content(soup, config)
                if content:
                    item = {
                        'url': config['url'], 
                        'title': config['output_prefix'], 
                        'main_content': content.get('main_content', '')
                    }
                    self._save_item_to_file(item, config, city)
                    return [item]
            return []
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
        self.base_url = "https://kudago.com"

    def _make_request_with_retry(self, url, max_retries=3):
        """Выполняет HTTP-запрос с повторными попытками при ошибке"""
        for attempt in range(max_retries):
            try:
                print(f"  Запрос к {url}")
                response = requests.get(url, headers=self.headers, timeout=30)
                if response.status_code == 200:
                    return response
                print(f"  Статус код {response.status_code} для {url}")
            except Exception as e:
                print(f"  Ошибка запроса {url}: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2)
        return None

    def _extract_events_from_html(self, soup, source_url):
        """
        Извлекает отдельные события/экскурсии из HTML-кода страницы KudaGo
        """
        events = []
        
        # Ищем все блоки с событиями на странице
        # На KudaGo каждое событие находится в блоке с эмодзи  в начале
        
        # Способ 1: Ищем все блоки, которые содержат эмодзи  (символ календаря/события)
        event_blocks = []
        
        # Ищем все элементы, которые могут быть контейнерами событий
        for element in soup.find_all(['div', 'article', 'section'], class_=re.compile(r'post|event|item|excursion|listing-item')):
            text = element.get_text()
            if '' in text and ('руб' in text.lower() or 'расписание' in text.lower() or 'экскурс' in text.lower()):
                event_blocks.append(element)
        
        # Если не нашли по классам, ищем по содержимому
        if not event_blocks:
            # Ищем все элементы с большим количеством текста
            for element in soup.find_all(['div', 'article', 'section', 'li']):
                text = element.get_text(strip=True)
                # Проверяем, что элемент содержит эмодзи и достаточно длинный
                if '' in text and len(text) > 100:
                    event_blocks.append(element)
        
        print(f"  Найдено потенциальных блоков событий: {len(event_blocks)}")
        
        # Обрабатываем каждый найденный блок
        for block in event_blocks:
            try:
                event = {}
                
                # Получаем весь текст блока
                full_text = block.get_text(" ", strip=True)
                
                # Извлекаем заголовок (обычно до эмодзи  или в начале)
                title_match = re.search(r'\s*(\d+)?\s*([^]+)', full_text)
                if title_match:
                    # Берем группу 2, которая содержит название
                    title = title_match.group(2).strip()
                    # Очищаем от лишних слов
                    title = re.sub(r'Реклама\s*\.\.\.\s*', '', title)
                    title = re.sub(r'^\.\.\.\s*', '', title)
                    event['title'] = title
                else:
                    # Если не нашли по паттерну, берем первые 100 символов
                    event['title'] = full_text[:100].split('')[-1].strip()
                
                # Извлекаем даты (после эмодзи )
                dates_match = re.search(r'\s*([^]+?)(?=|$)', full_text)
                if dates_match:
                    event['dates'] = dates_match.group(1).strip()
                
                # Извлекаем место (после эмодзи )
                place_match = re.search(r'\s*([^0-9]+?)(?=\d|руб|₽|$)', full_text, re.IGNORECASE)
                if place_match:
                    event['place'] = place_match.group(1).strip()
                
                # Извлекаем цену (ищем цифры с руб/₽)
                price_match = re.search(r'(\d[\d\s]*[₽руб]+)', full_text, re.IGNORECASE)
                if price_match:
                    event['price'] = price_match.group(1).strip()
                
                # Извлекаем описание (все, что не попало в другие поля)
                description = full_text
                if 'title' in event:
                    description = description.replace(event['title'], '')
                if 'dates' in event:
                    description = description.replace(event['dates'], '')
                if 'place' in event:
                    description = description.replace(event['place'], '')
                if 'price' in event:
                    description = description.replace(event['price'], '')
                
                # Очищаем описание от эмодзи и лишних пробелов
                description = re.sub(r'[]', '', description)
                description = re.sub(r'\s+', ' ', description).strip()
                if description and len(description) > 20:
                    event['description'] = description
                
                # Извлекаем ссылку, если есть
                link_tag = block.find('a', href=True)
                if link_tag:
                    href = link_tag.get('href')
                    if href:
                        if href.startswith('http'):
                            event['link'] = href
                        else:
                            event['link'] = urljoin(self.base_url, href)
                
                # Добавляем событие только если есть заголовок
                if event.get('title') and len(event['title']) > 5:
                    # Добавляем источник
                    event['source_url'] = source_url
                    event['page_type'] = 'event'
                    events.append(event)
                    print(f"    ✓ Найдено событие: {event['title'][:50]}...")
                
            except Exception as e:
                print(f"    ✗ Ошибка при обработке блока: {e}")
                continue
        
        return events

    def _extract_links_from_mosru(self, soup, base_url):
        """Извлекает ссылки на статьи с главной страницы mos.ru"""
        links = set()
        
        selectors = [
            'section.Telly_grid__lXFMU a.Telly_content__XGOvB',
            'div#id-1-4[role="tabpanel"] a.NewsList_card__Td36c',
            'section#main-themes a.MainTheme_link__XJZzA',
            'ul.MainTheme_list__ALst9 a.MainTheme_link__XJZzA'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if any(pattern in full_url for pattern in ['/news/item/', '/mayor/themes/', '/news/maintheme/']):
                        links.add(full_url)
        
        print(f"  Найдено ссылок для детального парсинга: {len(links)}")
        return list(links)

    def _parse_mosru_article(self, url, base_url):
        """Парсит отдельную страницу статьи на mos.ru"""
        response = self._make_request_with_retry(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        article = {
            'url': url,
            'title': '',
            'date': '',
            'category': '',
            'content': '',
            'images': []
        }
        
        # Заголовок
        title_elem = (soup.select_one('h1') or 
                     soup.select_one('article h1') or 
                     soup.select_one('.article-title') or
                     soup.select_one('.news-title'))
        if title_elem:
            article['title'] = title_elem.get_text(strip=True)
        
        # Дата
        date_elem = (soup.select_one('time') or 
                    soup.select_one('.article-date') or
                    soup.select_one('.news-date'))
        if date_elem:
            article['date'] = date_elem.get_text(strip=True)
            datetime_attr = date_elem.get('datetime')
            if datetime_attr:
                article['datetime'] = datetime_attr
        
        # Категория
        category_elem = (soup.select_one('.sphere') or 
                        soup.select_one('.article-category') or
                        soup.select_one('.news-category') or
                        soup.select_one('[data-testid="sphere"]'))
        if category_elem:
            article['category'] = category_elem.get_text(strip=True)
        
        # Изображения
        images = soup.select('article img, .article-content img, .news-content img')
        for img in images[:5]:
            src = img.get('src')
            if src:
                if src.startswith('/'):
                    src = urljoin(base_url, src)
                article['images'].append(src)
        
        # Контент
        content_selectors = [
            'article',
            '.article-content',
            '.news-content',
            '.content',
            'main'
        ]
        
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                for tag in content_div.select('script, style, nav, header, footer, .share, .comments, .related-news'):
                    tag.decompose()
                
                text = content_div.get_text("\n", strip=True)
                if len(text) > 200:
                    article['content'] = text
                    break
        
        if not article['content']:
            paragraphs = soup.select('p')
            if paragraphs:
                article['content'] = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])
        
        return article

    def _save_item_to_file(self, item, config, city, is_article=False):
        """Сохраняет элемент в JSON-файл"""

        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        
        project_root = os.path.abspath(os.path.join(current_file_dir, "..", ".."))
        
        base_dir = os.path.join(project_root, "data", city)

        os.makedirs(base_dir, exist_ok=True)
        
        if 'link' in item and item['link']:
            url_id = hashlib.md5(item['link'].encode()).hexdigest()[:8]
        elif 'title' in item:
            url_id = hashlib.md5(item['title'].encode()).hexdigest()[:8]
        else:
            url_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        
        # Очистка заголовка
        title = item.get('title', 'untitled')
        if isinstance(title, str):
            clean_title = re.sub(r'[^\w\s-]', '', title)
            clean_title = re.sub(r'[-\s]+', '_', clean_title)
            clean_title = clean_title[:50].strip('_')
        else:
            clean_title = 'untitled'
        
        prefix = 'article' if is_article else 'event'
        
        # Формируем имя файла
        filename = os.path.join(base_dir, f"{config['output_prefix']}_{prefix}_{clean_title}_{url_id}.json")
        
        # Добавляем метаданные (важно для твоего RAG бота!)
        item['city'] = city
        item['site'] = config.get('output_prefix', 'unknown')
        item['parsed_timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Сохраняем
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(item, f, ensure_ascii=False, indent=2, default=str)
            self.items_count += 1
            print(f"  [SAVE] ✓ {os.path.basename(filename)}")
        except Exception as e:
            print(f"  [ERROR] Не удалось сохранить файл {filename}: {e}")

    def parse_site(self, config, city='moscow'):
        """
        Основной метод для запуска парсинга сайта
        """
        print(f"\n{'='*60}")
        print(f"ЗАПУСК ПАРСЕРА ДЛЯ {city.upper()}")
        print(f"Сайт: {config.get('url', 'N/A')}")
        print(f"{'='*60}")
        
        # Сбрасываем состояние
        self.visited_urls.clear()
        self.items_count = 0
        start_time = time.time()
        
        # Определяем тип сайта по префиксу
        site_prefix = config.get('output_prefix', '')
        
        if 'kudago' in site_prefix:
            # Парсинг KudaGo
            urls_to_parse = config.get('start_urls', [config['url']])
            print(f"Стартовые URL: {len(urls_to_parse)}")
            
            for url in urls_to_parse:
                print(f"\n--- Парсинг страницы: {url} ---")
                
                response = self._make_request_with_retry(url)
                if not response:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Извлекаем события из HTML
                events = self._extract_events_from_html(soup, url)
                
                print(f"  Найдено событий на странице: {len(events)}")
                
                # Сохраняем каждое событие
                for event in events:
                    self._save_item_to_file(event, config, city, is_article=False)
        
        elif 'mosru' in site_prefix:
            # Парсинг Mos.ru
            print(f"\n--- Парсинг главной страницы: {config['url']} ---")
            
            response = self._make_request_with_retry(config['url'])
            if not response:
                print("❌ Не удалось загрузить главную страницу")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Извлекаем ссылки на статьи
            article_links = self._extract_links_from_mosru(soup, config.get('base_url', 'https://www.mos.ru'))
            
            print(f"\nНайдено ссылок на статьи: {len(article_links)}")
            
            # Парсим каждую статью
            for i, link in enumerate(article_links[:10], 1):  # Ограничиваем 10 статьями
                if link in self.visited_urls:
                    continue
                    
                print(f"\n  [{i}/{min(len(article_links), 10)}] Парсинг статьи: {link}")
                
                article = self._parse_mosru_article(link, config.get('base_url', 'https://www.mos.ru'))
                if article and article.get('content'):
                    self.visited_urls.add(link)
                    self._save_item_to_file(article, config, city, is_article=True)
                else:
                    print(f"  ⚠ Не удалось извлечь контент")
                
                time.sleep(1)
        
        # Выводим статистику
        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"ПАРСИНГ ЗАВЕРШЕН")
        print(f"Всего сохранено файлов: {self.items_count}")
        print(f"Время выполнения: {elapsed:.1f} сек")
        print(f"Данные сохранены в: data/{city}/")
        print(f"{'='*60}")
        
        return []
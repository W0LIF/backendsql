# Конфигурации для разных сайтов
CONFIGURATIONS = {

        # МФЦ Самары - ОСНОВНОЙ ПАРСИНГ УСЛУГ
    'mfc_samara_services': {
        'url': 'https://mfc-samara.ru/services/uslugi_fizicheskim_licam/',
        'output_prefix': 'mfc_samara_services',
        'recursive': True,
        'max_depth': 3,  # Увеличил глубину
        'start_urls': [
            'https://mfc-samara.ru/services/uslugi_fizicheskim_licam/',
            'https://mfc-samara.ru/services/zhiznennye_situacii/',
            'https://mfc-samara.ru/services/drugie_uslugi/',
            'https://mfc-samara.ru/services/uslugi_yuridicheskim_licam/',
            'https://mfc-samara.ru/services/biznes_pod_klyuch/',
            'https://mfc-samara.ru/services/bankrotstvo/'
        ],
        'allowed_domains': ['mfc-samara.ru'],
        'url_patterns': [
            r'/services/.*',  # Все страницы услуг
            r'/news/.*',       # Новости
            r'/about/.*'       # Информационные страницы
        ],
        'ignore_patterns': [
            r'.*\.(pdf|docx?|xlsx?|zip|jpg|png|gif|svg)$',  # Файлы
            r'/search.*',
            r'/feedback.*',
            r'/queue.*',
            r'/case_status.*'
        ],
        # Селекторы для поиска ссылок
        'list_selectors': [
            {
                'selector': 'a[href*="/services/"]',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            },
            {
                'selector': '.menu a[href*="/services/"]',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            },
            {
                'selector': '.area .menu li a',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            },
            {
                'selector': '.item a',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            }
        ],
        # Селекторы для извлечения контента
        'content_selectors': [
            'main',
            'article',
            '.content',
            '.service-content',
            '.area',
            '.entry',
            '.text',
            '.welcome-text'
        ],
        'min_content_length': 200  # Уменьшил минимальную длину контента
    },

                # Администрация г.о. Самара (ИСПРАВЛЕННАЯ ВЕРСИЯ)
    'samara_admin': {
        'url': 'https://samadm.ru/',
        'output_prefix': 'samara_admin',
        'recursive': True,
        'max_depth': 2,
        'allowed_domains': ['samadm.ru'],
        'start_urls': [  # Добавляем стартовые URL для более полного обхода
            'https://samadm.ru/',
            'https://samadm.ru/media/news/',
            'https://samadm.ru/docs/',
            'https://samadm.ru/authority/',
            'https://samadm.ru/city_life/'
        ],
        'url_patterns': [
            r'^/$',
            r'/about/.*',
            r'/authority/.*',
            r'/city_life/.*',
            r'/docs/.*',
            r'/feedback/.*',
            r'/media/news/\d+/$'
        ],
        'ignore_patterns': [
            r'.*\.(pdf|docx?|xlsx?|zip|jpg|png|gif|svg|ico|css|js)$',
            r'/bitrix/.*',
            r'/search.*',
            r'\?(.*)',
            r'#.*',
            r'https?://(ok|vk)\.(ru|com)',
            r'https?://(mc\.)?yandex\.(ru|com)',
            r'https?://stat\.sputnik\.ru',
            r'/en/',
        ],
        'list_selectors': [
            {
                'selector': '.nav-justified a',
                'fields': {'title': '', 'link': '@href'}
            },
            {
                'selector': '#news a[href^="/media/news/"]',
                'fields': {'title': '', 'link': '@href'}
            },
            {
                'selector': '#city-live a',
                'fields': {'title': '', 'link': '@href'}
            },
            {
                'selector': '.index.blocks a',
                'fields': {'title': '', 'link': '@href'}
            },
            {
                'selector': '#persons-list a',
                'fields': {'title': '', 'link': '@href'}
            },
            {
                'selector': '#good-links a',
                'fields': {'title': '', 'link': '@href'}
            },
            {
                'selector': '.inner-page a[href^="/"]',
                'fields': {'title': '', 'link': '@href'}
            },
            {
                # Добавляем селектор для ссылок в футере
                'selector': 'footer a',
                'fields': {'title': '', 'link': '@href'}
            }
        ],
        'content_selectors': [
            # Эти селекторы основаны на реальной структуре HTML
            '.inner-page',  # Основной контейнер контента
            '.news-detail',  # Для страниц новостей (исправлено с 'news detail')
            '.content-block',  # Блок с контентом
            '.docs-detail',  # Для страниц документов
            '.person-detail',  # Для страниц персон
            '.text-block',  # Текстовый блок
            'main .container',  # Основной контейнер
            'article',  # Статьи
            '.page-content',  # Контент страницы
            # Запасной вариант - любой div с большим количеством текста
            'div:has(p):has(h1):has(h2)'  
        ],
        'min_content_length': 700,  # Уменьшаем порог до 50 символов
        'fallback_to_title': True  # Добавим эту логику позже в код
    },

        # Культура.РФ - Гид по Самаре 
    'culture_samara_guide_new': {
        'url': 'https://www.culture.ru/s/goroda/samara/',
        'output_prefix': 'culture_samara_guide',
        'recursive': True,  # Включаем рекурсивный обход для сбора всех страниц музеев, театров и храмов
        'max_depth': 2,
        'allowed_domains': ['culture.ru'],
        'start_urls': [
            'https://www.culture.ru/s/goroda/samara/',  # Главная страница гида
        ],
        'url_patterns': [
            r'/institutes/\d+/.*',  # Страницы музеев и театров
            r'/objects/\d+/.*',      # Страницы объектов (храмы, достопримечательности)
            r'/persons/\d+/.*',       # Страницы персон
            r'/s/goroda/samara/.*',   # Страницы гида
            r'/afisha/.*',  # Добавить афишу
            r'/news/.*',
        ],
        'ignore_patterns': [
            r'.*\.(pdf|docx?|xlsx?|zip|jpg|png|gif|svg|ico|css|js)$',
            r'/js/.*',
            r'/css/.*',
            r'/fonts/.*',
            r'#.*',
            r'\?(.*)',
            r'https?://(vk|ok|telegram|zen)\.(com|ru)',
            r'https?://yandex\.ru',
            r'https?://mc\.yandex\.ru',
            r'/subscribe',
            r'/feedback',
        ],
        'list_selectors': [
            # Селекторы для поиска ссылок на страницы объектов
            {
                'selector': '.t336__title a.t-card__link',  # Ссылки в карточках музеев/театров
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            },
            {
                'selector': '.t334__col a[href*="/institutes/"]',  # Ссылки в карточках краеведческого музея
                'fields': {
                    'title': '.t334__title',  # Заголовок внутри ссылки
                    'link': '@href'
                }
            },
            {
                'selector': '.t334__col a[href*="/objects/"]',  # Ссылки на объекты (храмы)
                'fields': {
                    'title': '.t334__title',
                    'link': '@href'
                }
            },
            {
                'selector': '.t004 a[href*="/persons/"]',  # Ссылки на персон
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            },
            {
                'selector': '.t-card__link[href*="culture.ru/"]',  # Универсальный селектор для карточек
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            }
        ],

        'start_urls': [
        'https://www.culture.ru/s/goroda/samara/',
        'https://www.culture.ru/afisha/samarskaya-oblast-samara',  # Афиша мероприятий
        'https://www.culture.ru/news',  # Новости культуры
        ],

        'content_selectors': [
            # Селекторы для извлечения контента со страниц музеев/театров/объектов
            
            # Для страниц институций (музеи, театры)
            '.institute-page',
            '.institute__content',
            '.institute__description',
            '.object-card__content',
            
            # Для страниц гида
            '.t183__wrapper',  # Заголовок страницы
            '.t050 .t-container',  # Заголовки разделов
            '.t004 .t-container',  # Описания разделов
            '.t336 .t-card__container',  # Карточки с описаниями мест
            '.t334 .t-container',  # Карточки с описаниями (альтернативный формат)
            
            # Общие селекторы
            'main',
            '.t-container',
            'article',
            '.content',
            
            # Футер (информация о проекте) - только если ничего не нашли выше
            '.footer-group',
        ],
        'title_selector': 'h1, .t183__title, .t050__title, .institute__title, .object-card__title',
        'min_content_length': 100,
    },

    # Культура.РФ - Афиша Самары (ИСПРАВЛЕННАЯ ВЕРСИЯ)
    'culture_samara_afisha': {
        'url': 'https://www.culture.ru/afisha/samarskaya-oblast-samara',
        'output_prefix': 'culture_samara_afisha',
        'recursive': True,
        'max_depth': 2,
        'allowed_domains': ['culture.ru'],
        'start_urls': [
            'https://www.culture.ru/afisha/samarskaya-oblast-samara',
            'https://www.culture.ru/afisha/samarskaya-oblast-samara?page=2',
            'https://www.culture.ru/afisha/samarskaya-oblast-samara?page=3',
        ],
        'url_patterns': [
            r'/events/\d+/.*',  # Страницы событий
            r'/institutes/\d+/.*',  # Страницы организаций
        ],
        'ignore_patterns': [
            r'.*\.(pdf|docx?|xlsx?|zip|jpg|png|gif|svg|ico|css|js)$',
            r'#.*',
            r'/search.*',
            r'/feedback.*',
            r'/subscribe.*',
        ],
        # Селекторы для извлечения данных из JSON на странице списка
        'list_selectors': [
            {
                'selector': 'script#__NEXT_DATA__[type="application/json"]',
                'type': 'json',
                'extract': 'props.pageProps.events.items',
                'fields': {
                    'title': 'title',
                    'link': {
                        'template': '/events/{_id}/{name}',
                        'fields': ['_id', 'name']
                    },
                    'event_id': '_id',
                    'name': 'name',
                    'price_min': 'price.min',
                    'price_max': 'price.max',
                    'is_pushkins_card': 'isPushkinsCard',
                    'place_title': 'topPlaceTitle',  # Это может быть null на странице списка
                    'thumbnail_id': 'thumbnailFile.publicId',
                    'date_text': 'date.dayMonth.0',
                    'date_week': 'date.dayWeek',
                    'tags': 'tags',
                    'genres': 'genres',
                }
            }
        ],
        # Селекторы для страниц самих событий
        'content_selectors': [
            'script#__NEXT_DATA__[type="application/json"]',
            'main',
            'article',
            '.event-page',
            '.styles_Layout__Content__DtgXz',
        ],
        'title_selector': 'h1, .styles_CatalogTitleHeading__CNS0s',
        'min_content_length': 500,
    },

        # Кассы.Ру - Самара (афиша мероприятий)
    'samara_kassy': {
        'url': 'https://samara.kassy.ru/',
        'output_prefix': 'samara_kassy',
        'recursive': True,
        'max_depth': 2,
        'allowed_domains': ['samara.kassy.ru', 'kassy.ru'],
        'start_urls': [
            'https://samara.kassy.ru/',
            'https://samara.kassy.ru/events/koncerty-i-shou/',
            'https://samara.kassy.ru/events/teatr/',
            'https://samara.kassy.ru/events/detskie/',
            'https://samara.kassy.ru/events/cirk/',
            'https://samara.kassy.ru/events/range-soon/',
        ],
        'url_patterns': [
            r'^/$',
            r'/events/koncerty-i-shou/.*',
            r'/events/teatr/.*',
            r'/events/detskie/.*',
            r'/events/cirk/.*',
            r'/events/[^/]+/\d+-[^/]+/$',  # Страницы событий (пример: /events/koncerty-i-shou/64-48409359/)
            r'/venue/\d+-[^/]+/$',  # Страницы учреждений
        ],
        'ignore_patterns': [
            r'.*\.(pdf|docx?|xlsx?|zip|jpg|png|gif|svg|ico|css|js)$',
            r'#.*',
            r'/search.*',
            r'/feedback.*',
            r'/pushkin/.*',
            r'/text/.*',
            r'/news/.*',
            r'/salepoint/.*',
            r'/registration/.*',
            r'/login/.*',
            r'/remember/.*',
        ],
        # Селекторы для извлечения данных из JSON на странице списка
        'list_selectors': [
            {
                'selector': 'script:contains("events_ecom")',
                'type': 'json',
                'extract': '',  # Оставляем пустым, так как будем парсить весь скрипт
                'fields': {
                    'title': 'name',
                    'link': {
                        'template': '/events/{category_url}/{id}',
                        'fields': ['category_url', 'id']
                    },
                    'id': 'id',
                    'category': 'category',
                    'price_from': 'price',
                    'date': 'variant',
                    'brand': 'brand',
                    'position': 'position'
                }
            }
        ],
        # Селекторы для страниц самих событий
        'content_selectors': [
            'main',
            '#content',
            '.events',
            '.announce',
            '.price_line',
        ],
        'title_selector': 'h1, h2 a.event_link',
        'min_content_length': 200,
    },




}
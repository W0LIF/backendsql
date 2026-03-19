#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Конфигурация только для Москвы (KudaGo)
CONFIGURATIONS = {
    'moscow_kudago': {
        'url': 'https://kudago.com/msk/',
        'output_prefix': 'moscow_kudago',
        'recursive': True,
        'max_depth': 2,
        'allowed_domains': ['kudago.com'],
        'start_urls': [
            'https://kudago.com/msk/',
            'https://kudago.com/msk/events/',
            'https://kudago.com/msk/exhibitions/',
            'https://kudago.com/msk/concerts/',
            'https://kudago.com/msk/best-plays/',
            'https://kudago.com/msk/entertainment/',
            'https://kudago.com/msk/kino/',
            'https://kudago.com/msk/festival/',
            'https://kudago.com/msk/quests/',
            'https://kudago.com/msk/excursions/',
        ],
        'url_patterns': [
            r'/msk/?$',
            r'/msk/events/?$',
            r'/msk/exhibitions/?$',
            r'/msk/concerts/?$',
            r'/msk/best-plays/?$',
            r'/msk/entertainment/?$',
            r'/msk/kino/?$',
            r'/msk/festival/?$',
            r'/msk/quests/?$',
            r'/msk/excursions/?$',
            r'/msk/[\w-]+/\d+/$',  # события (пример: /msk/event/12345/)
            r'/place/\d+/$',        # места (пример: /place/12345/)
        ],
        'ignore_patterns': [
            r'.*\.(pdf|docx?|xlsx?|zip|jpg|png|gif|svg|ico|css|js|webmanifest)$',
            r'/search.*',
            r'/feedback.*',
            r'/account.*',
            r'/login.*',
            r'/api/.*',
            r'#.*',
            r'\?.*',
            r'https?://(vk|ok|telegram|facebook|twitter)\.(com|ru)',
        ],
        'list_selectors': [
            {
                'selector': 'script#__NEXT_DATA__[type="application/json"]',
                'type': 'json',
                'extract': 'props.pageProps.eventsList.events',  # Путь к данным на KudaGo
                'fields': {
                    'title': 'title',
                    'link': {
                        'template': '/msk/event/{id}/',
                        'fields': ['id']
                    },
                    'event_id': 'id',
                    'description': 'description',
                    'short_description': 'short_title',
                    'place_title': 'place.title',
                    'place_address': 'place.address',
                    'place_id': 'place.id',
                    'image_url': 'images.0.image',
                    'age_restriction': 'age_restriction',
                    'price': 'price',
                    'tags': 'tags',
                    'categories': 'categories',
                    'is_free': 'is_free',
                    'dates': 'dates',
                }
            }
        ],
        'content_selectors': [
            'main',
            'article',
            '.event-page',
            '.place-page',
            '.content',
            '.b-places-detail',
            '.b-events-detail',
        ],
        'title_selector': 'h1, .event-title, .place-title',
        'min_content_length': 200,
    },

     'moscow_mosru_main': {
        'url': 'https://www.mos.ru/',
        'output_prefix': 'moscow_mosru',
        'recursive': False,  # Не рекурсивный, парсим только главную
        'allowed_domains': ['mos.ru'],
        'sections': {
            'main_news': {
                'name': 'Главные новости',
                'selector': 'section.Telly_grid__lXFMU article.Telly_telly__gKpTj:first-child ul.Telly_news__z3a4Q li.Telly_card__fpjuz',
                'fields': {
                    'title': {
                        'selector': 'div.Telly_content__XGOvB div.Telly_title__jTvJv',
                        'type': 'text'
                    },
                    'link': {
                        'selector': 'a.Telly_content__XGOvB',
                        'type': 'attr',
                        'attribute': 'href'
                    },
                    'time': {
                        'selector': 'time.Telly_time__hXzpE',
                        'type': 'text'
                    },
                    'datetime': {
                        'selector': 'time.Telly_time__hXzpE',
                        'type': 'attr',
                        'attribute': 'datetime'
                    },
                    'category': {
                        'selector': 'span.Telly_sphere__jBfyw',
                        'type': 'text'
                    },
                    'image': {
                        'selector': 'picture.Telly_picture__vEx8I img',
                        'type': 'attr',
                        'attribute': 'src'
                    }
                }
            },
            'important_news': {
                'name': 'Важное',
                'selector': 'section.Telly_grid__lXFMU article.Telly_telly__gKpTj:last-child ul.banner_banners__7l7oD li.banner_ban__CPPIo',
                'fields': {
                    # Пустой, так как это баннеры
                }
            },
            'main_themes': {
                'name': 'Главные темы',
                'selector': 'section#main-themes ul.MainTheme_list__ALst9 li.MainTheme_container__hR5_X',
                'fields': {
                    'title': {
                        'selector': 'span.MainTheme_title__78UXQ',
                        'type': 'text'
                    },
                    'link': {
                        'selector': 'a.MainTheme_link__XJZzA',
                        'type': 'attr',
                        'attribute': 'href'
                    },
                    'icon': {
                        'selector': 'img.MainTheme_image__uQm3T',
                        'type': 'attr',
                        'attribute': 'src'
                    }
                }
            },
            'today_news': {
                'name': 'Сегодня в городе - Новости',
                'selector': 'div#id-1-4[role="tabpanel"] ul.NewsList_cardList__4YxDc li.NewsList_cardListItem__u0dqO',
                'fields': {
                    'title': {
                        'selector': 'div.NewsList_cardTitle__Ynudp',
                        'type': 'text'
                    },
                    'link': {
                        'selector': 'a.NewsList_card__Td36c',
                        'type': 'attr',
                        'attribute': 'href'
                    },
                    'time': {
                        'selector': 'time.NewsList_cardDate__h3Kf4',
                        'type': 'text'
                    },
                    'datetime': {
                        'selector': 'time.NewsList_cardDate__h3Kf4',
                        'type': 'attr',
                        'attribute': 'datetime'
                    },
                    'category': {
                        'selector': 'span.NewsList_cardSphere__whbnl',
                        'type': 'text'
                    },
                    'image': {
                        'selector': 'div.NewsList_imageWrapper__MqQ_L img',
                        'type': 'attr',
                        'attribute': 'src'
                    }
                }
            }
        }
    }
}
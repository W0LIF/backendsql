# Конфигурации для разных сайтов
CONFIGURATIONS = {
    # ГУ СПб - База знаний (все страницы через цикл)
    'gu_spb_knowledge_pages': {
        'url': 'https://gu.spb.ru/knowledge-base/?PAGEN_1=',
        'output_prefix': 'gu_spb_knowledge',
        'multiple_pages': True,
        'start_page': 1,
        'end_page': 21,  # С 1 по 21 страницу
        'list_selectors': [
            {
                'selector': 'div.element-card a.ambient__link-ctrl',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            },
            {
                'selector': '.element-card .title-usual a',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            }
        ],
        'content_selectors': [
            '.text-container',
            '.paragraph-base', 
            '.box._mode-usual',
            'main'
        ]
    },
    
    # ГУ СПб - МФЦ жизненные ситуации
    'gu_spb_mfc': {
        'url': 'https://gu.spb.ru/mfc/life_situations/',
        'output_prefix': 'gu_spb_mfc',
        'list_selectors': [
            {
                'selector': 'div.life-situation-item a',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            },
            {
                'selector': '.life-situation-item a',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            }
        ],
        'content_selectors': [
            '.content-block',
            '.text-container',
            'main'
        ]
    },
    
    # ГУ СПб - МФЦ услуги для граждан (основная страница)
    'gu_spb_mfc_services': {
        'url': 'https://gu.spb.ru/mfc/services/individual/',
        'output_prefix': 'gu_spb_mfc_services',
        'list_selectors': [
            {
                'selector': '.ambient__link-ctrl._theme-mfc',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            },
            {
                'selector': 'a.ambient__link-ctrl',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            }
        ],
        'content_selectors': [
            '.text-container',
            '.paragraph-base',
            'main'
        ]
    },
    
    # ГУ СПб - МФЦ услуги (все страницы 1-35)
    'gu_spb_mfc_services_pages': {
        'url': 'https://gu.spb.ru/mfc/services/individual/?PAGEN_1=',
        'output_prefix': 'gu_spb_mfc_services_page',
        'multiple_pages': True,
        'start_page': 1,
        'end_page': 35,
        'list_selectors': [
            {
                'selector': '.ambient__link-ctrl._theme-mfc',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            },
            {
                'selector': 'a.ambient__link-ctrl',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            }
        ],
        'content_selectors': [
            '.text-container',
            '.paragraph-base',
            'main'
        ]
    },
    
    # Правительство СПб - Помощник
    'gov_spb_helper': {
        'url': 'https://www.gov.spb.ru/helper/',
        'output_prefix': 'gov_spb_helper',
        'list_selectors': [
            {
                'selector': '.col-lg-4 h2 a',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            },
            {
                'selector': '.unstyled-list a',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            }
        ],
        'content_selectors': [
            '.content-block',
            '.text-block',
            'main'
        ]
    },
    
    # Правительство СПб - Социальные вопросы
    'gov_spb_social': {
        'url': 'https://www.gov.spb.ru/gov/otrasl/trud/socialnye-voprosy/',
        'output_prefix': 'gov_spb_social_issues',
        'list_selectors': [
            {
                'selector': '.block.content .unstyled-list a',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            },
            {
                'selector': '.col-lg-4 .unstyled-list a',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            }
        ],
        'content_selectors': [
            '.block.content',
            '.content-block',
            'main'
        ]
    },
    
    # Правительство СПб - Культура
    'gov_spb_helper_culture': {
        'url': 'https://www.gov.spb.ru/helper/culture/',
        'output_prefix': 'gov_spb_helper_culture',
        'list_selectors': [
            {
                'selector': '.sidemenu__item a.sidemenu__link',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            },
            {
                'selector': '.block.content a[href^="/helper/"]',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            }
        ],
        'content_selectors': [
            '.block.content',
            '.content-block',
            'main'
        ]
    },
    
    # КонсультантПлюс
    'consultant': {
        'url': 'https://www.consultant.ru/',
        'output_prefix': 'consultant',
        'list_selectors': [
            {
                'selector': 'a[href*="/document/"]',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            },
            {
                'selector': '.news-item a',
                'fields': {
                    'title': '',
                    'link': '@href'
                }
            }
        ],
        'content_selectors': [
            '.document-page',
            '.text',
            'main'
        ]
    }
}
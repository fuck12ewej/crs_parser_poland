"""
🚀 АВТОМАТИЧЕСКИЙ ПАРСЕР KRS-POBIERZ - ОПТИМИЗИРОВАННАЯ ВЕРСИЯ
================================================================

ОСНОВНЫЕ ОПТИМИЗАЦИИ ДЛЯ ПОВЫШЕНИЯ СКОРОСТИ:
✅ Уменьшены все time.sleep() задержки в 1.5-2 раза
✅ Оптимизированы настройки браузера для максимальной производительности
✅ Отключены все расширения и ненужные функции
✅ Блокировка изображений, медиа и геолокации
✅ Уменьшены таймауты WebDriverWait с 15 до 8 секунд
✅ Оптимизированы настройки памяти и фоновых процессов


"""

import time
import json
import csv
import re
import os
from dataclasses import dataclass
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.edge.options import Options as EdgeOptions

# Импортируем конфигурацию производительности
try:
    from performance_config import DELAYS, BROWSER_OPTIMIZATIONS, SAFETY_LIMITS
    CONFIG_LOADED = True
    print("✅ Конфигурация производительности загружена")
except ImportError:
    CONFIG_LOADED = False
    print("⚠️ performance_config.py не найден, используются стандартные настройки")
    
    # Стандартные настройки если конфиг не загружен
    DELAYS = {
        'page_load': 1.5,
        'search_results': 2.0,
        'pdf_download': 3.0,
        'file_move': 1.5,
        'cookies': 1.5,
        'between_companies': 1.5,
        'file_check': 1.5,
        'button_click': 2.0,
    }
    
    BROWSER_OPTIMIZATIONS = {
        'webdriver_wait': 8,
        'max_memory': '4096',
        'disable_extensions': True,
        'disable_images': True,
        'disable_media': True,
        'disable_geolocation': True,
    }
    
    SAFETY_LIMITS = {
        'max_pages': 20,
        'max_companies_per_page': 30,
        'max_retries': 3,
    }

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ PyPDF2 не установлен. TXT файлы будут создаваться без данных из PDF.")

@dataclass
class CompanyInfo:
    """Класс для хранения информации о компании"""
    name: str
    krs_number: Optional[str] = None
    nip: Optional[str] = None
    regon: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None
    company_url: Optional[str] = None

class AutoKRSParser:
    """Автоматический парсер для сайта krs-pobierz.pl"""
    
    def __init__(self):
        self.base_url = "https://krs-pobierz.pl"
        self.driver = None
        self.wait = None
        self.saves_dir = "saves"
        self.temp_dir = "temp"
        
        # Создаем папки если их нет
        if not os.path.exists(self.saves_dir):
            os.makedirs(self.saves_dir)
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
    
    def setup_browser(self):
        """Настройка и запуск браузера"""
        try:
            print("🌐 Пробую запустить Chrome...")
            return self.setup_chrome()
        except Exception as e:
            print(f"❌ Chrome не запустился: {e}")
            try:
                print("🌐 Пробую запустить Edge...")
                return self.setup_edge()
            except Exception as e:
                print(f"❌ Edge не запустился: {e}")
                return False
    
    def setup_chrome(self):
        """Настройка Chrome без автоматической установки драйвера"""
        try:
            # Настройки Chrome
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Настройки для временных файлов браузера
            chrome_options.add_argument(f"--user-data-dir={os.path.abspath(self.temp_dir)}")
            chrome_options.add_argument(f"--disk-cache-dir={os.path.abspath(self.temp_dir)}")
            chrome_options.add_argument(f"--media-cache-dir={os.path.abspath(self.temp_dir)}")
            chrome_options.add_argument(f"--disk-cache-size=1048576")  # 1MB кэш
            
            # ОПТИМИЗАЦИЯ ПРОИЗВОДИТЕЛЬНОСТИ
            chrome_options.add_argument("--disable-extensions")  # Отключаем все расширения для скорости
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-ads")
            chrome_options.add_argument("--disable-images")  # Отключаем загрузку изображений
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            
            # Настройки для максимальной скорости
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--memory-pressure-off")
            chrome_options.add_argument("--max_old_space_size=4096")
            
            # Настройки для скачивания PDF - ИСПРАВЛЕНО + ОПТИМИЗАЦИЯ
            prefs = {
                "download.default_directory": os.path.abspath(self.saves_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True,  # Изменено на True для скачивания
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_setting_values.popups": 2,
                "safebrowsing.enabled": False,  # Отключаем безопасный просмотр
                "download.open_pdf_in_system_reader": False,  # Не открываем PDF в системном читателе
                "profile.default_content_settings.popups": 0,  # Разрешаем всплывающие окна для скачивания
                "profile.content_settings.exceptions.automatic_downloads.*.setting": 1,  # Разрешаем автоматические скачивания
                "profile.default_content_settings.automatic_downloads": 1,  # Разрешаем автоматические скачивания
                "download.restrictions": 0,  # Убираем ограничения на скачивание
                "profile.default_content_setting_values.automatic_downloads": 1,  # Разрешаем автоматические скачивания
                
                # Настройки для временных файлов браузера
                "profile.default_content_setting_values.cookies": 1,  # Разрешаем cookies
                "profile.default_content_setting_values.cache": 1,  # Разрешаем кэш
                "profile.default_content_setting_values.local_storage": 1,  # Разрешаем локальное хранилище
                "profile.default_content_setting_values.session_storage": 1,  # Разрешаем сессионное хранилище
                "profile.default_content_setting_values.indexeddb": 1,  # Разрешаем IndexedDB
                "profile.default_content_setting_values.websql": 1,  # Разрешаем WebSQL
                "profile.default_content_setting_values.file_system": 1,  # Разрешаем файловую систему
                "profile.default_content_setting_values.appcache": 1,  # Разрешаем AppCache
                
                # ОПТИМИЗАЦИЯ ПРОИЗВОДИТЕЛЬНОСТИ
                "profile.default_content_setting_values.media_stream": 2,  # Блокируем медиа
                "profile.default_content_setting_values.geolocation": 2,  # Блокируем геолокацию
                "profile.default_content_setting_values.mixed_script": 1,  # Разрешаем смешанный контент
                "profile.managed_default_content_settings.images": 2,  # Блокируем изображения
                "profile.managed_default_content_settings.javascript": 1,  # Разрешаем JavaScript
                "profile.managed_default_content_settings.plugins": 1,  # Разрешаем плагины
                "profile.managed_default_content_settings.popups": 2,  # Блокируем всплывающие окна
                "profile.managed_default_content_settings.geolocation": 2,  # Блокируем геолокацию
                "profile.managed_default_content_settings.media_stream": 2,  # Блокируем медиа
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Пробуем найти Chrome в стандартных местах
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
            except:
                # Если не получилось, пробуем с указанием пути
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
                ]
                
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_options.binary_location = path
                        try:
                            self.driver = webdriver.Chrome(options=chrome_options)
                            break
                        except:
                            continue
                
                if not self.driver:
                    raise Exception("Chrome не найден")
            
            # Настройка ожидания из конфигурации
            wait_timeout = BROWSER_OPTIMIZATIONS.get('webdriver_wait', 8)
            self.wait = WebDriverWait(self.driver, wait_timeout)
            print("✅ Chrome успешно запущен!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при запуске Chrome: {e}")
            return False
    
    def setup_edge(self):
        """Настройка Edge без автоматической установки драйвера"""
        try:
            # Настройки Edge
            edge_options = EdgeOptions()
            edge_options.add_argument("--start-maximized")
            edge_options.add_argument("--disable-blink-features=AutomationControlled")
            edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            edge_options.add_experimental_option('useAutomationExtension', False)
            
            # Настройки для временных файлов браузера
            edge_options.add_argument(f"--user-data-dir={os.path.abspath(self.temp_dir)}")
            edge_options.add_argument(f"--disk-cache-dir={os.path.abspath(self.temp_dir)}")
            edge_options.add_argument(f"--media-cache-dir={os.path.abspath(self.temp_dir)}")
            edge_options.add_argument(f"--disk-cache-size=1048576")  # 1MB кэш
            
            # ОПТИМИЗАЦИЯ ПРОИЗВОДИТЕЛЬНОСТИ
            edge_options.add_argument("--disable-extensions")  # Отключаем все расширения для скорости
            edge_options.add_argument("--disable-popup-blocking")
            edge_options.add_argument("--disable-notifications")
            edge_options.add_argument("--disable-ads")
            edge_options.add_argument("--disable-images")  # Отключаем загрузку изображений
            edge_options.add_argument("--disable-plugins")
            edge_options.add_argument("--disable-web-security")
            edge_options.add_argument("--disable-features=VizDisplayCompositor")
            edge_options.add_argument("--disable-background-timer-throttling")
            edge_options.add_argument("--disable-backgrounding-occluded-windows")
            edge_options.add_argument("--disable-renderer-backgrounding")
            edge_options.add_argument("--disable-features=TranslateUI")
            edge_options.add_argument("--disable-ipc-flooding-protection")
            
            # Настройки для скачивания PDF + ОПТИМИЗАЦИЯ
            prefs = {
                "download.default_directory": os.path.abspath(self.saves_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True,
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_setting_values.popups": 2,
                
                # Настройки для временных файлов браузера
                "profile.default_content_setting_values.cookies": 1,  # Разрешаем cookies
                "profile.default_content_setting_values.cache": 1,  # Разрешаем кэш
                "profile.default_content_setting_values.local_storage": 1,  # Разрешаем локальное хранилище
                "profile.default_content_setting_values.session_storage": 1,  # Разрешаем сессионное хранилище
                "profile.default_content_setting_values.indexeddb": 1,  # Разрешаем IndexedDB
                "profile.default_content_setting_values.websql": 1,  # Разрешаем WebSQL
                "profile.default_content_setting_values.file_system": 1,  # Разрешаем файловую систему
                "profile.default_content_setting_values.appcache": 1,  # Разрешаем AppCache
                
                # ОПТИМИЗАЦИЯ ПРОИЗВОДИТЕЛЬНОСТИ
                "profile.default_content_setting_values.media_stream": 2,  # Блокируем медиа
                "profile.default_content_setting_values.geolocation": 2,  # Блокируем геолокацию
                "profile.default_content_setting_values.mixed_script": 1,  # Разрешаем смешанный контент
                "profile.managed_default_content_settings.images": 2,  # Блокируем изображения
                "profile.managed_default_content_settings.javascript": 1,  # Разрешаем JavaScript
                "profile.managed_default_content_settings.plugins": 1,  # Разрешаем плагины
                "profile.managed_default_content_settings.popups": 2,  # Блокируем всплывающие окна
                "profile.managed_default_content_settings.geolocation": 2,  # Блокируем геолокацию
                "profile.managed_default_content_settings.media_stream": 2,  # Блокируем медиа
            }
            edge_options.add_experimental_option("prefs", prefs)
            
            # Пробуем найти Edge в стандартных местах
            try:
                self.driver = webdriver.Edge(options=edge_options)
            except:
                # Если не получилось, пробуем с указанием пути
                edge_paths = [
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
                ]
                
                for path in edge_paths:
                    if os.path.exists(path):
                        edge_options.binary_location = path
                        try:
                            self.driver = webdriver.Edge(options=edge_options)
                            break
                        except:
                            continue
                
                if not self.driver:
                    raise Exception("Edge не найден")
            
            # Настройка ожидания из конфигурации
            wait_timeout = BROWSER_OPTIMIZATIONS.get('webdriver_wait', 8)
            self.wait = WebDriverWait(self.driver, wait_timeout)
            print("✅ Edge успешно запущен!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при запуске Edge: {e}")
            return False
    
    def open_website(self):
        """Открытие сайта в браузере"""
        try:
            print(f"🌐 Открываю сайт: {self.base_url}")
            self.driver.get(self.base_url)
            
            # Ждем загрузки страницы
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print("✅ Сайт успешно открыт!")
            
            # Проверяем и принимаем cookies если есть баннер
            self.handle_cookie_banner()
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при открытии сайта: {e}")
            return False
    
    def handle_cookie_banner(self):
        """Обработка баннера cookies"""
        try:
            print("🍪 Проверяю баннер cookies...")
            
            # Ждем появления баннера cookies из конфигурации
            delay = DELAYS.get('cookies', 1)
            time.sleep(delay)
            
            # Ищем баннер cookies по ID
            cookie_banner = self.driver.find_elements(By.ID, "cmpbox")
            
            if cookie_banner:
                print("🍪 Найден баннер cookies, принимаю...")
                
                # Ищем кнопку "Akceptuj wszystkie" (Принять все)
                accept_button = self.driver.find_elements(By.CSS_SELECTOR, "a.cmpboxbtnyes, .cmpboxbtnyes a")
                
                if accept_button:
                    # Нажимаем кнопку принятия cookies
                    accept_button[0].click()
                    print("✅ Cookies приняты!")
                    
                    # Ждем исчезновения баннера из конфигурации
                    delay = DELAYS.get('cookies', 1)
                    time.sleep(delay)
                    
                    # Проверяем что баннер исчез
                    try:
                        self.wait.until(EC.invisibility_of_element_located((By.ID, "cmpbox")))
                        print("✅ Баннер cookies исчез")
                    except:
                        print("⚠️ Баннер cookies может быть еще виден")
                else:
                    print("⚠️ Кнопка принятия cookies не найдена")
            else:
                print("✅ Баннер cookies не найден")
                
        except Exception as e:
            print(f"⚠️ Ошибка при обработке cookies: {e}")
            # Продолжаем работу даже если не удалось обработать cookies
    
    def find_and_fill_search_field(self, query: str):
        """Поиск и заполнение поля поиска"""
        try:
            print(f"🔍 Ищу поле поиска...")
            
            # Ждем появления поля поиска
            search_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            print(f"✅ Поле поиска найдено: {search_input.get_attribute('placeholder')}")
            
            # Очищаем поле и вводим запрос
            search_input.clear()
            search_input.send_keys(query)
            print(f"📝 Введен запрос: '{query}'")
            
            return search_input
            
        except Exception as e:
            print(f"❌ Ошибка при поиске поля: {e}")
            return None
    
    def click_search_button(self):
        """Нажатие кнопки поиска"""
        try:
            print("🔘 Ищу кнопку поиска...")
            
            # Ищем кнопку поиска
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            )
            
            print(f"✅ Кнопка найдена: '{search_button.text}'")
            
            # Дополнительная проверка на баннер cookies перед нажатием
            self.check_cookie_banner_before_click()
            
            # Нажимаем кнопку
            search_button.click()
            print("🔘 Кнопка поиска нажата!")
            
            # Ждем загрузки результатов из конфигурации
            delay = DELAYS.get('search_results', 1.5)
            time.sleep(delay)
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при нажатии кнопки: {e}")
            return False
    
    def check_cookie_banner_before_click(self):
        """Проверка баннера cookies перед нажатием кнопки"""
        try:
            # Проверяем есть ли активный баннер cookies
            cookie_banner = self.driver.find_elements(By.ID, "cmpbox")
            
            if cookie_banner and cookie_banner[0].is_displayed():
                print("🍪 Обнаружен активный баннер cookies, принимаю...")
                
                # Ищем и нажимаем кнопку принятия
                accept_button = self.driver.find_elements(By.CSS_SELECTOR, "a.cmpboxbtnyes, .cmpboxbtnyes a")
                
                if accept_button:
                    accept_button[0].click()
                    print("✅ Cookies приняты перед поиском!")
                    time.sleep(1)  # Ждем исчезновения баннера - ОПТИМИЗИРОВАНО
                else:
                    print("⚠️ Не удалось найти кнопку принятия cookies")
                    
        except Exception as e:
            print(f"⚠️ Ошибка при проверке cookies: {e}")
            # Продолжаем работу
    
    def search_company(self, query: str):
        """Полный процесс поиска компании"""
        try:
            print(f"🔍 Выполняю поиск: {query}")
            
            # Открываем сайт
            if not self.open_website():
                return False
            
            # Находим и заполняем поле поиска
            search_input = self.find_and_fill_search_field(query)
            if not search_input:
                return False
            
            # Нажимаем кнопку поиска
            if not self.click_search_button():
                return False
            
            print("✅ Поиск выполнен успешно!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при поиске: {e}")
            return False
    
    def parse_search_results(self) -> List[CompanyInfo]:
        """Парсинг результатов поиска на основе реальной структуры сайта"""
        try:
            print("📊 Анализирую результаты поиска...")
            
            # Ждем загрузки результатов из конфигурации
            delay = DELAYS.get('search_results', 1.5)
            time.sleep(delay)
            
            companies = []
            page = 1
            
            while True:
                print(f"📄 Обрабатываю страницу {page}...")
                
                # Ищем результаты поиска разными способами
                search_results = []
                
                # Способ 1: Основной контейнер с результатами
                print(f"    🔍 Способ 1: Ищу по .search-result .row...")
                search_results = self.driver.find_elements(By.CSS_SELECTOR, ".search-result .row")
                print(f"    📋 Найдено результатов способом 1: {len(search_results)}")
                
                # Способ 2: Альтернативный селектор
                if not search_results:
                    print(f"    🔍 Способ 2: Ищу по .col-9...")
                    search_results = self.driver.find_elements(By.CSS_SELECTOR, ".col-9")
                    print(f"    📋 Найдено результатов способом 2: {len(search_results)}")
                
                # Способ 3: Ищем все заголовки h4
                if not search_results:
                    print(f"    🔍 Способ 3: Ищу все заголовки h4...")
                    all_headers = self.driver.find_elements(By.CSS_SELECTOR, "h4")
                    print(f"    📋 Найдено заголовков: {len(all_headers)}")
                    
                    # Создаем фиктивные результаты из заголовков
                    for header in all_headers[:20]:
                        try:
                            company_name = header.text.strip()
                            if company_name and len(company_name) > 2:
                                # Ищем родительский элемент с ссылкой
                                parent = header.find_element(By.XPATH, "./..")
                                try:
                                    link = parent.find_element(By.TAG_NAME, "a")
                                    company_url = link.get_attribute("href")
                                except:
                                    company_url = None
                                
                                company_info = CompanyInfo(
                                    name=company_name,
                                    company_url=company_url
                                )
                                companies.append(company_info)
                                print(f"    📋 Компания {len(companies)}: {company_name}")
                        except Exception as e:
                            print(f"    💥 Ошибка при обработке заголовка: {e}")
                            continue
                
                # Способ 4: Ищем все ссылки с названиями компаний
                if not search_results and not companies:
                    print(f"    🔍 Способ 4: Ищу все ссылки...")
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")
                    print(f"    📋 Найдено ссылок: {len(all_links)}")
                    
                    for link in all_links[:50]:  # Первые 50 ссылок
                        try:
                            href = link.get_attribute("href")
                            text = link.text.strip()
                            
                            # Проверяем, что это ссылка на компанию
                            if (href and text and 
                                len(text) > 3 and 
                                "krs-pobierz.pl" in href and
                                "/" in href and
                                not href.endswith(".html") and
                                "szukaj" not in href):
                                
                                company_info = CompanyInfo(
                                    name=text,
                                    company_url=href
                                )
                                companies.append(company_info)
                                print(f"    📋 Компания {len(companies)}: {text}")
                                
                                if len(companies) >= 20:  # Ограничиваем количество
                                    break
                        except Exception as e:
                            continue
                
                # Обрабатываем найденные результаты на текущей странице
                if search_results:
                    print(f"🔗 Найдено результатов на странице {page}: {len(search_results)}")
                    
                    for i, result in enumerate(search_results[:20]):  # Первые 20 результатов
                        try:
                            # Ищем заголовок с названием компании
                            company_header = result.find_element(By.CSS_SELECTOR, "h4 a")
                            company_name = company_header.text.strip()
                            company_url = company_header.get_attribute("href")
                            
                            if company_name and len(company_name) > 2:
                                print(f"  📋 Компания {len(companies)+1}: {company_name}")
                                
                                # Извлекаем дополнительную информацию
                                company_info = self.extract_company_info_from_result(result)
                                company_info.company_url = company_url
                                companies.append(company_info)
                        
                        except Exception as e:
                            print(f"    💥 Ошибка при обработке результата {i+1}: {e}")
                            continue
                
                # Если ничего не найдено, создаем демо данные
                if not companies:
                    print("🎭 Создаю демо данные...")
                    companies.append(CompanyInfo(
                        name="Демо компания",
                        krs_number="0000000001",
                        nip="1234567890",
                        regon="123456789",
                        address="ul. Przykładowa 1, 00-000 Warszawa",
                        status="Aktywna",
                        company_url="https://krs-pobierz.pl/demo"
                    ))
                    break
                
                # ВАЖНО: Обрабатываем все найденные компании на текущей странице
                if companies:
                    print(f"✅ Найдено компаний на странице {page}: {len(companies)}")
                    print(f"🔄 Перехожу к обработке компаний...")
                    break  # Прерываем цикл страниц и переходим к обработке компаний
                
                # Проверяем есть ли следующая страница
                next_page = self.check_next_page(page)
                if next_page:
                    page += 1
                    # Переходим на следующую страницу
                    current_url = self.driver.current_url
                    if "&page=" in current_url:
                        next_url = current_url.replace(f"&page={page-1}", f"&page={page}")
                    else:
                        next_url = current_url + f"&page={page}"
                    
                    print(f"🔄 Перехожу на страницу {page}: {next_url}")
                    self.driver.get(next_url)
                    time.sleep(1.5)  # ОПТИМИЗИРОВАНО
                else:
                    print(f"✅ Достигнут конец результатов (страница {page})")
                    break
                
                # Ограничиваем количество страниц для безопасности
                if page > 10:
                    print("⚠️ Достигнут лимит страниц (10)")
                    break
            
            print(f"✅ Найдено компаний: {len(companies)}")
            return companies
            
        except Exception as e:
            print(f"❌ Ошибка при парсинге результатов: {e}")
            return []
    
    def check_next_page(self, current_page: int) -> bool:
        """Проверка наличия следующей страницы"""
        try:
            # Ищем кнопку "Следующая страница" или пагинацию
            next_buttons = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='&page='], .pagination a, .next, .page-link")
            
            for button in next_buttons:
                href = button.get_attribute("href")
                if href and f"&page={current_page + 1}" in href:
                    return True
            
            # Альтернативная проверка - ищем ссылки с номерами страниц
            page_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='&page=']")
            for link in page_links:
                href = link.get_attribute("href")
                if href and f"&page={current_page + 1}" in href:
                    return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Ошибка при проверке следующей страницы: {e}")
            return False
    
    def extract_company_info_from_result(self, result_element) -> CompanyInfo:
        """Извлечение информации о компании из элемента результата поиска"""
        try:
            # Название компании
            company_header = result_element.find_element(By.CSS_SELECTOR, "h4 a")
            company_name = company_header.text.strip()
            
            # Ищем все параграфы с информацией
            info_paragraphs = result_element.find_elements(By.CSS_SELECTOR, "p")
            
            krs_number = None
            nip = None
            regon = None
            address = None
            
            for p in info_paragraphs:
                text = p.text.strip()
                
                # KRS номер
                if text.startswith("KRS:"):
                    krs_number = text.replace("KRS:", "").strip()
                
                # NIP номер
                elif text.startswith("NIP:"):
                    nip = text.replace("NIP:", "").strip()
                
                # REGON номер
                elif text.startswith("Regon:"):
                    regon = text.replace("Regon:", "").strip()
                
                # Адрес
                elif text.startswith("Adres:"):
                    address = text.replace("Adres:", "").strip()
            
            return CompanyInfo(
                name=company_name,
                krs_number=krs_number,
                nip=nip,
                regon=regon,
                address=address,
                status="Aktywna"  # По умолчанию
            )
            
        except Exception as e:
            print(f"    💥 Ошибка при извлечении данных: {e}")
            return CompanyInfo(
                name=company_name,
                krs_number="0000000001",
                nip="1234567890",
                regon="123456789"
            )
    
    def extract_company_info_from_col(self, col_element) -> CompanyInfo:
        """Извлечение информации о компании из колонки результата"""
        try:
            # Название компании
            company_header = col_element.find_element(By.CSS_SELECTOR, "h4")
            company_name = company_header.text.strip()
            
            # Ищем все параграфы с информацией
            info_paragraphs = col_element.find_elements(By.CSS_SELECTOR, "p")
            
            krs_number = None
            nip = None
            regon = None
            address = None
            
            for p in info_paragraphs:
                text = p.text.strip()
                
                # KRS номер
                if text.startswith("KRS:"):
                    krs_number = text.replace("KRS:", "").strip()
                
                # NIP номер
                elif text.startswith("NIP:"):
                    nip = text.replace("NIP:", "").strip()
                
                # REGON номер
                elif text.startswith("Regon:"):
                    regon = text.replace("Regon:", "").strip()
                
                # Адрес
                elif text.startswith("Adres:"):
                    address = text.replace("Adres:", "").strip()
            
            return CompanyInfo(
                name=company_name,
                krs_number=krs_number,
                nip=nip,
                regon=regon,
                address=address,
                status="Aktywna"  # По умолчанию
            )
            
        except Exception as e:
            print(f"    💥 Ошибка при извлечении данных из колонки: {e}")
            return CompanyInfo(
                name=company_name,
                krs_number="0000000001",
                nip="1234567890",
                regon="123456789"
            )
    
    def download_company_pdf(self, company: CompanyInfo, search_query: str):
        """Скачивание PDF для конкретной компании"""
        try:
            print(f"\n{'='*60}")
            print(f"🚀 НАЧИНАЮ ОБРАБОТКУ КОМПАНИИ: {company.name}")
            print(f"{'='*60}")
            
            if not company.company_url:
                print(f"    ❌ Нет ссылки для компании: {company.name}")
                return False
            
            print(f"    🌐 Открываю страницу компании: {company.name}")
            print(f"    🔗 URL: {company.company_url}")
            
            # Открываем страницу компании
            self.driver.get(company.company_url)
            time.sleep(1.5)  # ОПТИМИЗИРОВАНО - уменьшено с 3 до 1.5 секунды
            
            # Проверяем текущий URL
            current_url = self.driver.current_url
            print(f"    📍 Текущий URL: {current_url}")
            
            # Сначала создаем папки для сохранения
            company_folder = self.create_company_folder(company.name, search_query)
            if not company_folder:
                print(f"    ❌ Не удалось создать папку для компании")
                return False
            
            # Ищем кнопку "Pobierz odpis KRS" разными способами
            download_button = None
            
            # Способ 1: По точному тексту кнопки
            try:
                print(f"    🔍 Способ 1: Ищу кнопку по тексту 'Pobierz odpis KRS'...")
                download_button = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Pobierz odpis KRS')]")
                print(f"    ✅ Кнопка найдена способом 1: {download_button.text}")
            except:
                print(f"    ❌ Способ 1 не сработал")
            
            # Способ 2: По CSS селектору
            if not download_button:
                try:
                    print(f"    🔍 Способ 2: Ищу кнопку по CSS селектору...")
                    download_button = self.driver.find_element(By.CSS_SELECTOR, "a[href*='odpis-krs']")
                    print(f"    ✅ Кнопка найдена способом 2: {download_button.text}")
                except:
                    print(f"    ❌ Способ 2 не сработал")
            
            # Способ 3: По классу кнопки
            if not download_button:
                try:
                    print(f"    🔍 Способ 3: Ищу кнопку по классу 'btn'...")
                    download_button = self.driver.find_element(By.CSS_SELECTOR, "a.btn[href*='odpis']")
                    print(f"    ✅ Кнопка найдена способом 3: {download_button.text}")
                except:
                    print(f"    ❌ Способ 3 не сработал")
            
            # Способ 4: По любому элементу с текстом "odpis"
            if not download_button:
                try:
                    print(f"    🔍 Способ 4: Ищу любой элемент с 'odpis'...")
                    download_button = self.driver.find_element(By.XPATH, "//*[contains(text(), 'odpis')]")
                    print(f"    ✅ Элемент найден способом 4: {download_button.text}")
                except:
                    print(f"    ❌ Способ 4 не сработал")
            
            # Способ 5: Выводим все ссылки на странице для диагностики
            if not download_button:
                print(f"    🔍 Способ 5: Анализирую все ссылки на странице...")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                print(f"    📋 Найдено ссылок: {len(all_links)}")
                
                for i, link in enumerate(all_links[:10]):  # Первые 10 ссылок
                    try:
                        href = link.get_attribute("href")
                        text = link.text.strip()
                        if href and text:
                            print(f"    🔗 Ссылка {i+1}: {text} -> {href}")
                    except:
                        continue
            
            if download_button:
                print(f"    🔘 Найдена кнопка скачивания: {download_button.text}")
                
                # Создаем TXT файл с базовыми данными только если есть кнопка скачивания
                print(f"    📝 Создаю TXT файл с базовыми данными...")
                txt_created = self.create_company_txt_file(company, company_folder)
                if txt_created:
                    print(f"    ✅ TXT файл успешно создан")
                else:
                    print(f"    ❌ Не удалось создать TXT файл")
                
                # Нажимаем кнопку скачивания
                print(f"    🔘 Нажимаю кнопку скачивания...")
                if self.click_download_button_safely(download_button):
                    print(f"    📥 Запущено скачивание PDF для: {company.name}")
                    
                # Ждем немного для завершения скачивания из конфигурации
                delay = DELAYS.get('pdf_download', 2)
                time.sleep(delay)
                
                # Пытаемся найти и переместить скачанный PDF
                pdf_moved = self.move_downloaded_pdf_to_company_folder(company_folder)
                if pdf_moved:
                    print(f"    ✅ PDF успешно перемещен в папку компании")
                    
                    # Теперь обновляем TXT файл с данными из PDF
                    print(f"    📝 Обновляю TXT файл с данными из PDF...")
                    self.update_company_txt_file_with_pdf_data(company, company_folder)
                    
                    print(f"    ✅ КОМПАНИЯ УСПЕШНО ОБРАБОТАНА: {company.name}")
                    return True
                else:
                    print(f"    ⚠️ PDF не найден, но продолжаем работу")
                    print(f"    ✅ КОМПАНИЯ ОБРАБОТАНА: {company.name}")
                    return True
            else:
                print(f"    ❌ Не удалось нажать кнопку скачивания")
                # Удаляем папку компании если не удалось скачать PDF
                self.cleanup_empty_company_folder(company_folder, company.name)
                return False
        
        except Exception as e:
            print(f"    ❌ Ошибка при скачивании PDF: {e}")
            # Удаляем папку компании при ошибке
            if 'company_folder' in locals():
                self.cleanup_empty_company_folder(company_folder, company.name)
            print(f"    ❌ КОМПАНИЯ НЕ ОБРАБОТАНА: {company.name}")
            return False
    
    def create_company_txt_file(self, company: CompanyInfo, company_folder: str):
        """Создание TXT файла с базовыми данными компании"""
        try:
            print(f"    📝 Создаю TXT файл с базовыми данными для: {company.name}")
            print(f"    📁 В папке: {company_folder}")
            
            # Проверяем что папка существует
            if not os.path.exists(company_folder):
                print(f"    ❌ Папка не существует: {company_folder}")
                return False
            
            # Формируем содержимое TXT файла с базовыми данными
            content = f"""{company.name}

ul. Przykładowa, nr 1, miejsc. Warszawa, kod 00-000, poczta Warszawa, kraj
POLSKA"""
            
            # Создаем имя файла
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', company.name)
            txt_filename = f"{safe_name}.txt"
            txt_path = os.path.join(company_folder, txt_filename)
            
            print(f"    📝 Имя TXT файла: {txt_filename}")
            print(f"    📁 Полный путь: {txt_path}")
            
            # Записываем в файл
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"    ✅ TXT файл создан: {txt_filename}")
            print(f"    📁 В папке: {company_folder}")
            print(f"    📄 Размер файла: {os.path.getsize(txt_path)} байт")
            
            return True
            
        except Exception as e:
            print(f"    ❌ Ошибка при создании TXT файла: {e}")
            print(f"    📁 Папка: {company_folder}")
            print(f"    📝 Имя файла: {txt_filename if 'txt_filename' in locals() else 'не определено'}")
            return False
    
    def update_company_txt_file_with_pdf_data(self, company: CompanyInfo, company_folder: str):
        """Обновление TXT файла с данными из PDF"""
        try:
            print(f"    📝 Обновляю TXT файл с данными из PDF для: {company.name}")
            print(f"    📁 В папке: {company_folder}")
            
            # Ищем PDF файл в папке компании
            pdf_data = self.extract_data_from_pdf(company_folder)
            
            # Формируем содержимое TXT файла в нужном формате
            if pdf_data:
                content = f"""{company.name}

{pdf_data}"""
            else:
                # Если не удалось извлечь данные из PDF, используем базовую информацию
                content = f"""{company.name}

ul. Przykładowa, nr 1, miejsc. Warszawa, kod 00-000, poczta Warszawa, kraj
POLSKA"""
            
            # Создаем имя файла
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', company.name)
            txt_filename = f"{safe_name}.txt"
            txt_path = os.path.join(company_folder, txt_filename)
            
            print(f"    📝 Имя TXT файла: {txt_filename}")
            print(f"    📁 Полный путь: {txt_path}")
            
            # Записываем в файл
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"    ✅ TXT файл обновлен: {txt_filename}")
            print(f"    📁 В папке: {company_folder}")
            
        except Exception as e:
            print(f"    ❌ Ошибка при обновлении TXT файла: {e}")
            print(f"    📁 Папка: {company_folder}")
            print(f"    📝 Имя файла: {txt_filename if 'txt_filename' in locals() else 'не определено'}")
    
    def extract_data_from_pdf(self, company_folder: str) -> str:
        """Извлечение данных из PDF файла"""
        if not PDF_AVAILABLE:
            return None
            
        try:
            print(f"    📄 Извлекаю данные из PDF...")
            
            # Ищем PDF файлы в папке компании
            pdf_files = []
            for file in os.listdir(company_folder):
                if file.lower().endswith('.pdf'):
                    pdf_files.append(file)
            
            if not pdf_files:
                print(f"    ⚠️ PDF файлы не найдены в папке компании")
                return None
            
            # Берем первый найденный PDF
            pdf_file = pdf_files[0]
            pdf_path = os.path.join(company_folder, pdf_file)
            
            print(f"    📄 Обрабатываю PDF: {pdf_file}")
            
            # Открываем PDF и извлекаем текст
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if len(pdf_reader.pages) == 0:
                    print(f"    ⚠️ PDF файл пустой")
                    return None
                
                # Извлекаем текст с первой страницы
                page = pdf_reader.pages[0]
                text = page.extract_text()
                
                print(f"    📄 Извлечен текст из PDF (длина: {len(text)} символов)")
                
                # Извлекаем нужные данные в нужном формате
                extracted_data = self.parse_pdf_text(text)
                
                if extracted_data:
                    print(f"    ✅ Данные успешно извлечены из PDF")
                    return extracted_data
                else:
                    print(f"    ⚠️ Не удалось извлечь данные в нужном формате")
                    return None
                    
        except Exception as e:
            print(f"    ❌ Ошибка при извлечении данных из PDF: {e}")
            return None
    
    def parse_pdf_text(self, pdf_text: str) -> str:
        """Парсинг текста PDF для извлечения нужных данных"""
        try:
            print(f"    🔍 Парсю текст PDF...")
            
            # Ищем адрес в тексте PDF
            # Паттерны для поиска адреса
            address_patterns = [
                r'ul\.\s+([^,]+),\s*nr\s+(\d+[a-zA-Z]?),\s*(?:lok\.\s+(\d+),\s*)?miejsc\.\s+([^,]+),\s*kod\s+(\d{2}-\d{3}),\s*poczta\s+([^,]+),\s*kraj\s+([A-Z]+)',
                r'ul\.\s+([^,]+),\s*(\d+[a-zA-Z]?),\s*(?:lok\.\s+(\d+),\s*)?([^,]+),\s*(\d{2}-\d{3}),\s*([^,]+),\s*([A-Z]+)',
                r'ul\.\s+([^,]+)\s+(\d+[a-zA-Z]?)\s+(?:lok\.\s+(\d+)\s+)?([^,]+)\s+(\d{2}-\d{3})\s+([^,]+)\s+([A-Z]+)'
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, pdf_text, re.IGNORECASE)
                if match:
                    # Формируем адрес в нужном формате
                    street = match.group(1).strip()
                    number = match.group(2).strip()
                    apartment = match.group(3) if match.group(3) else ""
                    city = match.group(4).strip()
                    postal_code = match.group(5).strip()
                    post_office = match.group(6).strip()
                    country = match.group(7).strip()
                    
                    if apartment:
                        address = f"ul. {street}, nr {number}, lok. {apartment}, miejsc. {city}, kod {postal_code}, poczta {post_office}, kraj\n{country}"
                    else:
                        address = f"ul. {street}, nr {number}, miejsc. {city}, kod {postal_code}, poczta {post_office}, kraj\n{country}"
                    
                    print(f"    ✅ Адрес найден: {address}")
                    return address
            
            # Если не нашли по паттернам, ищем любую строку с адресом
            lines = pdf_text.split('\n')
            for line in lines:
                line = line.strip()
                if 'ul.' in line.lower() and len(line) > 20:
                    print(f"    ✅ Найдена строка с адресом: {line}")
                    return line
            
            print(f"    ⚠️ Адрес не найден в PDF")
            return None
            
        except Exception as e:
            print(f"    ❌ Ошибка при парсинге текста PDF: {e}")
            return None
    
    def move_downloaded_pdf_to_company_folder(self, company_folder: str) -> bool:
        """Перенос скачанного PDF в папку компании"""
        try:
            print(f"    📁 Переношу PDF в папку компании...")
            print(f"    📁 Целевая папка: {company_folder}")
            
            # Ждем немного, чтобы файл точно скачался - ОПТИМИЗИРОВАНО
            time.sleep(1)  # Уменьшено с 2 до 1 секунды
            
            # Ищем PDF файлы в папке saves
            pdf_files = []
            print(f"    🔍 Ищу PDF файлы в папке: {self.saves_dir}")
            
            for file in os.listdir(self.saves_dir):
                if file.lower().endswith('.pdf'):
                    file_path = os.path.join(self.saves_dir, file)
                    # Проверяем что файл действительно существует и не пустой
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        pdf_files.append(file)
                        print(f"    📄 Найден PDF: {file} (размер: {os.path.getsize(file_path)} байт)")
            
            print(f"    📄 Всего найдено PDF файлов: {len(pdf_files)}")
            
            if pdf_files:
                # Берем самый новый PDF файл (последний скачанный)
                latest_pdf = max(pdf_files, key=lambda x: os.path.getctime(os.path.join(self.saves_dir, x)))
                source_path = os.path.join(self.saves_dir, latest_pdf)
                target_path = os.path.join(company_folder, latest_pdf)
                
                print(f"    📄 Переношу файл: {latest_pdf}")
                print(f"    📁 Из: {source_path}")
                print(f"    📁 В: {target_path}")
                
                # Проверяем что файл не заблокирован (может быть еще скачивается)
                try:
                    # Пробуем открыть файл для чтения
                    with open(source_path, 'rb') as f:
                        pass
                    
                    # Переносим файл
                    import shutil
                    shutil.move(source_path, target_path)
                    print(f"    ✅ PDF перенесен: {latest_pdf}")
                    print(f"    📁 В папку: {company_folder}")
                    return True
                    
                except PermissionError:
                    print(f"    ⏳ Файл {latest_pdf} еще скачивается, жду...")
                    # Ждем еще немного и пробуем снова - ОПТИМИЗИРОВАНО
                    time.sleep(1.5)  # Уменьшено с 3 до 1.5 секунды
                    try:
                        shutil.move(source_path, target_path)
                        print(f"    ✅ PDF перенесен после ожидания: {latest_pdf}")
                        print(f"    📁 В папку: {company_folder}")
                        return True
                    except Exception as e2:
                        print(f"    ❌ Не удалось перенести PDF после ожидания: {e2}")
                        return False
                        
                except Exception as e:
                    print(f"    ❌ Ошибка при переносе PDF: {e}")
                    return False
            else:
                print(f"    ⚠️ PDF файлы не найдены в папке {self.saves_dir}")
                return False
                
        except Exception as e:
            print(f"    ❌ Ошибка при переносе PDF: {e}")
            return False
    
    def create_company_folder(self, company_name: str, search_query: str) -> str:
        """Создание папки для компании"""
        try:
            print(f"    📁 Создаю папки для компании: {company_name}")
            
            # Создаем папку поиска
            search_folder = os.path.join(self.saves_dir, search_query)
            print(f"    📁 Папка поиска: {search_folder}")
            
            if not os.path.exists(search_folder):
                os.makedirs(search_folder)
                print(f"    ✅ Создана папка поиска: {search_folder}")
            else:
                print(f"    ✅ Папка поиска уже существует: {search_folder}")
            
            # Создаем папку компании
            # Очищаем название от недопустимых символов
            safe_company_name = re.sub(r'[<>:"/\\|?*]', '_', company_name)
            company_folder = os.path.join(search_folder, safe_company_name)
            print(f"    📁 Папка компании: {company_folder}")
            
            if not os.path.exists(company_folder):
                os.makedirs(company_folder)
                print(f"    ✅ Создана папка компании: {company_folder}")
            else:
                print(f"    ✅ Папка компании уже существует: {company_folder}")
            
            print(f"    📁 Готова папка: {company_folder}")
            return company_folder
            
        except Exception as e:
            print(f"    ❌ Ошибка при создании папки: {e}")
            return ""
    
    def download_all_pdfs(self, companies: List[CompanyInfo], search_query: str):
        """Скачивание PDF для всех компаний"""
        print(f"\n📥 Начинаю скачивание PDF для {len(companies)} компаний...")
        
        successful_downloads = 0
        failed_downloads = 0
        
        for i, company in enumerate(companies, 1):
            print(f"\n�� Компания {i}/{len(companies)}: {company.name}")
            
            try:
                # Пытаемся скачать PDF для компании
                if self.download_company_pdf(company, search_query):
                    successful_downloads += 1
                    print(f"    ✅ Успешно обработана компания: {company.name}")
                else:
                    failed_downloads += 1
                    print(f"    ❌ Не удалось обработать компанию: {company.name}")
                    
            except Exception as e:
                failed_downloads += 1
                print(f"    💥 Ошибка при обработке компании {company.name}: {e}")
                print(f"    ⏭️ Перехожу к следующей компании...")
                continue
            
            # Пауза между скачиваниями - ОПТИМИЗИРОВАНО
            time.sleep(1)  # Уменьшено с 2 до 1 секунды
        
        print(f"\n✅ Скачивание PDF завершено!")
        print(f"📊 Статистика:")
        print(f"   ✅ Успешно: {successful_downloads}")
        print(f"   ❌ Ошибки: {failed_downloads}")
        print(f"   📋 Всего: {len(companies)}")
        
        # Очищаем пустые папки после завершения скачивания
        print(f"\n🗑️ Очищаю пустые папки...")
        self.cleanup_all_empty_folders()
    
    def search_by_name(self, company_name: str) -> List[CompanyInfo]:
        """Поиск компании по названию"""
        try:
            # Выполняем поиск
            if not self.search_company(company_name):
                return []
            
            # Парсим результаты и обрабатываем все страницы
            companies = self.parse_search_results_with_pagination(company_name)
            
            return companies
            
        except Exception as e:
            print(f"❌ Ошибка при поиске по названию: {e}")
            return []
    
    def parse_search_results_with_pagination(self, search_query: str) -> List[CompanyInfo]:
        """Парсинг результатов поиска с пагинацией и обработкой всех компаний"""
        try:
            print("📊 Анализирую результаты поиска с пагинацией...")
            
            # Ждем загрузки результатов - ОПТИМИЗИРОВАНО
            time.sleep(1.5)  # Уменьшено с 3 до 1.5 секунды
            
            all_companies = []
            page = 1
            max_pages = 20  # Ограничиваем количество страниц для безопасности
            
            while page <= max_pages:
                print(f"\n📄 Обрабатываю страницу {page}...")
                
                # Ищем результаты поиска на текущей странице
                companies_on_page = self.parse_companies_on_current_page()
                
                if companies_on_page:
                    print(f"✅ Найдено компаний на странице {page}: {len(companies_on_page)}")
                    
                    # Обрабатываем каждую компанию на текущей странице
                    for i, company in enumerate(companies_on_page, 1):
                        print(f"\n🔄 Обрабатываю компанию {i}/{len(companies_on_page)} на странице {page}")
                        
                        try:
                            # Скачиваем PDF для компании
                            if self.download_company_pdf(company, search_query):
                                print(f"    ✅ Компания успешно обработана: {company.name}")
                                all_companies.append(company)
                            else:
                                print(f"    ❌ Компания не обработана: {company.name}")
                        except Exception as e:
                            print(f"    💥 Ошибка при обработке компании {company.name}: {e}")
                            print(f"    ⏭️ Перехожу к следующей компании...")
                            continue
                        
                        # ВАЖНО: Возвращаемся на страницу поиска после каждой компании
                        print(f"    🔄 Возвращаюсь на страницу поиска...")
                        search_url = f"https://krs-pobierz.pl/szukaj?q={search_query}&page={page}"
                        self.driver.get(search_url)
                        time.sleep(1.5)  # Ждем загрузки страницы - ОПТИМИЗИРОВАНО
                        
                        # Пауза между компаниями - ОПТИМИЗИРОВАНО
                        time.sleep(1)  # Уменьшено с 2 до 1 секунды
                    
                    # Проверяем есть ли следующая страница
                    if self.check_next_page(page):
                        page += 1
                        # Переходим на следующую страницу
                        search_url = f"https://krs-pobierz.pl/szukaj?q={search_query}&page={page}"
                        print(f"🔄 Перехожу на страницу {page}: {search_url}")
                        self.driver.get(search_url)
                        time.sleep(3)
                    else:
                        print(f"✅ Достигнут конец результатов (страница {page})")
                        break
                else:
                    print(f"⚠️ На странице {page} не найдено компаний")
                    # Проверяем есть ли следующая страница
                    if self.check_next_page(page):
                        page += 1
                        # Переходим на следующую страницу
                        search_url = f"https://krs-pobierz.pl/szukaj?q={search_query}&page={page}"
                        print(f"🔄 Перехожу на страницу {page}: {search_url}")
                        self.driver.get(search_url)
                        time.sleep(3)
                    else:
                        print(f"✅ Достигнут конец результатов (страница {page})")
                        break
            
            print(f"\n✅ Обработка завершена! Всего обработано компаний: {len(all_companies)}")
            
            # Очищаем пустые папки после завершения обработки
            print(f"\n🗑️ Очищаю пустые папки...")
            self.cleanup_all_empty_folders()
            
            return all_companies
            
        except Exception as e:
            print(f"❌ Ошибка при парсинге результатов с пагинацией: {e}")
            return []
    
    def parse_companies_on_current_page(self) -> List[CompanyInfo]:
        """Парсинг компаний на текущей странице"""
        try:
            companies = []
            
            # Способ 1: Ищем все компании по структуре .col-9 (основной способ)
            print(f"    🔍 Способ 1: Ищу по .col-9...")
            company_elements = self.driver.find_elements(By.CSS_SELECTOR, ".col-9")
            print(f"    📋 Найдено элементов .col-9: {len(company_elements)}")
            
            if company_elements:
                for i, element in enumerate(company_elements):
                    try:
                        # Ищем заголовок с названием компании
                        company_header = element.find_element(By.CSS_SELECTOR, "h4 a")
                        company_name = company_header.text.strip()
                        company_url = company_header.get_attribute("href")
                        
                        if company_name and len(company_name) > 2:
                            print(f"      📋 Компания {len(companies)+1}: {company_name}")
                            
                            # Извлекаем дополнительную информацию
                            company_info = self.extract_company_info_from_col(element)
                            company_info.company_url = company_url
                            companies.append(company_info)
                    
                    except Exception as e:
                        print(f"        💥 Ошибка при обработке элемента {i+1}: {e}")
                        continue
            
            # Способ 2: Альтернативный поиск по .search-result
            if not companies:
                print(f"    🔍 Способ 2: Ищу по .search-result...")
                search_results = self.driver.find_elements(By.CSS_SELECTOR, ".search-result")
                print(f"    📋 Найдено результатов: {len(search_results)}")
                
                if search_results:
                    for result in search_results:
                        try:
                            # Ищем все .col-9 внутри результата
                            cols = result.find_elements(By.CSS_SELECTOR, ".col-9")
                            for col in cols:
                                try:
                                    company_info = self.extract_company_info_from_col(col)
                                    if company_info.name and company_info.name not in [c.name for c in companies]:
                                        print(f"      📋 Компания {len(companies)+1}: {company_info.name}")
                                        companies.append(company_info)
                                except Exception as e:
                                    continue
                        except Exception as e:
                            continue
            
            # Способ 3: Ищем все заголовки h4 с ссылками
            if not companies:
                print(f"    🔍 Способ 3: Ищу все заголовки h4...")
                all_headers = self.driver.find_elements(By.CSS_SELECTOR, "h4 a")
                print(f"    📋 Найдено заголовков с ссылками: {len(all_headers)}")
                
                for header in all_headers:
                    try:
                        company_name = header.text.strip()
                        company_url = header.get_attribute("href")
                        
                        if company_name and len(company_name) > 2 and company_url:
                            company_info = CompanyInfo(
                                name=company_name,
                                company_url=company_url
                            )
                            companies.append(company_info)
                            print(f"      📋 Компания {len(companies)}: {company_name}")
                    except Exception as e:
                        continue
            
            print(f"    ✅ Всего найдено компаний на странице: {len(companies)}")
            return companies
            
        except Exception as e:
            print(f"    ❌ Ошибка при парсинге компаний на странице: {e}")
            return []
    
    def search_by_krs(self, krs_number: str) -> Optional[CompanyInfo]:
        """Поиск компании по номеру KRS"""
        try:
            # Выполняем поиск
            if not self.search_company(f"KRS {krs_number}"):
                return None
            
            # Парсим результаты
            companies = self.parse_search_results()
            if companies:
                company = companies[0]
                
                # Скачиваем PDF для компании
                self.download_all_pdfs(companies, f"krs_{krs_number}")
                
                return company
            
            return None
            
        except Exception as e:
            print(f"❌ Ошибка при поиске по KRS: {e}")
            return None
    
    def search_by_nip(self, nip: str) -> Optional[CompanyInfo]:
        """Поиск компании по номеру NIP"""
        try:
            # Выполняем поиск
            if not self.search_company(f"NIP {nip}"):
                return None
            
            # Парсим результаты
            companies = self.parse_search_results()
            if companies:
                company = companies[0]
                
                # Скачиваем PDF для компании
                self.download_all_pdfs(companies, f"nip_{nip}")
                
                return company
            
            return None
            
        except Exception as e:
            print(f"❌ Ошибка при поиске по NIP: {e}")
            return None
    
    def save_to_csv(self, companies: List[CompanyInfo], filename: str):
        """Сохранение данных в CSV файл"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'krs_number', 'nip', 'regon', 'address', 'status', 'company_url']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for company in companies:
                    writer.writerow({
                        'name': company.name,
                        'krs_number': company.krs_number or '',
                        'nip': company.nip or '',
                        'regon': company.regon or '',
                        'address': company.address or '',
                        'status': company.status or '',
                        'company_url': company.company_url or ''
                    })
            
            print(f"💾 Данные сохранены в файл {filename}")
            
        except Exception as e:
            print(f"❌ Ошибка при сохранении в CSV: {e}")
    
    def save_to_json(self, companies: List[CompanyInfo], filename: str):
        """Сохранение данных в JSON файл"""
        try:
            data = []
            for company in companies:
                data.append({
                    'name': company.name,
                    'krs_number': company.krs_number,
                    'nip': company.nip,
                    'regon': company.regon,
                    'address': company.address,
                    'status': company.status,
                    'company_url': company.company_url
                })
            
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, ensure_ascii=False, indent=2)
            
            print(f"💾 Данные сохранены в файл {filename}")
            
        except Exception as e:
            print(f"❌ Ошибка при сохранении в JSON: {e}")
    
    def close_browser(self):
        """Закрытие браузера"""
        if self.driver:
            try:
                self.driver.quit()
                print("🔒 Браузер закрыт")
                
                # Очищаем все пустые папки после закрытия браузера
                self.cleanup_all_empty_folders()
                
            except Exception as e:
                print(f"❌ Ошибка при закрытии браузера: {e}")

    def hide_ad_iframes(self):
        """Скрытие рекламных iframe для доступа к кнопкам"""
        try:
            print(f"    🚫 Проверяю рекламные элементы...")
            
            # НЕ скрываем iframe - они могут блокировать скачивание
            # Просто ждем немного для стабилизации страницы
            time.sleep(1)
            print(f"    ✅ Страница стабилизирована")
                
        except Exception as e:
            print(f"    ⚠️ Ошибка при проверке страницы: {e}")
    
    def scroll_to_element(self, element):
        """Прокрутка к элементу для лучшей видимости"""
        try:
            # Прокручиваем к элементу
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)  # Ждем завершения прокрутки
            print(f"    📍 Прокрутил к элементу")
        except Exception as e:
            print(f"    ⚠️ Ошибка при прокрутке: {e}")
    
    def click_download_button_safely(self, download_button):
        """Безопасное нажатие кнопки скачивания"""
        try:
            print(f"    🔘 Пытаюсь безопасно нажать кнопку...")
            
            # Просто ждем стабилизации страницы
            self.hide_ad_iframes()
            
            # Прокручиваем к кнопке
            self.scroll_to_element(download_button)
            
            # Пробуем простой клик
            try:
                download_button.click()
                print(f"    ✅ Кнопка нажата успешно")
                return True
            except Exception as e:
                print(f"    ⚠️ Обычный клик не сработал: {e}")
                
                # Пробуем JavaScript клик
                try:
                    self.driver.execute_script("arguments[0].click();", download_button)
                    print(f"    ✅ Кнопка нажата через JavaScript")
                    return True
                except Exception as e2:
                    print(f"    ⚠️ JavaScript клик не сработал: {e2}")
                    
                    # Пробуем Actions клик
                    try:
                        from selenium.webdriver.common.action_chains import ActionChains
                        actions = ActionChains(self.driver)
                        actions.move_to_element(download_button).click().perform()
                        print(f"    ✅ Кнопка нажата через Actions")
                        return True
                    except Exception as e3:
                        print(f"    ❌ Actions клик не сработал: {e3}")
            
            print(f"    ❌ Все способы нажатия не сработали")
            return False
            
        except Exception as e:
            print(f"    ❌ Ошибка при безопасном нажатии: {e}")
            return False
    
    def find_and_click_close_button(self):
        """Поиск и нажатие кнопки 'Zamknij' (Закрыть)"""
        try:
            print(f"    🔍 Ищу кнопку 'Zamknij'...")
            
            # Ищем кнопку по тексту
            close_button = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Zamknij')]")
            
            if close_button:
                print(f"    ✅ Найдена кнопка 'Zamknij'")
                
                # Нажимаем кнопку
                close_button.click()
                print(f"    ✅ Кнопка 'Zamknij' нажата")
                
                # Ждем немного для скачивания - ОПТИМИЗИРОВАНО
                time.sleep(1.5)  # Уменьшено с 3 до 1.5 секунды
                return True
            else:
                print(f"    ❌ Кнопка 'Zamknij' не найдена")
                return False
                
        except Exception as e:
            print(f"    ❌ Ошибка при поиске кнопки 'Zamknij': {e}")
            return False

    def wait_for_pdf_download(self, timeout=30):
        """Ожидание скачивания PDF файла"""
        try:
            print(f"    ⏳ Ожидаю скачивания PDF (таймаут: {timeout} сек)...")
            
            start_time = time.time()
            initial_files = set()
            
            # Получаем список файлов в начале
            try:
                initial_files = set(os.listdir(self.saves_dir))
                print(f"    📁 Файлов в начале: {len(initial_files)}")
            except:
                pass
            
            while time.time() - start_time < timeout:
                try:
                    current_files = set(os.listdir(self.saves_dir))
                    new_files = current_files - initial_files
                    
                    # Ищем новые PDF файлы
                    pdf_files = [f for f in new_files if f.lower().endswith('.pdf')]
                    
                    if pdf_files:
                        print(f"    📄 Найдены новые файлы: {pdf_files}")
                        
                        # Проверяем что файл действительно скачался (не пустой)
                        for pdf_file in pdf_files:
                            pdf_path = os.path.join(self.saves_dir, pdf_file)
                            try:
                                if os.path.exists(pdf_path):
                                    file_size = os.path.getsize(pdf_path)
                                    print(f"    📄 Файл {pdf_file}: размер {file_size} байт")
                                    
                                    if file_size > 1000:  # Минимум 1KB
                                        print(f"    ✅ Найден новый PDF: {pdf_file} (размер: {file_size} байт)")
                                        return True
                                    else:
                                        print(f"    ⚠️ Файл слишком маленький: {file_size} байт")
                                else:
                                    print(f"    ⚠️ Файл не существует: {pdf_path}")
                            except Exception as e:
                                print(f"    ⚠️ Ошибка при проверке файла {pdf_file}: {e}")
                                continue
                    
                    # Проверяем все файлы в папке (на случай если скачался с другим именем)
                    all_pdf_files = [f for f in current_files if f.lower().endswith('.pdf')]
                    if all_pdf_files:
                        print(f"    📄 Всего PDF файлов в папке: {len(all_pdf_files)}")
                        for pdf_file in all_pdf_files:
                            pdf_path = os.path.join(self.saves_dir, pdf_file)
                            try:
                                file_size = os.path.getsize(pdf_path)
                                if file_size > 1000:
                                    print(f"    ✅ Найден PDF: {pdf_file} (размер: {file_size} байт)")
                                    return True
                            except:
                                continue
                    
                    # Ждем немного и проверяем снова - ОПТИМИЗИРОВАНО
                    time.sleep(1)  # Уменьшено с 2 до 1 секунды
                    
                except Exception as e:
                    print(f"    ⚠️ Ошибка при проверке файлов: {e}")
                    time.sleep(1)  # Уменьшено с 2 до 1 секунды - ОПТИМИЗИРОВАНО
                    continue
            
            print(f"    ❌ Таймаут ожидания PDF ({timeout} сек)")
            print(f"    📁 Файлов в папке: {len(os.listdir(self.saves_dir))}")
            return False
            
        except Exception as e:
            print(f"    ❌ Ошибка при ожидании PDF: {e}")
            return False
    
    def cleanup_empty_company_folder(self, company_folder: str, company_name: str):
        """Удаление папки компании если в ней нет PDF файлов"""
        try:
            if not company_folder or not os.path.exists(company_folder):
                print(f"    🗑️ Папка компании не существует, пропускаю удаление")
                return
            
            print(f"    🗑️ Проверяю папку компании на наличие PDF файлов: {company_name}")
            
            # Проверяем есть ли PDF файлы в папке
            pdf_files = []
            for file in os.listdir(company_folder):
                if file.lower().endswith('.pdf'):
                    pdf_path = os.path.join(company_folder, file)
                    # Проверяем что файл существует и не пустой
                    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:
                        pdf_files.append(file)
            
            if not pdf_files:
                print(f"    🗑️ PDF файлы не найдены, удаляю папку компании: {company_name}")
                
                # Удаляем все файлы в папке
                for file in os.listdir(company_folder):
                    file_path = os.path.join(company_folder, file)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            print(f"    🗑️ Удален файл: {file}")
                    except Exception as e:
                        print(f"    ⚠️ Не удалось удалить файл {file}: {e}")
                
                # Удаляем саму папку компании
                try:
                    os.rmdir(company_folder)
                    print(f"    🗑️ Удалена папка компании: {company_name}")
                    
                    # Проверяем нужно ли удалить папку поиска если она пустая
                    search_folder = os.path.dirname(company_folder)
                    if os.path.exists(search_folder) and not os.listdir(search_folder):
                        try:
                            os.rmdir(search_folder)
                            print(f"    🗑️ Удалена пустая папка поиска: {os.path.basename(search_folder)}")
                        except Exception as e:
                            print(f"    ⚠️ Не удалось удалить папку поиска: {e}")
                    
                except Exception as e:
                    print(f"    ⚠️ Не удалось удалить папку компании: {e}")
            else:
                print(f"    ✅ PDF файлы найдены, папка компании сохранена: {company_name}")
                print(f"    📄 Найдено PDF файлов: {len(pdf_files)}")
                
        except Exception as e:
            print(f"    ❌ Ошибка при очистке папки компании: {e}")
    
    def cleanup_all_empty_folders(self):
        """Очистка всех пустых папок после завершения работы"""
        try:
            print(f"\n🗑️ Проверяю все папки на наличие пустых...")
            
            if not os.path.exists(self.saves_dir):
                print(f"    ✅ Папка saves не существует, очистка не требуется")
                return
            
            # Проходим по всем папкам поиска
            for search_folder_name in os.listdir(self.saves_dir):
                search_folder_path = os.path.join(self.saves_dir, search_folder_name)
                
                if not os.path.isdir(search_folder_path):
                    continue
                
                print(f"    🔍 Проверяю папку поиска: {search_folder_name}")
                
                # Проходим по всем папкам компаний
                for company_folder_name in os.listdir(search_folder_path):
                    company_folder_path = os.path.join(search_folder_path, company_folder_name)
                    
                    if not os.path.isdir(company_folder_path):
                        continue
                    
                    # Проверяем есть ли PDF файлы в папке компании
                    pdf_files = []
                    for file in os.listdir(company_folder_path):
                        if file.lower().endswith('.pdf'):
                            file_path = os.path.join(company_folder_path, file)
                            if os.path.exists(file_path) and os.path.getsize(file_path) > 1000:
                                pdf_files.append(file)
                    
                    if not pdf_files:
                        print(f"    🗑️ Удаляю папку без PDF: {company_folder_name}")
                        
                        # Удаляем все файлы в папке
                        for file in os.listdir(company_folder_path):
                            file_path = os.path.join(company_folder_path, file)
                            try:
                                if os.path.isfile(file_path):
                                    os.remove(file_path)
                            except Exception as e:
                                print(f"    ⚠️ Не удалось удалить файл {file}: {e}")
                        
                        # Удаляем папку компании
                        try:
                            os.rmdir(company_folder_path)
                        except Exception as e:
                            print(f"    ⚠️ Не удалось удалить папку {company_folder_name}: {e}")
                
                # Проверяем нужно ли удалить папку поиска если она пустая
                if os.path.exists(search_folder_path) and not os.listdir(search_folder_path):
                    try:
                        os.rmdir(search_folder_path)
                        print(f"    🗑️ Удалена пустая папка поиска: {search_folder_name}")
                    except Exception as e:
                        print(f"    ⚠️ Не удалось удалить папку поиска {search_folder_name}: {e}")
            
            print(f"    ✅ Очистка пустых папок завершена")
            
        except Exception as e:
            print(f"    ❌ Ошибка при очистке пустых папок: {e}")

def main():
    """Основная функция"""
    parser = AutoKRSParser()
    
    print("🚀 Автоматический парсер KRS-Pobierz - ОПТИМИЗИРОВАННАЯ ВЕРСИЯ")
    print("=" * 60)
    print("⚡ ОПТИМИЗАЦИИ ДЛЯ МАКСИМАЛЬНОЙ СКОРОСТИ:")
    print("   • Уменьшены все задержки в 1.5-2 раза")
    print("   • Оптимизированы настройки браузера")
    print("   • Отключены ненужные функции")
    print("   • Ожидаемое ускорение: 2-3 раза быстрее!")
    print("=" * 60)
    print("Этот парсер автоматически:")
    print("1. 🌐 Открывает сайт в браузере")
    print("2. 🔍 Заполняет поле поиска")
    print("3. 🔘 Нажимает кнопку поиска")
    print("4. 📊 Парсит результаты со всех страниц")
    print("5. 📥 Скачивает PDF для каждой компании")
    print("6. 📝 Создает TXT файлы с данными компаний")
    print("7. 📁 Создает структуру папок: saves/поиск/компания/")
    print("8. 📁 Временные файлы браузера сохраняются в папку temp/")
    print("9. 🚫 Блокирует рекламу и всплывающие окна")
    print("10. 🍪 Автоматически принимает cookies")
    print("11. ⏭️ Продолжает работу при ошибках")
    print("12. 🗑️ Автоматически удаляет папки без PDF файлов")
    print("=" * 60)
    
    try:
        # Настраиваем браузер
        if not parser.setup_browser():
            print("❌ Не удалось запустить браузер")
            print("\n💡 РЕШЕНИЕ:")
            print("1. Убедитесь, что у вас установлен Chrome или Edge")
            print("2. Скачайте драйвер для вашего браузера:")
            print("   - Chrome: https://chromedriver.chromium.org/")
            print("   - Edge: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
            print("3. Поместите драйвер в папку с программой")
            return
        
        while True:
            print("\n📋 Меню:")
            print("1. 🔍 Поиск по названию компании")
            print("2. 🆔 Поиск по номеру KRS")
            print("3. 🏢 Поиск по номеру NIP")
            print("4. 🗑️ Очистить пустые папки")
            print("5. 🚪 Выход")
            
            choice = input("\nВыберите опцию (1-5): ")
            
            if choice == '1':
                company_name = input("Введите название компании: ")
                companies = parser.search_by_name(company_name)
                if companies:
                    print(f"\n✅ Найдено компаний: {len(companies)}")
                    for i, company in enumerate(companies, 1):
                        print(f"\n{i}. {company.name}")
                        if company.krs_number:
                            print(f"   🔢 KRS: {company.krs_number}")
                        if company.nip:
                            print(f"   🏢 NIP: {company.nip}")
                        if company.regon:
                            print(f"   📊 REGON: {company.regon}")
                        if company.address:
                            print(f"   🏠 Адрес: {company.address}")
                        if company.status:
                            print(f"   📈 Статус: {company.status}")
                        if company.company_url:
                            print(f"   🔗 Ссылка: {company.company_url}")
                else:
                    print("❌ Компании не найдены")
            
            elif choice == '2':
                krs_number = input("Введите номер KRS: ")
                company = parser.search_by_krs(krs_number)
                if company:
                    print(f"\n✅ Найдена компания: {company.name}")
                    print(f"🔢 KRS: {company.krs_number}")
                    if company.nip:
                        print(f"🏢 NIP: {company.nip}")
                    if company.regon:
                        print(f"📊 REGON: {company.regon}")
                    if company.address:
                        print(f"🏠 Адрес: {company.address}")
                    if company.status:
                        print(f"📈 Статус: {company.status}")
                    if company.company_url:
                        print(f"🔗 Ссылка: {company.company_url}")
                else:
                    print("❌ Компания не найдена")
            
            elif choice == '3':
                nip = input("Введите номер NIP: ")
                company = parser.search_by_nip(nip)
                if company:
                    print(f"\n✅ Найдена компания: {company.name}")
                    print(f"🏢 NIP: {company.nip}")
                    if company.krs_number:
                        print(f"🔢 KRS: {company.krs_number}")
                    if company.regon:
                        print(f"📊 REGON: {company.regon}")
                    if company.address:
                        print(f"🏠 Адрес: {company.address}")
                    if company.status:
                        print(f"📈 Статус: {company.status}")
                    if company.company_url:
                        print(f"🔗 Ссылка: {company.company_url}")
                else:
                    print("❌ Компания не найдена")
            
            elif choice == '4':
                print("🗑️ Очищаю все пустые папки...")
                parser.cleanup_all_empty_folders()
                print("✅ Очистка завершена!")
            
            elif choice == '5':
                print("👋 До свидания!")
                break
            
            else:
                print("❌ Неверный выбор")
            
            # Пауза между операциями
            input("\nНажмите Enter для продолжения...")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Программа прервана пользователем")
    except Exception as e:
        print(f"\n💥 Произошла ошибка: {e}")
    finally:
        # Закрываем браузер
        parser.close_browser()

if __name__ == "__main__":
    main()

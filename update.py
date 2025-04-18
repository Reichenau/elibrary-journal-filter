from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
import pandas as pd
import math
import time
from typing import List, Tuple
from config import CHROMEDRIVER_PATH


BASE_URL = "https://elibrary.ru/titles.asp"
CAPTCHA_TIMEOUT = 120  
PAGE_LOAD_TIMEOUT = 15
JOURNALS_PER_PAGE = 100

def setup_driver() -> webdriver.Chrome:
    """Настройка и возврат драйвера Chrome с оптимальными параметрами"""
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(executable_path=CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)

def handle_captcha(driver: webdriver.Chrome) -> None:
    """Обработка CAPTCHA с ожиданием ручного решения"""
    if "captcha" in driver.page_source.lower():
        start_time = time.time()
        while "captcha" in driver.page_source.lower():
            if time.time() - start_time > CAPTCHA_TIMEOUT:
                raise TimeoutError("Превышено время ожидания CAPTCHA")
            time.sleep(5)

def scrape_page(driver: webdriver.Chrome, url: str) -> List[Tuple[str, str, str, int]]:
    """Скрапинг одной страницы с журналами"""
    try:
        driver.get(url)
        handle_captcha(driver)
        
        rows = WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
            EC.presence_of_all_elements_located((By.XPATH, "//tr[starts-with(@id, 'a')]")))
        
        page_data = []
        for row in rows:
            try:
                link_element = row.find_element(By.TAG_NAME, "a")
                title = link_element.text.strip()
                link = link_element.get_attribute("href")
                page_data.append((title, link))
            except Exception as e:
                print(f"Ошибка обработки строки: {str(e)}")
                continue
        
        return page_data
    
    except Exception as e:
        print(f"Ошибка при загрузке страницы {url}: {str(e)}")
        return []

def process_category(driver: webdriver.Chrome, vak: int, white: int) -> List[Tuple[str, str, str, int]]:
    """Обработка всех страниц для одной комбинации категорий"""
    
    # Первый запрос для получения общего количества
    try:
        driver.get(f"{BASE_URL}?vak={vak}&white={white}&pagenum=1")
        handle_captcha(driver)
        
        total_count = int(WebDriverWait(driver, PAGE_LOAD_TIMEOUT)
                         .until(EC.presence_of_element_located((By.CLASS_NAME, "redref")))
                         .text.split()[3])
    except Exception as e:
        return []

    total_pages = math.ceil(total_count / JOURNALS_PER_PAGE)
    category_data = []
    
    # Параллельно можно было бы использовать ThreadPool, но с Selenium это сложно
    for page in range(1, total_pages + 1):
        page_url = f"{BASE_URL}?vak={vak}&white={white}&pagenum={page}"
        page_data = scrape_page(driver, page_url)
        
        # Добавляем метаданные категорий
        adjusted_vak = "без категории" if vak == 1 else vak - 1
        adjusted_white = white - 1
        category_data.extend([(title, link, adjusted_vak, adjusted_white) for title, link in page_data])
        
        print(f"Обработано страниц: {page}/{total_pages}")
    
    return category_data

def scrape_journals() -> List[Tuple[str, str, str, int]]:
    """Основная функция сбора данных"""
    driver = setup_driver()
    all_journals = []
    
    try:
        vak_categories = [1, 2, 3, 4]  # 1 соответствует "без категории" после корректировки
        white_levels = [2, 3, 4, 5]    # После корректировки будет 1-4
        
        for vak in vak_categories:
            for white in white_levels:
                category_journals = process_category(driver, vak, white)
                all_journals.extend(category_journals)
                
                if len(all_journals) % 500 == 0:
                    save_to_excel(all_journals, "temp_journals.xlsx")
    
    finally:
        driver.quit()
    
    return all_journals

def save_to_excel(data: List[Tuple], filename: str = "journals.xlsx") -> None:
    """Сохранение данных в Excel файл"""
    df = pd.DataFrame(data, columns=[
        "Название журнала", 
        "Ссылка на журнал", 
        "Категория ВАК", 
        "Уровень белого списка"
    ])
    
    try:
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"Данные сохранены в {filename} (всего записей: {len(data)})")
    except Exception as e:
        print(f"Ошибка сохранения файла: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        start_time = time.time()
        journals_data = scrape_journals()
        save_to_excel(journals_data)
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")

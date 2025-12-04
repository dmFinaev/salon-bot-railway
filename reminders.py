"""
reminders.py - система напоминаний клиентам
"""
import datetime
import threading
import time
from database import load_all_records, update_record_field
import telebot
import os

class ReminderSystem:
    def __init__(self, bot_token):
        """
        Инициализация системы напоминаний
        bot_token - токен бота для отправки сообщений
        """
        self.bot = telebot.TeleBot(bot_token)
        self.running = False
        self.thread = None
    
    def start(self):
        """Запуск системы напоминаний в отдельном потоке"""
        if self.running:
            print("⚠️ Система напоминаний уже запущена")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._reminder_loop, daemon=True)
        self.thread.start()
        print("🔔 Система напоминаний запущена")
    
    def stop(self):
        """Остановка системы напоминаний"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("🔔 Система напоминаний остановлена")
    
    def _reminder_loop(self):
        """Основной цикл проверки напоминаний"""
        while self.running:
            try:
                self._check_and_send_reminders()
                time.sleep(60)  # Проверяем каждую минуту
            except Exception as e:
                print(f"❌ Ошибка в системе напоминаний: {e}")
                time.sleep(300)  # При ошибке ждем 5 минут
    
    def _check_and_send_reminders(self):
        """Проверяет и отправляет напоминания"""
        now = datetime.datetime.now()
        records = load_all_records()
        
        for record in records:
            self._check_record_for_reminders(record, now)
    
    def _check_record_for_reminders(self, record, now):
        """
        Проверяет одну запись на необходимость напоминаний
        """
        try:
            # Получаем дату и время записи
            date_str = record["client"].get("date", "")
            if not date_str or " в " not in date_str:
                return
            
            # Парсим дату и время (формат: "25.12 в 15:00")
            date_part, time_part = date_str.split(" в ")
            day, month = map(int, date_part.split("."))
            hour, minute = map(int, time_part.split(":"))
            
            # Создаем объект datetime записи
            current_year = now.year
            record_datetime = datetime.datetime(
                current_year, month, day, hour, minute
            )
            
            # Проверяем что запись в будущем
            if record_datetime <= now:
                return
            
            # Вычисляем разницу во времени
            time_diff = record_datetime - now
            
            # Проверяем условия для напоминаний
            self._check_one_day_reminder(record, time_diff, record_datetime)
            self._check_two_hours_reminder(record, time_diff, record_datetime)
            
        except Exception as e:
            print(f"❌ Ошибка при проверке записи {record.get('id')}: {e}")
    
    def _check_one_day_reminder(self, record, time_diff, record_datetime):
        """
        Проверяет и отправляет напоминание за день
        """
        # Если до записи осталось от 23 до 25 часов
        if datetime.timedelta(hours=23) <= time_diff <= datetime.timedelta(hours=25):
            reminder_sent = record.get("day_reminder_sent", False)
            
            if not reminder_sent:
                self._send_reminder(
                    record,
                    "📅 *Напоминание за день!*\n\n"
                    f"Завтра в {record_datetime.strftime('%H:%M')} у вас запись:\n"
                    f"👤 *{record['client']['name']}*\n"
                    f"📞 {record['client']['phone']}\n"
                    f"💇 {record['client']['service']}"
                )
                # Отмечаем что напоминание отправлено
                self._mark_reminder_sent(record["id"], "day")
    
    def _check_two_hours_reminder(self, record, time_diff, record_datetime):
        """
        Проверяет и отправляет напоминание за 2 часа
        """
        # Если до записи осталось от 1.5 до 2.5 часов
        if datetime.timedelta(hours=1, minutes=30) <= time_diff <= datetime.timedelta(hours=2, minutes=30):
            reminder_sent = record.get("hour_reminder_sent", False)
            
            if not reminder_sent:
                self._send_reminder(
                    record,
                    "⏰ *Напоминание за 2 часа!*\n\n"
                    f"Через 2 часа ({record_datetime.strftime('%H:%M')}) у вас запись:\n"
                    f"👤 *{record['client']['name']}*\n"
                    f"📞 {record['client']['phone']}\n"
                    f"💇 {record['client']['service']}"
                )
                # Отмечаем что напоминание отправлено
                self._mark_reminder_sent(record["id"], "hour")
    
    def _send_reminder(self, record, message):
        """
        Отправляет напоминание в чат
        """
        try:
            chat_id = record.get("chat_id")
            if chat_id:
                self.bot.send_message(chat_id, message, parse_mode='Markdown')
                print(f"🔔 Отправлено напоминание для записи {record.get('id')}")
        except Exception as e:
            print(f"❌ Ошибка отправки напоминания: {e}")
    
    def _mark_reminder_sent(self, record_id, reminder_type):
        """
        Отмечает что напоминание отправлено
        Для простоты будем хранить в отдельном файле
        """
        try:
            # Создаем или обновляем файл с отметками о напоминаниях
            reminders_file = "reminders_sent.json"
            reminders = {}
            
            try:
                import json
                with open(reminders_file, "r", encoding="utf-8") as f:
                    reminders = json.load(f)
            except FileNotFoundError:
                pass
            
            # Добавляем отметку
            if record_id not in reminders:
                reminders[record_id] = {}
            
            reminders[record_id][f"{reminder_type}_reminder_sent"] = True
            reminders[record_id][f"{reminder_type}_reminder_time"] = datetime.datetime.now().isoformat()
            
            # Сохраняем
            with open(reminders_file, "w", encoding="utf-8") as f:
                json.dump(reminders, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"❌ Ошибка сохранения отметки о напоминании: {e}")

# Глобальный экземпляр системы напоминаний
reminder_system = None

def init_reminder_system(bot_token):
    """
    Инициализирует и запускает систему напоминаний
    """
    global reminder_system
    if not reminder_system:
        reminder_system = ReminderSystem(bot_token)
        reminder_system.start()
    return reminder_system

def stop_reminder_system():
    """Останавливает систему напоминаний"""
    global reminder_system
    if reminder_system:
        reminder_system.stop()
        reminder_system = None
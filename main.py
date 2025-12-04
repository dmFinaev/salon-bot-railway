"""
main.py - точка входа в приложение
Запускает бота и систему напоминаний
"""
from bot_core import run_bot
import reminders
import os
import signal
import sys

def signal_handler(sig, frame):
    """Обработчик сигналов для корректного завершения"""
    print("\n🛑 Получен сигнал завершения...")
    reminders.stop_reminder_system()
    print("✅ Бот остановлен корректно")
    sys.exit(0)

if __name__ == "__main__":
    # Настраиваем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Получаем токен бота
    bot_token = os.environ.get('BOT_TOKEN')
    if not bot_token:
        print("❌ ОШИБКА: BOT_TOKEN не установлен!")
        print("⚙️ Установите переменную окружения BOT_TOKEN")
        sys.exit(1)
    
    # Запускаем систему напоминаний
    print("🔔 Запускаем систему напоминаний...")
    reminders.init_reminder_system(bot_token)
    
    # Запускаем бота
    print("🚀 Запускаем основного бота...")
    run_bot()
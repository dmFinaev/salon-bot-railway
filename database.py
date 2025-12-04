"""
database.py - работа с хранением данных (файловая БД)
"""
import json
import datetime
import uuid

def generate_record_id():
    """Генерирует уникальный ID для записи"""
    return "rec_" + str(uuid.uuid4())[:8]

def save_client_record(chat_id, client_data):
    """
    Сохраняет запись клиента в файл
    chat_id - ID чата Telegram
    client_data - словарь с данными клиента
    Возвращает ID созданной записи
    """
    try:
        record = {
            "id": generate_record_id(),
            "chat_id": chat_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "client": client_data
        }
        
        with open("clients.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        print(f"✅ Запись сохранена с ID: {record['id']}")
        return record['id']
        
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return None

def load_all_records():
    """Загружает ВСЕ записи из файла"""
    records = []
    try:
        with open("clients.json", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    except FileNotFoundError:
        print("📝 Файл записей не найден, создадим при первой записи")
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
    
    return records

def delete_record_by_id(record_id):
    """Удаляет запись по ID"""
    try:
        records = load_all_records()
        new_records = [r for r in records if r.get("id") != record_id]
        
        if len(records) == len(new_records):
            return False  # Запись не найдена
        
        with open("clients.json", "w", encoding="utf-8") as f:
            for record in new_records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        print(f"✅ Запись {record_id} удалена")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка удаления: {e}")
        return False

def update_record_field(record_id, field, new_value):
    """Обновляет одно поле в записи"""
    try:
        records = load_all_records()
        updated = False
        
        for record in records:
            if record.get("id") == record_id:
                if field in record["client"]:
                    record["client"][field] = new_value
                    record["timestamp"] = datetime.datetime.now().isoformat()
                    updated = True
                    break
        
        if not updated:
            return False
        
        with open("clients.json", "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        print(f"✅ Запись {record_id} обновлена")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обновления: {e}")
        return False

def get_today_records():
    """Возвращает записи на сегодня"""
    records = load_all_records()
    today = datetime.datetime.now().strftime("%d.%m")
    
    today_records = []
    for record in records:
        if today in record["client"].get("date", ""):
            today_records.append(record)
    
    return today_records

def load_reminder_status(record_id):
    """
    Загружает статус напоминаний для записи
    """
    try:
        with open("reminders_sent.json", "r", encoding="utf-8") as f:
            reminders = json.load(f)
            return reminders.get(record_id, {})
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"❌ Ошибка загрузки статуса напоминаний: {e}")
        return {}

def save_reminder_status(record_id, status):
    """
    Сохраняет статус напоминаний для записи
    """
    try:
        reminders = {}
        
        try:
            with open("reminders_sent.json", "r", encoding="utf-8") as f:
                reminders = json.load(f)
        except FileNotFoundError:
            pass
        
        reminders[record_id] = status
        
        with open("reminders_sent.json", "w", encoding="utf-8") as f:
            json.dump(reminders, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"❌ Ошибка сохранения статуса напоминаний: {e}")
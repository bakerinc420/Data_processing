from src.database.provider.connector import db_connector
from sqlalchemy import text

def test_connection():
    try:
        # 1. Пытаемся получить engine
        engine = db_connector.get_engine()
        
        # 2. Пробуем выполнить простейший запрос (выбор текущего времени в БД)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT NOW()"))
            db_time = result.fetchone()[0]
            
            print("✅ Подключение успешно!")
            print(f"🕒 Текущее время в базе данных: {db_time}")
            
            # 3. Дополнительно проверим наличие твоей таблицы
            table_check = connection.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'data_mio')"
            ))
            exists = table_check.fetchone()[0]
            if exists:
                print("📊 Таблица 'data_mio' найдена.")
            else:
                print("⚠️ Таблица 'data_mio' пока не создана в этой базе.")
                
    except Exception as e:
        print("❌ Ошибка при подключении к БД:")
        print(f"Текст ошибки: {e}")

if __name__ == "__main__":
    test_connection()
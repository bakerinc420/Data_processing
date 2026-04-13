import pandas as pd
from src.database.provider.reader import EMGReader

reader = EMGReader()
engine = reader.engine # Достаем движок подключения к БД

print("🔍 ПРОВЕРКА СТРУКТУРЫ БАЗЫ ДАННЫХ")

table_to_check = "Spectrum_Compress_CMD"

try:
    # 1. Проверяем, существует ли таблица и какие в ней колонки
    query = f"SELECT * FROM {table_to_check} LIMIT 0"
    df = pd.read_sql(query, engine)
    print(f"✅ Таблица '{table_to_check}' найдена!")
    print(f"📋 Список колонок в этой таблице: {df.columns.tolist()}")

    # 2. Проверяем первую строку данных, чтобы понять формат
    query_data = f"SELECT * FROM {table_to_check} LIMIT 1"
    df_data = pd.read_sql(query_data, engine)
    print(f"📥 Первая строка данных:\n{df_data}")

except Exception as e:
    print(f"❌ Ошибка при доступе к таблице: {e}")
    print("💡 Попробуем проверить таблицу в нижнем регистре...")
    # Попытка №2 с маленькими буквами в кавычках
    try:
        query_alt = f'SELECT * FROM "{table_to_check.lower()}" LIMIT 0'
        df_alt = pd.read_sql(query_alt, engine)
        print(f"✅ Найдена таблица в нижнем регистре: {table_to_check.lower()}")
    except:
        print("❌ Таблица не найдена даже в нижнем регистре.")
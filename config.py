import os

# Параметры сигналов
FS = 2000  # Частота дискретизации 2 кГц
MICROVOLT_FACTOR = 1_000_000  # Коэффициент перевода в мкВ

# Настройки базы данных
DB_CONFIG = {
    'drivername': 'postgresql',
    'user': 'postgres',
    'password': 'postgres',
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'nauchka' # или 'nauchka' в зависимости от задачи
}

# Пути к папкам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR_DATA_MIO = os.path.join(BASE_DIR, "documents_data_mio")

# Создаем папку для отчетов, если её нет
if not os.path.exists(REPORTS_DIR_DATA_MIO):
    os.makedirs(REPORTS_DIR_DATA_MIO)
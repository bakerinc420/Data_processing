from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from config import DB_CONFIG

class DBConnector:
    """Класс для централизованного управления подключением к БД."""
    
    def __init__(self):
        # Формируем URL из словаря в config.py
        self.connection_url = URL.create(
            drivername="postgresql",
            username=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database']
        )
        self.engine = create_engine(self.connection_url)

    def get_engine(self):
        """Возвращает объект engine для работы с базой."""
        return self.engine

# Создаем экземпляр для переиспользования в provider и ingestion
db_connector = DBConnector()
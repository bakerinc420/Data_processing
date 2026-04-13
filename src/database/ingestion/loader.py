import scipy.io
import pandas as pd
from src.database.provider.connector import db_connector

class DataIngestor:
    def __init__(self):
        self.engine = db_connector.get_engine()

    def load_mio_data(self, file_path):
        """Загрузка основных данных ЭМГ (data_mio)"""
        print(f"📂 Загрузка ЭМГ из {file_path}...")
        mat = scipy.io.loadmat(file_path)
        # Извлекаем вложенную структуру (согласно вашему формату)
        raw_data = mat['data'][0][0][0] 
        
        arrays = []
        keys = []
        for i, arr in enumerate(raw_data):
            # Создаем DataFrame для каждого пациента
            df_patient = pd.DataFrame(arr)
            arrays.append(df_patient)
            keys.append(f"Patient nomber:{i+1}")

        # Соединяем всех пациентов в одну широкую таблицу
        df_all = pd.concat(arrays, axis=1, keys=keys)
        
        # Записываем в БД
        df_all.to_sql('data_mio', self.engine, if_exists='replace', index=False)
        print("✅ Таблица 'data_mio' успешно обновлена.")

    def load_border_data(self, file_path, border_keys=['k1', 'k2', 'k3', 'k4']):
        """Загрузка таблиц границ (border_k1, border_k3 и т.д.)"""
        print(f"📂 Загрузка границ из {file_path}...")
        mat = scipy.io.loadmat(file_path)
        
        # В ваших файлах структура границ: mat['data'][0][0][0][0][0]
        data_tables = mat['data'][0][0][0][0][0]
        
        for i, key in enumerate(border_keys):
            if i >= len(data_tables):
                break
                
            table_name = f"data_border_{key}"
            df_border = pd.DataFrame(data_tables[i])
            
            # Записываем каждую границу в свою таблицу
            df_border.to_sql(table_name, self.engine, if_exists='replace', index=False)
            print(f"✅ Таблица '{table_name}' успешно загружена.")
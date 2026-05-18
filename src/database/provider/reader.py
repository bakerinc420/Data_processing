import pandas as pd
import numpy as np
from src.database.provider.connector import db_connector
from config import MICROVOLT_FACTOR

class EMGReader:
    def __init__(self):
        self.engine = db_connector.get_engine()

    def get_signal(self, patient_id: int, table_name: str):
        """Загружает сигнал из любой таблицы (например, 'data_mio')"""
        # Проверяем оба варианта написания колонки
        possible_cols = [
            f"('Patient nomber:{patient_id}', 0)",
            f"('Patient number:{patient_id}', 0)"
        ]
        
        for col in possible_cols:
            query = f'SELECT "{col}" FROM "{table_name}";'
            try:
                df = pd.read_sql(query, self.engine)
                return df[col].to_numpy() * MICROVOLT_FACTOR
            except Exception:
                continue
        
        print(f"❌ Колонки для пациента {patient_id} в {table_name} не найдены.")
        return None

    def get_compression_borders(self, patient_id: int):
        """Загружает границы k1-k4 из таблиц 'data_border_kX'"""
        borders = {}
        try:
            for k in ['k1', 'k2', 'k3', 'k4']:
                table_name = f"data_border_{k}"
                # Берем первую пробу (колонка '0') для пациента (смещение OFFSET)
                query = f'SELECT "0" FROM "{table_name}" LIMIT 1 OFFSET {patient_id - 1};'
                val = pd.read_sql(query, self.engine).iloc[0, 0]
                borders[k] = val
            return borders
        except Exception as e:
            print(f"⚠️ Ошибка при загрузке границ: {e}")
            return None
        
    def get_specific_borders(self, patient_id, trial_index):
        """
        Получает k3 и k4 для пациента. 
        trial_index: 0-7 (колонки в таблице)
        """
        col_name = f'"{trial_index}"' 
        
        try:
            # 1. Поиск по ID
            query_k2 = f'SELECT {col_name} FROM "data_border_k2" WHERE id = {patient_id};'
            query_k3 = f'SELECT {col_name} FROM "data_border_k3" WHERE id = {patient_id};'
            
            val_k2 = pd.read_sql(query_k2, self.engine).iloc[0, 0]
            val_k3 = pd.read_sql(query_k3, self.engine).iloc[0, 0]
            
            return int(val_k2), int(val_k3)
        except Exception:
            try:
                # 2. Поиск по OFFSET (смещение строки)
                query_k3 = f'SELECT {col_name} FROM "data_border_k3" LIMIT 1 OFFSET {patient_id - 1};'
                query_k4 = f'SELECT {col_name} FROM "data_border_k4" LIMIT 1 OFFSET {patient_id - 1};'
                
                val_k3 = pd.read_sql(query_k3, self.engine).iloc[0, 0]
                val_k4 = pd.read_sql(query_k4, self.engine).iloc[0, 0]
                return int(val_k3), int(val_k4)
            except Exception as e:
                print(f"❌ Ошибка: Границы k3/k4 для пациента {patient_id} не найдены.")
                return None, None
from src.database.provider.reader import EMGReader
import numpy as np

def test_multi_table_loading():
    reader = EMGReader()
    patient_id = 1
    
    # Список таблиц для проверки (выберите те, что точно есть в вашей БД)
    tables_to_test = [
        "Chewing_MassDex_v7", 
        "Relax_TempSix_v7",
        "data_mio"  # Убедитесь, что эта таблица есть и содержит данные для пациента 1
    ]
    
    print(f"--- Тестирование выгрузки для Пациента №{patient_id} ---")

    for table in tables_to_test:
        print(f"\nПроверка таблицы: {table}")
        try:
            signal = reader.get_signal(patient_id, table)
            
            if signal is not None and len(signal) > 0:
                print(f"  ✅ Сигнал загружен. Точек: {len(signal)}")
                print(f"  📈 Средняя амплитуда: {np.mean(np.abs(signal)):.2f} мкВ")
            else:
                print(f"  ❌ Ошибка: Сигнал из {table} пуст или не найден.")
        except Exception as e:
            print(f"  ❌ Критическая ошибка при тесте {table}: {e}")

    # Проверка загрузки границ
    print("\n--- Проверка временных границ (border) ---")
    borders = reader.get_compression_borders(patient_id)
    if borders and all(borders.values()):
        print(f"  ✅ Все границы k1-k4 получены: {borders}")
    else:
        print("  ⚠️ Внимание: Некоторые границы равны 0 или не найдены.")

if __name__ == "__main__":
    test_multi_table_loading()
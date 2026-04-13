from src.core.signal_mgr.orchestrator import SignalOrchestrator
import pandas as pd

def test_full_patient_processing():
    print("🎻 Запуск Оркестратора: Анализ всех проб пациента...")
    
    orchestrator = SignalOrchestrator()
    patient_id = 70
    table_name = "data_mio" # или "Chewing_MassDex_v7"

    # Запускаем полный цикл обработки
    results = orchestrator.process_patient(patient_id, table_name)

    if not results:
        print("❌ Ошибка: Оркестратор не смог обработать данные.")
        return

    # Превращаем список словарей в DataFrame для красивого вывода таблицы
    df_results = pd.DataFrame(results)
    
    print(f"\n✅ Результаты анализа для Пациента №{patient_id} ({table_name}):")
    print("=" * 80)
    # Выводим таблицу, округляя значения до 2 знаков после запятой
    print(df_results.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
    print("=" * 80)

    # Простая проверка на адекватность данных
    avg_rms = df_results['rms'].mean()
    print(f"📈 Средний RMS по всем пробам: {avg_rms:.2f} мкВ")

if __name__ == "__main__":
    test_full_patient_processing()
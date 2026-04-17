import os
from src.reporting.one_report_data_mio import MioReportGenerator  # Замените your_module_name на имя вашего файла

def main():
    # Инициализируем генератор один раз
    generator = MioReportGenerator()
    
    # Список ID пациентов от 1 до 100
    patient_ids = range(1, 101)
    
    print(f"🚀 Начало массовой генерации отчетов для {len(patient_ids)} пациентов...")
    
    for p_id in patient_ids:
        try:
            # Вызываем ваш метод, который создает docx и графики
            generator.create_combined_mio_report(p_id=p_id)
        except Exception as e:
            # Если данных для какого-то ID нет в БД или произошла ошибка
            print(f"⚠️ Ошибка при обработке пациента {p_id}: {e}")
            continue

    print("✨ Все доступные отчеты сформированы в папке, указанной в REPORTS_DIR.")

if __name__ == "__main__":
    main()
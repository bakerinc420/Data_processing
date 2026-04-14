import os
import warnings

# Подавляем предупреждения Qt/Wayland, если они возникают
os.environ["QT_LOGGING_RULES"] = "qt.qpa.wayland=false"
warnings.filterwarnings("ignore")

from src.core.signal_mgr.freq_orchestrator import FreqOrchestrator
from src.utils.freq_visualizer import FreqVisualizer

def run_full_report(orchestrator, p_id, trial):
    """Функция для межканальной диагностики (POC и ATT)"""
    mode = input("Выберите режим (Chewing/Relax): ").strip() or "Chewing"
    
    print(f"\n🔬 ЗАПУСК ПОЛНОЙ ДИАГНОСТИКИ ДЛЯ ПАЦИЕНТА {p_id} ({mode})...")
    full_data = orchestrator.run_full_diagnostic(p_id, trial, mode=mode)
    
    if full_data is None:
        return

    idx = full_data['indices']
    
    print("\n" + "="*60)
    print(f" КЛИНИЧЕСКИЙ ОТЧЕТ (Межканальный) | Пациент: {p_id} | Проба: {trial}")
    print("="*60)
    print(f"Индекс симметрии Masseter (POC):   {idx['poc_mass']:.1f}%")
    print(f"Индекс симметрии Temporalis (POC):  {idx['poc_temp']:.1f}%")
    print(f"Индекс активности (ATT):            {idx['att_index']:.1f}%")
    print("-" * 60)
    
    # Вывод вердиктов из компаратора
    verdicts = orchestrator.comparator.get_clinical_verdict(idx)
    for v in verdicts:
        print(v)
    print("=" * 60)

def run_main():
    orchestrator = FreqOrchestrator()
    viz = FreqVisualizer()

    print("\n" + "—"*60)
    print("   ЭМГ АНАЛИЗ: ЧАСТОТНАЯ ОБЛАСТЬ (СПЕКТР И ИНДЕКСЫ) ")
    print("—"*60)
    
    print("Выберите тип анализа:")
    print("1. Одиночный канал (полная статистика)")
    print("2. Сравнительная диагностика (4 канала + индексы)")
    print("3. СУПЕР-ОТЧЕТ (Relax vs Chewing комплекс)")
    
    choice = input("\nВаш выбор (1/2/3): ")

    try:
        p_id = int(input("Введите ID пациента: "))
        trial = int(input("Номер пробы (1-8): "))
    except ValueError:
        print("❌ Ошибка: Введены некорректные данные.")
        return

    if choice == "1":
        table = input("Имя таблицы (например, Chewing_MassDex_v7): ")
        print(f"\n🔄 Расчет спектра для {table}...")
        results = orchestrator.run_frequency_analysis(p_id, table, trial)
        
        if results:
            print(f"\n" + "="*50)
            print(f"ОТЧЕТ ПО СПЕКТРУ: {table} | Проба: {trial}")
            print(f"-"*50)
            # ТВОЙ БЛОК ДАННЫХ (БЕЗ ИЗМЕНЕНИЙ):
            print(f"Медианная частота (MDF):          {results['median_frequency']:.2f} Гц")
            print(f"Средняя частота (MNF):            {results['mean_frequency']:.2f} Гц")
            print(f"Пиковая частота:                  {results['peak_frequency']:.2f} Гц")
            print(f"Коэффициент H/L (баланс):          {results['hl_ratio']:.3f}")
            print(f"Спектральная энтропия (сложность): {results['entropy']:.3f}")
            print(f"Утомление (Slope):                {results['fatigue_slope']:.2f} Гц/сек")
            print(f"Падение MDF за пробу:             {results['fatigue_drop_pct']:.1f} %")
            print(f"="*50)
            print(f"💡 Подсказка: Смещение MDF вниз говорит о мышечном утомлении.")
            
            viz.plot_window_freq(results)

            full_sig = orchestrator.reader.get_signal(p_id, table) #
            if full_sig is not None:
                # Повторяем логику нарезки как в оркестраторе
                sample = full_sig[(trial-1)*24000 : trial*24000]
                
                print(f"📊 Отрисовка спектрограммы для текущего массива...")
                viz.plot_single_spectrogram(sample, results['info'])
            
    elif choice == "2":
        run_full_report(orchestrator, p_id, trial)
    elif choice == "3":
        run_super_report(orchestrator, p_id, trial)
    elif choice == "4":
        p_id = int(input("Введите ID пациента: "))
        trial = int(input("Номер пробы (1-8): "))
        
        matrix = orchestrator.get_raw_signals_for_24(p_id, trial)
        viz.plot_24_spectrograms(matrix, p_id, trial)
    else:
        print("❌ Неверный выбор.")

def run_super_report(orchestrator, p_id, trial):
    """
    Функция вывода комплексного отчета: сравнение Покоя и Жевательной нагрузки.
    """
    data = orchestrator.run_super_diagnostic(p_id, trial)
    if not data: 
        return

    r_idx = data['relax']['indices']
    c_idx = data['chewing']['indices']

    # 1. Отрисовка сравнительной таблицы
    print("\n" + "╔" + "═"*68 + "╗")
    print(f"║   КОМПЛЕКСНЫЙ ГНАТОЛОГИЧЕСКИЙ ОТЧЕТ | Пациент: {p_id:3d} | Проба: {trial:d}   ║")
    print("╠" + "═"*25 + "╦" + "═"*20 + "╦" + "═"*21 + "╣")
    print("║ Параметр                ║ Покой (Relax)      ║ Жевательная проба   ║")
    print("╠" + "═"*25 + "╬" + "═"*20 + "╬" + "═"*21 + "╣")
    print(f"║ Симметрия Masseter (POC)║ {r_idx['poc_mass']:17.1f}% ║ {c_idx['poc_mass']:18.1f}% ║")
    print(f"║ Симметрия Temp (POC)    ║ {r_idx['poc_temp']:17.1f}% ║ {c_idx['poc_temp']:18.1f}% ║")
    print(f"║ Инд. активности (ATT)   ║ {r_idx['att_index']:17.1f}% ║ {c_idx['att_index']:18.1f}% ║")
    print("╚" + "═"*25 + "╩" + "═"*20 + "╩" + "═"*21 + "╝")

    # 2. КЛИНИЧЕСКИЙ АНАЛИЗ ДИНАМИКИ
    print("\n📝 КЛИНИЧЕСКИЙ АНАЛИЗ ДИНАМИКИ:")
    
    # -- Проверка на перенапряжение в покое --
    if r_idx['att_index'] < 0 and c_idx['att_index'] > 0:
        print("🚨 ВНИМАНИЕ: Височные мышцы перенапряжены в покое, но включаются жевательные при работе.")
        print("   Это признак того, что пациент не может полностью расслабить челюсть.")
    
    # -- Проверка стабильности симметрии --
    if abs(r_idx['poc_mass'] - c_idx['poc_mass']) > 20:
        print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Резкое падение симметрии при переходе от покоя к нагрузке.")

    # -- 3. Анализ доминирования височных (как у Пациента 1) --
    if c_idx['att_index'] < 0:
        print("🚨 ПАТОЛОГИЯ: Доминирование височных мышц при нагрузке.")
        print("   Вероятен бруксизм или дистальное смещение нижней челюсти.")
        
    # -- 4. Анализ компенсации прикусом --
    if r_idx['poc_temp'] < 80 and c_idx['poc_temp'] > 90:
        print("⚠️ СИМПТОМ: Мышцы выравниваются только при смыкании зубов.")
        print("   Прикус 'маскирует' мышечный дисбаланс.")

    # -- 5. Если всё хорошо (Здоровый паттерн) --
    if r_idx['poc_mass'] > 85 and c_idx['poc_mass'] > 85 and c_idx['att_index'] > 5:
        print("✅ ЗАКЛЮЧЕНИЕ: Нейромышечный баланс в пределах нормы.")

    print("\n" + "="*70)

    matrix = orchestrator.get_raw_signals_for_24(p_id, trial)
    
    # Вызываем визуализатор
    viz = FreqVisualizer()
    viz.plot_24_spectrograms(matrix, p_id, trial)


    
if __name__ == "__main__":
    run_main()
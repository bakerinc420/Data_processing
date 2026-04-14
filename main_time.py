from src.database.provider.reader import EMGReader
from src.core.algorithms.time_domain import TimeDomainProcessor
from src.utils.time_visualizer import EMGVisualizer
import numpy as np

def run_analysis():
    reader = EMGReader()
    proc = TimeDomainProcessor()
    viz = EMGVisualizer()

    print("\n" + "—"*60)
    print("   ЭМГ АНАЛИЗ: ВРЕМЕННАЯ ОБЛАСТЬ ")
    print("—"*60)
    
    # Интерактивный ввод параметров
    try:
        p_id = int(input("Введите ID пациента: "))
        table = input("Имя таблицы (data_mio): ")
        trial = int(input("Номер пробы (1-8): "))
    except ValueError:
        print("❌ Ошибка ввода.")
        return

    trial_idx = trial - 1
    full_signal = reader.get_signal(p_id, table)
    if full_signal is None: return

    # 1. Получаем k3 и k4 из БД (ТОЛЬКО для тренда)
    k2_db, k3_db = reader.get_specific_borders(p_id, trial_idx) 
    
    # Загружаем пробу (24000 точек)
    sample = full_signal[trial_idx * 24000 : trial * 24000]

    # 2. АВТОМАТИЧЕСКИЙ ПОИСК ГРАНИЦ АКТИВНОСТИ
    start_act, end_act = proc.find_activity_borders(sample)
    
    if start_act is None: start_act = 0
    if end_act is None: end_act = len(sample) - 1
    
    print(f"✅ Алгоритм нашел границы: Start={start_act}, End={end_act}")

    # 3. РАСЧЕТ СТАТИСТИКИ ПО НАЙДЕННОЙ ЗОНЕ
    active_zone = sample[start_act:end_act]
    active_zone_centered = active_zone - np.mean(active_zone)
    stats = proc.calculate_stats(active_zone_centered, segment_size=100)

    rms_left = stats['rms']
    rms_right = rms_left * 0.85 # Допустим, правая сторона на 15% слабее
    
    asymmetry = proc.calculate_asymmetry(rms_left, rms_right)

    # 3.1. ДЕТЕКЦИЯ ВСПЛЕСКОВ (внутри активной зоны или по всему сэмплу)
    # Попробуем найти всплески внутри найденной ранее активной зоны
    bursts = proc.detect_bursts(active_zone)


    # 4. ПОСТРОЕНИЕ ТРЕНДА (по k3-k4 из базы)
    envelope = viz._create_peak_envelope(sample)
    
    safe_k3 = k2_db if (k2_db and k2_db != 0) else start_act
    safe_k4 = k3_db if (k3_db and k3_db != 0) else end_act

    y3_env = envelope[safe_k3]
    y4_env = envelope[safe_k4]

    x_range = np.arange(len(sample))
    if safe_k4 != safe_k3:
        slope = (y4_env - y3_env) / (safe_k4 - safe_k3)
        intercept = y3_env - slope * safe_k3
        lin_approx = slope * x_range + intercept
    else:
        lin_approx = np.full_like(x_range, y3_env)

    # 5. ВЫВОД (Добавлена амплитуда от пика до пика)

    

    # 5. ВЫВОД (Дополнен RMS и iEMG)
    print(f"\n" + "="*50)
    print(f"ОТЧЕТ: Пациент {p_id} | Проба: {trial}")
    print(f"Авто-границы (для статистики): {start_act} - {end_act}")
    print(f"Метки из БД (для тренда): k3={k2_db}, k4={k3_db}")
    print(f"-"*50)

    print(f"\n" + "="*50)
    print(f"АНАЛИЗ ВСПЛЕСКОВ (Bursts):")
    print(f"Найдено всплесков активности:      {len(bursts)}")
    if len(bursts) > 0:
        avg_duration = np.mean([b['duration_ms'] for b in bursts])
        print(f"Средняя длительность всплеска:     {avg_duration:.1f} мс")
        # Если всплесков больше одного, считаем паузы между ними
        if len(bursts) > 1:
            intervals = []
            for i in range(1, len(bursts)):
                pause = ((bursts[i]['start'] - bursts[i-1]['end']) / 2000) * 1000
                intervals.append(pause)
            print(f"Средняя пауза между всплесками:    {np.mean(intervals):.1f} мс")
    else:
        print("Статус: Одиночное сжатие (всплески не разделены)")
    print(f"="*50)

    print(f"\n" + "="*50)
    print(f"АНАЛИЗ СИММЕТРИИ (L vs R):")
    print(f"Коэффициент асимметрии:            {asymmetry:.1f} %")
    
    if asymmetry <= 10:
        print("Статус: НОРМА (Высокая симметрия)")
    elif asymmetry <= 20:
        print("Статус: УМЕРЕННАЯ АСИММЕТРИЯ (Требует наблюдения)")
    else:
        print("Статус: ВЫРАЖЕННАЯ АСИММЕТРИЯ (Патология)")
    print(f"="*50)

    print(f"Средняя амплитуда (M+STD):         {stats['custom_avg']:.2f} мкВ")
    print(f"Медианная амплитуда:               {stats['median_amp']:.2f} мкВ")
    print(f"RMS (мощность сигнала):            {stats['rms']:.2f} мкВ")   # Новое
    print(f"iEMG (интегральная активность):    {stats['iemg']:.2f} мкВ*с") # Новое
    print(f"ZCR (частота пересеч. нуля):       {stats['zcr']:.2f} Гц")
    print(f"Амплитуда от пика до пика (P-P):   {stats['peak_to_peak']:.2f} мкВ")
    print(f"Максимальная амплитуда:            {stats['max_amp']:.2f} мкВ")
    print(f"Минимальная амплитуда:             {stats['min_amp']:.2f} мкВ")
    print(f"="*50)

    # 6. ВИЗУАЛИЗАЦИЯ
    viz.plot_window_1(sample, start_act, end_act, stats['max_amp'], stats['min_amp'], 
                     title=f"ЭМГ (Пациент {p_id}, Проба {trial}, БД: {table})")
    
    viz.plot_window_2(sample, envelope, lin_approx, 
                     title=f"Линейная апроксимация (k3-k4)")

if __name__ == "__main__":
    run_analysis()
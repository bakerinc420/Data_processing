import numpy as np
from src.database.provider.reader import EMGReader
from src.core.algorithms.time_domain import TimeDomainProcessor
from src.core.algorithms.frequency_domain import FrequencyDomainProcessor

def test_emg_algorithms():
    print("🚀 Запуск тестирования алгоритмов обработки ЭМГ...")
    
    # 1. Загрузка данных
    reader = EMGReader()
    patient_id = 1
    # Используем таблицу, которая точно работает (из прошлых тестов)
    signal = reader.get_signal(patient_id, "Chewing_MassDex_v7")
    
    if signal is None or len(signal) == 0:
        print("❌ Ошибка: Не удалось загрузить сигнал для теста.")
        return

    print(f"📊 Сигнал загружен (длина: {len(signal)} точек)")

    # 2. Тест Time Domain (Временная область)
    print("\n--- Проверка Time Domain ---")
    stats = TimeDomainProcessor.calculate_stats(signal)
    start, end = TimeDomainProcessor.find_activity_borders(signal)
    active_signal = signal[start:end] # Берем только участок сжатия
    median_amp_active = TimeDomainProcessor.get_median_amplitude(active_signal)
    envelope = TimeDomainProcessor.get_envelope(signal)

    print(f"✅ СКО (порог): {stats['std']:.2f} мкВ")
    print(f"✅ Медианная амплитуда: {median_amp_active:.2f} мкВ")
    print(f"✅ Начало активности (индекс): {start}")
    print(f"✅ Конец активности (индекс): {end}")
    print(f"✅ Огибающая рассчитана (длина: {len(envelope)})")

    # 3. Тест Frequency Domain (Частотная область)
    print("\n--- Проверка Frequency Domain ---")
    freq_proc = FrequencyDomainProcessor(fs=2000)
    freqs, magnitude = freq_proc.get_fft(signal)
    
    comp_freq = freq_proc.get_compression_frequency(freqs, magnitude)
    avg_freq = freq_proc.get_average_frequency(freqs, magnitude)
    med_freq = freq_proc.get_median_frequency(freqs, magnitude)

    print(f"✅ Частота сжатия (пиковая): {comp_freq:.2f} Гц")
    print(f"✅ Средняя частота: {avg_freq:.2f} Гц")
    print(f"✅ Медианная частота: {med_freq:.2f} Гц")

    # Валидация значений (простая логика)
    if 0 < med_freq < 1000 and stats['std'] > 0:
        print("\n✨ ТЕСТ ПРОЙДЕН: Алгоритмы выдают правдоподобные значения.")
    else:
        print("\n⚠️ ПРЕДУПРЕЖДЕНИЕ: Значения выходят за типичные пределы ЭМГ.")

if __name__ == "__main__":
    test_emg_algorithms()
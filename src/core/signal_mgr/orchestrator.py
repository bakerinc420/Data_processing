import numpy as np
from src.database.provider.reader import EMGReader
from src.core.algorithms.time_domain import TimeDomainProcessor
from src.core.algorithms.frequency_domain import FrequencyDomainProcessor

class SignalOrchestrator:
    def __init__(self):
        self.reader = EMGReader()
        self.freq_proc = FrequencyDomainProcessor(fs=2000)
        self.time_proc = TimeDomainProcessor()

    def process_patient(self, patient_id: int, table_name: str):
        """Полный цикл обработки данных пациента"""
        # 1. Загрузка данных
        signal = self.reader.get_signal(patient_id, table_name)
        borders = self.reader.get_compression_borders(patient_id)
        
        if signal is None or borders is None:
            return None

        # 2. Нарезаем на 8 проб (по 24000 точек)
        num_samples = 8
        sample_len = 24000
        results = []

        for i in range(num_samples):
            start_idx = i * sample_len
            end_idx = (i + 1) * sample_len
            sample = signal[start_idx:end_idx]
            
            # 3. Выделяем фазу сжатия внутри пробы (используем границы k2 и k3)
            # Примечание: границы в БД обычно указаны глобально или относительно начала пробы
            k2, k3 = int(borders['k2']), int(borders['k3'])
            
            # Если границы указаны для каждой пробы, берем срез
            compression_zone = sample[k2:k3] if k3 > k2 else sample
            
            # 4. Считаем метрики для этой пробы
            stats = self.time_proc.calculate_stats(compression_zone)
            freqs, mag = self.freq_proc.get_fft(compression_zone)
            
            trial_results = {
                "trial_number": i + 1,
                "rms": stats['rms'],
                "median_amp": self.time_proc.get_median_amplitude(compression_zone),
                "median_freq": self.freq_proc.get_median_frequency(freqs, mag),
                "mean_freq": self.freq_proc.get_average_frequency(freqs, mag)
            }
            results.append(trial_results)
            
        return results
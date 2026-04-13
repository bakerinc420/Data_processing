import numpy as np
from scipy.signal import hilbert

class TimeDomainProcessor:
    @staticmethod
    def calculate_stats(array, segment_size=100):
        if len(array) == 0:
            return None

        segment_amplitudes = []
        for i in range(0, len(array), segment_size):
            segment = array[i:i + segment_size]
            if len(segment) > 0:
                amp = (np.max(segment) - np.min(segment)) / 2
                segment_amplitudes.append(amp)
        
        amplitudes = np.array(segment_amplitudes)
        mean_val = np.mean(amplitudes)
        std_val = np.std(amplitudes)
        custom_avg = mean_val + std_val
        median_val = np.median(amplitudes)

        # --- НОВЫЙ БЛОК: RMS и iEMG ---
        # RMS: Квадратный корень из среднего арифметического квадратов значений
        rms_val = np.sqrt(np.mean(array**2))
        
        # iEMG (Интегральная ЭМГ): Сумма абсолютных значений (площадь под сигналом)
        # Часто нормируется на длительность или частоту дискретизации
        iemg_val = np.sum(np.abs(array))
        # ------------------------------
        zcr_val = TimeDomainProcessor.calculate_zcr(array)

        return {
            "mean": mean_val,
            "std": std_val,
            "custom_avg": custom_avg,
            "median_amp": median_val,
            "peak_to_peak": np.max(array) - np.min(array),
            "max_amp": np.max(array),
            "min_amp": np.min(array),
            "rms": rms_val,        # Добавлено
            "iemg": iemg_val,      # Добавлено
            "zcr": zcr_val
        }

    # Остальные методы (find_activity_borders, get_envelope, linear_approximation) 
    # оставляем без изменений, как в твоем исходнике.
    @staticmethod
    def find_activity_borders(array):
        std_dev = np.std(array)
        start = None
        end = None
        for i in range(len(array) - 1):
            if array[i] > std_dev and array[i+1] > std_dev:
                start = i
                break
        for i in range(len(array) - 1, 0, -1):
            if array[i] > std_dev and array[i-1] > std_dev:
                end = i
                break
        return start, end

    @staticmethod
    def get_envelope(array):
        return np.abs(hilbert(array))
    
    @staticmethod
    def get_linear_approximation_by_points(y2, y3, length):
        x = np.arange(length)
        k = (y3 - y2) / (length - 1) if length > 1 else 0
        b = y2
        return k * x + b
    
    @staticmethod
    def get_trend_line(x1, y1, x2, y2, total_length):
        """Строит прямую y = kx + b через две точки."""
        x = np.arange(total_length)
        if x1 == x2:
            return np.full(total_length, y1)
        
        # Наклон прямой
        k = (y2 - y1) / (x2 - x1)
        # Точка пересечения с осью Y
        b = y1 - k * x1
        
        return k * x + b
    
    @staticmethod
    def calculate_zcr(array):
        """
        Расчет частоты пересечения нуля (Zero Crossing Rate).
        Возвращает количество пересечений в секунду (Гц).
        """
        if len(array) < 2:
            return 0
            
        # Находим точки, где произведение соседних отсчетов отрицательно 
        # (значит знак изменился)
        zero_crossings = np.where(np.diff(np.sign(array)))[0]
        count = len(zero_crossings)
        
        # Пересчитываем в количество событий в секунду (Hz)
        # Так как частота дискретизации fs = 2000 Гц
        fs = 2000
        duration_sec = len(array) / fs
        
        zcr_hz = count / duration_sec if duration_sec > 0 else 0
        return zcr_hz
    
    @staticmethod
    def calculate_asymmetry(rms_left, rms_right):
        """
        Расчет коэффициента асимметрии (POC - Percentage Overlapping Coefficient).
        Сравнивает мощность (RMS) левой и правой сторон.
        """
        if rms_left == 0 and rms_right == 0:
            return 0
            
        # Формула асимметрии: разница, деленная на сумму, в процентах
        # 0% - идеальная симметрия, чем выше %, тем больше перекос
        asymmetry_idx = abs(rms_left - rms_right) / (rms_left + rms_right) * 100
        return asymmetry_idx
    
    @staticmethod
    def detect_bursts(array, fs=2000, threshold_factor=1.5, min_burst_ms=50):
        """
        Находит отдельные всплески активности в сигнале.
        threshold_factor — во сколько раз сигнал должен превысить STD, чтобы считаться всплеском.
        min_burst_ms — минимальная длительность всплеска, чтобы отсечь шум.
        """
        abs_signal = np.abs(array)
        threshold = np.std(array) * threshold_factor
        min_samples = int(fs * min_burst_ms / 1000)
        
        # Бинаризация: 1 если выше порога, 0 если ниже
        binary_signal = (abs_signal > threshold).astype(int)
        
        bursts = []
        start_idx = None
        
        for i in range(1, len(binary_signal)):
            # Начало всплеска
            if binary_signal[i] == 1 and binary_signal[i-1] == 0:
                start_idx = i
            # Конец всплеска
            elif binary_signal[i] == 0 and binary_signal[i-1] == 1 and start_idx is not None:
                duration = i - start_idx
                if duration >= min_samples:
                    bursts.append({
                        "start": start_idx,
                        "end": i,
                        "duration_ms": (duration / fs) * 1000
                    })
                start_idx = None
                
        return bursts
import numpy as np
from scipy.fft import fft, fftfreq
from scipy.stats import entropy
from scipy.signal import butter, filtfilt

class FrequencyDomainProcessor:
    @staticmethod
    def _highpass_filter(data, cutoff=15, fs=2000, order=4):
        """Отсекаем низкочастотные артефакты (ниже 15 Гц)."""
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='high', analog=False)
        return filtfilt(b, a, data)
    
    @staticmethod
    def calculate_psd(array, fs=2000):
        """Расчет спектральной плотности мощности (PSD)."""
        n = len(array)
        if n == 0: return np.array([]), np.array([])
        # Для FFT лучше использовать центрированный сигнал (уже сделано в get_frequency_report)
        yf = fft(array)
        xf = fftfreq(n, 1 / fs)
        positive_mask = xf >= 0
        freqs = xf[positive_mask]
        psd = np.abs(yf[positive_mask])**2 / n
        return freqs, psd

    @staticmethod
    def calculate_median_frequency(freqs, psd):
        if len(psd) == 0: return 0
        cumulative_power = np.cumsum(psd)
        total_power = cumulative_power[-1]
        idx = np.where(cumulative_power >= total_power / 2)[0][0]
        return freqs[idx]

    @staticmethod
    def calculate_mean_frequency(freqs, psd):
        if len(psd) == 0 or np.sum(psd) == 0: return 0
        return np.sum(freqs * psd) / np.sum(psd)

    @staticmethod
    def calculate_fatigue_rate(array, fs=2000, window_ms=500):
        window_size = int(fs * window_ms / 1000)
        step = window_size // 2
        mdf_trend = []
        time_axis = []

        for start in range(0, len(array) - window_size, step):
            segment = array[start:start + window_size]
            f, p = FrequencyDomainProcessor.calculate_psd(segment, fs)
            mdf_trend.append(FrequencyDomainProcessor.calculate_median_frequency(f, p))
            time_axis.append(start / fs)

        if len(mdf_trend) > 1:
            # Находим наклон прямой (slope)
            slope, intercept = np.polyfit(time_axis, mdf_trend, 1)
            # Избегаем деления на ноль при расчете drop_pct
            mdf_start = mdf_trend[0] if mdf_trend[0] != 0 else 1 
            drop_pct = ((mdf_start - mdf_trend[-1]) / mdf_start) * 100
            return slope, drop_pct, mdf_trend, time_axis
        return 0, 0, [], []

    @staticmethod
    def calculate_hl_ratio(freqs, psd, split_freq=100):
        low_mask = (freqs >= 20) & (freqs < split_freq)
        high_mask = (freqs >= split_freq) & (freqs <= 500)
        low_power = np.sum(psd[low_mask])
        high_power = np.sum(psd[high_mask])
        return high_power / low_power if low_power > 0 else 0

    @staticmethod
    def calculate_spectral_entropy(psd):
        if np.sum(psd) == 0: return 0
        psd_norm = psd / np.sum(psd)
        return entropy(psd_norm)

    @staticmethod
    def get_frequency_report(array, fs=2000):
        """Полный расширенный отчет по частотке с фильтрацией."""
        # 1. Сначала фильтруем исходный массив
        clean_signal = FrequencyDomainProcessor._highpass_filter(array, cutoff=15, fs=fs)
        
        # 2. Убираем постоянную составляющую (DC offset)
        array_centered = clean_signal - np.mean(clean_signal)
        
        # 3. Считаем PSD по ОЧИЩЕННОМУ сигналу
        freqs, psd = FrequencyDomainProcessor.calculate_psd(array_centered, fs)
        
        mdf = FrequencyDomainProcessor.calculate_median_frequency(freqs, psd)
        mnf = FrequencyDomainProcessor.calculate_mean_frequency(freqs, psd)
        
        # Утомление считаем тоже по чистому сигналу
        slope, drop_pct, trend, t_axis = FrequencyDomainProcessor.calculate_fatigue_rate(array_centered, fs)
        
        # Доп. метрики
        hl_ratio = FrequencyDomainProcessor.calculate_hl_ratio(freqs, psd)
        spec_entropy = FrequencyDomainProcessor.calculate_spectral_entropy(psd)
        peak_freq = freqs[np.argmax(psd)] if len(psd) > 0 else 0

        # Контроль качества
        is_reliable = True
        warning_msg = ""
        # После фильтра 15Гц пик ниже 20Гц — явный признак мусора
        if peak_freq < 20:
            is_reliable = False
            warning_msg = "⚠️ ВНИМАНИЕ: Пик частоты слишком низкий. Сигнал может быть недостоверным."

        return {
            "freqs": freqs, "psd": psd,
            "median_frequency": mdf,
            "mean_frequency": mnf,
            "peak_frequency": peak_freq,
            "fatigue_slope": slope,
            "fatigue_drop_pct": drop_pct,
            "hl_ratio": hl_ratio,
            "entropy": spec_entropy,
            "mdf_trend": trend,
            "time_axis": t_axis,
            "is_reliable": is_reliable,
            "warning": warning_msg
        }
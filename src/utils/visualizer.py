import matplotlib.pyplot as plt
import numpy as np

class EMGVisualizer:
    @staticmethod
    def _create_peak_envelope(array, fs=2000, window_ms=150):
        """
        Улучшенная плавная огибающая по пикам.
        window_ms=150 — увеличенное окно для стабильного удержания пиков.
        """
        if len(array) == 0:
            return array
            
        abs_signal = np.abs(array)
        
        # 1. Находим скользящий максимум (Rolling Maximum)
        window_size = int(fs * window_ms / 1000)
        rolling_max = np.zeros_like(abs_signal)
        
        for i in range(len(abs_signal)):
            start = max(0, i - window_size // 2)
            end = min(len(abs_signal), i + window_size // 2)
            rolling_max[i] = np.max(abs_signal[start:end])
            
        # 2. ВТОРИЧНОЕ СГЛАЖИВАНИЕ (Low-pass filter)
        # Увеличиваем окно сглаживания для эффекта "плавной линии"
        smooth_window = int(fs * 0.2) # 200 мс для идеальной плавности
        kernel = np.ones(smooth_window) / smooth_window
        
        # Используем mode='same' для сохранения длины
        peak_envelope = np.convolve(rolling_max, kernel, mode='same')
        
        return peak_envelope

    @staticmethod
    def plot_window_1(signal, start_act, end_act, max_val, min_val, title=""):
        # Без изменений (Точка 1)
        plt.figure("Окно 1: Сигнал и Активность", figsize=(12, 6))
        plt.plot(signal, color='gray', alpha=0.5, label='ЭМГ сигнал')
        plt.axvline(x=start_act, color='green', linestyle='--', label=f'Start: {start_act}')
        plt.axvline(x=end_act, color='red', linestyle='--', label=f'End: {end_act}')
        plt.scatter(np.argmax(signal), max_val, color='darkred', zorder=5, label=f'Max: {max_val:.2f}')
        plt.scatter(np.argmin(signal), min_val, color='blue', zorder=5, label=f'Min: {min_val:.2f}')
        plt.title(f"Сигнал - {title}")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()

    @staticmethod
    def plot_window_2(signal, envelope, lin_approx, title=""):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Если огибающая не передана, считаем ее
        if envelope is None:
            envelope = EMGVisualizer._create_peak_envelope(signal)
            
        # Верхний график: Огибающая
        ax1.plot(signal, color='gray', alpha=0.15)
        ax1.plot(envelope, color='red', linewidth=2, label='Огибающая')
        ax1.set_title("Огибающая Гилберта")
        
        # Нижний график: Прямая через k2 и k3
        ax2.plot(signal, color='gray', alpha=0.2)
        ax2.plot(envelope, color='red', alpha=0.3) # Огибающая фоном
        
        # Рисуем саму прямую
        ax2.plot(lin_approx, color='blue', linewidth=3, linestyle='--', label='Линия тренда (k3-k4)')
        
        ax2.set_title("Линейная апроксимация (k3-k4)")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
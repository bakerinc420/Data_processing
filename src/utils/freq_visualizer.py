import matplotlib.pyplot as plt
import numpy as np

from scipy.signal import spectrogram


class FreqVisualizer:
    @staticmethod
    def plot_window_freq(freq_results):
        """
        Отрисовка спектра мощности с медианной и средней частотами.
        Принимает словарь с результатами (частоты, psd, MDF, MNF, info).
        """
        if freq_results is None:
            print("❌ Ошибка: Нет данных для отрисовки спектра.")
            return

        # Достаем данные из словаря (результат freq_orchestrator)
        freqs = freq_results['freqs']
        psd = freq_results['psd']
        mdf = freq_results['median_frequency']
        mnf = freq_results['mean_frequency']
        info = freq_results['info']

        # Создаем окно с подробным заголовком (БД, Пациент, Проба)
        title_str = f"Спектр ЭМГ (Пациент {info['p_id']}, Проба {info['trial']}, БД: {info['table']})"
        plt.figure(title_str, figsize=(12, 6))

        # 1. Основной график спектра
        plt.plot(freqs, psd, color='black', alpha=0.8, linewidth=1.5, label='Спектр мощности (PSD)')

        # 2. Метки ключевых частот
        # Отмечаем Медианную частоту (MDF) вертикальной линией
        plt.axvline(x=mdf, color='green', linestyle='--', linewidth=2, label=f'MDF (Медианная): {mdf:.1f} Гц')
        # Отмечаем Среднюю частоту (MNF) пунктиром
        plt.axvline(x=mnf, color='blue', linestyle=':', linewidth=2, label=f'MNF (Средняя): {mnf:.1f} Гц')

        # Заголовок графика и подписи осей
        plt.title(f"Спектральная плотность мощности (PSD)", fontsize=14, fontweight='bold')
        plt.xlabel("Частота (Гц)", fontsize=12)
        plt.ylabel("Мощность (мкВ²/Гц)", fontsize=12)

        # 3. Настройка осей (Ограничим спектр до 500 Гц)
        # У ЭМГ выше 500 Гц обычно только шум
        plt.xlim(0, 500)
        # Логарифмическая шкала по Y удобна, если есть сильные выбросы (по желанию)
        # plt.yscale('log') 

        # Легенда, сетка и оформление
        plt.legend(fontsize=11)
        plt.grid(True, which='both', linestyle='--', alpha=0.4)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_24_spectrograms(data_matrix, p_id, trial):
        """
        Отрисовка сетки спектрограмм (8x3) с защитой от коротких сигналов.
        """
        muscles = list(data_matrix.keys())
        if not muscles:
            print("❌ Ошибка: Матрица данных пуста.")
            return
            
        states = list(data_matrix[muscles[0]].keys())
        
        # Увеличиваем высоту (3 * len(muscles)), так как строк теперь 8
        fig, axes = plt.subplots(len(muscles), len(states), 
                                 figsize=(18, 2.5 * len(muscles)), 
                                 constrained_layout=True)
        
        # Заголовок всего окна
        fig.suptitle(f"КОМПЛЕКСНАЯ ПАНОРАМА СПЕКТРОГРАММ | Пациент: {p_id} | Проба: {trial}", 
                     fontsize=16, fontweight='bold')

        im = None 
        
        for r, muscle in enumerate(muscles):
            for c, state in enumerate(states):
                # Обработка случая, если осей меньше чем нужно (на всякий случай)
                ax = axes[r, c] if len(muscles) > 1 else axes[c]
                
                signal = data_matrix[muscle].get(state)
                
                # Проверка: сигнал должен быть достаточно длинным для анализа
                if signal is not None and len(signal) > 10: 
                    sig_len = len(signal)
                    
                    # --- ЗАЩИТА ОТ ValueError: noverlap must be less than nperseg ---
                    # Базовые параметры
                    n_per_seg = 512
                    n_overlap = 256
                    
                    # Если сигнал короче 512 точек, уменьшаем окно до длины сигнала
                    if sig_len <= n_per_seg:
                        n_per_seg = sig_len if sig_len % 2 == 0 else sig_len - 1
                        n_overlap = n_per_seg // 2 # Гарантируем, что overlap меньше seg
                    
                    try:
                        # Проверка на вырожденный случай после корректировки
                        if n_per_seg > 2:
                            f, t, Sxx = spectrogram(signal, fs=2000, nperseg=n_per_seg, noverlap=n_overlap)
                            
                            if Sxx.size > 0:
                                # Отрисовка в децибелах
                                im = ax.pcolormesh(t, f, 10 * np.log10(Sxx + 1e-10), 
                                                   shading='gouraud', cmap='magma', vmin=-30, vmax=30)
                                ax.set_ylim(15, 500)
                        else:
                            ax.text(0.5, 0.5, "TOO SHORT", color='orange', ha='center', va='center', transform=ax.transAxes)
                            
                    except Exception as e:
                        print(f"⚠️ Ошибка spectrogram для {muscle}-{state}: {e}")
                        ax.text(0.5, 0.5, "PROC ERROR", color='red', ha='center', va='center', transform=ax.transAxes)
                else:
                    # Если данных нет совсем или сигнал < 10 точек
                    ax.set_facecolor('#1a1a1a')
                    ax.text(0.5, 0.5, "EMPTY", color='white', ha='center', va='center', transform=ax.transAxes)

                # Подписи только для крайних графиков, чтобы не загромождать
                if r == 0: 
                    ax.set_title(state, fontweight='bold')
                if c == 0: 
                    ax.set_ylabel(muscle, fontweight='bold', rotation=90, labelpad=10)
                
                # Убираем лишние цифры с осей внутри сетки (опционально для красоты)
                if r < len(muscles) - 1:
                    ax.set_xticklabels([])

        # Рисуем общую цветовую шкалу справа
        if im is not None:
            cbar = fig.colorbar(im, ax=axes, location='right', aspect=50, pad=0.02)
            cbar.set_label("Мощность (дБ)", fontsize=12)
        
        plt.show()
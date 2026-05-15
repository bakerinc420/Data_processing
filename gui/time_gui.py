import sys
import numpy as np
from PyQt6.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QLabel, QSplitter, QScrollArea)
from PyQt6.QtCore import Qt
import pyqtgraph as pg

# Импортируем твои оригинальные классы
from src.database.provider.reader import EMGReader
from src.core.algorithms.time_domain import TimeDomainProcessor

class EMGWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ЭМГ Анализ: Временная область")
        self.resize(1400, 850) # Немного увеличим ширину для правой панели

        self.reader = EMGReader()
        self.proc = TimeDomainProcessor()

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # ГЛАВНЫЙ ГОРИЗОНТАЛЬНЫЙ МАКЕТ
        main_h_layout = QHBoxLayout(central_widget)

        # --- ЛЕВАЯ ЧАСТЬ (ГРАФИКИ + КНОПКИ) ---
        left_container = QWidget()
        left_v_layout = QVBoxLayout(left_container)
        left_v_layout.setContentsMargins(0, 0, 0, 0)

        # Панель управления (сверху слева)
        controls_layout = QHBoxLayout()
        self.input_patient = QLineEdit("1") 
        self.input_table = QLineEdit("data_mio")
        self.input_trial = QLineEdit("1") 
        btn_analyze = QPushButton("Запустить анализ")
        btn_analyze.clicked.connect(self.start_analysis)

        controls_layout.addWidget(QLabel("ID:"))
        controls_layout.addWidget(self.input_patient)
        controls_layout.addWidget(QLabel("Таблица:"))
        controls_layout.addWidget(self.input_table)
        controls_layout.addWidget(QLabel("Проба:"))
        controls_layout.addWidget(self.input_trial)
        controls_layout.addWidget(btn_analyze)
        left_v_layout.addLayout(controls_layout)

        # Сплиттер для графиков
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.plot_raw = pg.PlotWidget(title="ЭМГ Сигнал")
        self.plot_raw.setMouseEnabled(x=True, y=False)
        self.curve_emg = self.plot_raw.plot(pen='g')
        self.line_start = pg.InfiniteLine(pos=0, angle=90, pen='y', label="Start")
        self.line_end = pg.InfiniteLine(pos=0, angle=90, pen='r', label="End")
        self.plot_raw.addItem(self.line_start)
        self.plot_raw.addItem(self.line_end)

        self.plot_trend = pg.PlotWidget(title="Огибающая и Тренды")
        self.plot_trend.setXLink(self.plot_raw)
        self.curve_env = self.plot_trend.plot(pen=pg.mkPen('r', width=2))
        self.curve_trend = self.plot_trend.plot(pen=pg.mkPen('b', width=2, style=Qt.PenStyle.DashLine))

        self.splitter.addWidget(self.plot_raw)
        self.splitter.addWidget(self.plot_trend)
        left_v_layout.addWidget(self.splitter)

        # --- ПРАВАЯ ЧАСТЬ (ОТЧЕТ) ---
        self.right_panel = QScrollArea()
        self.right_panel.setFixedWidth(350) # Фиксируем ширину отчета
        self.right_panel.setWidgetResizable(True)
        self.right_panel.setStyleSheet("background-color: #1e1e1e; border: none;")

        self.stats_label = QLabel("Ожидание данных...")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.stats_label.setWordWrap(True)
        self.stats_label.setContentsMargins(15, 15, 15, 15)
        self.stats_label.setStyleSheet("color: #dcdcdc; font-family: 'Segoe UI', sans-serif;")
        
        self.right_panel.setWidget(self.stats_label)

        # Добавляем все в главный макет
        main_h_layout.addWidget(left_container, stretch=4) # Графики занимают больше места
        main_h_layout.addWidget(self.right_panel, stretch=1)

        self.dot_max = self.plot_raw.plot(pen=None, symbol='o', symbolBrush='r', symbolSize=10, name="Max")
        self.dot_min = self.plot_raw.plot(pen=None, symbol='o', symbolBrush='b', symbolSize=10, name="Min")

    def calculate_custom_envelope(self, array, fs=2000, window_ms=150):
        if len(array) == 0: return array
        abs_signal = np.abs(array)
        window_size = int(fs * window_ms / 1000)
        rolling_max = np.zeros_like(abs_signal)
        for i in range(len(abs_signal)):
            start = max(0, i - window_size // 2)
            end = min(len(abs_signal), i + window_size // 2)
            rolling_max[i] = np.max(abs_signal[start:end])
        smooth_window = int(fs * 0.2)
        kernel = np.ones(smooth_window) / smooth_window
        return np.convolve(rolling_max, kernel, mode='same')

    def start_analysis(self):
        try:
            # 1. Получение параметров из интерфейса
            p_id = int(self.input_patient.text())
            table = self.input_table.text()
            trial = int(self.input_trial.text())
            trial_idx = trial - 1

            # 2. Загрузка сигнала
            full_signal = self.reader.get_signal(p_id, table)
            if full_signal is None:
                self.stats_label.setText(f"<b style='color:red;'>Ошибка:</b> Пациент {p_id} не найден.")
                return
            
            # Нарезка пробы (24000 точек)
            sample = full_signal[trial_idx * 24000 : trial * 24000]
            if len(sample) == 0:
                self.stats_label.setText("<b style='color:red;'>Ошибка:</b> Проба пуста.")
                return

            # 3. Загрузка границ из БД
            k3_db, k4_db = self.reader.get_specific_borders(p_id, trial_idx)

            # 4. Поиск автоматических границ активности
            start_act, end_act = self.proc.find_activity_borders(sample)
            s_safe = start_act if start_act is not None else 0
            e_safe = end_act if end_act is not None else len(sample) - 1

            # 5. Расчет статистики по активной зоне
            active_zone = sample[s_safe:e_safe]
            active_zone_centered = active_zone - np.mean(active_zone)
            stats = self.proc.calculate_stats(active_zone_centered)
            
            # 6. Анализ всплесков (Bursts)
            bursts = self.proc.detect_bursts(active_zone)
            
            # 7. Анализ асимметрии (L vs R)
            # В данном примере используется эмуляция правого канала (rms * 0.85) как в вашем исходнике
            rms_left = stats['rms']
            rms_right = rms_left * 0.85 
            asymmetry = self.proc.calculate_asymmetry(rms_left, rms_right)

            # 8. Расчет огибающей (Ваш метод)
            envelope = self.calculate_custom_envelope(sample)
            
            # 9. Построение тренда (Линейная аппроксимация)
            x_range = np.arange(len(sample))
            idx_start = max(0, min(k3_db if (k3_db and k3_db != 0) else s_safe, 23999))
            idx_end = max(0, min(k4_db if (k4_db and k4_db != 0) else e_safe, 23999))
            
            if idx_end > idx_start:
                slope = (envelope[idx_end] - envelope[idx_start]) / (idx_end - idx_start)
                intercept = envelope[idx_start] - slope * idx_start
                lin_approx = slope * x_range + intercept
                self.curve_trend.setData(lin_approx)
            else:
                self.curve_trend.setData(np.full_like(x_range, envelope[idx_start]))

            # 10. Визуализация на графиках
            self.curve_emg.setData(sample)
            
            # Добавленные точки пиков
            idx_max = np.argmax(sample)
            idx_min = np.argmin(sample)
            self.dot_max.setData([idx_max], [stats['max_amp']])
            self.dot_min.setData([idx_min], [stats['min_amp']])

            self.line_start.setValue(s_safe)
            self.line_end.setValue(e_safe)
            self.curve_env.setData(envelope)
            self.plot_raw.autoRange()

            # Устанавливаем точки (используем значения из stats, которые уже посчитаны)
            self.dot_max.setData([idx_max], [stats['max_amp']])
            self.dot_min.setData([idx_min], [stats['min_amp']])

            # 11. Формирование информативного отчета
            status_color = "#4CAF50" if asymmetry <= 10 else "#1707FF" if asymmetry <= 20 else "#F44336"
            status_text = "НОРМА" if asymmetry <= 10 else "УМЕРЕННАЯ" if asymmetry <= 20 else "ПАТОЛОГИЯ"

            # Формирование блока всплесков
            burst_info = ""
            if len(bursts) > 0:
                avg_dur = np.mean([b['duration_ms'] for b in bursts])
                burst_info = f"Ср. длит: <b>{avg_dur:.1f} мс</b>"
                if len(bursts) > 1:
                    intervals = [((bursts[i]['start'] - bursts[i-1]['end']) / 2000) * 1000 for i in range(1, len(bursts))]
                    burst_info += f" | Пауза: <b>{np.mean(intervals):.1f} мс</b>"
            else:
                burst_info = "<i>Одиночное сжатие</i>"

            html = f"""
            <div style='line-height: 130%; font-family: Segoe UI, sans-serif; color: #EEE;'>
                <h2 style='color: #55aaff; margin-bottom: 5px; border-bottom: 2px solid #333;'>ПАЦИЕНТ {p_id}</h2>
                
                <table width='100%' style='margin-bottom: 10px;'>
                    <tr><td>Проба:</td><td align='right'><b>№{trial}</b></td></tr>
                    <tr><td>Авто-границы:</td><td align='right' style='color: #888;'>{s_safe} - {e_safe}</td></tr>
                    <tr><td>Метки БД:</td><td align='right' style='color: #888;'>k3={k3_db}, k4={k4_db}</td></tr>
                </table>

                <h3 style='color: #55aaff; font-size: 14px; margin-bottom: 5px;'>АНАЛИЗ АКТИВНОСТИ</h3>
                <div style='background-color: #252525; padding: 10px; border-radius: 5px; border-left: 4px solid {status_color};'>
                    Всплески: <b>{len(bursts)} шт.</b> ({burst_info})<br>
                    Асимметрия: <b style='color: {status_color};'>{asymmetry:.1f}% ({status_text})</b>
                </div>

                <h3 style='color: #55aaff; font-size: 14px; margin-top: 15px; margin-bottom: 5px;'>СТАТИСТИКА АМПЛИТУД</h3>
                <table width='100%' style='border-collapse: collapse;'>
                    <tr style='border-bottom: 1px solid #333;'>
                        <td style='padding: 3px 0;'>Средняя (M+STD):</td>
                        <td align='right'><b>{stats['custom_avg']:.2f} мкВ</b></td>
                    </tr>
                    <tr style='border-bottom: 1px solid #333;'>
                        <td style='padding: 3px 0;'>Медианная:</td>
                        <td align='right'>{stats['median_amp']:.2f} мкВ</td>
                    </tr>
                    <tr style='border-bottom: 1px solid #333;'>
                        <td style='padding: 3px 0;'>Пик-Пик (P-P):</td>
                        <td align='right'>{stats['peak_to_peak']:.2f} мкВ</td>
                    </tr>
                    <tr style='border-bottom: 1px solid #333;'>
                        <td style='padding: 3px 0;'>Максимальная:</td>
                        <td align='right' style='color: #ff5555;'>{stats['max_amp']:.2f} мкВ</td>
                    </tr>
                    <tr>
                        <td style='padding: 3px 0;'>Минимальная:</td>
                        <td align='right' style='color: #5555ff;'>{stats['min_amp']:.2f} мкВ</td>
                    </tr>
                </table>

                <h3 style='color: #55aaff; font-size: 14px; margin-top: 15px; margin-bottom: 5px;'>ЭНЕРГИЯ И ЧАСТОТА</h3>
                <table width='100%' style='border-collapse: collapse;'>
                    <tr style='border-bottom: 1px solid #333;'>
                        <td style='padding: 3px 0;'>RMS (Мощность):</td>
                        <td align='right' style='color: #00FF00;'><b>{stats['rms']:.2f} мкВ</b></td>
                    </tr>
                    <tr style='border-bottom: 1px solid #333;'>
                        <td style='padding: 3px 0;'>iEMG (Интеграл):</td>
                        <td align='right'>{stats['iemg']:.2f} мкВ*с</td>
                    </tr>
                    <tr>
                        <td style='padding: 3px 0;'>ZCR (Частота):</td>
                        <td align='right'><b>{stats['zcr']:.2f} Гц</b></td>
                    </tr>
                </table>
            </div>
            """
            self.stats_label.setText(html)
            
            # Вывод в консоль для контроля
            print(f"\n{'='*50}\nОТЧЕТ: Пациент {p_id} | Проба {trial}\nRMS: {stats['rms']:.2f} | ZCR: {stats['zcr']:.2f}\n{'='*50}")

        except Exception as e:
            print(f"Ошибка анализа: {e}")
            self.stats_label.setText(f"<b style='color:red;'>Ошибка:</b> {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EMGWindow()
    window.show()
    sys.exit(app.exec())
import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QPushButton, QLabel, 
                             QTabWidget, QGroupBox, QScrollArea, QComboBox, 
                             QSpinBox, QStackedWidget, QSplitter)
from PyQt6.QtCore import Qt, QRectF
import pyqtgraph as pg
from scipy.signal import spectrogram
import matplotlib as mpl

# Импорты для Частотной области
from src.core.signal_mgr.freq_orchestrator import FreqOrchestrator
# Импорты для Временной области
from src.database.provider.reader import EMGReader
from src.core.algorithms.time_domain import TimeDomainProcessor

class EMGAnalyzerPro(QMainWindow):
    def __init__(self):
        super().__init__()
        # Инициализация бэкенда
        self.freq_orchestrator = FreqOrchestrator()
        self.time_reader = EMGReader()
        self.time_proc = TimeDomainProcessor()
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("EMG Analyzer Pro: Time & Frequency Domain")
        self.setGeometry(50, 50, 1650, 900)

        main_layout = QHBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # =================================================================
        # ЛЕВАЯ ПАНЕЛЬ: ДИНАМИЧЕСКИЕ НАСТРОЙКИ (3 состояния)
        # =================================================================
        self.left_stack = QStackedWidget()
        self.left_stack.setFixedWidth(200) 
        
        # --- Состояние 0: ВРЕМЕННОЙ АНАЛИЗ ---
        time_widget = QWidget()
        time_layout = QVBoxLayout(time_widget)
        time_group = QGroupBox("Анализ во времени")
        tl = QVBoxLayout()
        
        self.t_input_pid = QSpinBox(); self.t_input_pid.setRange(1, 9999)
        self.t_input_trial = QSpinBox(); self.t_input_trial.setRange(1, 8)
        self.t_input_table = QComboBox()
        self.t_input_table.addItems([
            "Chewing_MassDex_v7", "Chewing_MassSix_v7",
            "Chewing_TempDex_v7", "Chewing_TempSix_v7",
            "Relax_MassDex_v7", "Relax_MassSix_v7",
            "Relax_TempDex_v7", "Relax_TempSix_v7"
        ])
        
        tl.addWidget(QLabel("ID Пациента:"))
        tl.addWidget(self.t_input_pid)
        tl.addWidget(QLabel("Номер пробы (1-8):"))
        tl.addWidget(self.t_input_trial)
        tl.addWidget(QLabel("Таблица (мышца):"))
        tl.addWidget(self.t_input_table)
        
        self.btn_time = QPushButton("🚀 Анализ Времени")
        self.btn_time.clicked.connect(self.run_time_analysis)
        tl.addWidget(self.btn_time)
        time_group.setLayout(tl)
        time_layout.addWidget(time_group)
        time_layout.addStretch()

        # --- Состояние 1: ЧАСТОТНЫЙ ОДИНОЧНЫЙ ---
        single_widget = QWidget()
        single_layout = QVBoxLayout(single_widget)
        single_group = QGroupBox("Параметры пробы (Частота 1к)")
        sl = QVBoxLayout()
        
        self.s_input_pid = QSpinBox(); self.s_input_pid.setRange(1, 9999)
        self.s_input_trial = QSpinBox(); self.s_input_trial.setRange(1, 8)
        self.s_input_table = QComboBox()
        self.s_input_table.addItems([
            "Chewing_MassDex_v7", "Chewing_MassSix_v7",
            "Chewing_TempDex_v7", "Chewing_TempSix_v7",
            "Relax_MassDex_v7", "Relax_MassSix_v7",
            "Relax_TempDex_v7", "Relax_TempSix_v7"
        ])
        
        sl.addWidget(QLabel("ID Пациента:"))
        sl.addWidget(self.s_input_pid)
        sl.addWidget(QLabel("Номер пробы (1-8):"))
        sl.addWidget(self.s_input_trial)
        sl.addWidget(QLabel("Таблица (мышца):"))
        sl.addWidget(self.s_input_table)
        
        self.btn_single = QPushButton("🚀 Спектр 1 канала")
        self.btn_single.clicked.connect(self.run_single_analysis)
        sl.addWidget(self.btn_single)
        single_group.setLayout(sl)
        single_layout.addWidget(single_group)
        single_layout.addStretch()
        
        # --- Состояние 2: ЧАСТОТНЫЙ КОМПЛЕКСНЫЙ ---
        complex_widget = QWidget()
        complex_layout = QVBoxLayout(complex_widget)
        complex_group = QGroupBox("Протокол (Частота 4к)")
        cl = QVBoxLayout()
        
        self.c_input_pid = QSpinBox(); self.c_input_pid.setRange(1, 9999)
        self.c_input_trial = QSpinBox(); self.c_input_trial.setRange(1, 8)
        self.c_input_proto = QComboBox()
        self.c_input_proto.addItems(["Сжатие (Chewing)", "Покой (Relax)"])
        
        cl.addWidget(QLabel("ID Пациента:"))
        cl.addWidget(self.c_input_pid)
        cl.addWidget(QLabel("Номер пробы (1-8):"))
        cl.addWidget(self.c_input_trial)
        cl.addWidget(QLabel("Тип протокола:"))
        cl.addWidget(self.c_input_proto)
        
        self.btn_complex = QPushButton("🚀 Анализ Симметрии")
        self.btn_complex.clicked.connect(self.run_complex_analysis)
        cl.addWidget(self.btn_complex)
        complex_group.setLayout(cl)
        complex_layout.addWidget(complex_group)
        complex_layout.addStretch()
        
        self.left_stack.addWidget(time_widget)     # 0
        self.left_stack.addWidget(single_widget)   # 1
        self.left_stack.addWidget(complex_widget)  # 2
        main_layout.addWidget(self.left_stack)

        # =================================================================
        # ЦЕНТРАЛЬНАЯ ПАНЕЛЬ: 5 ВКЛАДОК
        # =================================================================
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Настройки палитры для спектрограмм
        try:
            mpl_cmap = mpl.colormaps['magma']
            mpl_colors = (mpl_cmap(np.linspace(0, 1, 256)) * 255).astype(np.ubyte)
            self.colormap = pg.ColorMap(np.linspace(0, 1, 256), mpl_colors)
        except Exception:
            self.colormap = pg.colormap.get('magma')

        # --- Вкладка 0: Временной анализ ---
        self.tab_time = QWidget()
        time_l = QVBoxLayout(self.tab_time)
        self.time_splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.plot_raw = pg.PlotWidget(title="ЭМГ Сигнал")
        self.plot_raw.setMouseEnabled(x=True, y=False)
        self.curve_emg = self.plot_raw.plot(pen='g')
        self.line_start = pg.InfiniteLine(pos=0, angle=90, pen='y', label="Start")
        self.line_end = pg.InfiniteLine(pos=0, angle=90, pen='r', label="End")
        self.plot_raw.addItem(self.line_start); self.plot_raw.addItem(self.line_end)
        self.dot_max = self.plot_raw.plot(pen=None, symbol='o', symbolBrush='r', symbolSize=10)
        self.dot_min = self.plot_raw.plot(pen=None, symbol='o', symbolBrush='b', symbolSize=10)

        self.plot_trend = pg.PlotWidget(title="Огибающая и Тренды")
        self.plot_trend.setXLink(self.plot_raw)
        self.curve_env = self.plot_trend.plot(pen=pg.mkPen('r', width=2))
        self.curve_trend = self.plot_trend.plot(pen=pg.mkPen('b', width=2, style=Qt.PenStyle.DashLine))

        self.time_splitter.addWidget(self.plot_raw)
        self.time_splitter.addWidget(self.plot_trend)
        time_l.addWidget(self.time_splitter)

        # --- Вкладка 1: Одиночный PSD ---
        self.tab_single_psd = QWidget()
        l_s_psd = QVBoxLayout(self.tab_single_psd)
        self.plot_s_psd = pg.PlotWidget(title="Спектральная плотность мощности (PSD)")
        self.plot_s_psd.setLabel('left', 'Мощность'); self.plot_s_psd.setLabel('bottom', 'Частота', units='Гц')
        self.curve_s_psd = self.plot_s_psd.plot(pen=pg.mkPen('w', width=1.5))
        self.line_s_mdf = pg.InfiniteLine(angle=90, pen=pg.mkPen('g', width=2, style=Qt.PenStyle.DashLine), label="MDF", labelOpts={'position': 0.8, 'color': (0, 255, 0), 'movable': False})
        self.line_s_mnf = pg.InfiniteLine(angle=90, pen=pg.mkPen('b', width=2, style=Qt.PenStyle.DashLine), label="MNF", labelOpts={'position': 0.7, 'color': (50, 100, 255), 'movable': False})
        self.plot_s_psd.addItem(self.line_s_mdf); self.plot_s_psd.addItem(self.line_s_mnf)
        l_s_psd.addWidget(self.plot_s_psd)

        # --- Вкладка 2: Одиночная Спектрограмма ---
        self.tab_single_spec = QWidget()
        l_s_spec = QVBoxLayout(self.tab_single_spec)
        self.view_s_spec = pg.GraphicsLayoutWidget()
        self.plot_s_spec = self.view_s_spec.addPlot(title="Спектрограмма")
        self.plot_s_spec.setLabel('left', 'Частота', units='Гц'); self.plot_s_spec.setLabel('bottom', 'Время', units='с')
        self.img_s_spec = pg.ImageItem(); self.img_s_spec.setOpts(axisOrder='col-major')
        self.plot_s_spec.addItem(self.img_s_spec)
        self.bar_s_spec = pg.ColorBarItem(values=(0, 1))
        self.bar_s_spec.setColorMap(self.colormap); self.bar_s_spec.setImageItem(self.img_s_spec)
        self.view_s_spec.addItem(self.bar_s_spec)
        l_s_spec.addWidget(self.view_s_spec)

        # --- Вкладки 3 и 4: Комплексные сетки 2х2 ---
        self.channel_keys = ["MassDex", "MassSix", "TempDex", "TempSix"]
        self.channel_titles = {"MassDex": "Masseter Dex", "MassSix": "Masseter Six", "TempDex": "Temporalis Dex", "TempSix": "Temporalis Six"}
        grid_pos = {"MassDex": (0, 0), "MassSix": (0, 1), "TempDex": (1, 0), "TempSix": (1, 1)}

        self.tab_comp_psd = QWidget()
        comp_psd_grid = QGridLayout(self.tab_comp_psd)
        self.plots_c_psd = {}; self.curves_c_psd = {}; self.lines_c_mdf = {}; self.lines_c_mnf = {}

        self.tab_comp_spec = QWidget()
        comp_spec_grid = QGridLayout(self.tab_comp_spec)
        self.views_c_spec = {}; self.plots_c_spec = {}; self.imgs_c_spec = {}; self.bars_c_spec = {}

        for k in self.channel_keys:
            # Для вкладки 3
            p_psd = pg.PlotWidget(title=self.channel_titles[k])
            c_psd = p_psd.plot(pen=pg.mkPen('w', width=1.2))
            l_mdf = pg.InfiniteLine(angle=90, pen=pg.mkPen('g', width=1.5, style=Qt.PenStyle.DashLine), label="MDF", labelOpts={'position': 0.8, 'color': (0, 255, 0), 'movable': False})
            l_mnf = pg.InfiniteLine(angle=90, pen=pg.mkPen('b', width=1.5, style=Qt.PenStyle.DashLine), label="MNF", labelOpts={'position': 0.7, 'color': (50, 100, 255), 'movable': False})
            p_psd.addItem(l_mdf); p_psd.addItem(l_mnf)
            comp_psd_grid.addWidget(p_psd, grid_pos[k][0], grid_pos[k][1])
            self.plots_c_psd[k] = p_psd; self.curves_c_psd[k] = c_psd; self.lines_c_mdf[k] = l_mdf; self.lines_c_mnf[k] = l_mnf

            # Для вкладки 4
            v_spec = pg.GraphicsLayoutWidget()
            p_spec = v_spec.addPlot(title=self.channel_titles[k])
            i_spec = pg.ImageItem(); i_spec.setOpts(axisOrder='col-major')
            p_spec.addItem(i_spec)
            b_spec = pg.ColorBarItem(values=(0, 1)); b_spec.setColorMap(self.colormap); b_spec.setImageItem(i_spec)
            v_spec.addItem(b_spec)
            comp_spec_grid.addWidget(v_spec, grid_pos[k][0], grid_pos[k][1])
            self.views_c_spec[k] = v_spec; self.plots_c_spec[k] = p_spec; self.imgs_c_spec[k] = i_spec; self.bars_c_spec[k] = b_spec

        # Добавляем все 5 вкладок
        self.tabs.addTab(self.tab_time, "⏱ Временная Область")
        self.tabs.addTab(self.tab_single_psd, "1к. PSD")
        self.tabs.addTab(self.tab_single_spec, "1к. Спектрограмма")
        self.tabs.addTab(self.tab_comp_psd, "4к. Сравнение PSD")
        self.tabs.addTab(self.tab_comp_spec, "4к. Панорама Спектрограмм")
        
        main_layout.addWidget(self.tabs, stretch=10) 

        # =================================================================
        # ПРАВАЯ ПАНЕЛЬ: ДИНАМИЧЕСКИЕ ОТЧЕТЫ (3 состояния)
        # =================================================================
        self.right_stack = QStackedWidget()
        self.right_stack.setFixedWidth(320)
        
        # 0: Отчет времени
        scroll_time = QScrollArea(); scroll_time.setWidgetResizable(True); scroll_time.setStyleSheet("border: none; background: #1e1e1e;")
        self.lbl_report_time = QLabel("<span style='color:#ccc;'>Ожидание запуска (Время)...</span>")
        self.lbl_report_time.setStyleSheet("background: #1e1e1e; padding: 15px;"); self.lbl_report_time.setTextFormat(Qt.TextFormat.RichText); self.lbl_report_time.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_time.setWidget(self.lbl_report_time)

        # 1: Отчет частоты (1 канал)
        scroll_single = QScrollArea(); scroll_single.setWidgetResizable(True); scroll_single.setStyleSheet("border: none; background: #1e1e1e;")
        self.lbl_report_single = QLabel("<span style='color:#ccc;'>Ожидание запуска (Спектр 1к)...</span>")
        self.lbl_report_single.setStyleSheet("background: #1e1e1e; padding: 15px;"); self.lbl_report_single.setTextFormat(Qt.TextFormat.RichText); self.lbl_report_single.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_single.setWidget(self.lbl_report_single)
        
        # 2: Отчет частоты (4 канала)
        scroll_complex = QScrollArea(); scroll_complex.setWidgetResizable(True); scroll_complex.setStyleSheet("border: none; background: #1e1e1e;")
        self.lbl_report_complex = QLabel("<span style='color:#ccc;'>Ожидание запуска (Симметрия)...</span>")
        self.lbl_report_complex.setStyleSheet("background: #1e1e1e; padding: 15px;"); self.lbl_report_complex.setTextFormat(Qt.TextFormat.RichText); self.lbl_report_complex.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_complex.setWidget(self.lbl_report_complex)
        
        self.right_stack.addWidget(scroll_time)     # 0
        self.right_stack.addWidget(scroll_single)   # 1
        self.right_stack.addWidget(scroll_complex)  # 2
        main_layout.addWidget(self.right_stack)

    # --- ЛОГИКА ПЕРЕКЛЮЧЕНИЯ ИНТЕРФЕЙСОВ ---
    def on_tab_changed(self, index):
        if index == 0:        # Временная область
            self.left_stack.setCurrentIndex(0)
            self.right_stack.setCurrentIndex(0)
        elif index in [1, 2]: # Одиночная частотная
            self.left_stack.setCurrentIndex(1)
            self.right_stack.setCurrentIndex(1)
        elif index in [3, 4]: # Комплексная частотная
            self.left_stack.setCurrentIndex(2)
            self.right_stack.setCurrentIndex(2)

    # =================================================================
    # ЛОГИКА АНАЛИЗА: ВРЕМЕННАЯ ОБЛАСТЬ
    # =================================================================
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

    def run_time_analysis(self):
        try:
            p_id = self.t_input_pid.value()
            table = self.t_input_table.currentText()
            trial = self.t_input_trial.value()
            trial_idx = trial - 1

            full_signal = self.time_reader.get_signal(p_id, table)
            if full_signal is None:
                self.lbl_report_time.setText(f"<b style='color:red;'>Ошибка:</b> Пациент {p_id} не найден.")
                return
            
            sample = full_signal[trial_idx * 24000 : trial * 24000]
            if len(sample) == 0:
                self.lbl_report_time.setText("<b style='color:red;'>Ошибка:</b> Проба пуста.")
                return

            k2_db, k3_db = self.time_reader.get_specific_borders(p_id, trial_idx)
            start_act, end_act = self.time_proc.find_activity_borders(sample)
            s_safe = start_act if start_act is not None else 0
            e_safe = end_act if end_act is not None else len(sample) - 1

            active_zone = sample[s_safe:e_safe]
            active_zone_centered = active_zone - np.mean(active_zone)
            stats = self.time_proc.calculate_stats(active_zone_centered)
            bursts = self.time_proc.detect_bursts(active_zone)
            
            rms_left = stats['rms']
            rms_right = rms_left * 0.85 
            asymmetry = self.time_proc.calculate_asymmetry(rms_left, rms_right)

            envelope = self.calculate_custom_envelope(sample)
            
            x_range = np.arange(len(sample))
            idx_start = max(0, min(k2_db if (k2_db and k2_db != 0) else s_safe, 23999))
            idx_end = max(0, min(k3_db if (k3_db and k3_db != 0) else e_safe, 23999))
            
            if idx_end > idx_start:
                slope = (envelope[idx_end] - envelope[idx_start]) / (idx_end - idx_start)
                intercept = envelope[idx_start] - slope * idx_start
                lin_approx = slope * x_range + intercept
                self.curve_trend.setData(lin_approx)
            else:
                self.curve_trend.setData(np.full_like(x_range, envelope[idx_start]))

            self.curve_emg.setData(sample)
            idx_max = np.argmax(sample)
            idx_min = np.argmin(sample)
            self.dot_max.setData([idx_max], [stats['max_amp']])
            self.dot_min.setData([idx_min], [stats['min_amp']])

            self.line_start.setValue(s_safe)
            self.line_end.setValue(e_safe)
            self.curve_env.setData(envelope)
            self.plot_raw.autoRange()

            status_color = "#4CAF50" if asymmetry <= 10 else "#1707FF" if asymmetry <= 20 else "#F44336"
            status_text = "НОРМА" if asymmetry <= 10 else "УМЕРЕННАЯ" if asymmetry <= 20 else "ПАТОЛОГИЯ"

            burst_info = ""
            if len(bursts) > 0:
                avg_dur = np.mean([b['duration_ms'] for b in bursts])
                burst_info = f"Ср. длит: <b>{avg_dur:.1f} мс</b>"
            else:
                burst_info = "<i>Одиночное сжатие</i>"

            html = f"""
            <div style='line-height: 130%; font-family: Segoe UI, sans-serif; color: #EEE; font-size: 12px;'>
                <h2 style='color: #55aaff; margin-bottom: 5px; border-bottom: 2px solid #333; font-size: 14px;'>ВРЕМЕННОЙ ОТЧЕТ</h2>
                <p>Пациент: <b>ID {p_id}</b> | Проба: <b>№{trial}</b><br>Таблица: <b>{table}</b></p>
                <p style='color: #888;'>Границы: {s_safe} - {e_safe}</p>

                <h3 style='color: #55aaff; font-size: 13px; margin-bottom: 5px;'>АНАЛИЗ АКТИВНОСТИ</h3>
                <div style='background-color: #252525; padding: 10px; border-radius: 5px; border-left: 4px solid {status_color};'>
                    Всплески: <b>{len(bursts)} шт.</b> ({burst_info})<br>
                    Асимметрия: <b style='color: {status_color};'>{asymmetry:.1f}% ({status_text})</b>
                </div>

                <h3 style='color: #55aaff; font-size: 13px; margin-top: 15px; margin-bottom: 5px;'>СТАТИСТИКА АМПЛИТУД</h3>
                <table width='100%' style='border-collapse: collapse; text-align: left;'>
                    <tr style='border-bottom: 1px solid #333;'><td style='padding: 3px 0;'>Средняя (M+STD):</td><td align='right'><b>{stats['custom_avg']:.2f} мкВ</b></td></tr>
                    <tr style='border-bottom: 1px solid #333;'><td style='padding: 3px 0;'>Медианная:</td><td align='right'>{stats['median_amp']:.2f} мкВ</td></tr>
                    <tr style='border-bottom: 1px solid #333;'><td style='padding: 3px 0;'>Пик-Пик (P-P):</td><td align='right'>{stats['peak_to_peak']:.2f} мкВ</td></tr>
                    <tr style='border-bottom: 1px solid #333;'><td style='padding: 3px 0;'>Максимальная:</td><td align='right' style='color: #ff5555;'>{stats['max_amp']:.2f} мкВ</td></tr>
                    <tr><td style='padding: 3px 0;'>Минимальная:</td><td align='right' style='color: #5555ff;'>{stats['min_amp']:.2f} мкВ</td></tr>
                </table>

                <h3 style='color: #55aaff; font-size: 13px; margin-top: 15px; margin-bottom: 5px;'>ЭНЕРГИЯ И ЧАСТОТА</h3>
                <table width='100%' style='border-collapse: collapse;'>
                    <tr style='border-bottom: 1px solid #333;'><td style='padding: 3px 0;'>RMS (Мощность):</td><td align='right' style='color: #00FF00;'><b>{stats['rms']:.2f} мкВ</b></td></tr>
                    <tr style='border-bottom: 1px solid #333;'><td style='padding: 3px 0;'>iEMG (Интеграл):</td><td align='right'>{stats['iemg']:.2f} мкВ*с</td></tr>
                    <tr><td style='padding: 3px 0;'>ZCR (Частота):</td><td align='right'><b>{stats['zcr']:.2f} Гц</b></td></tr>
                </table>
            </div>
            """
            self.lbl_report_time.setText(html)
        except Exception as e:
            self.lbl_report_time.setText(f"<b style='color:red;'>Ошибка:</b> {str(e)}")

    # =================================================================
    # ЛОГИКА АНАЛИЗА: ЧАСТОТНАЯ ОБЛАСТЬ (ОДИНОЧНЫЙ)
    # =================================================================
    def run_single_analysis(self):
        try:
            p_id = self.s_input_pid.value()
            trial = self.s_input_trial.value()
            table = self.s_input_table.currentText()
            
            res = self.freq_orchestrator.run_frequency_analysis(p_id, table, trial)
            if not res:
                self.lbl_report_single.setText(f"<b style='color:red;'>Ошибка: Нет данных для {table} (Проба {trial})</b>")
                return
                
            full_sig = self.freq_orchestrator.reader.get_signal(p_id, table)
            sample = full_sig[(trial - 1) * 24000 : trial * 24000] if full_sig is not None else np.array([])
            
            freqs = res['freqs']; psd = res['psd']; mask = (freqs >= 0) & (freqs <= 500)
            self.curve_s_psd.setData(freqs[mask], psd[mask])
            self.line_s_mdf.setValue(res['median_frequency']); self.line_s_mnf.setValue(res['mean_frequency'])
            self.plot_s_psd.autoRange()
            
            self.render_spectrogram(sample, self.img_s_spec, self.plot_s_spec, self.bar_s_spec)
            self.lbl_report_single.setText(self.generate_single_html(res, p_id, trial, table))
        except Exception as e:
            self.lbl_report_single.setText(f"<b style='color:red;'>Ошибка:</b> {str(e)}")

    # =================================================================
    # ЛОГИКА АНАЛИЗА: ЧАСТОТНАЯ ОБЛАСТЬ (КОМПЛЕКСНЫЙ)
    # =================================================================
    def run_complex_analysis(self):
        try:
            p_id = self.c_input_pid.value()
            trial = self.c_input_trial.value()
            prefix = "Chewing" if "Сжатие" in self.c_input_proto.currentText() else "Relax"
            
            tables = {
                "MassDex": f"{prefix}_MassDex_v7", "MassSix": f"{prefix}_MassSix_v7",
                "TempDex": f"{prefix}_TempDex_v7", "TempSix": f"{prefix}_TempSix_v7"
            }
            
            all_results = {}
            for k in self.channel_keys:
                res = self.freq_orchestrator.run_frequency_analysis(p_id, tables[k], trial)
                if res:
                    full_sig = self.freq_orchestrator.reader.get_signal(p_id, tables[k])
                    sample = full_sig[(trial - 1) * 24000 : trial * 24000] if full_sig is not None else np.array([])
                    all_results[k] = {"metrics": res, "sample": sample}
                else:
                    all_results[k] = None

            for k in self.channel_keys:
                if not all_results[k]: continue
                data = all_results[k]["metrics"]; sample = all_results[k]["sample"]
                
                f = data['freqs']; p = data['psd']; m = (f >= 0) & (f <= 500)
                self.curves_c_psd[k].setData(f[m], p[m])
                
                self.lines_c_mdf[k].setValue(data['median_frequency'])
                self.lines_c_mnf[k].setValue(data['mean_frequency'])
                
                self.plots_c_psd[k].autoRange()
                self.render_spectrogram(sample, self.imgs_c_spec[k], self.plots_c_spec[k], self.bars_c_spec[k])

            self.lbl_report_complex.setText(self.generate_complex_html(all_results, p_id, trial, self.c_input_proto.currentText()))
        except Exception as e:
            self.lbl_report_complex.setText(f"<b style='color:red;'>Ошибка:</b> {str(e)}")

    # =================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ (РЕНДЕР И HTML)
    # =================================================================
    def render_spectrogram(self, sample, img_item, plot_widget, color_bar):
        if len(sample) == 0: 
            img_item.clear()
            return
        
        fs = 2000; n_per_seg = 1024
        sig_len = len(sample)
        if sig_len <= n_per_seg: n_per_seg = sig_len if sig_len % 2 == 0 else sig_len - 1
        
        f_spec, t_spec, Sxx = spectrogram(sample, fs=fs, nperseg=n_per_seg, noverlap=int(n_per_seg * 0.8))
        f_mask = (f_spec >= 20) & (f_spec <= 500)
        
        Sxx_log = 10 * np.log10(Sxx[f_mask, :] + 1e-10)
        f_filtered = f_spec[f_mask]
        
        img_item.setImage(Sxx_log.T)
        img_item.setRect(QRectF(0.0, f_filtered[0], t_spec[-1], f_filtered[-1] - f_filtered[0]))
        plot_widget.setXRange(0, t_spec[-1], padding=0)
        plot_widget.setYRange(20, 500, padding=0)
        color_bar.setLevels((-25, 15))

    def generate_single_html(self, res, p_id, trial, table):
        return f"""
        <div style='line-height: 130%; font-family: Segoe UI, sans-serif; color: #dcdcdc; font-size: 12px;'>
            <h2 style='color: #55aaff; margin-bottom: 5px; border-bottom: 2px solid #333; padding-bottom: 3px; font-size: 14px;'>ОТЧЕТ ПО СПЕКТРУ</h2>
            <table style='width: 100%; table-layout: fixed; margin-bottom: 15px; color: #aaa; font-size: 12px;'>
                <tr><td style='width: 25%;'>Таблица:</td><td style='width: 75%; text-align: right; color: #fff; word-wrap: break-word;'><b>{table}</b></td></tr>
                <tr><td>Пациент:</td><td style='text-align: right; color: #fff;'><b>ID {p_id}</b></td></tr>
                <tr><td>Проба:</td><td style='text-align: right; color: #fff;'><b>№{trial}</b></td></tr>
            </table>
            <hr style='border: none; border-top: 1px solid #333; margin: 10px 0;'>
            <table style='width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 12px; color: #dcdcdc;'>
                <tr style='border-bottom: 1px solid #2a2a2a;'><td style='width: 65%; padding: 6px 0;'>Медианная частота (MDF):</td><td style='width: 35%; text-align: right; color: #00FF00;'><b>{res['median_frequency']:.2f} Гц</b></td></tr>
                <tr style='border-bottom: 1px solid #2a2a2a;'><td style='padding: 6px 0;'>Средняя частота (MNF):</td><td style='text-align: right; color: #3366ff;'><b>{res['mean_frequency']:.2f} Гц</b></td></tr>
                <tr style='border-bottom: 1px solid #2a2a2a;'><td style='padding: 6px 0;'>Пиковая частота:</td><td style='text-align: right; color: #fff;'><b>{res['peak_frequency']:.2f} Гц</b></td></tr>
                <tr style='border-bottom: 1px solid #2a2a2a;'><td style='padding: 6px 0;'>Коэффициент H/L:</td><td style='text-align: right; color: #fff;'><b>{res.get('hl_ratio', 0):.3f}</b></td></tr>
                <tr style='border-bottom: 1px solid #2a2a2a;'><td style='padding: 6px 0;'>Спектральная энтропия:</td><td style='text-align: right; color: #fff;'><b>{res.get('entropy', 0):.3f}</b></td></tr>
                <tr style='border-bottom: 1px solid #2a2a2a;'><td style='padding: 6px 0;'>Утомление (Slope):</td><td style='text-align: right; color: #ff5555;'><b>{res['fatigue_slope']:.2f} Гц/с</b></td></tr>
                <tr><td style='padding: 6px 0;'>Падение MDF за пробу:</td><td style='text-align: right; color: #fff;'><b>{res.get('fatigue_drop_pct', 0):.1f} %</b></td></tr>
            </table>
            <hr style='border: none; border-top: 1px solid #333; margin: 15px 0;'>
            <div style='background-color: #252525; padding: 8px; border-radius: 5px; border-left: 3px solid #55aaff; font-size: 11px; color: #ccc;'>
                💡 <b>Подсказка:</b> Смещение MDF вниз говорит о мышечном утомлении.
            </div>
        </div>
        """

    def generate_complex_html(self, data, p_id, trial, proto):
        if any(data[k] is None for k in self.channel_keys):
            return "<b style='color:orange;'>Не все 4 таблицы доступны для расчёта. Проверьте БД.</b>"

        md = data["MassDex"]["metrics"]["median_frequency"]
        ms = data["MassSix"]["metrics"]["median_frequency"]
        td = data["TempDex"]["metrics"]["median_frequency"]
        ts = data["TempSix"]["metrics"]["median_frequency"]

        poc_mass = (1.0 - abs(md - ms) / (md + ms)) * 100.0
        poc_temp = (1.0 - abs(td - ts) / (td + ts)) * 100.0
        att_mass = ((md - ms) / (md + ms)) * 100.0
        att_temp = ((td - ts) / (td + ts)) * 100.0

        return f"""
        <div style='font-family: Segoe UI, sans-serif; color: #dcdcdc; font-size: 12px; word-wrap: break-word;'>
            <h2 style='color: #55aaff; border-bottom: 1px solid #555; padding-bottom: 3px; font-size: 14px;'>СИММЕТРИЯ СИСТЕМЫ</h2>
            <p style='margin-bottom: 5px;'>Пациент: <b>ID {p_id}</b> | Проба: <b>№{trial}</b><br>Протокол: <b>{proto}</b></p>
            <h3 style='color: #fc0; margin-top: 10px; margin-bottom: 3px; font-size: 12px;'>📊 Перекрытие спектров (POC)</h3>
            <p style='margin: 2px 0;'>Массетеры: <b style='color:{"#0f0" if poc_mass>=85 else "#f55"};'>{poc_mass:.1f}%</b></p>
            <p style='margin: 2px 0;'>Височные: <b style='color:{"#0f0" if poc_temp>=85 else "#f55"};'>{poc_temp:.1f}%</b></p>
            <h3 style='color: #fc0; margin-top: 10px; margin-bottom: 3px; font-size: 12px;'>⚖️ Асимметрия (ATT)</h3>
            <p style='margin: 2px 0;'>Смещение массетеров: <b style='color:#fff;'>{att_mass:+.1f}%</b></p>
            <p style='margin: 2px 0;'>Смещение височных: <b style='color:#fff;'>{att_temp:+.1f}%</b></p>
            <h2 style='color: #55aaff; margin-top: 15px; border-bottom: 1px solid #555; padding-bottom: 3px; font-size: 13px;'>СРАВНИТЕЛЬНЫЕ МЕТРИКИ</h2>
            <table style='width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 11px; text-align: left;'>
                <thead>
                    <tr style='color: #888; border-bottom: 1px solid #444;'><th style='width: 32%; padding-bottom: 4px;'>Мышца</th><th style='width: 17%; text-align: right;'>MDF</th><th style='width: 17%; text-align: right;'>MNF</th><th style='width: 17%; text-align: right;'>Peak</th><th style='width: 17%; text-align: right;'>Slope</th></tr>
                </thead>
                <tbody>
                    <tr style='border-bottom: 1px solid #2a2a2a;'><td style='padding: 6px 0; color:#fff;'><b>Mass Dex</b></td><td style='text-align: right; color:#00ff00;'>{md:.0f}</td><td style='text-align: right;'>{data["MassDex"]["metrics"]["mean_frequency"]:.0f}</td><td style='text-align: right;'>{data["MassDex"]["metrics"]["peak_frequency"]:.0f}</td><td style='text-align: right; color:#ff5555;'>{data["MassDex"]["metrics"]["fatigue_slope"]:.1f}</td></tr>
                    <tr style='border-bottom: 1px solid #2a2a2a;'><td style='padding: 6px 0; color:#fff;'><b>Mass Six</b></td><td style='text-align: right; color:#00ff00;'>{ms:.0f}</td><td style='text-align: right;'>{data["MassSix"]["metrics"]["mean_frequency"]:.0f}</td><td style='text-align: right;'>{data["MassSix"]["metrics"]["peak_frequency"]:.0f}</td><td style='text-align: right; color:#ff5555;'>{data["MassSix"]["metrics"]["fatigue_slope"]:.1f}</td></tr>
                    <tr style='border-bottom: 1px solid #2a2a2a;'><td style='padding: 6px 0; color:#fff;'><b>Temp Dex</b></td><td style='text-align: right; color:#00ff00;'>{td:.0f}</td><td style='text-align: right;'>{data["TempDex"]["metrics"]["mean_frequency"]:.0f}</td><td style='text-align: right;'>{data["TempDex"]["metrics"]["peak_frequency"]:.0f}</td><td style='text-align: right; color:#ff5555;'>{data["TempDex"]["metrics"]["fatigue_slope"]:.1f}</td></tr>
                    <tr style='border-bottom: 1px solid #444;'><td style='padding: 6px 0; color:#fff;'><b>Temp Six</b></td><td style='text-align: right; color:#00ff00;'>{ts:.0f}</td><td style='text-align: right;'>{data["TempSix"]["metrics"]["mean_frequency"]:.0f}</td><td style='text-align: right;'>{data["TempSix"]["metrics"]["peak_frequency"]:.0f}</td><td style='text-align: right; color:#ff5555;'>{data["TempSix"]["metrics"]["fatigue_slope"]:.1f}</td></tr>
                </tbody>
            </table>
        </div>"""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EMGAnalyzerPro()
    window.show()
    sys.exit(app.exec())
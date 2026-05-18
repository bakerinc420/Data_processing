import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTabWidget, 
                             QGroupBox, QScrollArea, QComboBox, QSpinBox)
from PyQt6.QtCore import Qt, QRectF
import pyqtgraph as pg
from scipy.signal import spectrogram
import matplotlib.cm as cm

# Импортируем оригинальный оркестратор
from src.core.signal_mgr.freq_orchestrator import FreqOrchestrator

class FrequencyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Инициализируем ваш бэкенд-оркестратор
        self.orchestrator = FreqOrchestrator()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("EMG Frequency Analyzer Pro")
        self.setGeometry(100, 100, 1400, 850)

        main_layout = QHBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # =================================================================
        # ЛЕВАЯ ПАНЕЛЬ: УПРАВЛЕНИЕ И ВВОД ДАННЫХ
        # =================================================================
        side_panel = QVBoxLayout()
        input_group = QGroupBox("Параметры пробы")
        input_layout = QVBoxLayout()
        
        self.input_pid = QSpinBox()
        self.input_pid.setRange(1, 9999) 
        self.input_pid.setValue(1)
        
        self.input_trial = QSpinBox()
        self.input_trial.setRange(1, 8)  
        self.input_trial.setValue(1)
        
        self.input_table = QComboBox()
        self.input_table.addItems([
            "Chewing_MassDex_v7",
            "Chewing_MassSix_v7",
            "Chewing_TempDex_v7",
            "Chewing_TempSix_v7",
            "Clenching_MassDex_v7",
            "Clenching_MassSix_v7",
            "Clenching_TempDex_v7",
            "Clenching_TempSix_v7"
        ])
        
        input_layout.addWidget(QLabel("ID Пациента:"))
        input_layout.addWidget(self.input_pid)
        input_layout.addWidget(QLabel("Номер пробы (1-8):"))
        input_layout.addWidget(self.input_trial)
        input_layout.addWidget(QLabel("Таблица (мышца):"))
        input_layout.addWidget(self.input_table)
        
        self.btn_analyze = QPushButton("🚀 Запустить анализ")
        self.btn_analyze.clicked.connect(self.start_analysis)
        input_layout.addWidget(self.btn_analyze)
        
        input_group.setLayout(input_layout)
        side_panel.addWidget(input_group)
        side_panel.addStretch()
        main_layout.addLayout(side_panel, 1)

        # =================================================================
        # ЦЕНТРАЛЬНАЯ ПАНЕЛЬ: ГРАФИКИ И ВКЛАДКИ
        # =================================================================
        self.tabs = QTabWidget()
        
        # --- Вкладка 1: PSD Частотный спектр и Тренд ---
        self.tab_psd = QWidget()
        psd_layout = QVBoxLayout(self.tab_psd)
        
        self.plot_psd = pg.PlotWidget(title="Спектральная плотность мощности (PSD)")
        self.plot_psd.setLabel('left', 'Мощность', units='мкВ²/Гц')
        self.plot_psd.setLabel('bottom', 'Частота', units='Гц')
        self.curve_psd = self.plot_psd.plot(pen=pg.mkPen('w', width=1.5))
        
        self.line_mdf = pg.InfiniteLine(
            pos=0, angle=90, 
            pen=pg.mkPen('g', width=2, style=Qt.PenStyle.DashLine), 
            label="MDF", labelOpts={'position': 0.8, 'color': (0, 255, 0), 'movable': False}
        )
        self.plot_psd.addItem(self.line_mdf)

        self.line_mnf = pg.InfiniteLine(
            pos=0, angle=90, 
            pen=pg.mkPen('b', width=2, style=Qt.PenStyle.DashLine), 
            label="MNF", labelOpts={'position': 0.7, 'color': (50, 100, 255), 'movable': False}
        )
        self.plot_psd.addItem(self.line_mnf)
        
        self.plot_trend = pg.PlotWidget(title="Динамика утомления (Тренд медианной частоты MDF)")
        self.plot_trend.setLabel('left', 'MDF', units='Гц')
        self.plot_trend.setLabel('bottom', 'Время', units='с')
        self.curve_trend = self.plot_trend.plot(pen=pg.mkPen('y', width=2))
        
        psd_layout.addWidget(self.plot_psd, stretch=2)
        psd_layout.addWidget(self.plot_trend, stretch=1)
        
        # --- Вкладка 2: Спектрограмма ---
        self.tab_spec = QWidget()
        spec_layout = QVBoxLayout(self.tab_spec)
        
        self.graphics_view = pg.GraphicsLayoutWidget()
        spec_layout.addWidget(self.graphics_view)
        
        self.plot_spec = self.graphics_view.addPlot(title="Спектрограмма (Развертка частоты во времени)")
        self.plot_spec.setLabel('left', 'Частота', units='Гц')
        self.plot_spec.setLabel('bottom', 'Время', units='с')
        
        self.img_spec = pg.ImageItem()
        self.plot_spec.addItem(self.img_spec)
        self.plot_spec.setMouseEnabled(x=True, y=False)
        
        # 1 в 1 палитра MAGMA
        try:
            mpl_cmap = cm.get_cmap('magma')
            mpl_colors = (mpl_cmap(np.linspace(0, 1, 256)) * 255).astype(np.ubyte)
            pos = np.linspace(0, 1, 256)
            self.colormap = pg.ColorMap(pos, mpl_colors)
        except Exception:
            self.colormap = pg.colormap.get('magma')

        self.color_bar = pg.ColorBarItem(values=(0, 1))
        self.color_bar.setColorMap(self.colormap)
        self.color_bar.setImageItem(self.img_spec)
        
        self.graphics_view.addItem(self.color_bar)
        
        self.tabs.addTab(self.tab_psd, "Частотный спектр (PSD)")
        self.tabs.addTab(self.tab_spec, "Спектрограмма")
        
        main_layout.addWidget(self.tabs, 3)

        # =================================================================
        # ПРАВАЯ ПАНЕЛЬ: КЛИНИЧЕСКИЙ ОТЧЕТ
        # =================================================================
        self.right_panel = QScrollArea()
        self.right_panel.setFixedWidth(380)
        self.right_panel.setWidgetResizable(True)
        self.right_panel.setStyleSheet("background-color: #1e1e1e; border: none;")

        self.results_display = QLabel()
        self.results_display.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.results_display.setWordWrap(True)
        self.results_display.setContentsMargins(15, 15, 15, 15)
        self.results_display.setStyleSheet("background-color: #1e1e1e; color: #dcdcdc; font-family: 'Segoe UI', sans-serif; font-size: 13px;")
        
        self.results_display.setTextFormat(Qt.TextFormat.RichText)
        
        self.right_panel.setWidget(self.results_display)
        main_layout.addWidget(self.right_panel, 1)
        
        self.results_display.setText("<span style='color: #dcdcdc;'>Ожидание запуска анализа...</span>")

    def start_analysis(self):
        try:
            p_id = self.input_pid.value()
            trial = self.input_trial.value()
            table = self.input_table.currentText()
            
            results = self.orchestrator.run_frequency_analysis(p_id, table, trial)
            
            if results:
                full_sig = self.orchestrator.reader.get_signal(p_id, table)
                if full_sig is not None:
                    sample = full_sig[(trial - 1) * 24000 : trial * 24000]
                else:
                    sample = np.array([])
                
                self.update_plots(results, sample)
                self.update_text_results(results, p_id, trial, table)
            else:
                self.results_display.setText("<b style='color:red;'>Ошибка:</b> Оркестратор не вернул данные.")
        except Exception as e:
            self.results_display.setText(f"<b style='color:red;'>Ошибка анализа:</b><br><span style='color:white;'>{str(e)}</span>")

    def update_plots(self, data, sample):
        freqs = data['freqs']
        psd = data['psd']
        
        # --- 1. График PSD (0–500 Гц) ---
        mask = (freqs >= 0) & (freqs <= 500)
        self.curve_psd.setData(freqs[mask], psd[mask])
        
        self.line_mdf.setValue(data['median_frequency'])
        self.line_mnf.setValue(data['mean_frequency'])
        self.plot_psd.autoRange()
        
        # --- 2. График тренда MDF ---
        trend_data = data.get('mdf_trend', [])
        time_axis = data.get('time_axis', [])
        
        if len(trend_data) > 0 and len(time_axis) > 0:
            self.curve_trend.setData(time_axis, trend_data)
            self.plot_trend.autoRange()
        else:
            self.curve_trend.clear()

        # --- 3. Отрисовка Спектрограммы (STFT) ---
        if len(sample) > 0:
            fs = 2000  
            n_per_seg = 1024
            n_overlap = 900 
            
            sig_len = len(sample)
            if sig_len <= n_per_seg:
                n_per_seg = sig_len if sig_len % 2 == 0 else sig_len - 1
                n_overlap = int(n_per_seg * 0.8)

            f_spec, t_spec, Sxx = spectrogram(sample, fs=fs, nperseg=n_per_seg, noverlap=n_overlap)
            
            f_mask = (f_spec >= 20) & (f_spec <= 500)
            Sxx_filtered = Sxx[f_mask, :]
            f_filtered = f_spec[f_mask]
            
            Sxx_log = 10 * np.log10(Sxx_filtered + 1e-10)
            
            # ИСПРАВЛЕНИЕ ЗДЕСЬ: Добавлен .T для правильного поворота матрицы!
            self.img_spec.setImage(Sxx_log.T)
            
            height_y = f_filtered[-1] - f_filtered[0]
            self.img_spec.setRect(QRectF(0.0, f_filtered[0], t_spec[-1], height_y))
            
            self.plot_spec.setXRange(0, t_spec[-1], padding=0)
            self.plot_spec.setYRange(20, 500, padding=0)
            
            self.color_bar.setLevels((-25, 15))
        else:
            self.img_spec.clear()

    def update_text_results(self, res, p_id, trial, table):
        warning_html = ""
        if res.get('warning'):
            warning_html = f"<div style='color: #ff5555; font-weight: bold; margin-top: 15px; background-color: #3a1e1e; padding: 8px; border-radius: 4px;'>{res['warning']}</div>"

        html = f"""
        <div style='line-height: 140%; font-family: Segoe UI, sans-serif; color: #dcdcdc;'>
            <h2 style='color: #55aaff; margin-bottom: 5px; border-bottom: 2px solid #333; padding-bottom: 5px;'>ОТЧЕТ ПО СПЕКТРУ</h2>
            
            <table width='100%' style='margin-bottom: 15px; color: #aaa;'>
                <tr><td>Таблица:</td><td align='right' style='color: #fff;'><b>{table}</b></td></tr>
                <tr><td>Пациент:</td><td align='right' style='color: #fff;'><b>ID {p_id}</b></td></tr>
                <tr><td>Проба:</td><td align='right' style='color: #fff;'><b>№{trial}</b></td></tr>
            </table>

            <hr style='border: none; border-top: 1px solid #333; margin: 10px 0;'>

            <table width='100%' style='border-collapse: collapse; font-size: 14px; color: #dcdcdc;'>
                <tr style='border-bottom: 1px solid #2a2a2a;'>
                    <td style='padding: 6px 0;'>Медианная частота (MDF):</td>
                    <td align='right' style='color: #00FF00;'><b>{res['median_frequency']:.2f} Гц</b></td>
                </tr>
                <tr style='border-bottom: 1px solid #2a2a2a;'>
                    <td style='padding: 6px 0;'>Средняя частота (MNF):</td>
                    <td align='right' style='color: #3366ff;'><b>{res['mean_frequency']:.2f} Гц</b></td>
                </tr>
                <tr style='border-bottom: 1px solid #2a2a2a;'>
                    <td style='padding: 6px 0;'>Пиковая частота:</td>
                    <td align='right' style='color: #fff;'><b>{res['peak_frequency']:.2f} Гц</b></td>
                </tr>
                <tr style='border-bottom: 1px solid #2a2a2a;'>
                    <td style='padding: 6px 0;'>Коэффициент H/L (баланс):</td>
                    <td align='right' style='color: #fff;'><b>{res['hl_ratio']:.3f}</b></td>
                </tr>
                <tr style='border-bottom: 1px solid #2a2a2a;'>
                    <td style='padding: 6px 0;'>Спектральная энтропия (сложность):</td>
                    <td align='right' style='color: #fff;'><b>{res['entropy']:.3f}</b></td>
                </tr>
                <tr style='border-bottom: 1px solid #2a2a2a;'>
                    <td style='padding: 6px 0;'>Утомление (Slope):</td>
                    <td align='right' style='color: #ff5555;'><b>{res['fatigue_slope']:.2f} Гц/сек</b></td>
                </tr>
                <tr>
                    <td style='padding: 6px 0;'>Падение MDF за пробу:</td>
                    <td align='right' style='color: #fff;'><b>{res['fatigue_drop_pct']:.1f} %</b></td>
                </tr>
            </table>

            <hr style='border: none; border-top: 1px solid #333; margin: 15px 0;'>
            
            <div style='background-color: #252525; padding: 10px; border-radius: 5px; border-left: 4px solid #55aaff; font-size: 12px; color: #ddd;'>
                💡 <b>Подсказка:</b> Смещение MDF вниз говорит о мышечном утомлении.
            </div>

            {warning_html}
        </div>
        """
        self.results_display.setText(html)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FrequencyApp()
    window.show()
    sys.exit(app.exec())
import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLineEdit, QLabel, 
                             QTabWidget, QTextEdit, QGroupBox)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.core.signal_mgr.freq_orchestrator import FreqOrchestrator

class FrequencyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.orchestrator = FreqOrchestrator()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("EMG Frequency Analyzer Pro")
        self.setGeometry(100, 100, 1200, 800)

        main_layout = QHBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # --- ЛЕВАЯ ПАНЕЛЬ: ВВОД ДАННЫХ ---
        side_panel = QVBoxLayout()
        input_group = QGroupBox("Параметры пациента")
        input_layout = QVBoxLayout()
        
        self.input_pid = QLineEdit("1")
        self.input_trial = QLineEdit("1")
        self.input_table = QLineEdit("Chewing_MassDex_v7")
        
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

        # --- ЦЕНТРАЛЬНАЯ ПАНЕЛЬ: ГРАФИКИ ---
        self.tabs = QTabWidget()
        self.canvas_psd = self.create_canvas()
        self.canvas_spec = self.create_canvas()
        
        self.tabs.addTab(self.canvas_psd, "Спектр мощности (PSD)")
        self.tabs.addTab(self.canvas_spec, "Спектрограмма")
        main_layout.addWidget(self.tabs, 3)

        # --- ПРАВАЯ ПАНЕЛЬ: РЕЗУЛЬТАТЫ ---
        res_panel = QVBoxLayout()
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        res_panel.addWidget(QLabel("Метрики и вердикт:"))
        res_panel.addWidget(self.results_display)
        main_layout.addLayout(res_panel, 1)

    def create_canvas(self):
        figure = Figure()
        canvas = FigureCanvas(figure)
        return canvas

    def start_analysis(self):
        try:
            p_id = int(self.input_pid.text())
            trial = int(self.input_trial.text())
            table = self.input_table.text()
            
            # ВЫЗОВ ТВОЕГО БЭКЕНДА
            results = self.orchestrator.run_frequency_analysis(p_id, table, trial)
            
            if results:
                self.update_plots(results)
                self.update_text_results(results)
        except Exception as e:
            self.results_display.setText(f"Ошибка: {str(e)}")

    def update_plots(self, data):
        # 1. Отрисовка PSD (используем твою логику из FreqVisualizer)
        ax = self.canvas_psd.figure.clear()
        ax = self.canvas_psd.figure.add_subplot(111)
        ax.plot(data['freqs'], data['psd'], color='black', lw=1)
        ax.axvline(x=data['median_frequency'], color='green', ls='--', label='MDF')
        ax.set_title("Power Spectral Density")
        ax.set_xlim(0, 500)
        ax.grid(True)
        self.canvas_psd.draw()
        
        # 2. Отрисовка Спектрограммы (заглушка, вызовем твой метод spectrogram)
        # Здесь мы можем адаптировать plot_single_spectrogram под self.canvas_spec.figure
        self.canvas_spec.draw()

    def update_text_results(self, res):
        report = (
            f"MDF: {res['median_frequency']:.2f} Hz\n"
            f"MNF: {res['mean_frequency']:.2f} Hz\n"
            f"H/L Ratio: {res['hl_ratio']:.3f}\n"
            f"Entropy: {res['entropy']:.3f}\n"
            f"Fatigue: {res['fatigue_slope']:.2f} Hz/sec\n"
            f"{'-'*20}\n"
            f"{res['warning']}"
        )
        self.results_display.setText(report)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FrequencyApp()
    window.show()
    sys.exit(app.exec())
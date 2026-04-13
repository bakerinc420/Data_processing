from src.database.provider.reader import EMGReader
from src.core.algorithms.frequency_domain import FrequencyDomainProcessor
from src.core.algorithms.time_domain import TimeDomainProcessor # Используем для поиска границ
from src.core.signal_mgr.comparative_orchestrator import ComparativeOrchestrator

import numpy as np

class FreqOrchestrator:
    def __init__(self):
        self.reader = EMGReader()
        self.freq_proc = FrequencyDomainProcessor()
        self.time_proc = TimeDomainProcessor() # Для выделения зоны активности
        self.comparator = ComparativeOrchestrator(self.reader, self.freq_proc)

    def run_full_diagnostic(self, p_id, trial, mode="Chewing"):
        """
        Полный клинический анализ 4-х мышц.
        """
        # Определяем список таблиц на основе режима (Chewing или Relax)
        muscle_keys = ["MassDex", "MassSix", "TempDex", "TempSix"]
        reports = {}

        for key in muscle_keys:
            table_name = f"{mode}_{key}_v7"
            # Используем твой готовый метод анализа одного канала
            res = self.run_frequency_analysis(p_id, table_name, trial)
            if res is None:
                print(f"⚠️ Данные для {table_name} не найдены.")
                return None
            reports[key] = res

        # Считаем индексы через наш новый comparator
        # 1. Симметрия жевательных
        poc_mass = self.comparator.calculate_poc(
            reports["MassDex"]["median_frequency"], 
            reports["MassSix"]["median_frequency"]
        )
        
        # 2. Симметрия височных
        poc_temp = self.comparator.calculate_poc(
            reports["TempDex"]["median_frequency"], 
            reports["TempSix"]["median_frequency"]
        )
        
        # 3. Индекс активности (берем среднее по сторонам для Mass и Temp)
        avg_mass = (reports["MassDex"]["median_frequency"] + reports["MassSix"]["median_frequency"]) / 2
        avg_temp = (reports["TempDex"]["median_frequency"] + reports["TempSix"]["median_frequency"]) / 2
        att_index = self.comparator.calculate_activity_index(avg_mass, avg_temp)

        return {
            "reports": reports,
            "indices": {
                "poc_mass": poc_mass,
                "poc_temp": poc_temp,
                "att_index": att_index
            }
        }

    def run_frequency_analysis(self, p_id, table, trial):
        """
        Полный цикл частотного анализа: Загрузка -> Обрезка -> FFT -> Статистика
        """
        trial_idx = trial - 1
        
        # 1. Загрузка данных
        full_signal = self.reader.get_signal(p_id, table)
        if full_signal is None:
            return None

        # Выделяем нужную пробу (24000 точек)
        sample = full_signal[trial_idx * 24000 : trial * 24000]

        # 2. Поиск границ активности (чтобы считать спектр только работающей мышцы)
        # Мы используем уже готовый метод из временной области
        start_act, end_act = self.time_proc.find_activity_borders(sample)
        
        if start_act is None or end_act is None:
            active_zone = sample
        else:
            active_zone = sample[start_act:end_act]

        # 3. Частотный анализ
        # get_frequency_report сделает FFT и посчитает MDF, MNF
        freq_results = self.freq_proc.get_frequency_report(active_zone)

        # Добавляем информацию о пациенте для визуализатора
        freq_results['info'] = {
            'p_id': p_id,
            'table': table,
            'trial': trial,
            'start_act': start_act,
            'end_act': end_act
        }

        return freq_results
    
    def run_super_diagnostic(self, p_id, trial):
        """
        Комплексный анализ: сравнение состояния Покоя (Relax) и Жевательной пробы (Chewing).
        """
        print(f"📊 Сбор комплексных данных для Пациента {p_id}...")
        
        # Запускаем полную диагностику для обоих режимов
        relax_data = self.run_full_diagnostic(p_id, trial, mode="Relax")
        chewing_data = self.run_full_diagnostic(p_id, trial, mode="Chewing")
        
        if relax_data is None or chewing_data is None:
            return None
            
        return {
            "relax": relax_data,
            "chewing": chewing_data
        }
    
    def get_raw_signals_for_24(self, p_id, trial):
        import pandas as pd
        import numpy as np
        from config import MICROVOLT_FACTOR
        
        # 1. Теперь здесь 8 мышц (строк графика)
        # Суффиксы точно как в твоей БД: CMD, CMS, CTD, CTS + RMD, RMS, RTD, RTS
        muscle_map = {
            "MassDex_C": "CMD", "MassSix_C": "CMS",
            "TempDex_C": "CTD", "TempSix_C": "CTS",
            "MassDex_R": "RMD", "MassSix_R": "RMS",
            "TempDex_R": "RTD", "TempSix_R": "RTS"
        }

        states_map = {
            "BEFORE": "Spectrum_Before_Compress",
            "COMPRESS": "Spectrum_Compress",
            "AFTER": "Spectrum_After_Compress"
        }
        
        full_matrix = {}
        engine = self.reader.engine 
        target_column = f"patient_{p_id}"

        for m_name, suffix in muscle_map.items():
            full_matrix[m_name] = {}
            for col_name, prefix in states_map.items():
                table_name = f"{prefix}_{suffix}"
                
                try:
                    # Прямой запрос к конкретной колонке и таблице
                    query = f'SELECT "{target_column}" FROM "{table_name}"'
                    df = pd.read_sql(query, engine)
                    signal = df[target_column].to_numpy()
                    
                    # Убираем нули и применяем коэффициент
                    active_signal = signal[signal != 0]
                    
                    if len(active_signal) > 0:
                        processed_sig = active_signal * MICROVOLT_FACTOR
                        full_matrix[m_name][col_name] = self.freq_proc._highpass_filter(processed_sig)
                    else:
                        full_matrix[m_name][col_name] = None
                        
                except Exception as e:
                    # Если таблицы не существует, просто забиваем ячейку None
                    full_matrix[m_name][col_name] = None
                    
        return full_matrix
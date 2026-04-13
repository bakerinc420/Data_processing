from src.core.algorithms.frequency_domain import FrequencyDomainProcessor

class ComparativeOrchestrator:
    def __init__(self, reader, freq_proc):
        self.reader = reader
        self.freq_proc = freq_proc

    def calculate_poc(self, val_dex, val_six):
        """
        POC (Percentage Overlapping Coefficient) — индекс симметрии.
        val_dex: значение (напр. MDF) правой стороны
        val_six: значение (напр. MDF) левой стороны
        """
        if (val_dex + val_six) == 0:
            return 100.0
        # Коэффициент пересечения: 100% — идеальная симметрия
        return (1 - abs(val_dex - val_six) / (val_dex + val_six)) * 100

    def calculate_activity_index(self, mass_avg, temp_avg):
        """
        Activity Index (ATT) — баланс между жевательными и височными мышцами.
        Положительный результат (>0) — доминируют жевательные (Mass).
        Отрицательный результат (<0) — доминируют височные (Temp).
        """
        if (mass_avg + temp_avg) == 0:
            return 0.0
        return ((mass_avg - temp_avg) / (mass_avg + temp_avg)) * 100
    
    def get_clinical_verdict(self, indices):
        """
        Превращает сухие цифры в клиническую оценку.
        """
        verdicts = []
        
        # Оценка симметрии (Норма > 80-85%)
        if indices['poc_mass'] < 80:
            verdicts.append("⚠️ Асимметрия жевательных мышц (проверьте окклюзионные контакты)")
        else:
            verdicts.append("✅ Симметрия жевательных мышц в норме")

        if indices['poc_temp'] < 80:
            verdicts.append("⚠️ Асимметрия височных мышц (возможен перекос челюсти)")
        else:
            verdicts.append("✅ Симметрия височных мышц в норме")

        # Оценка индекса активности (ATT)
        # Норма для жевания: +10 до +30 (Mass доминирует)
        att = indices['att_index']
        if att < 0:
            verdicts.append("🚨 Патологическое доминирование височных мышц (признак бруксизма или дистального прикуса)")
        elif att > 50:
            verdicts.append("⚠️ Избыточное доминирование жевательных мышц")
        else:
            verdicts.append("✅ Баланс Masseter/Temporalis в норме")

        return verdicts
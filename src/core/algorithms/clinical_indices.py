class ClinicalIndices:
    @staticmethod
    def calculate_poc(val_left, val_right):
        """Расчет индекса симметрии (POC)"""
        if val_left == 0 and val_right == 0: return 100
        # Коэффициент пересечения в процентах
        return (1 - abs(val_left - val_right) / (val_left + val_right)) * 100

    @staticmethod
    def calculate_activity(mass_avg, temp_avg):
        """Расчет индекса активности (отношение жевательных к височным)"""
        if (mass_avg + temp_avg) == 0: return 0
        return ((mass_avg - temp_avg) / (mass_avg + temp_avg)) * 100
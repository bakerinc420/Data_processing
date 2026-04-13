from src.database.ingestion.loader import DataIngestor
import os

def run_ingestion():
    ingestor = DataIngestor()
    
    # Пути к вашим mat-файлам (проверьте, что они лежат в папке data)
    mio_path = "./data/data_mio_v7.mat"
    border_path = "./data/border_v7.mat"

    if os.path.exists(mio_path):
        ingestor.load_mio_data(mio_path)
    else:
        print(f"❌ Файл {mio_path} не найден!")

    if os.path.exists(border_path):
        ingestor.load_border_data(border_path)
    else:
        print(f"❌ Файл {border_path} не найден!")

if __name__ == "__main__":
    run_ingestion()
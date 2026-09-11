from pathlib import Path
from datetime import datetime


class logTut:

    def __init__(self):
        folder = Path(__file__).resolve().parent
        print(folder)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = folder / f"ucus_logu_{timestamp}.txt"

    def write(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

        print(message + "\n")

    def info(self, message):
        self.write(f"INFO: {message}")
        

    def error(self, message):
        self.write(f"HATA: {message}")

    def start(self):
        self.write("========== PROGRAM BAŞLADI ==========")

    def stop(self):
        self.write("========== PROGRAM DURDU ==========")
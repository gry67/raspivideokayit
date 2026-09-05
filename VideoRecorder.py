import cv2
from datetime import datetime


class VideoRecorder:
    """
    Sadece video kaydının başlatılması, frame yazılması ve güvenli sonlandırılmasından sorumlu sınıf.
    """

    def __init__(self, kayit_klasoru="/home/guray/Desktop", fps=30, resolution=(640, 480)):
        self.kayit_klasoru = kayit_klasoru
        self.fps = fps
        self.resolution = resolution
        self.writer = None
        self.is_recording = False
        self.filename = None

    def _yeni_dosya_adi_olustur(self):
        zaman_etiketi = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        return f"{self.kayit_klasoru}/ucus_kaydi_{zaman_etiketi}.avi"

    def start(self):
        if not self.is_recording:
            self.filename = self._yeni_dosya_adi_olustur()

            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            self.writer = cv2.VideoWriter(
                self.filename,
                fourcc,
                self.fps,
                self.resolution
            )

            self.is_recording = True
            print(f"[*] Kayıt BAŞLADI: {self.filename}")

    def write_frame(self, frame):
        if self.is_recording and self.writer is not None:
            self.writer.write(frame)

    def stop(self):
        if self.is_recording:
            self.writer.release()
            self.writer = None
            self.is_recording = False
            print(f"[*] Kayıt GÜVENLE DURDURULDU: {self.filename}")
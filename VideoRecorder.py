import cv2

class VideoRecorder:
    """
    Sadece video kaydının başlatılması, frame yazılması ve güvenli sonlandırılmasından sorumlu sınıf.
    """
    def __init__(self, filename="flight_video.avi", fps=30, resolution=(640, 480)):
        self.filename = filename
        self.fps = fps
        self.resolution = resolution
        self.writer = None
        self.is_recording = False

    def start(self):
        if not self.is_recording:
            # XVID yerine MJPG codec kullanıyoruz
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            self.writer = cv2.VideoWriter(self.filename, fourcc, self.fps, self.resolution)
            self.is_recording = True
            print(f"[*] Kayıt BAŞLADI: {self.filename}")

    def write_frame(self, frame):
        if self.is_recording and self.writer is not None:
            self.writer.write(frame)

    def stop(self):
        if self.is_recording:
            self.writer.release()
            self.is_recording = False
            print("[*] Kayıt GÜVENLE DURDURULDU. Dosya kapatıldı.")
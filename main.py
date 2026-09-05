import time
import cv2
from datetime import datetime
from picamera2 import Picamera2

# ==========================================
# SİSTEM MODU ŞALTERİ
# ==========================================
USE_PIXHAWK = False  

if USE_PIXHAWK:
    from MavlinkNode import MavlinkNode

from VideoRecorder import VideoRecorder

def main():
    print("[INFO] Picamera2 başlatılıyor...")
    # Picamera2 nesnesini oluştur
    picam2 = Picamera2()
    
    # Kamerayı RGB formatında ve 640x480 çözünürlüğünde yapılandırıyoruz
    config = picam2.create_video_configuration(main={"size": (640, 480), "format": "RGB888"})
    picam2.configure(config)
    picam2.start()
    print("[INFO] Kamera başarıyla yapılandırıldı ve başlatıldı.")

    cam_width = 640
    cam_height = 480

    # Dosya adını ve yolunu oluştur
    zaman_etiketi = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    VIDEO_FILE = f"/home/guray/Desktop/ucus_kaydi_{zaman_etiketi}.avi"
    
    recorder = VideoRecorder(filename=VIDEO_FILE, fps=30, resolution=(cam_width, cam_height))
    
    uav_link = None
    recording_active = False

    # MOD SEÇİMİNE GÖRE BAŞLANGIÇ DAVRANIŞI
    if USE_PIXHAWK:
        print("[INFO] MOD: PIXHAWK AKTİF. Bağlantı kuruluyor ve RC sinyali bekleniyor...")
        uav_link = MavlinkNode(connection_string='/dev/ttyACM0', baudrate=57600)
        RC_RECORD_CHANNEL = 8
    else:
        print(f"[INFO] MOD: BAĞIMSIZ (STANDALONE). Pixhawk devre dışı.")
        print(f"[*] Kayıt doğrudan başlatılıyor: {VIDEO_FILE}")
        recorder.start()
        recording_active = True

    try:
        while True:
            # 1. Picamera2'den doğrudan numpy dizisi (frame) olarak görüntüyü al
            frame = picam2.capture_array()
            
            if frame is None:
                continue

            # ==========================================
            # İleride OpenCV Target Detection kodlarını buraya ekleyebilirsin
            # ==========================================

            # 2. Pixhawk modu açıksa RC komutlarını dinle
            if USE_PIXHAWK and uav_link:
                uav_link.send_heartbeat_if_needed()
                rc_switch = uav_link.update_rc_channel_state(channel=RC_RECORD_CHANNEL)
                
                if rc_switch == True and not recording_active:
                    recorder.start()
                    recording_active = True
                elif rc_switch == False and recording_active:
                    recorder.stop()
                    recording_active = False

            # 3. Kayıt aktifse frame'i diske yaz
            if recording_active:
                recorder.write_frame(frame)

    except KeyboardInterrupt:
        print("\n[INFO] Kod terminalden (Ctrl+C) durduruldu.")
    except Exception as e:
        print(f"\n[!] Beklenmeyen Hata: {e}")
    finally:
        # Program kapanırken her şeyi güvenle temizle
        recorder.stop()
        picam2.stop()
        print("[INFO] Video dosyası başarıyla kaydedildi, sistem kapatıldı.")

if __name__ == '__main__':
    main()
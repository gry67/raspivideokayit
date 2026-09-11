import time
import cv2
from logTut import logTut


# ==========================================
# SİSTEM MODU ŞALTERİ
# ==========================================
USE_PIXHAWK = True

if USE_PIXHAWK:
    from MavlinkNode import MavlinkNode
    from picamera2 import Picamera2

from VideoRecorder import VideoRecorder
from VisionProcessor import VisionProcessor as vp



KAMERA_YENIDEN_DENE_SURESI = 3
MAVLINK_YENIDEN_DENE_SURESI = 3


def kamera_baslat():
    """Kamera hazır olana kadar tekrar dener ve hazır kamerayı döndürür."""
    while True:
        picam2 = None
        try:
            print("[INFO] Kamera başlatılıyor...")

            picam2 = Picamera2()
            config = picam2.create_video_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )
            picam2.configure(config)
            picam2.start()

            print("[INFO] Kamera başarıyla yapılandırıldı ve başlatıldı.")
            return picam2

        except Exception as e:
            print(f"[HATA] Kamera başlatılamadı: {e}")
            print(f"[INFO] {KAMERA_YENIDEN_DENE_SURESI} saniye sonra kamera tekrar denenecek...")

            if picam2 is not None:
                try:
                    picam2.stop()
                except Exception:
                    pass

                try:
                    picam2.close()
                except Exception:
                    pass

            time.sleep(KAMERA_YENIDEN_DENE_SURESI)


def main():
    picam2 = None
    recorder = None
    uav_link = None
    recording_active = False
    goruntu_isleyici = vp()
    mavi_servo_calisti_mi = False
    mavi_gorulen_frame_sayisi  = 0
    kirmizi_gorulen_frame_sayisi = 0
    log = logTut()

    try:
        # ==========================================
        # KAMERA
        # ==========================================
        picam2 = kamera_baslat()

        cam_width = 640
        cam_height = 480

        recorder = VideoRecorder(
        kayit_klasoru="/home/atlas/Desktop",
        fps=30,
        resolution=(cam_width, cam_height)
        )

        # ==========================================
        # PIXHAWK / MAVLINK
        # ==========================================
        RC_RECORD_CHANNEL = 8

        if USE_PIXHAWK:
            log.info("[INFO] MOD: PIXHAWK AKTİF.")
            log.info("[INFO] Pixhawk/MAVLink bağlantısı bekleniyor...")
        else:
            log.info("[INFO] MOD: BAĞIMSIZ (STANDALONE). Pixhawk devre dışı.")
            log.info(f"[*] Kayıt doğrudan başlatılıyor: {VIDEO_FILE}")
            recorder.start()
            recording_active = True

        # ==========================================
        # ANA DÖNGÜ
        # ==========================================
        while True:
            # ------------------------------------------
            # Kamera görüntüsü
            # ------------------------------------------
            try:
                frame = picam2.capture_array()

                tespitler = goruntu_isleyici.detect_all(frame=frame)
                frame = goruntu_isleyici.draw_detections(frame=frame,detections=tespitler)

                mavi_guven_orani = tespitler["blue"][0].confidence if tespitler["blue"] else 0
                kirmizi_guven_orani = tespitler["red"][0].confidence if tespitler["red"] else 0  



                if frame is None:
                    log.info("[UYARI] Kameradan frame alınamadı.")
                    time.sleep(0.1)
                    continue

            except Exception as e:
                log.info(f"[HATA] Kamera çalışırken hata oluştu: {e}")
                log.info(f"[INFO] Kamera yeniden başlatılmaya çalışılıyor...")

                try:
                    picam2.stop()
                except Exception:
                    pass

                try:
                    picam2.close()
                except Exception:
                    pass

                picam2 = kamera_baslat()
                continue

            # ------------------------------------------
            # Pixhawk / RC kontrolü
            # ------------------------------------------
            if USE_PIXHAWK:
                if uav_link is None:
                    try:
                        log.info("[INFO] Pixhawk'a MAVLink bağlantısı kuruluyor...")
                        uav_link = MavlinkNode(
                            connection_string='/dev/ttyACM0',
                            baudrate=57600
                        )
                        log.info("[INFO] MAVLink bağlantısı başarıyla kuruldu.")

                    except Exception as e:
                        log.info(f"[HATA] MAVLink bağlantısı kurulamadı: {e}")
                        log.info(f"[INFO] {MAVLINK_YENIDEN_DENE_SURESI} saniye sonra tekrar denenecek...")
                        uav_link = None
                        time.sleep(MAVLINK_YENIDEN_DENE_SURESI)
                        continue

                try:
                    uav_link.send_heartbeat_if_needed()
                    rc_switch = uav_link.update_rc_channel_state(
                        channel=RC_RECORD_CHANNEL
                    )

                    # None = henüz geçerli RC mesajı gelmedi.
                    # Bu durumda kayıt durumuna dokunmuyoruz.
                    if rc_switch is True and not recording_active:
                        recorder.start()
                        recording_active = True

                    elif rc_switch is False and recording_active:
                        recorder.stop()
                        recording_active = False

                except Exception as e:
                    log.info(f"[HATA] MAVLink/RC iletişiminde hata oluştu: {e}")
                    log.info("[INFO] MAVLink bağlantısı sıfırlanıyor, tekrar bağlanılacak...")
                    uav_link = None
                    time.sleep(MAVLINK_YENIDEN_DENE_SURESI)
                    continue

            # ------------------------------------------
            # Video kaydı
            # ------------------------------------------
            if recording_active:
                try:
                    recorder.write_frame(frame)
        
                except Exception as e:
                    log.info(f"[HATA] Video frame'i yazılamadı: {e}")                    

                try:
                    mavi_goruldu = bool(tespitler["blue"])
                    kirmizi_goruldu = bool(tespitler["red"])

                    if mavi_goruldu and mavi_guven_orani > 85:
                        #Hedef Görüldü
                        mavi_gorulen_frame_sayisi+=1

                        if mavi_gorulen_frame_sayisi >10:
                            uav_link.set_servo_pwm(6, 1900)
                            mavi_servo_calisti_mi = True
                    
                except Exception as e:
                    log.info(f"[HATA] mavi yada kirmizi gorulduyse atis yapan kodun olduğu yerde sikinti var: {e} \n" +
                             f"mavi_goruldu: {mavi_goruldu}\n" + f"kirmizi_goruldu: {kirmizi_goruldu} \n" +
                               f"mavi_gorulen_frame_sayisi: {mavi_gorulen_frame_sayisi}")

    except KeyboardInterrupt:
        log.info("\n[INFO] Kod terminalden (Ctrl+C) durduruldu.")

    except Exception as e:
        log.info(f"\n[!] Beklenmeyen kritik hata: {e}")

    finally:
        if recorder is not None:
            try:
                recorder.stop()
            except Exception as e:
                log.info(f"[UYARI] Recorder kapatılırken hata: {e}")

        if picam2 is not None:
            try:
                picam2.stop()
            except Exception as e:
                log.info(f"[UYARI] Kamera durdurulurken hata: {e}")

            try:
                picam2.close()
            except Exception:
                pass

        log.info("[INFO] ATLAS güvenli şekilde kapatıldı.")


if __name__ == '__main__':
    main()

from pymavlink import mavutil
import time

class MavlinkNode:
    """
    Sadece Pixhawk ile olan MAVLink haberleşmesinden sorumlu sınıf.
    ID: 191 (MAV_COMP_ID_ONBOARD_COMPUTER) olarak kendini tanıtır.
    """
    def __init__(self, connection_string, baudrate):
        print(f"MAVLink bağlantısı başlatılıyor: {connection_string} @ {baudrate}")
        # Companion computer olarak bağlanıyoruz (System ID: 1, Component ID: 191)
        self.master = mavutil.mavlink_connection(
            connection_string, 
            baud=baudrate, 
            source_system=1, 
            source_component=191
        )
        self.last_heartbeat_time = 0
        self.latest_rc_state = False

    def send_heartbeat_if_needed(self, interval=1.0):
        """Saniyede bir Heartbeat gönderir (ArduPilot'un bizi canlı görmesi için)."""
        current_time = time.time()
        if current_time - self.last_heartbeat_time >= interval:
            self.master.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER,
                mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                0, 0, 0
            )
            self.last_heartbeat_time = current_time

    def update_rc_channel_state(self, channel=7, threshold=1500):
        """
        RC_CHANNELS mesajlarını okur.
        Kuyrukta biriken eski mesajları tüketip en güncel olanı alır.
        """
        msg = None
        while True:
            # Buffer'ı temizlemek için mesajları bloklanmadan oku
            m = self.master.recv_match(type='RC_CHANNELS', blocking=False)
            if not m:
                break
            msg = m
        
        if msg:
            # İlgili kanalı dinamik olarak çekiyoruz (örneğin: chan7_raw)
            chan_val = getattr(msg, f"chan{channel}_raw", None)
            if chan_val is not None:
                self.latest_rc_state = (chan_val > threshold)
        
        return self.latest_rc_state
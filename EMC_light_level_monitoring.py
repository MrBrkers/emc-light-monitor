import sys
import time
import cv2
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QPushButton, QDoubleSpinBox, QHBoxLayout, 
                             QVBoxLayout, QGroupBox, QFileDialog, QMessageBox)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Windows/Linux bip sesi desteği
try:
    import winsound
    def play_beep():
        winsound.Beep(1000, 200)  # 1000 Hz, 200 ms
except ImportError:
    import os
    def play_beep():
        os.system('play -nq -t alsa synth 0.2 sine 1000' if sys.platform.startswith('linux') else 'printf "\a"')

class EMCLightMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EMC Test - Işık Şiddeti Monitor & Veri Kaydı")
        self.setGeometry(100, 100, 1150, 620)

        # Temel Değişkenler
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        self.is_monitoring = False
        self.selected_roi = None  # (x, y, w, h)
        self.ref_brightness = None
        
        # Grafik ve Veri Depolama (Sınır yok, baştan sona tutulur)
        self.time_data = []
        self.brightness_data = []
        self.status_data = []
        self.start_time = None

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Sol Taraf: Kamera Görüntüsü ve Kontroller
        left_layout = QVBoxLayout()
        
        self.video_label = QLabel("Kamera Başlatılmadı")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("border: 2px solid gray; background-color: black; color: white;")
        self.video_label.setFixedSize(640, 480)
        left_layout.addWidget(self.video_label)

        # Durum Etiketi (PASS / FAIL)
        self.status_label = QLabel("DURUM: BEKLEMEDE")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 20px; font-weight: bold; background-color: lightgray; padding: 5px;")
        left_layout.addWidget(self.status_label)

        # Kontrol Paneli
        control_group = QGroupBox("Kontroller")
        control_layout = QHBoxLayout()

        self.btn_select_roi = QPushButton("Bölge Seç (ROI)")
        self.btn_select_roi.clicked.connect(self.select_roi)
        
        self.lbl_tolerance = QLabel("Tolerans (%):")
        self.spin_tolerance = QDoubleSpinBox()
        self.spin_tolerance.setRange(0.1, 100.0)
        self.spin_tolerance.setValue(10.0)  # Varsayılan %10 tolerans

        self.btn_toggle = QPushButton("Başlat")
        self.btn_toggle.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        self.btn_toggle.clicked.connect(self.toggle_monitoring)

        self.btn_export = QPushButton("CSV Export")
        self.btn_export.setEnabled(False)  # Test bitmeden aktif olmasın
        self.btn_export.clicked.connect(self.export_csv)

        control_layout.addWidget(self.btn_select_roi)
        control_layout.addWidget(self.lbl_tolerance)
        control_layout.addWidget(self.spin_tolerance)
        control_layout.addWidget(self.btn_toggle)
        control_layout.addWidget(self.btn_export)
        control_group.setLayout(control_layout)
        
        left_layout.addWidget(control_group)
        main_layout.addLayout(left_layout)

        # Sağ Taraf: Matplotlib Grafiği
        right_layout = QVBoxLayout()
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)
        main_layout.addLayout(right_layout)

        # Kamerayı Başlat
        self.cap = cv2.VideoCapture(0)
        self.timer.start(30)  # ~33 FPS

    def select_roi(self):
        """Kullanıcının farenin sol tuşuyla ekranda kutu çizerek alan seçmesini sağlar."""
        if not self.cap or not self.cap.isOpened():
            return
        
        ret, frame = self.cap.read()
        if ret:
            roi = cv2.selectROI("Takip Edilecek Bolgeyi Secin ve ENTER'a Basin", frame, showCrosshair=True)
            cv2.destroyWindow("Takip Edilecek Bolgeyi Secin ve ENTER'a Basin")
            
            if roi[2] > 0 and roi[3] > 0:  # Genişlik ve yükseklik > 0 ise
                self.selected_roi = roi
                x, y, w, h = roi
                crop = frame[y:y+h, x:x+w]
                gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                self.ref_brightness = np.mean(gray_crop)

    def toggle_monitoring(self):
        if not self.is_monitoring:
            if self.selected_roi is None:
                self.status_label.setText("LÜTFEN ÖNCE BÖLGE SEÇİN!")
                self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; background-color: orange; color: white;")
                return
            
            # Yeni Testi Başlat
            self.is_monitoring = True
            self.start_time = time.time()
            self.time_data.clear()
            self.brightness_data.clear()
            self.status_data.clear()

            self.btn_toggle.setText("Durdur")
            self.btn_toggle.setStyleSheet("background-color: red; color: white; font-weight: bold;")
            self.btn_select_roi.setEnabled(False)
            self.spin_tolerance.setEnabled(False)
            self.btn_export.setEnabled(False)
        else:
            # Testi Durdur
            self.is_monitoring = False
            self.btn_toggle.setText("Başlat")
            self.btn_toggle.setStyleSheet("background-color: green; color: white; font-weight: bold;")
            self.btn_select_roi.setEnabled(True)
            self.spin_tolerance.setEnabled(True)
            
            if len(self.time_data) > 0:
                self.btn_export.setEnabled(True)  # CSV indirmeyi aktif et
            
            self.status_label.setText("DURUM: DURDURULDU")
            self.status_label.setStyleSheet("font-size: 20px; font-weight: bold; background-color: lightgray;")

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        current_brightness = 0

        # Eğer bölge seçildiyse ekranda yeşil kutu ile göster
        if self.selected_roi:
            x, y, w, h = self.selected_roi
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            crop = frame[y:y+h, x:x+w]
            gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            current_brightness = np.mean(gray_crop)

        # İzleme modundaysa tolerans kontrolü ve veri toplama
        if self.is_monitoring and self.ref_brightness is not None:
            tolerance_percent = self.spin_tolerance.value()
            lower_bound = self.ref_brightness * (1 - tolerance_percent / 100.0)
            upper_bound = self.ref_brightness * (1 + tolerance_percent / 100.0)

            elapsed_time = time.time() - self.start_time
            self.time_data.append(elapsed_time)
            self.brightness_data.append(current_brightness)

            # Tolerans kontrolü
            if lower_bound <= current_brightness <= upper_bound:
                self.status_label.setText("DURUM: PASS")
                self.status_label.setStyleSheet("font-size: 24px; font-weight: bold; background-color: green; color: white;")
                self.status_data.append("PASS")
            else:
                self.status_label.setText("DURUM: FAIL (HATA DEĞERİ!)")
                self.status_label.setStyleSheet("font-size: 24px; font-weight: bold; background-color: red; color: white;")
                self.status_data.append("FAIL")
                play_beep()

            # Grafiği Çizdir (Eski veriler silinmeden baştan sona çizilir)
            self.ax.clear()
            self.ax.plot(self.time_data, self.brightness_data, 'b-', label='Işık Şiddeti')
            self.ax.axhline(y=self.ref_brightness, color='g', linestyle='--', label='Referans')
            self.ax.axhline(y=upper_bound, color='r', linestyle=':', label='Üst Limit')
            self.ax.axhline(y=lower_bound, color='r', linestyle=':', label='Alt Limit')
            self.ax.set_title("Işık Şiddeti Zaman Grafiği (Tüm Test)")
            self.ax.set_xlabel("Zaman (saniye)")
            self.ax.set_ylabel("Parlaklık Değeri (0-255)")
            self.ax.legend(loc="upper right")
            self.canvas.draw()

        # OpenCV görüntüsünü PyQt5 formatına çevirme
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
        self.video_label.setPixmap(QPixmap.fromImage(p))

    def export_csv(self):
        """Toplanan zaman, ışık şiddeti ve durum verilerini CSV dosyasına kaydeder."""
        if not self.time_data:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "CSV Dosyasını Kaydet", "emc_test_sonuclari.csv", "CSV Files (*.csv)")
        if file_path:
            tolerance_percent = self.spin_tolerance.value()
            lower_bound = self.ref_brightness * (1 - tolerance_percent / 100.0)
            upper_bound = self.ref_brightness * (1 + tolerance_percent / 100.0)

            df = pd.DataFrame({
                "Zaman_Saniye": self.time_data,
                "Isik_Siddeti": self.brightness_data,
                "Durum": self.status_data,
                "Referans_Deger": [self.ref_brightness] * len(self.time_data),
                "Alt_Limit": [lower_bound] * len(self.time_data),
                "Ust_Limit": [upper_bound] * len(self.time_data)
            })

            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, "Başarılı", f"Veriler başarıyla kaydedildi:\n{file_path}")

    def closeEvent(self, event):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = EMCLightMonitor()
    win.show()
    sys.exit(app.exec_())

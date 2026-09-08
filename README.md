# EMC Light Monitor 💡⚡

An automated real-time light intensity monitoring system designed for **Electromagnetic Compatibility (EMC) testing**. Built with Python, OpenCV, PyQt5, and Matplotlib.

Instead of manually observing status LEDs, indicators, or display lights during immunity/emissions tests, this application allows engineers to delegate visual monitoring to a webcam. It tracks ROI (Region of Interest) light levels, alerts on deviations, plots continuous time-series graphs, and exports test telemetry.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-orange)
![License](https://img.shields.io/badge/License-MIT-brightgreen)

---

## 🔑 Key Features

- 🎯 **Interactive ROI Selection:** Select any LED or light source on the camera feed with a simple click-and-drag box.
- ⚙️ **Configurable Tolerance (%):** Set allowable light intensity fluctuation limits dynamically.
- 🚨 **Real-Time Pass/Fail & Audio Alerts:** Visual indicator on screen with an audible beep instantly triggered when light drops below or spikes above threshold.
- 📈 **Continuous Time-Series Plotting:** Full historical light-intensity graph retained from test start to end (no data dropping/rolling frame limits).
- 📊 **CSV Telemetry Export:** Easily export full test data (timestamps, measured intensity, threshold boundaries, and pass/fail status) for reporting and compliance documentation.

---

## 🛠️ Installation & Setup

### Prerequisites
Make sure you have Python 3.8 or higher installed on your system.

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/emc-light-monitor.git](https://github.com/your-username/emc-light-monitor.git)
cd emc-light-monitor

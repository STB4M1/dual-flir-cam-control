import numpy as np
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QCheckBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class HistogramDialog(QDialog):
    def __init__(self, image: np.ndarray, title: str = "Histogram", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(620, 480)

        self.image = image
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.canvas)

        # ==== チェックボックス ====
        checkbox_layout = QHBoxLayout()
        self.cb_gray = QCheckBox("Gray")
        self.cb_r = QCheckBox("R")
        self.cb_g = QCheckBox("G")
        self.cb_b = QCheckBox("B")

        if image.ndim == 2:
            self.cb_gray.setChecked(True)
        else:
            for cb in [self.cb_gray, self.cb_r, self.cb_g, self.cb_b]:
                cb.setChecked(True)

        for cb in [self.cb_gray, self.cb_r, self.cb_g, self.cb_b]:
            checkbox_layout.addWidget(cb)
            cb.stateChanged.connect(self.update_histogram)

        layout.addLayout(checkbox_layout)

        # ==== 統計ラベル ====
        self.label_stats = QLabel()
        self.label_stats.setStyleSheet("font-family: Consolas, monospace;")
        layout.addWidget(self.label_stats)

        # 初期描画
        self.plot_histogram()
        self.update_stats()

    def plot_histogram(self):
        # 🔹 ここで完全にリセット！
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        img = self.image
        if img.ndim == 2:
            if self.cb_gray.isChecked():
                ax.hist(img.ravel(), bins=256, range=(0, 255),
                        color='gray', alpha=0.8, label="Gray")
        elif img.ndim == 3 and img.shape[2] == 3:
            if self.cb_r.isChecked():
                ax.hist(img[:, :, 0].ravel(), bins=256, range=(0, 255),
                        color='red', alpha=0.4, label='R')
            if self.cb_g.isChecked():
                ax.hist(img[:, :, 1].ravel(), bins=256, range=(0, 255),
                        color='green', alpha=0.4, label='G')
            if self.cb_b.isChecked():
                ax.hist(img[:, :, 2].ravel(), bins=256, range=(0, 255),
                        color='blue', alpha=0.4, label='B')
            if self.cb_gray.isChecked():
                gray = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
                ax.hist(gray.ravel(), bins=256, range=(0, 255),
                        color='black', alpha=0.7, label='Gray (Luminance)')

        ax.legend()
        ax.set_xlabel("Pixel Value")
        ax.set_ylabel("Frequency")
        ax.set_title("Selected Histograms")
        self.canvas.draw_idle()  # draw() よりもQtに優しい

    def update_histogram(self):
        self.plot_histogram()
        self.update_stats()

    def update_stats(self):
        img = self.image
        text_lines = []

        def stats_line(label, data):
            data = data.astype(np.float32)
            mean = np.mean(data)
            median = np.median(data)
            max_val = np.max(data)
            min_val = np.min(data)
            mode_val = int(np.bincount(data.astype(np.uint8).ravel()).argmax())
            return (
                f"{label:<7s}: μ={mean:6.2f}  med={median:6.2f}  "
                f"mode={mode_val:3d}  min={min_val:3.0f}  max={max_val:3.0f}"
            )

        if img.ndim == 2:
            if self.cb_gray.isChecked():
                text_lines.append(stats_line("Gray", img))
        elif img.ndim == 3 and img.shape[2] == 3:
            if self.cb_r.isChecked():
                text_lines.append(stats_line("R", img[:, :, 0]))
            if self.cb_g.isChecked():
                text_lines.append(stats_line("G", img[:, :, 1]))
            if self.cb_b.isChecked():
                text_lines.append(stats_line("B", img[:, :, 2]))
            if self.cb_gray.isChecked():
                gray = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
                text_lines.append(stats_line("Gray(L)", gray))

        if text_lines:
            self.label_stats.setText("\n".join(text_lines))
        else:
            self.label_stats.setText("（表示チャンネルなし）")


def show_histogram_window(image_np: np.ndarray, title: str = "Histogram"):
    dialog = HistogramDialog(image_np, title=title)
    dialog.exec()

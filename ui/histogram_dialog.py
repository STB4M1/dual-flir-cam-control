import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QCheckBox
)
import pyqtgraph as pg


class HistogramDialog(QDialog):
    def __init__(self, image: np.ndarray = None, title: str = "Histogram", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(620, 480)

        self.image = image

        layout = QVBoxLayout()
        self.setLayout(layout)

        # ==== Plot Widget ====
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel("bottom", "Pixel Value")
        self.plot_widget.setLabel("left", "Frequency")
        self.plot_widget.addLegend()
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.plot_widget)

        # ==== チェックボックス ====
        checkbox_layout = QHBoxLayout()
        self.cb_gray = QCheckBox("Gray")
        self.cb_r = QCheckBox("R")
        self.cb_g = QCheckBox("G")
        self.cb_b = QCheckBox("B")

        for cb in [self.cb_gray, self.cb_r, self.cb_g, self.cb_b]:
            checkbox_layout.addWidget(cb)
            cb.stateChanged.connect(self.update_histogram)
            cb.setChecked(True)

        layout.addLayout(checkbox_layout)

        # ==== 統計ラベル ====
        self.label_stats = QLabel()
        self.label_stats.setStyleSheet("font-family: Consolas, monospace;")
        layout.addWidget(self.label_stats)

        # ==== カラー設定 ====
        self.colors = {
            "gray": (200, 200, 200),
            "r": (255, 100, 100),
            "g": (100, 255, 100),
            "b": (100, 100, 255),
        }

        # ==== 更新タイマー ====
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # 🔹1秒ごとに更新
        self.timer.timeout.connect(self.refresh_display)
        self.timer.start()

        if self.image is not None:
            self.plot_histogram()
            self.update_stats()

    # 🔹 LiveView から画像を受け取る
    def update_image(self, image: np.ndarray):
        """最新のフレームを保存（描画はタイマーで行う）"""
        self.image = image

    # 🔹 定期的に更新
    def refresh_display(self):
        if self.image is not None:
            self.plot_histogram()
            self.update_stats()

    # 🔹 ヒストグラム描画
    def plot_histogram(self):
        if self.image is None:
            return

        img = self.image
        self.plot_widget.clear()

        # ==== グレースケール画像 ====
        if img.ndim == 2:
            if self.cb_gray.isChecked():
                hist, bins = np.histogram(img, bins=256, range=(0, 255))
                self.plot_widget.plot(
                    bins[:-1], hist, pen=pg.mkPen(self.colors["gray"], width=2), name="Gray"
                )

        # ==== カラー画像 ====
        elif img.ndim == 3 and img.shape[2] == 3:
            if self.cb_r.isChecked():
                hist, bins = np.histogram(img[:, :, 0], bins=256, range=(0, 255))
                self.plot_widget.plot(
                    bins[:-1], hist, pen=pg.mkPen(self.colors["r"], width=2), name="R"
                )
            if self.cb_g.isChecked():
                hist, bins = np.histogram(img[:, :, 1], bins=256, range=(0, 255))
                self.plot_widget.plot(
                    bins[:-1], hist, pen=pg.mkPen(self.colors["g"], width=2), name="G"
                )
            if self.cb_b.isChecked():
                hist, bins = np.histogram(img[:, :, 2], bins=256, range=(0, 255))
                self.plot_widget.plot(
                    bins[:-1], hist, pen=pg.mkPen(self.colors["b"], width=2), name="B"
                )
            if self.cb_gray.isChecked():
                gray = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
                hist, bins = np.histogram(gray, bins=256, range=(0, 255))
                self.plot_widget.plot(
                    bins[:-1], hist, pen=pg.mkPen(self.colors["gray"], width=2), name="Gray (L)"
                )

    # 🔹 チェックボックス変更時
    def update_histogram(self):
        self.plot_histogram()
        self.update_stats()

    # 🔹 統計情報の更新
    def update_stats(self):
        if self.image is None:
            self.label_stats.setText("（画像なし）")
            return

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

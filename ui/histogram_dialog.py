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
        self.setMinimumSize(640, 500)

        self.image = image

        # ======== メインレイアウト ========
        layout = QVBoxLayout()
        self.setLayout(layout)

        # ======== PlotWidget ========
        self.plot_widget = pg.PlotWidget()
        self.apply_matplotlib_style(self.plot_widget)
        layout.addWidget(self.plot_widget)

        # ======== チェックボックス ========
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

        # ======== 統計ラベル ========
        self.label_stats = QLabel()
        self.label_stats.setStyleSheet("font-family: Consolas, monospace; color: #222;")
        layout.addWidget(self.label_stats)

        # ======== カラー設定 ========
        # RGBA形式 (最後の数値は透明度)
        self.colors = {
            "gray": (80, 80, 80, 100),
            "r": (220, 70, 70, 80),
            "g": (70, 180, 70, 80),
            "b": (70, 70, 220, 80),
        }

        # ======== タイマー（1秒ごとに更新） ========
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh_display)
        self.timer.start()

        if self.image is not None:
            self.plot_histogram()
            self.update_stats()

    # ======== Matplotlib風スタイル適用 ========
    def apply_matplotlib_style(self, plot_widget: pg.PlotWidget):
        pg.setConfigOptions(antialias=True)
        plot_widget.setBackground("w")
        plot_widget.showGrid(x=True, y=True, alpha=0.25)
        plot_widget.setLabel("bottom", "Pixel Value", color="#000000", size="13pt")
        plot_widget.setLabel("left", "Frequency", color="#000000", size="13pt")
        for axis in ["bottom", "left"]:
            ax = plot_widget.getAxis(axis)
            ax.setGrid(255)  # 255: デフォルトの色に戻す（内部的にグリッド描画に影響）
            ax.setTextPen(pg.mkPen(color=(0, 0, 0), width=1))
            ax.setTickFont(pg.QtGui.QFont("Arial", 9))

        vb = plot_widget.getPlotItem().getViewBox()
        vb.setBorder(pg.mkPen(color=(0, 0, 0), width=2))

        plot_widget.addLegend(labelTextColor="#000000")

    # ======== LiveView から画像更新 ========
    def update_image(self, image: np.ndarray):
        """最新フレームを保存（描画はタイマーで行う）"""
        self.image = image

    # ======== タイマーで更新 ========
    def refresh_display(self):
        if self.image is not None:
            self.plot_histogram()
            self.update_stats()

    # ======== ヒストグラム描画 ========
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
                    bins[:-1],
                    hist,
                    pen=pg.mkPen(self.colors["gray"][:3], width=1.5),
                    brush=pg.mkBrush(self.colors["gray"]),
                    fillLevel=0,
                    name="Gray",
                )

        # ==== カラー画像 ====
        elif img.ndim == 3 and img.shape[2] == 3:
            if self.cb_r.isChecked():
                hist, bins = np.histogram(img[:, :, 0], bins=256, range=(0, 255))
                self.plot_widget.plot(
                    bins[:-1],
                    hist,
                    pen=pg.mkPen(self.colors["r"][:3], width=1.5),
                    brush=pg.mkBrush(self.colors["r"]),
                    fillLevel=0,
                    name="R",
                )
            if self.cb_g.isChecked():
                hist, bins = np.histogram(img[:, :, 1], bins=256, range=(0, 255))
                self.plot_widget.plot(
                    bins[:-1],
                    hist,
                    pen=pg.mkPen(self.colors["g"][:3], width=1.5),
                    brush=pg.mkBrush(self.colors["g"]),
                    fillLevel=0,
                    name="G",
                )
            if self.cb_b.isChecked():
                hist, bins = np.histogram(img[:, :, 2], bins=256, range=(0, 255))
                self.plot_widget.plot(
                    bins[:-1],
                    hist,
                    pen=pg.mkPen(self.colors["b"][:3], width=1.5),
                    brush=pg.mkBrush(self.colors["b"]),
                    fillLevel=0,
                    name="B",
                )
            if self.cb_gray.isChecked():
                gray = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
                hist, bins = np.histogram(gray, bins=256, range=(0, 255))
                self.plot_widget.plot(
                    bins[:-1],
                    hist,
                    pen=pg.mkPen(self.colors["gray"][:3], width=1.5),
                    brush=pg.mkBrush(self.colors["gray"]),
                    fillLevel=0,
                    name="Gray (L)",
                )

    # ======== チェックボックス変更時 ========
    def update_histogram(self):
        self.plot_histogram()
        self.update_stats()

    # ======== 統計更新 ========
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


# ======== 外部呼び出し用関数 ========
def show_histogram_window(image_np: np.ndarray, title: str = "Histogram"):
    dialog = HistogramDialog(image_np, title=title)
    dialog.exec()

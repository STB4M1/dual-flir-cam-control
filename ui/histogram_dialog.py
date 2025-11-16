import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox
import pyqtgraph as pg


# ============================================================
# 🔍 PixelFormat → Bayerパターン自動判定
# ============================================================
def detect_bayer_pattern(pixel_format: str):
    if pixel_format is None:
        return None
    if not pixel_format.startswith("Bayer"):
        return None

    pf = pixel_format[5:7].upper()  # RG / GR / GB / BG

    mapping = {
        "RG": "RGGB",
        "GR": "GRBG",
        "GB": "GBRG",
        "BG": "BGGR",
    }
    return mapping.get(pf, None)


# 🔍 PixelFormat → ビット深度
def detect_bit_depth(pixel_format: str):
    if pixel_format is None:
        return 8

    import re
    m = re.search(r"(\d+)", pixel_format)
    if m:
        return int(m.group(1))
    return 8


# ============================================================
# 🔧 Bayer → R/G/B 抽出（どのフォーマットでもOK）
# ============================================================
def extract_bayer_channels(raw, pattern):
    H, W = raw.shape
    raw = raw.astype(np.float32)

    if pattern == "RGGB":
        R = raw[0::2, 0::2]
        G1 = raw[0::2, 1::2]
        G2 = raw[1::2, 0::2]
        B = raw[1::2, 1::2]

    elif pattern == "GRBG":
        G1 = raw[0::2, 0::2]
        R = raw[0::2, 1::2]
        B = raw[1::2, 0::2]
        G2 = raw[1::2, 1::2]

    elif pattern == "GBRG":
        G1 = raw[0::2, 0::2]
        B = raw[0::2, 1::2]
        R = raw[1::2, 0::2]
        G2 = raw[1::2, 1::2]

    elif pattern == "BGGR":
        B = raw[0::2, 0::2]
        G1 = raw[0::2, 1::2]
        G2 = raw[1::2, 0::2]
        R = raw[1::2, 1::2]

    else:
        return None

    G = (G1 + G2) / 2.0
    return R, G, B


# ============================================================
# 🎨 Histogram Dialog（フル機能版）
# ============================================================
class HistogramDialog(QDialog):
    def __init__(self, image: np.ndarray = None, title: str = "Histogram",
                 parent=None, pixel_format=None):

        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(640, 500)

        self.image = image
        self.pixel_format = pixel_format
        self.bayer_pattern = detect_bayer_pattern(pixel_format)
        self.bit_depth = detect_bit_depth(pixel_format)
        self.log_scale = False

        # ======== メインレイアウト ========
        layout = QVBoxLayout()
        self.setLayout(layout)

        # ======== PlotWidget ========
        self.plot_widget = pg.PlotWidget()
        self.apply_matplotlib_style(self.plot_widget)
        layout.addWidget(self.plot_widget)

        # ======== チェックボックス群 ========
        checkbox_layout = QHBoxLayout()
        self.cb_gray = QCheckBox("Gray")
        self.cb_r = QCheckBox("R")
        self.cb_g = QCheckBox("G")
        self.cb_b = QCheckBox("B")
        self.cb_log = QCheckBox("Log表示（Y軸）")

        for cb in [self.cb_gray, self.cb_r, self.cb_g, self.cb_b]:
            checkbox_layout.addWidget(cb)
            cb.stateChanged.connect(self.update_histogram)
            cb.setChecked(True)

        self.cb_log.stateChanged.connect(self.toggle_log_scale)
        checkbox_layout.addWidget(self.cb_log)
        layout.addLayout(checkbox_layout)

        # ======== 統計ラベル ========
        self.label_stats = QLabel()
        self.label_stats.setStyleSheet("font-family: Consolas, monospace; color: #222;")
        layout.addWidget(self.label_stats)

        # ======== カラー設定 ========
        self.colors = {
            "gray": (80, 80, 80, 100),
            "r": (220, 70, 70, 80),
            "g": (70, 180, 70, 80),
            "b": (70, 70, 220, 80),
        }

        # ======== タイマー（1秒ごと） ========
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh_display)
        self.timer.start()

        if self.image is not None:
            self.plot_histogram()
            self.update_stats()

    # ======== Matplotlib風スタイル ========
    def apply_matplotlib_style(self, plot_widget):
        pg.setConfigOptions(antialias=True)
        plot_widget.setBackground("w")
        plot_widget.showGrid(x=True, y=True, alpha=0.25)
        plot_widget.setLabel("bottom", "Pixel Value", color="#000000", size="13pt")
        plot_widget.setLabel("left", "Frequency", color="#000000", size="13pt")

        for axis in ["bottom", "left"]:
            ax = plot_widget.getAxis(axis)
            ax.setTextPen(pg.mkPen(color=(0, 0, 0), width=1))
            ax.setTickFont(pg.QtGui.QFont("Arial", 9))

        vb = plot_widget.getPlotItem().getViewBox()
        vb.setBorder(pg.mkPen(color=(0, 0, 0), width=2))
        plot_widget.addLegend(labelTextColor="#000000")

    # ======== LiveView更新 ========
    def update_image(self, image: np.ndarray):
        self.image = image

    def refresh_display(self):
        if self.image is not None:
            self.plot_histogram()
            self.update_stats()

    def toggle_log_scale(self):
        self.log_scale = self.cb_log.isChecked()
        self.plot_histogram()

    # ======== RAW値 → 8bitに正規化 ========
    def normalize_to_8bit(self, img):
        if self.bit_depth <= 8:
            return img.astype(np.uint8)

        maxval = float((1 << self.bit_depth) - 1)
        img = (img.astype(np.float32) / maxval) * 255.0
        return img.clip(0, 255).astype(np.uint8)

    # ======== ヒストグラム描画 ========
    def plot_histogram(self):
        if self.image is None:
            return

        img = self.image

        self.plot_widget.clear()
        self.plot_widget.setLogMode(False, self.log_scale)

        def safe_hist(data):
            hist, bins = np.histogram(data, bins=256, range=(0, 255))
            if self.log_scale:
                hist = np.clip(hist, 1, None)
            return hist, bins

        # ========================================================
        # ▶ RAW Bayer の場合
        # ========================================================
        if self.bayer_pattern is not None and img.ndim == 2:

            raw8 = self.normalize_to_8bit(img)
            R, G, B = extract_bayer_channels(raw8, self.bayer_pattern)

            if self.cb_r.isChecked():
                hist, bins = safe_hist(R)
                self.plot_widget.plot(bins[:-1], hist,
                                      pen=pg.mkPen(self.colors["r"][:3], width=1.5),
                                      brush=pg.mkBrush(self.colors["r"]),
                                      fillLevel=0, name="R")

            if self.cb_g.isChecked():
                hist, bins = safe_hist(G)
                self.plot_widget.plot(bins[:-1], hist,
                                      pen=pg.mkPen(self.colors["g"][:3], width=1.5),
                                      brush=pg.mkBrush(self.colors["g"]),
                                      fillLevel=0, name="G")

            if self.cb_b.isChecked():
                hist, bins = safe_hist(B)
                self.plot_widget.plot(bins[:-1], hist,
                                      pen=pg.mkPen(self.colors["b"][:3], width=1.5),
                                      brush=pg.mkBrush(self.colors["b"]),
                                      fillLevel=0, name="B")

            if self.cb_gray.isChecked():
                gray = 0.299 * R + 0.587 * G + 0.114 * B
                hist, bins = safe_hist(gray)
                self.plot_widget.plot(bins[:-1], hist,
                                      pen=pg.mkPen(self.colors["gray"][:3], width=1.5),
                                      brush=pg.mkBrush(self.colors["gray"]),
                                      fillLevel=0, name="Gray(L)")

            return

        # ========================================================
        # ▶ Mono（元のコード）
        # ========================================================
        if img.ndim == 2:
            if self.cb_gray.isChecked():
                hist, bins = safe_hist(img)
                self.plot_widget.plot(
                    bins[:-1], hist,
                    pen=pg.mkPen(self.colors["gray"][:3], width=1.5),
                    brush=pg.mkBrush(self.colors["gray"]),
                    fillLevel=0, name="Gray"
                )
            return

        # ========================================================
        # ▶ RGB / BGR（元のコード）
        # ========================================================
        if img.ndim == 3 and img.shape[2] == 3:

            if self.cb_r.isChecked():
                hist, bins = safe_hist(img[:, :, 2])
                self.plot_widget.plot(bins[:-1], hist,
                                      pen=pg.mkPen(self.colors["r"][:3], width=1.5),
                                      brush=pg.mkBrush(self.colors["r"]),
                                      fillLevel=0, name="R")

            if self.cb_g.isChecked():
                hist, bins = safe_hist(img[:, :, 1])
                self.plot_widget.plot(bins[:-1], hist,
                                      pen=pg.mkPen(self.colors["g"][:3], width=1.5),
                                      brush=pg.mkBrush(self.colors["g"]),
                                      fillLevel=0, name="G")

            if self.cb_b.isChecked():
                hist, bins = safe_hist(img[:, :, 0])
                self.plot_widget.plot(bins[:-1], hist,
                                      pen=pg.mkPen(self.colors["b"][:3], width=1.5),
                                      brush=pg.mkBrush(self.colors["b"]),
                                      fillLevel=0, name="B")

            if self.cb_gray.isChecked():
                gray = 0.299 * img[:, :, 2] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 0]
                hist, bins = safe_hist(gray)
                self.plot_widget.plot(bins[:-1], hist,
                                      pen=pg.mkPen(self.colors["gray"][:3], width=1.5),
                                      brush=pg.mkBrush(self.colors["gray"]),
                                      fillLevel=0, name="Gray(L)")

    # ======== 統計表示（元のまま） ========
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
            return f"{label:<7s}: μ={mean:6.2f}  med={median:6.2f}  mode={mode_val:3d}  min={min_val:3.0f}  max={max_val:3.0f}"

        # RAW Bayer の場合
        if self.bayer_pattern is not None and img.ndim == 2:
            raw8 = self.normalize_to_8bit(img)
            R, G, B = extract_bayer_channels(raw8, self.bayer_pattern)

            if self.cb_r.isChecked():
                text_lines.append(stats_line("R", R))
            if self.cb_g.isChecked():
                text_lines.append(stats_line("G", G))
            if self.cb_b.isChecked():
                text_lines.append(stats_line("B", B))
            if self.cb_gray.isChecked():
                gray = 0.299 * R + 0.587 * G + 0.114 * B
                text_lines.append(stats_line("Gray", gray))

        # Mono
        elif img.ndim == 2:
            if self.cb_gray.isChecked():
                text_lines.append(stats_line("Gray", img))

        # RGB/BGR
        elif img.ndim == 3 and img.shape[2] == 3:
            if self.cb_r.isChecked():
                text_lines.append(stats_line("R", img[:, :, 2]))
            if self.cb_g.isChecked():
                text_lines.append(stats_line("G", img[:, :, 1]))
            if self.cb_b.isChecked():
                text_lines.append(stats_line("B", img[:, :, 0]))
            if self.cb_gray.isChecked():
                gray = 0.299 * img[:, :, 2] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 0]
                text_lines.append(stats_line("Gray", gray))

        if text_lines:
            self.label_stats.setText("\n".join(text_lines))
        else:
            self.label_stats.setText("（表示チャンネルなし）")

    def update_histogram(self):
        self.plot_histogram()
        self.update_stats()

# ============================================================
# 外から呼び出す関数
# ============================================================
def show_histogram_window(image_np: np.ndarray, title: str = "Histogram", pixel_format=None):
    dialog = HistogramDialog(image_np, title=title, pixel_format=pixel_format)
    dialog.exec()

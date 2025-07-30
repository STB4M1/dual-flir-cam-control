
import numpy as np
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class HistogramDialog(QDialog):
    def __init__(self, image: np.ndarray, title: str = "Histogram", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # ヒストグラム描画領域
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.canvas)

        # 統計表示
        self.label_stats = QLabel()
        layout.addWidget(self.label_stats)

        self.plot_histogram(image)
        self.update_stats(image)

    def plot_histogram(self, image: np.ndarray):
        ax = self.figure.add_subplot(111)
        ax.clear()
        ax.hist(image.ravel(), bins=256, range=(0, 255), color='gray', alpha=0.75)
        ax.set_title("Histogram")
        ax.set_xlabel("Pixel Value")
        ax.set_ylabel("Frequency")
        self.canvas.draw()

    def update_stats(self, image: np.ndarray):
        mean = np.mean(image)
        max_val = np.max(image)
        min_val = np.min(image)
        mode_val = int(np.bincount(image.ravel()).argmax())

        stats_text = f"平均: {mean:.2f}    最頻値: {mode_val}    最小: {min_val}    最大: {max_val}"
        self.label_stats.setText(stats_text)


def show_histogram_window(image_np: np.ndarray, title: str = "Histogram"):
    dialog = HistogramDialog(image_np, title=title)
    dialog.exec()

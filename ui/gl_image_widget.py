from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QPainter, QPixmap, QPaintEvent
from PySide6.QtCore import Qt

class ImageGLWidget(QOpenGLWidget):
    """
    QPixmap を受け取って OpenGL 上に描画するカスタムWidget
    Qt Designer で QOpenGLWidget を配置し、
    promote してこのクラスを割り当てることで使える。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None

    def setPixmap(self, pixmap: QPixmap):
        self.pixmap = pixmap
        self.update()

    def paintEvent(self, event: QPaintEvent):
        if self.pixmap:
            painter = QPainter(self)
            painter.fillRect(self.rect(), Qt.black)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            # ウィジェットサイズ
            widget_rect = self.rect()

            # pixmap のアスペクト比を保ったまま fit させたサイズを計算
            scaled_pixmap = self.pixmap.scaled(
                widget_rect.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            # 中央に配置する位置を計算
            x = (widget_rect.width() - scaled_pixmap.width()) // 2
            y = (widget_rect.height() - scaled_pixmap.height()) // 2

            painter.drawPixmap(x, y, scaled_pixmap)

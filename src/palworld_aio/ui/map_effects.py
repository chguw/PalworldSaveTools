import math
import random
from PySide6.QtWidgets import QGraphicsObject
from PySide6.QtCore import Qt, QRectF, QPointF, Property
from PySide6.QtGui import QPainter, QPen, QColor, QRadialGradient
class EffectItem(QGraphicsObject):
    def __init__(self, x, y, duration=1000):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.duration = duration
        self._progress = 0.0
        self.setPos(x, y)
    @Property(float)
    def progress(self):
        return self._progress
    @progress.setter
    def progress(self, value):
        self._progress = value
        self.update()
    def boundingRect(self):
        return QRectF(-200, -200, 400, 400)
class DeleteEffect(EffectItem):
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        radius = self._progress * 150
        alpha = int(255 * (1 - self._progress))
        painter.setPen(QPen(QColor(255, 80, 80, alpha), 5))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), radius, radius)
        if radius > 30:
            painter.setPen(QPen(QColor(255, 150, 0, alpha), 3))
            painter.drawEllipse(QPointF(0, 0), radius - 30, radius - 30)
        if self._progress < 0.3:
            flash_alpha = int(200 * (1 - self._progress / 0.3))
            painter.setBrush(QColor(255, 200, 0, flash_alpha))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(0, 0), 40, 40)
class ImportEffect(EffectItem):
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        for i in range(3):
            phase = (self._progress + i * 0.33) % 1.0
            radius = phase * 100
            alpha = int(180 * (1 - phase))
            painter.setPen(QPen(QColor(0, 255, 150, alpha), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(0, 0), radius, radius)
        if self._progress < 0.7:
            painter.setBrush(QColor(100, 255, 200, int(255 * (1 - self._progress))))
            painter.setPen(Qt.NoPen)
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                dist = 60 + self._progress * 40
                x = math.cos(rad) * dist
                y = math.sin(rad) * dist
                size = 8 - self._progress * 6
                painter.drawEllipse(QPointF(x, y), size, size)
class ExportEffect(EffectItem):
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        beam_height = self._progress * 200
        alpha = int(200 * (1 - self._progress))
        gradient = QRadialGradient(0, -beam_height / 2, 30)
        gradient.setColorAt(0, QColor(100, 200, 255, alpha))
        gradient.setColorAt(1, QColor(100, 200, 255, 0))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRect(QRectF(-20, -beam_height, 40, beam_height))
        for i in range(5):
            particle_y = -(i * 40 + self._progress * 150) % 200
            particle_alpha = int(alpha * (1 - abs(particle_y) / 200))
            painter.setBrush(QColor(150, 220, 255, particle_alpha))
            painter.drawEllipse(QPointF(random.randint(-15, 15), particle_y), 4, 4)
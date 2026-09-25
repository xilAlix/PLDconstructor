import math

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QGraphicsView
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPointF, QLineF
from PyQt6.QtGui import QWheelEvent

class PcbGraphicsView(QGraphicsView):
    """Кастомный QGraphicsView для перехвата событий мыши (включая колесико)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom_callback = None
        self.setMouseTracking(True)

    def set_zoom_callback(self, callback):
        """Регистрирует внешнюю функцию изменения зума."""
        self.zoom_callback = callback

    def wheelEvent(self, event: QWheelEvent):
        """Перехват прокрутки колесика мыши для шагового изменения зума."""
        if self.zoom_callback:
            # delta() > 0 означает увеличение
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_callback(step=1)
            elif delta < 0:
                self.zoom_callback(step=-1)
            event.accept()
        else:
            super().wheelEvent(event)


class PcbGraphicsScene(QGraphicsScene):
    """Графическая сцена для PCB с отрисовкой сетки и отслеживанием координат."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.grid_size: float = 1.27
        self.grid_color: QColor = QColor(150, 150, 150, 51)
        self.axis_color: QColor = QColor(0, 120, 255, 220)
        self.cursor_pen: QPen = QPen(QColor(220, 220, 220, 200), 0)

        self.setSceneRect(-250, -250, 500, 500)

        self.mouse_move_callback = None
        self.snapped_pos: QPointF = QPointF(0.0, 0.0)

    def set_grid_size(self, size_mm: float):
        """Обновляет шаг сетки и перерисовывает сцену."""
        self.grid_size = size_mm
        self.update()

    def set_mouse_move_callback(self, callback):
        """Регистрирует функцию для передачи координат в статус-бар."""
        self.mouse_move_callback = callback

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """Перехват движения мыши и привязка к узлам сетки."""
        super().mouseMoveEvent(event)
        raw_pos = event.scenePos()

        if self.grid_size > 0:
            snapped_x = round(raw_pos.x() / self.grid_size) * self.grid_size
            snapped_y = round(raw_pos.y() / self.grid_size) * self.grid_size
        else:
            snapped_x, snapped_y = raw_pos.x(), raw_pos.y()
        self.snapped_pos = QPointF(snapped_x, snapped_y)

        if self.mouse_move_callback:
            self.mouse_move_callback(snapped_x, -snapped_y)
        self.update()

    def drawBackground(self, painter: QPainter, rect):
        """Отрисовка полупрозрачной сетки линиями и глобальных осей (0,0)."""
        super().drawBackground(painter, rect)

        if self.grid_size <= 0:
            return

        # Отрисовка основной фоновой сетки
        grid_pen = QPen(self.grid_color, 0)
        painter.setPen(grid_pen)

        first_col = math.floor(rect.left() / self.grid_size)
        last_col = math.ceil(rect.right() / self.grid_size)
        first_row = math.floor(rect.top() / self.grid_size)
        last_row = math.ceil(rect.bottom() / self.grid_size)

        for col in range(first_col, last_col + 1):
            x = col * self.grid_size
            painter.drawLine(QLineF(x, rect.top(), x, rect.bottom()))

        for row in range(first_row, last_row + 1):
            y = row * self.grid_size
            painter.drawLine(QLineF(rect.left(), y, rect.right(), y))

        # Отрисовка центральных осей X/Y в точке (0, 0)
        axis_pen = QPen(self.axis_color, 0)  # Косметическая линия
        painter.setPen(axis_pen)

        if rect.top() <= 0 <= rect.bottom():
            painter.drawLine(QLineF(rect.left(), 0, rect.right(), 0))

        if rect.left() <= 0 <= rect.right():
            painter.drawLine(QLineF(0, rect.top(), 0, rect.bottom()))

    def drawForeground(self, painter: QPainter, rect):
        """Отрисовка светлого перекрестия KiCad поверх всех элементов."""
        super().drawForeground(painter, rect)

        painter.setPen(self.cursor_pen)
        cross_size = max(0.5, self.grid_size * 0.8)

        x = self.snapped_pos.x()
        y = self.snapped_pos.y()

        painter.drawLine(QLineF(x - cross_size, y, x + cross_size, y))
        painter.drawLine(QLineF(x, y - cross_size, x, y + cross_size))
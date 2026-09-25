import math

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QGraphicsView
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPointF, QLineF
from PyQt6.QtGui import QWheelEvent

from general.grid import PcbGrid

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

        self.grid = PcbGrid(grid_size=1.27)
        self.cursor_pen: QPen = QPen(QColor(220, 220, 220, 200), 0)

        self.setSceneRect(-250, -250, 500, 500)

        self.mouse_move_callback = None
        self.selection_changed_callback = None
        self.snapped_pos: QPointF = QPointF(0.0, 0.0)

        self.selectionChanged.connect(self._on_selection_changed)

    def set_grid_size(self, size_mm: float):
        """Обновляет шаг сетки и перерисовывает сцену."""
        self.grid.set_grid_size(size_mm)
        self.update()

    def set_mouse_move_callback(self, callback):
        """Регистрирует функцию для передачи координат в статус-бар."""
        self.mouse_move_callback = callback

    def set_selection_changed_callback(self, callback):
        """Регистрирует функцию передачи выбранных элементов в панель свойств."""
        self.selection_changed_callback = callback

    def _on_selection_changed(self):
        """Срабатывает при выделении/снятии выделения объектов."""
        if self.selection_changed_callback:
            selected_items = self.selectedItems()
            self.selection_changed_callback(selected_items)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """Перехват движения мыши и привязка к узлам сетки."""
        super().mouseMoveEvent(event)
        raw_pos = event.scenePos()

        self.snapped_pos = self.grid.get_snapped_point(raw_pos)

        if self.mouse_move_callback:
            self.mouse_move_callback(self.snapped_pos.x(), -self.snapped_pos.y())
        self.update()

    def drawBackground(self, painter: QPainter, rect):
        """Отрисовка сетки."""
        super().drawBackground(painter, rect)

        current_zoom = painter.transform().m11()
        self.grid.draw(painter, rect, current_zoom)

    def drawForeground(self, painter: QPainter, rect):
        """Отрисовка светлого перекрестия поверх всех элементов."""
        super().drawForeground(painter, rect)

        painter.setPen(self.cursor_pen)
        cross_size = self.grid.grid_size * 0.8

        x = self.snapped_pos.x()
        y = self.snapped_pos.y()

        painter.drawLine(QLineF(x - cross_size, y, x + cross_size, y))
        painter.drawLine(QLineF(x, y - cross_size, x, y + cross_size))
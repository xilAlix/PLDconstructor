import math
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import QPointF, QLineF


class PcbGrid:
    """Модуль отрисовки адаптивной сетки и привязки координат."""

    def __init__(self, grid_size: float = 1.27):
        self.grid_size: float = grid_size

        self.base_grid_color: QColor = QColor(100, 100, 100, 40)
        self.major_grid_color: QColor = QColor(160, 160, 160, 80)
        self.axis_color: QColor = QColor(0, 120, 255, 200)

        self.major_step_multiplier: int = 5

    def set_grid_size(self, size_mm: float):
        """Обновляет базовый шаг сетки."""
        self.grid_size = size_mm

    def get_snapped_point(self, raw_pos: QPointF) -> QPointF:
        """Привязывает сырые координаты к текущему шагу сетки."""
        if self.grid_size <= 0:
            return raw_pos

        snapped_x = round(raw_pos.x() / self.grid_size) * self.grid_size
        snapped_y = round(raw_pos.y() / self.grid_size) * self.grid_size
        return QPointF(snapped_x, snapped_y)

    def draw(self, painter: QPainter, rect, current_zoom: float = 1.0):
        """Отрисовка адаптивной оптимизированной сетки."""
        if self.grid_size <= 0:
            return

        visual_step = self.grid_size
        pixel_step = visual_step * current_zoom

        multiplier = 1
        while pixel_step < 4.0:
            multiplier *= 2
            visual_step = self.grid_size * multiplier
            pixel_step = visual_step * current_zoom

        first_col = math.floor(rect.left() / visual_step)
        last_col = math.ceil(rect.right() / visual_step)
        first_row = math.floor(rect.top() / visual_step)
        last_row = math.ceil(rect.bottom() / visual_step)

        minor_lines = []
        major_lines = []

        for col in range(first_col, last_col + 1):
            x = col * visual_step
            line = QLineF(x, rect.top(), x, rect.bottom())

            if col % self.major_step_multiplier == 0:
                major_lines.append(line)
            else:
                minor_lines.append(line)

        for row in range(first_row, last_row + 1):
            y = row * visual_step
            line = QLineF(rect.left(), y, rect.right(), y)

            if row % self.major_step_multiplier == 0:
                major_lines.append(line)
            else:
                minor_lines.append(line)

        if minor_lines:
            painter.setPen(QPen(self.base_grid_color, 0))
            painter.drawLines(minor_lines)

        if major_lines:
            painter.setPen(QPen(self.major_grid_color, 0))
            painter.drawLines(major_lines)

        painter.setPen(QPen(self.axis_color, 0))
        if rect.top() <= 0 <= rect.bottom():
            painter.drawLine(QLineF(rect.left(), 0, rect.right(), 0))
        if rect.left() <= 0 <= rect.right():
            painter.drawLine(QLineF(0, rect.top(), 0, rect.bottom()))
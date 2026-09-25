import math

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QGraphicsView, QGraphicsItem, QMenu
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QWheelEvent, QAction
from PyQt6.QtCore import Qt, QPointF, QLineF, pyqtSignal, QRectF

from general.grid import PcbGrid

class PcbPinItem(QGraphicsItem):
    """Графический элемент Контакта (Pin/Pad) платы."""

    def __init__(self, pin_number="1", x=0.0, y=0.0, parent=None):
        super().__init__(parent)
        self.pin_number = str(pin_number)
        self.width = 2.0
        self.height = 2.0
        self.pin_type = "THT (Сквозной)"

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setPos(x, y)

    def boundingRect(self) -> QRectF:
        """Габариты элемента для кликов и перерисовки."""
        w, h = self.width, self.height
        return QRectF(-w / 2, -h / 2, w, h)

    def paint(self, painter: QPainter, option, widget=None):
        """Отрисовка контакта."""
        rect = self.boundingRect()

        if self.isSelected():
            pen = QPen(QColor(0, 191, 255), 0.3)
            brush = QBrush(QColor(0, 191, 255, 130))
        else:
            pen = QPen(QColor(180, 40, 40), 0.2)
            brush = QBrush(QColor(200, 50, 50, 220))

        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRect(rect)

        painter.setPen(QPen(QColor(255, 255, 255), 0.2))
        font = painter.font()
        font.setPointSizeF(1.2)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.pin_number)

    def itemChange(self, change, value):
        """Автоматическая привязка координат к сетке при перемещении мышью."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value
            grid_size = self.scene().grid.grid_size
            snapped_x = round(new_pos.x() / grid_size) * grid_size
            snapped_y = round(new_pos.y() / grid_size) * grid_size
            return QPointF(snapped_x, snapped_y)
        return super().itemChange(change, value)


class PcbGraphicsView(QGraphicsView):
    """Кастомный QGraphicsView для перехвата событий мыши."""

    zoom_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        self._selection_start_pt = QPointF()
        self._is_selecting = False

    def wheelEvent(self, event: QWheelEvent):
        """Перехват прокрутки колесика мыши."""
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_changed.emit(1)
        elif delta < 0:
            self.zoom_changed.emit(-1)
        event.accept()

    def mousePressEvent(self, event):
        """Фиксация точки старта рамки выделения."""
        if event.button() == Qt.MouseButton.LeftButton and self.scene():
            if self.scene().active_tool == "select":
                self._is_selecting = True
                self._selection_start_pt = event.position()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Переключение логики выделения в зависимости от направления рамки."""
        if self._is_selecting and event.button() == Qt.MouseButton.LeftButton:
            self._is_selecting = False
            end_pt = event.position()

            # Рисуется рамка:
            if (end_pt - self._selection_start_pt).manhattanLength() > 6:
                is_left_to_right = end_pt.x() > self._selection_start_pt.x()

                if is_left_to_right:
                    # Слева направо: Только элементы целиком внутри
                    self.setRubberBandSelectionMode(Qt.ItemSelectionMode.ContainsItemBoundingRect)
                else:
                    # Справа налево: Любые пересечения
                    self.setRubberBandSelectionMode(Qt.ItemSelectionMode.IntersectsItemBoundingRect)

        super().mouseReleaseEvent(event)


class PcbGraphicsScene(QGraphicsScene):
    """Графическая сцена для PCB с отрисовкой сетки и отслеживанием координат."""

    mouse_moved = pyqtSignal(float, float)
    items_selected = pyqtSignal(list)
    pin_placed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.grid = PcbGrid(grid_size=1.27)
        self.cursor_pen: QPen = QPen(QColor(220, 220, 220, 200), 0)
        self.setSceneRect(-250, -250, 500, 500)

        self.snapped_pos: QPointF = QPointF(0.0, 0.0)
        self.active_tool = "select"
        self.select_mode = "cycle"

        self.next_pin_number = 1
        self._cycle_index = 0
        self._last_click_pos = QPointF(-9999, -9999)

        self.selectionChanged.connect(self._on_selection_changed)

    def set_active_tool(self, tool_name: str):
        self.active_tool = tool_name

    def set_select_mode(self, mode_name: str):
        self.select_mode = mode_name

    def set_grid_size(self, size_mm: float):
        self.grid.set_grid_size(size_mm)
        self.update()

    def _on_selection_changed(self):
        """Испускает сигнал при смене выделения."""
        self.items_selected.emit(self.selectedItems())

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Инструмент «Контакт платы»
            if self.active_tool == "pin":
                pos = self.snapped_pos
                pin = PcbPinItem(pin_number=str(self.next_pin_number), x=pos.x(), y=pos.y())
                self.addItem(pin)
                self.next_pin_number += 1
                self.pin_placed.emit()
                return

            # Инструмент «Курсор/Выделение»
            elif self.active_tool == "select":
                items_under = [it for it in self.items(event.scenePos()) if isinstance(it, PcbPinItem)]

                if len(items_under) > 1:
                    if self.select_mode == "list":
                        # Показ контекстного меню со списком
                        menu = QMenu()
                        for item in items_under:
                            act = menu.addAction(f"Контакт №{item.pin_number}")
                            act.setData(item)

                        chosen_action = menu.exec(event.screenPos())
                        if chosen_action:
                            self.clearSelection()
                            chosen_item = chosen_action.data()
                            chosen_item.setSelected(True)
                        return

                    elif self.select_mode == "cycle":
                        # Циклический перебор при повторных кликах в одну точку
                        dist = (event.scenePos() - self._last_click_pos).manhattanLength()
                        if dist < 0.8:
                            self._cycle_index = (self._cycle_index + 1) % len(items_under)
                        else:
                            self._cycle_index = 0

                        self._last_click_pos = event.scenePos()
                        self.clearSelection()
                        items_under[self._cycle_index].setSelected(True)
                        return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        super().mouseMoveEvent(event)
        raw_pos = event.scenePos()

        self.snapped_pos = self.grid.get_snapped_point(raw_pos)
        self.mouse_moved.emit(self.snapped_pos.x(), -self.snapped_pos.y())
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

        x, y = self.snapped_pos.x(), self.snapped_pos.y()
        painter.drawLine(QLineF(x - cross_size, y, x + cross_size, y))
        painter.drawLine(QLineF(x, y - cross_size, x, y + cross_size))
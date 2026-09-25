from PyQt6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import QRectF, QPointF


class PcbBaseItem(QGraphicsItem):
    """Базовый класс для всех интерактивных элементов PCB/корпусов """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self.selected_pen = QPen(QColor(0, 160, 255), 0.3)

    def get_properties(self) -> dict:
        """Возвращает словарь параметров объекта для отображения в правой панели (dockProperties)."""
        return {
            "X": f"{self.pos().x():.3f} мм",
            "Y": f"{-self.pos().y():.3f} мм",
        }

    def set_properties(self, props: dict):
        """Обновляет свойства объекта из правой панели."""
        pass
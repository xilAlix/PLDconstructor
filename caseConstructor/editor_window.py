import sys
from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QComboBox, QSlider
from PyQt6.QtGui import QPainter, QTransform
from PyQt6.QtCore import QPointF, Qt

from caseConstructor.ui_caseRedactor import Ui_MainWindow
from caseConstructor.pcb_scene import PcbGraphicsScene, PcbGraphicsView
from general.styles import get_caseRedactor_stylesheet
from general.config import load_settings


class CaseEditorWindow(QMainWindow):
    """Класс главного окна редактора корпусов."""

    GRID_PRESETS = [
        # Дюймовые
        (2.5400, "Сетка 2,540 мм (100 mil)"),
        (1.2700, "Сетка 1,270 мм (50 mil)"),
        (0.6350, "Сетка 0,635 мм (25 mil)"),
        (0.5080, "Сетка 0,508 мм (20 mil)"),
        (0.2540, "Сетка 0,254 мм (10 mil)"),
    ]

    ZOOM_PRESETS = [1, 2, 5, 10, 15, 20, 25, 30, 50, 100]

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._replace_graphics_view()

        self.settings = load_settings()
        self.current_theme = self.settings.get("General", {}).get("theme", "dark")
        self.version = self.settings.get("Version", {}).get("caseRedactor", "0.0.0")
        start_zoom = self.settings.get("General", {}).get("startZoom", 20)
        self.start_zoom = self.ZOOM_PRESETS.index(start_zoom)

        self._setup_ui()
        self._setup_tab_canvas()
        self.set_theme(self.current_theme)

    def set_theme(self, theme_name: str):
        """Переключает тему оформления приложения."""
        self.current_theme = theme_name
        qss = get_caseRedactor_stylesheet(theme_name)
        self.setStyleSheet(qss)

    def _replace_graphics_view(self):
        """Динамическая замена базового QGraphicsView на PcbGraphicsView."""
        old_view = self.ui.graphicsView
        parent_layout = self.ui.gridLayout_2

        self.graphics_view = PcbGraphicsView(self.ui.tab)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        parent_layout.replaceWidget(old_view, self.graphics_view)
        old_view.deleteLater()

        self.graphics_view.set_zoom_callback(self._on_wheel_zoom)

    def _setup_ui(self):
        """Метод для финальной подгонки UI и настройки динамических виджетов."""
        self.setWindowTitle(f"Редактор корпусов v{self.version}")

        self.ui.dockSubjects.setTitleBarWidget(QWidget())
        self.ui.dockProperties.setTitleBarWidget(QWidget())

        self._setup_statusbar()

    def _setup_statusbar(self):
        """Создание и добавление элементов в нижний статус-бар."""
        # Слева
        self.lbl_zoom = QLabel(f"{self.ZOOM_PRESETS[self.start_zoom]}x")
        self.lbl_zoom.setMinimumWidth(35)

        self.slider_zoom = QSlider(Qt.Orientation.Horizontal)
        self.slider_zoom.setRange(0, len(self.ZOOM_PRESETS) - 1)
        self.slider_zoom.setValue(self.start_zoom)
        self.slider_zoom.setFixedWidth(100)
        self.slider_zoom.valueChanged.connect(self._on_zoom_slider_changed)

        self.ui.statusBar.addWidget(QLabel(" Масштаб: "))
        self.ui.statusBar.addWidget(self.slider_zoom)
        self.ui.statusBar.addWidget(self.lbl_zoom)

        # Справа
        self.lbl_coords = QLabel("X: 0.000 mm (0.000 in) | Y: 0.000 mm (0.000 in)")

        self.combo_grid = QComboBox()
        for size_mm, label_text in self.GRID_PRESETS:
            self.combo_grid.addItem(label_text, userData=size_mm)
        default_index = 1

        self.combo_grid.setCurrentIndex(default_index)
        self.combo_grid.currentIndexChanged.connect(self._on_grid_changed)

        self.ui.statusBar.addPermanentWidget(self.lbl_coords)
        self.ui.statusBar.addPermanentWidget(self.combo_grid)

    def _setup_tab_canvas(self):
        """Привязка интерактивной сцены и холста к первой вкладке."""

        self.scene_tab = PcbGraphicsScene(self)
        self.graphics_view.setScene(self.scene_tab)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.graphics_view.centerOn(0, 0)

        self.scene_tab.set_mouse_move_callback(self._update_coordinates_label)
        self.scene_tab.set_selection_changed_callback(self._on_selection_changed)

        initial_grid_size = self.combo_grid.currentData()
        self.scene_tab.set_grid_size(initial_grid_size)
        self._apply_zoom_factor(self.ZOOM_PRESETS[self.slider_zoom.value()])

    def _on_selection_changed(self, selected_items: list):
        """Обработчик выделения объектов: задел для забивания панели dockProperties."""
        if not selected_items:
            return

        first_item = selected_items[0]
        if hasattr(first_item, 'get_properties'):
            props = first_item.get_properties()

    def _update_coordinates_label(self, x_mm: float, y_mm: float):
        """Выводит точно привязанные координаты в статус-бар."""
        x_in = x_mm / 25.4
        y_in = y_mm / 25.4
        self.lbl_coords.setText(f"X: {x_mm:.3f} mm ({x_in:.3f} in) | Y: {y_mm:.3f} mm ({y_in:.3f} in)")

    def _on_grid_changed(self, index: int):
        """Обработчик смены шага сетки из статус-бара."""
        grid_size = self.combo_grid.itemData(index)
        if grid_size and hasattr(self, 'scene_tab'):
            self.scene_tab.set_grid_size(grid_size)

    def _on_zoom_slider_changed(self, index: int):
        """Срабатывает при сдвиге ползунка масштаба."""
        zoom_factor = self.ZOOM_PRESETS[index]
        self.lbl_zoom.setText(f"{zoom_factor}x")
        self._apply_zoom_factor(zoom_factor)

    def _on_wheel_zoom(self, step: int):
        """Срабатывает при вращении колесика мыши над холстом."""
        current_index = self.slider_zoom.value()
        new_index = max(0, min(len(self.ZOOM_PRESETS) - 1, current_index + step))
        if new_index != current_index:
            self.slider_zoom.setValue(new_index)

    def _apply_zoom_factor(self, factor: float):
        """Применяет коэффициент трансформации масштаба к холсту."""
        transform = QTransform()
        transform.scale(factor, factor)
        self.graphics_view.setTransform(transform)

def run_editor():
    """Функция для автономного запуска окна редактора корпусов."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = CaseEditorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_editor()
import sys
import json
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QToolBar, QLabel, QSlider, QComboBox, QWidget, QFormLayout, QMenu
from PyQt6.QtGui import QAction, QIcon, QPixmap, QColor, QPainter, QTransform
from PyQt6.QtCore import QPointF, Qt, QSize

from caseConstructor.ui_caseRedactor import Ui_MainWindow
from caseConstructor.pcb_scene import PcbGraphicsScene, PcbGraphicsView, PcbPinItem

from general.styles import get_caseRedactor_stylesheet
from general.config import load_settings


class CaseEditorWindow(QMainWindow):
    """Класс главного окна редактора корпусов."""

    ZOOM_PRESETS = [1, 2, 5, 10, 15, 20, 25, 30, 50, 100]
    GRID_PRESETS = [
        (2.54, "2.54 mm (100 mil)"),
        (1.27, "1.27 mm (50 mil)"),
        (0.635, "0.635 mm (25 mil)"),
        (0.5, "0.500 mm"),
        (0.1, "0.100 mm")
    ]

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.current_file_path = None
        self._replace_graphics_view()

        # Загрузка настроек из файла конфигурации
        self.settings = load_settings()
        self.current_theme = self.settings.get("General", {}).get("theme", "dark")
        self.version = self.settings.get("Version", {}).get("caseRedactor", "0.0.0")
        start_zoom = self.settings.get("General", {}).get("startZoom", 20)
        self.start_zoom = self.ZOOM_PRESETS.index(start_zoom) if start_zoom in self.ZOOM_PRESETS else 5

        self._setup_ui()
        self._setup_left_toolbar()
        self._setup_top_toolbar()
        self._setup_menu()
        self._setup_tab_canvas()
        self._setup_properties_panel()
        self.set_theme(self.current_theme)

    def set_theme(self, theme_name: str):
        """Переключает тему оформления приложения."""
        self.current_theme = theme_name
        qss = get_caseRedactor_stylesheet(theme_name)
        self.setStyleSheet(qss)

    def _create_placeholder_icon(self, text: str, color_hex="#2C3E50") -> QIcon:
        """Временный генератор иконок, пока файлы в папке icons/ отсутствуют."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(color_hex))
        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        return QIcon(pixmap)

    def _get_icon_or_placeholder(self, path: str, fallback_text: str, color: str) -> QIcon:
        if os.path.exists(path):
            return QIcon(path)
        return self._create_placeholder_icon(fallback_text, color)

    def _replace_graphics_view(self):
        """Динамическая замена базового QGraphicsView на PcbGraphicsView."""
        old_view = self.ui.graphicsView
        parent_layout = self.ui.gridLayout_2

        self.graphics_view = PcbGraphicsView(self.ui.tab)

        parent_layout.replaceWidget(old_view, self.graphics_view)
        old_view.deleteLater()

        self.graphics_view.zoom_changed.connect(self._on_wheel_zoom)

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
        self.lbl_active_tool = QLabel("Инструмент: Выдел. (Циклич.)")
        self.lbl_active_tool.setStyleSheet("font-weight: bold; color: #4A90E2; padding: 0 10px;")

        self.combo_grid = QComboBox()
        for size_mm, label_text in self.GRID_PRESETS:
            self.combo_grid.addItem(label_text, userData=size_mm)
        default_index = 1

        self.combo_grid.setCurrentIndex(default_index)
        self.combo_grid.currentIndexChanged.connect(self._on_grid_changed)

        self.ui.statusBar.addPermanentWidget(self.lbl_coords)
        self.ui.statusBar.addPermanentWidget(self.lbl_active_tool)
        self.ui.statusBar.addPermanentWidget(self.combo_grid)

    def _setup_left_toolbar(self):
        """Панель инструментов с 3-мя разделами слева."""
        self.left_toolbar = QToolBar("Инструменты", self)
        self.left_toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.left_toolbar)

        # --- СЕКЦИЯ 1: КУРСОРЫ И ВЫДЕЛЕНИЕ ---
        icon_cursor = self._get_icon_or_placeholder("icons/cursor.svg", "SEL", "#2C3E50")
        self.act_tool_select = QAction(icon_cursor, "Выдел. и редакт.", self)
        self.act_tool_select.setToolTip("Выдел. и редакт. (Клик или комбинация рамок)")
        self.act_tool_select.setCheckable(True)
        self.act_tool_select.setChecked(True)

        # Выпадающее подменю режимов выбора при наложении элементов
        select_menu = QMenu(self)
        act_mode_cycle = QAction("Циклический выбор", self)
        act_mode_cycle.triggered.connect(lambda: self._set_selection_mode("cycle", "Циклич."))

        act_mode_list = QAction("Выбор из списка", self)
        act_mode_list.triggered.connect(lambda: self._set_selection_mode("list", "Из списка"))

        select_menu.addAction(act_mode_cycle)
        select_menu.addAction(act_mode_list)
        self.act_tool_select.setMenu(select_menu)

        self.act_tool_select.triggered.connect(
            lambda: self._select_tool("select", "Выдел. и редакт.", self.act_tool_select)
        )
        self.left_toolbar.addAction(self.act_tool_select)

        self.left_toolbar.addSeparator()

        # --- СЕКЦИЯ 2: КОНТАКТЫ ---
        icon_pin = self._get_icon_or_placeholder("icons/pin.svg", "PIN", "#E74C3C")
        self.act_tool_pin = QAction(icon_pin, "Добавить контакт платы", self)
        self.act_tool_pin.setToolTip("Добавить контакт платы (Установка контактов)")
        self.act_tool_pin.setCheckable(True)
        self.act_tool_pin.triggered.connect(
            lambda: self._select_tool("pin", "Добавить контакт платы", self.act_tool_pin)
        )
        self.left_toolbar.addAction(self.act_tool_pin)

        self.left_toolbar.addSeparator()

        # --- СЕКЦИЯ 3: ЛИНИИ ---
        icon_line = self._get_icon_or_placeholder("icons/line.svg", "LINE", "#7F8C8D")
        self.act_tool_line = QAction(icon_line, "Добавить линию (В разработке)", self)
        self.act_tool_line.setToolTip("Добавить проводник / линию связи")
        self.act_tool_line.setEnabled(False)  # Заблокирована
        self.left_toolbar.addAction(self.act_tool_line)

    def _set_selection_mode(self, mode_id: str, label_text: str):
        self.scene_tab.set_select_mode(mode_id)
        self.lbl_active_tool.setText(f"Инструмент: Выдел. ({label_text})")

    def _select_tool(self, tool_id: str, tool_name: str, action: QAction):
        self.act_tool_select.setChecked(False)
        self.act_tool_pin.setChecked(False)
        action.setChecked(True)

        self.scene_tab.set_active_tool(tool_id)
        self.lbl_active_tool.setText(f"Инструмент: {tool_name}")
        self._update_properties_panel()

    def _setup_top_toolbar(self):
        """Верхняя панель инструментов с кнопкой сохранения."""
        icon_save = self._get_icon_or_placeholder("icons/save.svg", "SAV", "#27AE60")
        act_save = QAction(icon_save, "Сохранить модуль", self)
        act_save.setToolTip("Сохранить модуль в файл")
        act_save.triggered.connect(self._save_file)
        self.ui.toolBar.addAction(act_save)

    def _setup_menu(self):
        """Настройка главного меню."""
        self.ui.file.clear()
        act_new = QAction("Новый модуль", self)
        act_new.triggered.connect(self._new_file)
        self.ui.file.addAction(act_new)

        act_save = QAction("Сохранить", self)
        act_save.triggered.connect(self._save_file)
        self.ui.file.addAction(act_save)

    def _setup_tab_canvas(self):
        """Привязка интерактивной сцены и холста к первой вкладке."""

        self.scene_tab = PcbGraphicsScene(self)
        self.graphics_view.setScene(self.scene_tab)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.graphics_view.centerOn(0, 0)

        self.scene_tab.mouse_moved.connect(self._update_coordinates_label)
        self.scene_tab.items_selected.connect(self._on_selection_changed)

        initial_grid_size = self.combo_grid.currentData()
        self.scene_tab.set_grid_size(initial_grid_size)
        self._apply_zoom_factor(self.ZOOM_PRESETS[self.slider_zoom.value()])

    def _setup_properties_panel(self):
        """Подготовка панели self.ui.dockProperties под свойства объектов."""
        self.prop_container = QWidget()
        self.prop_layout = QFormLayout(self.prop_container)
        self.prop_layout.setContentsMargins(4, 4, 4, 4)

        self.ui.dockProperties.setWidget(self.prop_container)
        self._update_properties_panel()

    def _update_properties_panel(self):
        """Отрисовка параметров выбранного объекта в панели справа."""
        while self.prop_layout.count():
            item = self.prop_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        selected = self.scene_tab.selectedItems()

        if len(selected) == 1 and isinstance(selected[0], PcbPinItem):
            pin = selected[0]
            self.prop_layout.addRow(QLabel("<b>Параметры контакта:</b>"))
            self.prop_layout.addRow("Номер контакта:", QLabel(str(pin.pin_number)))
            self.prop_layout.addRow("Тип:", QLabel(str(pin.pin_type)))
            self.prop_layout.addRow("Ширина (мм):", QLabel(f"{pin.width:.2f}"))
            self.prop_layout.addRow("Высота (мм):", QLabel(f"{pin.height:.2f}"))
            self.prop_layout.addRow("Позиция X:", QLabel(f"{pin.pos().x():.3f}"))
            self.prop_layout.addRow("Позиция Y:", QLabel(f"{-pin.pos().y():.3f}"))
        elif len(selected) > 1:
            self.prop_layout.addRow(QLabel(f"<b>Выбрано объектов: {len(selected)}</b>"))
        else:
            if self.scene_tab.active_tool == "pin":
                self.prop_layout.addRow(QLabel("<b>Параметры нового пина:</b>"))
                self.prop_layout.addRow("След. номер:", QLabel(str(self.scene_tab.next_pin_number)))
                self.prop_layout.addRow("Тип:", QLabel("Сквозной (THT)"))
                self.prop_layout.addRow("Размер:", QLabel("2.00 x 2.00 мм"))
            else:
                self.prop_layout.addRow(QLabel("<i>Нет выбранных объектов</i>"))

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

    # --- ФАЙЛОВЫЕ ОПЕРАЦИИ ---

    def _new_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Создать новый модуль", "", "PCB Module (*.kicad_mod *.json)"
        )
        if file_path:
            self.current_file_path = file_path
            self.setWindowTitle(f"Редактор корпусов v{self.version} - [{os.path.basename(file_path)}]")
            self.scene_tab.clear()
            self.scene_tab.next_pin_number = 1
            self._save_file()

    def _save_file(self):
        if not self.current_file_path:
            self._new_file()
            return

        module_data = {
            "version": 1,
            "name": os.path.splitext(os.path.basename(self.current_file_path))[0],
            "pins": []
        }

        for item in self.scene_tab.items():
            if isinstance(item, PcbPinItem):
                module_data["pins"].append({
                    "number": item.pin_number,
                    "x": item.pos().x(),
                    "y": -item.pos().y(),
                    "width": item.width,
                    "height": item.height,
                    "type": item.pin_type
                })

        with open(self.current_file_path, "w", encoding="utf-8") as f:
            json.dump(module_data, f, indent=4, ensure_ascii=False)

        self.ui.statusBar.showMessage(f"Файл сохранен: {self.current_file_path}", 3000)

def run_editor():
    """Функция для автономного запуска окна редактора корпусов."""
    app = QApplication(sys.argv)
    window = CaseEditorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_editor()
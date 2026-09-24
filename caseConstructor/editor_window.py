import sys
from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QComboBox

from caseConstructor.ui_caseRedactor import Ui_MainWindow
from general.styles import get_stylesheet


class CaseEditorWindow(QMainWindow):
    """Класс главного окна редактора корпусов."""

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.current_theme = "light"

        self._setup_ui()
        self.set_theme(self.current_theme)

    def set_theme(self, theme_name: str):
        """Переключает тему оформления приложения."""
        self.current_theme = theme_name
        qss = get_stylesheet(theme_name)
        self.setStyleSheet(qss)

    def _setup_ui(self):
        """Метод для финальной подгонки UI и настройки динамических виджетов."""
        self.setWindowTitle("Редактор корпусов")

        self.ui.dockWidget.setTitleBarWidget(QWidget())
        self._setup_statusbar()

    def _setup_statusbar(self):
        """Создание и добавление элементов в нижний статус-бар."""
        self.lbl_coords = QLabel("X: 0.000 | Y: 0.000 mm")

        self.combo_grid = QComboBox()
        self.combo_grid.addItems([
            "Сетка: 0.1 mm",
            "Сетка: 0.25 mm",
            "Сетка: 0.5 mm",
            "Сетка: 1.0 mm"
        ])

        self.combo_units = QComboBox()
        self.combo_units.addItems(["mm", "mil", "inch"])

        self.ui.statusBar.addPermanentWidget(self.lbl_coords)
        self.ui.statusBar.addPermanentWidget(self.combo_grid)
        self.ui.statusBar.addPermanentWidget(self.combo_units)


def run_editor():
    """Функция для автономного запуска окна редактора корпусов."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = CaseEditorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_editor()
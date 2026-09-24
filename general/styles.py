THEMES = {
    "dark": {
        "bg_main": "#2b2b2b",  # Фон главного окна и вкладок
        "bg_panel": "#3c3f41",  # Тулбары, статусбар, неактивные вкладки
        "bg_dock": "#313335",  # Боковая панель
        "bg_canvas": "#1e1e1e",  # Холст (редактор)
        "bg_tab_active": "#4e5254",  # Активная вкладка
        "bg_hover": "#45494a",  # Подсветка элементов при наведении
        "text_main": "#bbbbbb",  # Основной текст
        "text_active": "#ffffff",  # Активный/выделенный текст
        "border": "#1e1e1e",  # Разделительные линии
        "menu_bg": "#3c3f41",  # Выпадающие меню
    },
    "light": {
        "bg_main": "#f5f5f5",  # Фон главного окна
        "bg_panel": "#e8e8e8",  # Тулбары, статусбар
        "bg_dock": "#f0f0f0",  # Боковая панель
        "bg_canvas": "#ffffff",  # Холст (белый как бумага/CAD)
        "bg_tab_active": "#ffffff",  # Активная вкладка
        "bg_hover": "#dcdcdc",  # Подсветка элементов при наведении
        "text_main": "#222222",  # Основной текст
        "text_active": "#000000",  # Активный текст
        "border": "#d0d0d0",  # Разделительные линии
        "menu_bg": "#f9f9f9",  # Выпадающие меню
    }
}


def get_caseRedactor_stylesheet(theme_name: str = "dark") -> str:
    """Генерирует QSS-строку на основе выбранной темы без скачков геометрии."""
    colors = THEMES.get(theme_name, THEMES["dark"])

    return f"""
        /* Главное окно */
        QMainWindow {{
            background-color: {colors['bg_main']};
        }}

        /* Меню Верхней панели (QMenuBar) */
        QMenuBar {{
            background-color: {colors['bg_panel']};
            color: {colors['text_main']};
            border-bottom: 1px solid {colors['border']};
        }}

        QMenuBar::item {{
            background-color: transparent;
            padding: 4px 8px;
            border: 1px solid transparent; /* Фиксируем рамку заранее */
            border-radius: 3px;
        }}

        QMenuBar::item:selected {{
            background-color: {colors['bg_hover']};
            color: {colors['text_active']};
        }}

        /* Выпадающие списки меню */
        QMenu {{
            background-color: {colors['menu_bg']};
            color: {colors['text_main']};
            border: 1px solid {colors['border']};
            padding: 2px;
        }}

        QMenu::item {{
            padding: 4px 20px 4px 10px;
            border: 1px solid transparent;
        }}

        QMenu::item:selected {{
            background-color: {colors['bg_hover']};
            color: {colors['text_active']};
        }}

        /* Панель инструментов (QToolBar) и её кнопки */
        QToolBar {{
            background-color: {colors['bg_panel']};
            border-bottom: 1px solid {colors['border']};
            padding: 2px;
            spacing: 3px;
        }}

        QToolButton {{
            background-color: transparent;
            border: 1px solid transparent; /* Заранее резервируем место под рамку */
            border-radius: 3px;
            padding: 3px;
            color: {colors['text_main']};
        }}

        QToolButton:hover {{
            background-color: {colors['bg_hover']};
            color: {colors['text_active']};
        }}

        /* Боковая панель (Dock) */
        QDockWidget, #dockWidgetContents {{
            background-color: {colors['bg_dock']};
            border-left: 1px solid {colors['border']};
        }}

        /* Вкладки */
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            background-color: {colors['bg_main']};
        }}

        QTabBar::tab {{
            background-color: {colors['bg_panel']};
            color: {colors['text_main']};
            padding: 6px 12px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            border: 1px solid {colors['border']};
            margin-right: 2px;
        }}

        QTabBar::tab:hover:!selected {{
            background-color: {colors['bg_hover']};
            color: {colors['text_active']};
        }}

        QTabBar::tab:selected {{
            background-color: {colors['bg_tab_active']};
            color: {colors['text_active']};
            border-bottom: 1px solid {colors['bg_tab_active']};
        }}

        /* Статусбар */
        QStatusBar {{
            background-color: {colors['bg_panel']};
            color: {colors['text_main']};
            border-top: 1px solid {colors['border']};
        }}

        /* Графический холст */
        QGraphicsView {{
            background-color: {colors['bg_canvas']};
            border: 1px solid {colors['border']};
        }}

        /* Элементы внутри Статусбара */
        QLabel {{
            color: {colors['text_main']};
            padding: 2px 5px;
        }}

        QComboBox {{
            color: {colors['text_main']};
            background-color: {colors['bg_main']};
            border: 1px solid {colors['border']};
            padding: 2px 5px;
            border-radius: 3px;
        }}

        QComboBox:hover {{
            background-color: {colors['bg_hover']};
            color: {colors['text_active']};
        }}

        QComboBox QAbstractItemView {{
            background-color: {colors['menu_bg']};
            color: {colors['text_main']};
            selection-background-color: {colors['bg_hover']};
            selection-color: {colors['text_active']};
            border: 1px solid {colors['border']};
        }}
    """
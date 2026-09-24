import sys
from PyQt6.QtWidgets import QApplication

from caseConstructor.editor_window import CaseEditorWindow


def main():
    app = QApplication(sys.argv)

    window = CaseEditorWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
import sys

from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("CCR 管理工具")
    app.setOrganizationName("myModels")
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    return app.exec()

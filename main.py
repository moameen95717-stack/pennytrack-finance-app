"""PennyTrack - Personal Finance Tracker. Run with: python main.py"""
from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from database import Database, DatabaseError
from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PennyTrack")
    app.setStyle("Fusion")  # consistent base style for the custom dark theme

    try:
        database = Database()
    except (DatabaseError, OSError) as exc:
        QMessageBox.critical(
            None,
            "PennyTrack",
            f"PennyTrack could not open its database.\n\n{exc}",
        )
        return 1

    window = MainWindow(database)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

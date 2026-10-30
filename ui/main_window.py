"""Main application window: sidebar navigation, pages and data flow."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from database import Database, DatabaseError
from models import Transaction, format_inr
from ui.dashboard import DashboardPage, TransactionsPage
from ui.transaction_dialog import TransactionDialog

RECENT_LIMIT = 10

STYLESHEET = """
* {
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 14px;
    color: #E6EBF5;
}
QMainWindow, QDialog, QMessageBox, QWidget#root {
    background-color: #0B1426;
}
QLabel {
    background: transparent;
}

/* ---------- sidebar ---------- */
QFrame#sidebar {
    background-color: #0F1B33;
    border: none;
    border-right: 1px solid #1B2A47;
}
QLabel#brand {
    font-size: 22px;
    font-weight: 700;
    color: #FFFFFF;
}
QLabel#brandSub {
    font-size: 12px;
    color: #8A98B3;
}
QLabel#sidebarFooter {
    font-size: 12px;
    color: #6B7A99;
}
QPushButton#navButton {
    background-color: transparent;
    color: #9AA8C4;
    text-align: left;
    padding: 12px 16px;
    border-radius: 10px;
    font-weight: 600;
}
QPushButton#navButton:hover {
    background-color: #16264A;
    color: #FFFFFF;
}
QPushButton#navButton:checked {
    background-color: #1D3463;
    color: #FFFFFF;
}

/* ---------- headings ---------- */
QLabel#pageTitle {
    font-size: 26px;
    font-weight: 700;
    color: #FFFFFF;
}
QLabel#pageSubtitle, QLabel#panelMeta, QLabel#cardCaption {
    color: #8A98B3;
    font-size: 13px;
}
QLabel#dialogTitle {
    font-size: 20px;
    font-weight: 700;
    color: #FFFFFF;
}

/* ---------- cards and panels ---------- */
QFrame#card, QFrame#panel {
    background-color: #13213B;
    border: 1px solid #1F3050;
    border-radius: 16px;
}
QLabel#cardTitle {
    color: #9AA8C4;
    font-size: 13px;
    font-weight: 600;
}
QLabel#cardValue {
    font-size: 28px;
    font-weight: 700;
    color: #FFFFFF;
}
QLabel#cardValue[tone="income"] { color: #22C55E; }
QLabel#cardValue[tone="expense"] { color: #EF4444; }
QLabel#cardValue[tone="balance"] { color: #60A5FA; }
QLabel#panelTitle {
    font-size: 17px;
    font-weight: 700;
    color: #FFFFFF;
}
QLabel#emptyState {
    color: #8A98B3;
    font-size: 15px;
}
QLabel#errorLabel {
    color: #F87171;
    background-color: #3B1220;
    border: 1px solid #7F1D1D;
    border-radius: 8px;
    padding: 8px 12px;
}

/* ---------- buttons ---------- */
QPushButton {
    background-color: #1B2A47;
    color: #E6EBF5;
    border: none;
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 600;
}
QPushButton:hover { background-color: #243759; }
QPushButton:pressed { background-color: #2B4068; }
QPushButton[variant="income"] { background-color: #16A34A; color: #FFFFFF; }
QPushButton[variant="income"]:hover { background-color: #15803D; }
QPushButton[variant="expense"] { background-color: #DC2626; color: #FFFFFF; }
QPushButton[variant="expense"]:hover { background-color: #B91C1C; }
QPushButton[variant="primary"] { background-color: #3B82F6; color: #FFFFFF; }
QPushButton[variant="primary"]:hover { background-color: #2563EB; }
QPushButton[variant="danger"] {
    background-color: transparent;
    color: #F87171;
    border: 1px solid #7F1D1D;
}
QPushButton[variant="danger"]:hover { background-color: #3B1220; }
QPushButton:disabled, QPushButton[variant]:disabled {
    background-color: #142039;
    color: #5A6985;
    border: none;
}

/* ---------- inputs ---------- */
QLineEdit, QComboBox, QDateEdit {
    background-color: #0F1B33;
    border: 1px solid #24365A;
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: #3B82F6;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
    border: 1px solid #3B82F6;
}
QComboBox QAbstractItemView {
    background-color: #13213B;
    border: 1px solid #24365A;
    selection-background-color: #1D3463;
    outline: 0;
}
QCalendarWidget QWidget {
    background-color: #13213B;
    color: #E6EBF5;
}
QCalendarWidget QAbstractItemView {
    background-color: #0F1B33;
    selection-background-color: #3B82F6;
    selection-color: #FFFFFF;
}
QCalendarWidget QToolButton {
    background-color: transparent;
    color: #E6EBF5;
    padding: 4px 8px;
}

/* ---------- table ---------- */
QTableWidget {
    background-color: transparent;
    alternate-background-color: #101D36;
    border: none;
    outline: 0;
    selection-background-color: #1E3A8A;
}
QTableWidget::item {
    padding: 4px 10px;
    border-bottom: 1px solid #1B2A47;
}
QHeaderView::section {
    background-color: #0F1B33;
    color: #8A98B3;
    padding: 10px;
    border: none;
    border-bottom: 1px solid #1B2A47;
    font-weight: 600;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2A3C61;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { height: 0; }

QStatusBar {
    background-color: #0F1B33;
    color: #8A98B3;
}
QStatusBar QLabel { color: #8A98B3; }
"""


class MainWindow(QMainWindow):
    """Hosts the sidebar and pages, and coordinates the database and dialogs."""

    def __init__(self, database: Database) -> None:
        super().__init__()
        self._db = database

        self.setWindowTitle("PennyTrack \u2014 Personal Finance Tracker")
        self.resize(1200, 760)
        self.setMinimumSize(980, 620)
        self.setStyleSheet(STYLESHEET)

        self.dashboard_page = DashboardPage()
        self.transactions_page = TransactionsPage()
        for page in (self.dashboard_page, self.transactions_page):
            page.add_requested.connect(self._add_transaction)
            page.edit_requested.connect(self._edit_transaction)
            page.delete_requested.connect(self._delete_transaction)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(self.transactions_page)

        central = QWidget()
        central.setObjectName("root")
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(central)

        self.statusBar().showMessage("Ready")
        self.refresh()

    # ----------------------------------------------------------------- sidebar
    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)

        brand = QLabel("PennyTrack")
        brand.setObjectName("brand")
        brand_sub = QLabel("Personal Finance Tracker")
        brand_sub.setObjectName("brandSub")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 26, 16, 20)
        layout.setSpacing(6)
        layout.addWidget(brand)
        layout.addWidget(brand_sub)
        layout.addSpacing(26)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        for index, label in enumerate(("Dashboard", "Transactions")):
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setChecked(index == 0)
            button.clicked.connect(lambda _checked=False, i=index: self.pages.setCurrentIndex(i))
            self._nav_group.addButton(button)
            layout.addWidget(button)

        layout.addStretch(1)
        footer = QLabel("Offline \u2022 Data stays on this PC")
        footer.setObjectName("sidebarFooter")
        layout.addWidget(footer)
        return sidebar

    # ----------------------------------------------------------------- refresh
    def refresh(self) -> None:
        """Reload everything from the database and update all pages."""
        try:
            summary = self._db.get_summary()
            recent = self._db.get_recent(RECENT_LIMIT)
            everything = self._db.get_all()
        except DatabaseError as exc:
            self._show_db_error("load your transactions", exc)
            return
        self.dashboard_page.refresh(summary, recent)
        self.transactions_page.refresh(everything)

    def _show_db_error(self, action: str, exc: Exception) -> None:
        QMessageBox.critical(self, "Database error", f"PennyTrack could not {action}.\n\n{exc}")

    # ---------------------------------------------------------------- handlers
    def _add_transaction(self, tx_type: str) -> None:
        dialog = TransactionDialog(self, default_type=tx_type)
        if dialog.exec() != QDialog.DialogCode.Accepted or dialog.transaction is None:
            return
        try:
            self._db.add_transaction(dialog.transaction)
        except DatabaseError as exc:
            self._show_db_error("save the transaction", exc)
            return
        self.refresh()
        self.statusBar().showMessage("Transaction added.", 4000)

    def _edit_transaction(self, tx_id: int) -> None:
        try:
            existing = self._db.get_transaction(tx_id)
        except DatabaseError as exc:
            self._show_db_error("load the transaction", exc)
            return
        if existing is None:
            QMessageBox.warning(self, "Not found", "That transaction no longer exists.")
            self.refresh()
            return

        dialog = TransactionDialog(self, transaction=existing)
        if dialog.exec() != QDialog.DialogCode.Accepted or dialog.transaction is None:
            return
        try:
            updated = self._db.update_transaction(dialog.transaction)
        except DatabaseError as exc:
            self._show_db_error("update the transaction", exc)
            return
        if not updated:
            QMessageBox.warning(self, "Not found", "That transaction no longer exists.")
        self.refresh()
        if updated:
            self.statusBar().showMessage("Transaction updated.", 4000)

    def _delete_transaction(self, tx_id: int) -> None:
        try:
            existing: Optional[Transaction] = self._db.get_transaction(tx_id)
        except DatabaseError as exc:
            self._show_db_error("load the transaction", exc)
            return
        if existing is None:
            self.refresh()
            return

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Delete transaction")
        box.setText("Delete this transaction?")
        box.setInformativeText(
            f"{existing.category}  \u2022  {format_inr(existing.amount)}  \u2022  "
            f"{existing.date:%d %b %Y}\n\nThis cannot be undone."
        )
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        box.button(QMessageBox.StandardButton.Yes).setText("Delete")
        box.button(QMessageBox.StandardButton.No).setText("Cancel")
        if box.exec() != QMessageBox.StandardButton.Yes:
            return

        try:
            self._db.delete_transaction(tx_id)
        except DatabaseError as exc:
            self._show_db_error("delete the transaction", exc)
            return
        self.refresh()
        self.statusBar().showMessage("Transaction deleted.", 4000)

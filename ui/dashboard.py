"""Dashboard and Transactions pages plus the reusable widgets they share."""
from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QKeyEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models import EXPENSE, INCOME, Summary, Transaction, format_inr

INCOME_COLOR = "#22C55E"
EXPENSE_COLOR = "#EF4444"


# --------------------------------------------------------------------- widgets
class SummaryCard(QFrame):
    """A rounded card showing a title, a large value and a caption."""

    def __init__(self, title: str, caption: str, tone: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")

        self._title = QLabel(title)
        self._title.setObjectName("cardTitle")
        self._value = QLabel(format_inr(0))
        self._value.setObjectName("cardValue")
        self._value.setProperty("tone", tone)
        self._caption = QLabel(caption)
        self._caption.setObjectName("cardCaption")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(6)
        layout.addWidget(self._title)
        layout.addWidget(self._value)
        layout.addWidget(self._caption)

    def set_value(self, text: str, tone: Optional[str] = None) -> None:
        self._value.setText(text)
        if tone is not None:
            self._value.setProperty("tone", tone)
            style = self._value.style()
            style.unpolish(self._value)
            style.polish(self._value)


class TransactionTable(QTableWidget):
    """Read-only table of transactions with edit/delete signals."""

    edit_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    HEADERS = ["Date", "Category", "Description", "Type", "Amount"]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(0, len(self.HEADERS), parent)
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.horizontalHeaderItem(4).setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(44)

        header = self.horizontalHeader()
        header.setHighlightSections(False)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.itemDoubleClicked.connect(self._on_double_click)

    def _id_at(self, row: int) -> Optional[int]:
        item = self.item(row, 0)
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return int(value) if value is not None else None

    def selected_id(self) -> Optional[int]:
        rows = self.selectionModel().selectedRows()
        if not rows:
            return None
        return self._id_at(rows[0].row())

    def set_transactions(self, transactions: List[Transaction]) -> None:
        self.setRowCount(len(transactions))
        align_right = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        for row, tx in enumerate(transactions):
            is_income = tx.type == INCOME
            colour = QColor(INCOME_COLOR if is_income else EXPENSE_COLOR)

            date_item = QTableWidgetItem(tx.date.strftime("%d %b %Y"))
            date_item.setData(Qt.ItemDataRole.UserRole, tx.id)

            category_item = QTableWidgetItem(tx.category)

            description_item = QTableWidgetItem(tx.description or "-")
            if tx.description:
                description_item.setToolTip(tx.description)

            type_item = QTableWidgetItem("Income" if is_income else "Expense")
            type_item.setForeground(colour)

            sign = "+" if is_income else "-"
            amount_item = QTableWidgetItem(f"{sign}{format_inr(tx.amount)}")
            amount_item.setForeground(colour)
            amount_item.setTextAlignment(align_right)

            for column, item in enumerate(
                (date_item, category_item, description_item, type_item, amount_item)
            ):
                self.setItem(row, column, item)

        self.clearSelection()

    def _on_double_click(self, item: QTableWidgetItem) -> None:
        tx_id = self._id_at(item.row())
        if tx_id is not None:
            self.edit_requested.emit(tx_id)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 (Qt naming)
        if event.key() == Qt.Key.Key_Delete:
            tx_id = self.selected_id()
            if tx_id is not None:
                self.delete_requested.emit(tx_id)
                return
        super().keyPressEvent(event)


class TransactionsPanel(QFrame):
    """A rounded panel: title, table (or empty-state message) and Edit/Delete buttons."""

    edit_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")

        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")
        self._count_label = QLabel("")
        self._count_label.setObjectName("panelMeta")

        header = QHBoxLayout()
        header.addWidget(title_label)
        header.addStretch(1)
        header.addWidget(self._count_label)

        self.table = TransactionTable()
        self.table.edit_requested.connect(self.edit_requested)
        self.table.delete_requested.connect(self.delete_requested)
        self.table.itemSelectionChanged.connect(self._update_buttons)

        self._empty_label = QLabel(
            "No transactions yet.\nUse 'Add Income' or 'Add Expense' to record your first one."
        )
        self._empty_label.setObjectName("emptyState")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._edit_button = QPushButton("Edit")
        self._edit_button.clicked.connect(self._emit_edit)
        self._delete_button = QPushButton("Delete")
        self._delete_button.setProperty("variant", "danger")
        self._delete_button.clicked.connect(self._emit_delete)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        hint = QLabel("Select a row, or double-click to edit.")
        hint.setObjectName("panelMeta")
        actions.addWidget(hint)
        actions.addStretch(1)
        actions.addWidget(self._edit_button)
        actions.addWidget(self._delete_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)
        layout.addLayout(header)
        layout.addWidget(self.table, 1)
        layout.addWidget(self._empty_label, 1)
        layout.addLayout(actions)

        self.set_transactions([])

    def set_transactions(self, transactions: List[Transaction]) -> None:
        self.table.set_transactions(transactions)
        has_rows = bool(transactions)
        self.table.setVisible(has_rows)
        self._empty_label.setVisible(not has_rows)
        count = len(transactions)
        self._count_label.setText(f"{count} transaction{'s' if count != 1 else ''}")
        self._update_buttons()

    def _update_buttons(self) -> None:
        has_selection = self.table.selected_id() is not None
        self._edit_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)

    def _emit_edit(self) -> None:
        tx_id = self.table.selected_id()
        if tx_id is not None:
            self.edit_requested.emit(tx_id)

    def _emit_delete(self) -> None:
        tx_id = self.table.selected_id()
        if tx_id is not None:
            self.delete_requested.emit(tx_id)


def build_page_header(title: str, subtitle: str, add_signal) -> QHBoxLayout:
    """Page title block on the left, Add Income / Add Expense buttons on the right."""
    title_label = QLabel(title)
    title_label.setObjectName("pageTitle")
    subtitle_label = QLabel(subtitle)
    subtitle_label.setObjectName("pageSubtitle")

    text_block = QVBoxLayout()
    text_block.setSpacing(2)
    text_block.addWidget(title_label)
    text_block.addWidget(subtitle_label)

    income_button = QPushButton("+  Add Income")
    income_button.setProperty("variant", "income")
    income_button.clicked.connect(lambda _checked=False: add_signal.emit(INCOME))

    expense_button = QPushButton("+  Add Expense")
    expense_button.setProperty("variant", "expense")
    expense_button.clicked.connect(lambda _checked=False: add_signal.emit(EXPENSE))

    header = QHBoxLayout()
    header.setSpacing(10)
    header.addLayout(text_block)
    header.addStretch(1)
    header.addWidget(income_button)
    header.addWidget(expense_button)
    return header


# ----------------------------------------------------------------------- pages
class DashboardPage(QWidget):
    """Summary cards plus the most recent transactions."""

    add_requested = pyqtSignal(str)
    edit_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.income_card = SummaryCard("Total Income", "All money received", "income")
        self.expense_card = SummaryCard("Total Expenses", "All money spent", "expense")
        self.balance_card = SummaryCard("Remaining Balance", "Income minus expenses", "balance")

        cards = QHBoxLayout()
        cards.setSpacing(18)
        cards.addWidget(self.income_card, 1)
        cards.addWidget(self.expense_card, 1)
        cards.addWidget(self.balance_card, 1)

        self.panel = TransactionsPanel("Recent Transactions")
        self.panel.edit_requested.connect(self.edit_requested)
        self.panel.delete_requested.connect(self.delete_requested)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(22)
        layout.addLayout(
            build_page_header(
                "Dashboard", "Your income, expenses and balance at a glance.", self.add_requested
            )
        )
        layout.addLayout(cards)
        layout.addWidget(self.panel, 1)

    def refresh(self, summary: Summary, recent: List[Transaction]) -> None:
        self.income_card.set_value(format_inr(summary.total_income))
        self.expense_card.set_value(format_inr(summary.total_expenses))
        balance_tone = "balance" if summary.balance >= 0 else "expense"
        self.balance_card.set_value(format_inr(summary.balance), balance_tone)
        self.panel.set_transactions(recent)


class TransactionsPage(QWidget):
    """Full transaction history."""

    add_requested = pyqtSignal(str)
    edit_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.panel = TransactionsPanel("All Transactions")
        self.panel.edit_requested.connect(self.edit_requested)
        self.panel.delete_requested.connect(self.delete_requested)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(22)
        layout.addLayout(
            build_page_header("Transactions", "Every transaction, newest first.", self.add_requested)
        )
        layout.addWidget(self.panel, 1)

    def refresh(self, transactions: List[Transaction]) -> None:
        self.panel.set_transactions(transactions)

"""Dialog used for adding and editing transactions."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QDate, QRegularExpression, Qt
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models import (
    CURRENCY_SYMBOL,
    EXPENSE,
    EXPENSE_CATEGORIES,
    INCOME,
    INCOME_CATEGORIES,
    MAX_CATEGORY_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MIN_DATE,
    Transaction,
    ValidationError,
    build_transaction,
)


class TransactionDialog(QDialog):
    """Modal form for creating a new transaction or editing an existing one."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        transaction: Optional[Transaction] = None,
        default_type: str = EXPENSE,
    ) -> None:
        super().__init__(parent)
        self._editing_id: Optional[int] = transaction.id if transaction else None
        self._transaction: Optional[Transaction] = None

        title = "Edit Transaction" if transaction else "Add Transaction"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(460)

        heading = QLabel(title)
        heading.setObjectName("dialogTitle")

        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItem("Income", INCOME)
        self.type_combo.addItem("Expense", EXPENSE)

        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd MMM yyyy")
        self.date_edit.setMinimumDate(QDate(MIN_DATE.year, MIN_DATE.month, MIN_DATE.day))
        self.date_edit.setMaximumDate(QDate.currentDate())

        # Amount
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("e.g. 1250.50")
        self.amount_edit.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^\d{0,10}(\.\d{0,2})?$"), self)
        )

        # Category (editable so users can type their own)
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        category_line_edit = self.category_combo.lineEdit()
        category_line_edit.setPlaceholderText("Choose or type a category")
        category_line_edit.setMaxLength(MAX_CATEGORY_LENGTH)

        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional note")
        self.description_edit.setMaxLength(MAX_DESCRIPTION_LENGTH)

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.addRow("Type", self.type_combo)
        form.addRow("Date", self.date_edit)
        form.addRow(f"Amount ({CURRENCY_SYMBOL})", self.amount_edit)
        form.addRow("Category", self.category_combo)
        form.addRow("Description", self.description_edit)

        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        self.save_button = QPushButton("Save Changes" if transaction else "Add Transaction")
        self.save_button.setProperty("variant", "primary")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self._on_save)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)
        buttons.addWidget(cancel_button)
        buttons.addWidget(self.save_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)
        layout.addWidget(heading)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addLayout(buttons)

        # Initial values
        if transaction:
            self.type_combo.setCurrentIndex(self.type_combo.findData(transaction.type))
            self._populate_categories(selected=transaction.category)
            self.date_edit.setDate(
                QDate(transaction.date.year, transaction.date.month, transaction.date.day)
            )
            self.amount_edit.setText(f"{transaction.amount:.2f}")
            self.description_edit.setText(transaction.description)
        else:
            self.type_combo.setCurrentIndex(self.type_combo.findData(default_type))
            self._populate_categories()
            self.date_edit.setDate(QDate.currentDate())

        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        self.amount_edit.setFocus()

    # ----------------------------------------------------------------- helpers
    @property
    def transaction(self) -> Optional[Transaction]:
        """The validated transaction after the dialog was accepted."""
        return self._transaction

    def _categories_for_current_type(self) -> list:
        return INCOME_CATEGORIES if self.type_combo.currentData() == INCOME else EXPENSE_CATEGORIES

    def _populate_categories(self, selected: Optional[str] = None) -> None:
        self.category_combo.clear()
        self.category_combo.addItems(self._categories_for_current_type())
        if selected:
            self.category_combo.setCurrentText(selected)
        else:
            self.category_combo.setCurrentIndex(-1)

    def _on_type_changed(self) -> None:
        current = self.category_combo.currentText().strip()
        keep = current if current in self._categories_for_current_type() else None
        self._populate_categories(selected=keep)

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.setVisible(True)

    # ------------------------------------------------------------------ actions
    def _on_save(self) -> None:
        qdate = self.date_edit.date()
        try:
            self._transaction = build_transaction(
                tx_type=self.type_combo.currentData(),
                amount_text=self.amount_edit.text(),
                category=self.category_combo.currentText(),
                description=self.description_edit.text(),
                tx_date=qdate.toPyDate(),
                tx_id=self._editing_id,
            )
        except ValidationError as exc:
            self._transaction = None
            self._show_error(str(exc))
            return
        self.accept()

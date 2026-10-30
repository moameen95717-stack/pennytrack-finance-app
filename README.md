# PennyTrack - Personal Finance Tracker

An offline-first Windows desktop app for tracking income and expenses in Indian Rupees (₹).
Built with Python 3.11, PyQt6 and SQLite.

## Features (Phase 1)

- Dashboard with total income, total expenses and remaining balance
- Recent transactions list and a full Transactions page
- Add, edit and delete transactions (delete asks for confirmation)
- Date, amount, category and description for every transaction
- Input validation: amounts must be positive with at most 2 decimals, dates cannot be in the future
- Indian digit grouping (for example ₹12,34,567.50)
- Dashboard refreshes automatically after every change
- All data stored locally in SQLite, nothing leaves your PC

## Requirements

- Windows 10 or 11
- Python 3.11

## Setup and run (Windows CMD)

```bat
cd path\to\PennyTrack
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

## Where is my data?

The database is created automatically on first launch at `data\pennytrack.db`.
Back it up by copying that file while the app is closed. The app starts empty;
it never inserts sample data.

## Project layout

| Path | Purpose |
|------|---------|
| `main.py` | Entry point |
| `database.py` | SQLite access (parameterized queries, amounts stored as integer paise) |
| `models.py` | Data classes, validation, ₹ formatting |
| `ui/main_window.py` | Window, sidebar, theme, add/edit/delete flow |
| `ui/dashboard.py` | Dashboard and Transactions pages, summary cards, table |
| `ui/transaction_dialog.py` | Add/Edit transaction form |

## Tips

- Double-click a row to edit it, or select it and press **Delete** to remove it.
- Categories are editable: type your own if the list does not fit.

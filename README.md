# 🏛️ Telangana Citizen Grievance Router

Route civic complaints to the correct Telangana government department — instantly, in **English**, **తెలుగు**, or **हिंदी**.

---

## Features

- **Intelligent Routing** — keyword scoring matches your complaint to the right department
- **Trilingual** — full UI + keyword matching in English, Telugu, and Hindi
- **Dynamic Forms** — each department asks only for the fields it needs
- **SQLite History** — every submission persisted locally; session history panel
- **Glassmorphic UI** — green + gold Telangana brand palette

---

## Departments Covered

| Code | Department |
|------|-----------|
| GHMC | Greater Hyderabad Municipal Corporation |
| TSSPDCL | TS Southern Power Distribution Company Ltd |
| HMWSSB | Hyderabad Metro Water Supply & Sewerage Board |
| TSRTC | Telangana State Road Transport Corporation |
| TSPSC | TS Public Service Commission |
| DLTC | District Labour & Training Centre |
| TGPSC | Telangana Government Pensions |
| FOOD | Food Safety Authority of Telangana |

---

## Quick Start

### Prerequisites
- Python 3.11+
- [UV](https://docs.astral.sh/uv/getting-started/installation/) installed

### Install UV (if not already)
```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Run the App

**Windows:**
```bat
start.bat
```

**macOS / Linux:**
```bash
chmod +x start.sh
./start.sh
```

**Manual:**
```bash
uv run streamlit run app.py
```

The first run automatically:
1. Creates a UV virtual environment
2. Installs `streamlit`
3. Creates `telangana_grievances.db` and seeds all data
4. Opens the app at `http://localhost:8501`

---

## Project Structure

```
.
├── .specify/
│   └── memory/
│       ├── constitution.md   # Project laws
│       ├── spec.md           # Functional requirements
│       ├── plan.md           # Technical architecture
│       └── tasks.md          # Task checklist
├── app.py                    # Streamlit UI (all pages)
├── database.py               # SQLite I/O layer
├── pyproject.toml            # UV project + dependencies
├── start.bat                 # Windows launcher
├── start.sh                  # Unix launcher
└── telangana_grievances.db   # Auto-created on first run
```

---

## Usage

1. **Select Language** in the sidebar (English / తెలుగు / हिंदी)
2. **Type your problem** in the search box — e.g. `pothole on my road`, `రోడ్డు పాడైంది`, `बिजली नहीं है`
3. The app **matches a department** and shows its contact info
4. **Fill the dynamic form** with required details
5. **Submit** — your grievance is saved and appears in the history panel

---

## Architecture Notes

- `database.py` owns **all** SQLite I/O — `app.py` never touches the DB directly
- Routing is fully data-driven: keyword lists live in the `complaints` table
- Adding a new department = inserting rows into `departments` + `complaints` — no code change required
- UV manages the virtualenv; never use `pip install` directly

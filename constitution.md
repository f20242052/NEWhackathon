# Constitution — Telangana Citizen Grievance Router

## Project Laws (Non-negotiable Constraints)

### 1. Frontend Framework
- **Streamlit only.** No Flask, FastAPI, or standalone HTML files as primary UI.
- All pages are implemented in `app.py` using `st.*` APIs.
- Custom CSS injected via `st.markdown(..., unsafe_allow_html=True)`.

### 2. Environment & Package Management
- **UV exclusively.** Never use `pip install` directly or `venv` commands.
- All dependencies declared in `pyproject.toml` under `[project.dependencies]`.
- Application launched via `uv run streamlit run app.py`.

### 3. Localization
- The application MUST support three languages: **English**, **తెలుగు (Telugu)**, **हिंदी (Hindi)**.
- All user-visible strings (labels, placeholders, messages, department names) must be translatable.
- Language selection is a sidebar control persisted in `st.session_state`.

### 4. Data Storage
- **SQLite only.** No hard-coded complaint or department lists in Python source files.
- All departments, complaint types, and keywords live in `telangana_grievances.db`.
- Seed data loaded once on first run via `database.py`.
- All grievance submissions written to the `grievances` table; history is read from DB.

### 5. No Hard-Coded Routing Logic
- Department routing MUST query the `complaints` table using keyword matching.
- Adding a new department or complaint type requires only a DB seed entry — no code change.

### 6. UI Aesthetic
- Color palette: **deep green (#1a472a) + gold (#c9a84c)** as primary brand colors.
- Glassmorphism card style applied to all panels.
- Responsive layout; sidebar for controls, main area for search + form + history.

### 7. Code Quality
- Each function has a single responsibility.
- `database.py` owns all DB I/O; `app.py` owns all UI logic.
- No raw SQL strings in `app.py`.

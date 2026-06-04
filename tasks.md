# Task Tracker — Telangana Citizen Grievance Router

## Status Legend
- [x] Done  |  [ ] Pending  |  [~] In Progress

---

## Phase 1 — Spec Kit Scaffold
- [x] `.specify/memory/constitution.md` — project laws
- [x] `.specify/memory/spec.md` — functional requirements
- [x] `.specify/memory/plan.md` — technical architecture
- [x] `.specify/memory/tasks.md` — this file

## Phase 2 — Project Configuration
- [x] `pyproject.toml` — UV project + dependencies
- [x] `start.bat` — Windows run script
- [x] `start.sh` — Unix run script
- [x] `.gitignore` — standard Python + Streamlit ignores
- [x] `README.md` — setup + usage guide

## Phase 3 — Database Layer (`database.py`)
- [x] `init_db()` — create tables if not exist
- [x] `seed_departments()` — 8 Telangana departments (EN/TE/HI)
- [x] `seed_complaints()` — complaint types with trilingual keywords
- [x] `route_query()` — keyword scoring across selected language
- [x] `save_grievance()` — write submission to grievances table
- [x] `get_grievance_history()` — read last N grievances

## Phase 4 — Streamlit Application (`app.py`)
- [x] `inject_css()` — glassmorphism gold/green theme
- [x] `get_translations()` — UI string map for EN/TE/HI
- [x] Sidebar: language picker + department directory
- [x] Main: multilingual search bar with live routing
- [x] Dept card: matched department display
- [x] Dynamic form: fields driven by `required_fields` JSON
- [x] Form submission → DB write → success toast
- [x] History panel: `st.dataframe` from SQLite

## Phase 5 — Verification
- [ ] `uv run streamlit run app.py` launches without errors
- [ ] English search ("pothole", "water leak", "power cut") routes correctly
- [ ] Telugu search ("రోడ్డు", "నీళ్ళు", "కరెంట్") routes correctly
- [ ] Hindi search ("सड़क", "पानी", "बिजली") routes correctly
- [ ] Form submission writes row to DB, appears in history
- [ ] Language switch changes all UI labels instantly

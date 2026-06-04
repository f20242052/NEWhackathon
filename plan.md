# Technical Plan — Telangana Citizen Grievance Router

## Architecture

```
app.py  (Streamlit UI)
  │
  ├── database.py  (SQLite I/O layer)
  │     └── telangana_grievances.db  (auto-created on first run)
  │
  └── pyproject.toml  (UV dependencies)
```

## Database Schema

### Table: `departments`
```sql
CREATE TABLE departments (
    id          TEXT PRIMARY KEY,   -- e.g. 'GHMC'
    name_en     TEXT NOT NULL,
    name_te     TEXT NOT NULL,
    name_hi     TEXT NOT NULL,
    helpline    TEXT,
    portal_url  TEXT
);
```

### Table: `complaints`
```sql
CREATE TABLE complaints (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_id       TEXT REFERENCES departments(id),
    category_en   TEXT NOT NULL,
    category_te   TEXT NOT NULL,
    category_hi   TEXT NOT NULL,
    keywords_en   TEXT NOT NULL,   -- comma-separated
    keywords_te   TEXT NOT NULL,
    keywords_hi   TEXT NOT NULL,
    required_fields TEXT NOT NULL  -- JSON: ["field_id", ...]
);
```

### Table: `grievances`
```sql
CREATE TABLE grievances (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_id      TEXT,
    category_en  TEXT,
    fields_json  TEXT,    -- submitted form data as JSON
    language     TEXT,    -- 'en' | 'te' | 'hi'
    created_at   TEXT DEFAULT (datetime('now','localtime'))
);
```

## Keyword Matching Algorithm

```python
def route(query: str, lang: str) -> list[dict]:
    query_tokens = set(query.lower().split())
    results = []
    for complaint in all_complaints():
        kw_col = f"keywords_{lang}"
        keywords = set(complaint[kw_col].lower().split(","))
        score = len(query_tokens & keywords)
        if score > 0:
            results.append((score, complaint))
    results.sort(key=lambda x: -x[0])
    return [c for _, c in results]
```

## Streamlit App Structure

```
st.set_page_config(...)
inject_css()            # glassmorphism + brand colors
─── sidebar ───────────
  language_selector()
  about_panel()
─── main ───────────────
  search_bar()
  if match:
    dept_card()         # shows matched dept info
    grievance_form()    # dynamic fields based on required_fields JSON
    on submit → save_grievance()
  history_panel()       # st.dataframe from DB
```

## UV Environment Setup

```toml
# pyproject.toml
[project]
name = "telangana-grievance-router"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "streamlit>=1.35.0",
]
```

## Session State Keys

| Key | Type | Purpose |
|-----|------|---------|
| `lang` | str | Active language: 'en', 'te', 'hi' |
| `matched_complaint` | dict | Current routing result |
| `form_submitted` | bool | Guard double-submit |
| `search_query` | str | Last search text |

## CSS Approach

Inject once via `st.markdown` at app start:
- CSS custom properties: `--brand-green`, `--brand-gold`
- `.glass-card` class: `backdrop-filter: blur(12px); background: rgba(255,255,255,0.08)`
- Override Streamlit default font with 'Noto Sans Telugu' for multilingual support
- Hide Streamlit header/footer chrome

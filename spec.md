# Functional Specification — Telangana Citizen Grievance Router

## Problem Statement
Telangana citizens often don't know which government department to approach when they have a civic problem. This causes misdirected complaints, delays, and frustration. This application routes citizen grievances to the correct department instantly using keyword-based matching across three languages.

## Target Departments (seeded in DB)

| Dept Code | Department Name | Handles |
|-----------|----------------|---------|
| GHMC | Greater Hyderabad Municipal Corporation | Roads, garbage, drainage, footpaths, potholes |
| TSSPDCL | TS Southern Power Distribution | Electricity outages, transformer faults, billing |
| HMWSSB | Hyd. Metro Water Supply & Sewerage Board | Water supply, leakage, pipe bursts, sewage |
| TSRTC | Telangana State Road Transport Corporation | Bus route, bus stop, driver complaints |
| TSPSC | TS Public Service Commission | Exam hall ticket, result, recruitment |
| DLTC | Dist. Labour & Training Centre | Labour dispute, wage theft, PF issues |
| TGPSC | Telangana Govt Pensions | Pension delay, old-age support |
| FOOD | Food Safety Authority | Adulterated food, restaurant hygiene |

## User Journey

```
1. Citizen opens app
2. Selects language (EN / TE / HI)
3. Types problem in natural language or own language
4. App searches DB → returns matched department + complaint category
5. Dynamic form renders based on department's required fields
6. Citizen fills and submits form
7. Submission saved to `grievances` table
8. History panel shows all past submissions from this session
```

## Required Form Fields by Department

| Department | Required Inputs |
|------------|----------------|
| GHMC | Location / Ward Number, Photo (optional) |
| TSSPDCL | Service Connection Number, Area/Mandal |
| HMWSSB | Water Connection Number, Colony Name |
| TSRTC | Route Number, Bus Stop Name |
| All others | Aadhar Number (last 4 digits), Description |

## Multilingual Keyword Mapping (sample)

| English | Telugu | Hindi | Routes to |
|---------|--------|-------|-----------|
| pothole, road, footpath | రోడ్డు, గుంత | सड़क, गड्ढा | GHMC |
| power cut, electricity, transformer | కరెంట్, విద్యుత్ | बिजली, करंट | TSSPDCL |
| water leak, pipe burst, no water | నీళ్ళు, లీకేజీ | पानी, रिसाव | HMWSSB |
| bus, route, driver | బస్సు, రూట్ | बस, रूट | TSRTC |
| food, adulterated, hygiene | ఆహారం, కల్తీ | खाना, मिलावट | FOOD |

## Non-Functional Requirements

- App loads in < 3 seconds on first run (SQLite seed).
- Works fully offline after install.
- Search is case-insensitive and strips punctuation.
- History limited to 50 most recent per session for performance.

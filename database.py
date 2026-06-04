"""
database.py
===========
All SQLite I/O for the Telangana Citizen Grievance Router.

Responsibilities:
- Schema creation (departments, complaints, grievances)
- One-time data seeding (departments + complaint types in EN/TE/HI)
- Query routing via keyword scoring
- Grievance save + history retrieval

Rule: app.py must NEVER import sqlite3 directly. All DB access goes through
the public functions at the bottom of this module.
"""

import json
import re
import sqlite3
from pathlib import Path


from supabase_client import supabase

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).parent / "telangana_grievances.db"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _already_seeded(conn: sqlite3.Connection) -> bool:
    cur = conn.execute("SELECT COUNT(*) FROM departments")
    return cur.fetchone()[0] > 0


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS departments (
    id          TEXT PRIMARY KEY,
    name_en     TEXT NOT NULL,
    name_te     TEXT NOT NULL,
    name_hi     TEXT NOT NULL,
    helpline    TEXT NOT NULL DEFAULT '',
    portal_url  TEXT NOT NULL DEFAULT '',
    icon        TEXT NOT NULL DEFAULT '🏛️'
);

CREATE TABLE IF NOT EXISTS complaints (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_id         TEXT NOT NULL REFERENCES departments(id),
    category_en     TEXT NOT NULL,
    category_te     TEXT NOT NULL,
    category_hi     TEXT NOT NULL,
    keywords_en     TEXT NOT NULL,
    keywords_te     TEXT NOT NULL,
    keywords_hi     TEXT NOT NULL,
    required_fields TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS grievances (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_id     TEXT NOT NULL,
    category_en TEXT NOT NULL,
    fields_json TEXT NOT NULL DEFAULT '{}',
    language    TEXT NOT NULL DEFAULT 'en',
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
"""


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

_DEPARTMENTS = [
    {
        "id": "GHMC",
        "name_en": "Greater Hyderabad Municipal Corporation",
        "name_te": "గ్రేటర్ హైదరాబాద్ మునిసిపల్ కార్పొరేషన్",
        "name_hi": "ग्रेटर हैदराबाद नगर निगम",
        "helpline": "040-21111111",
        "portal_url": "https://ghmc.gov.in",
        "icon": "🏙️",
    },
    {
        "id": "TSSPDCL",
        "name_en": "TS Southern Power Distribution Company",
        "name_te": "తెలంగాణ దక్షిణ విద్యుత్ పంపిణీ సంస్థ",
        "name_hi": "तेलंगाना दक्षिण विद्युत वितरण कंपनी",
        "helpline": "1912",
        "portal_url": "https://tssouthernpower.com",
        "icon": "⚡",
    },
    {
        "id": "HMWSSB",
        "name_en": "Hyderabad Metro Water Supply & Sewerage Board",
        "name_te": "హైదరాబాద్ మెట్రో వాటర్ సప్లై & సీవరేజ్ బోర్డు",
        "name_hi": "हैदराबाद मेट्रो जल आपूर्ति एवं सीवरेज बोर्ड",
        "helpline": "155313",
        "portal_url": "https://hmwssb.gov.in",
        "icon": "💧",
    },
    {
        "id": "TSRTC",
        "name_en": "Telangana State Road Transport Corporation",
        "name_te": "తెలంగాణ రాష్ట్ర రోడ్డు రవాణా సంస్థ",
        "name_hi": "तेलंगाना राज्य सड़क परिवहन निगम",
        "helpline": "040-69440000",
        "portal_url": "https://tsrtconline.in",
        "icon": "🚌",
    },
    {
        "id": "TSPSC",
        "name_en": "Telangana State Public Service Commission",
        "name_te": "తెలంగాణ రాష్ట్ర పబ్లిక్ సర్వీస్ కమిషన్",
        "name_hi": "तेलंगाना राज्य लोक सेवा आयोग",
        "helpline": "040-23542185",
        "portal_url": "https://tspsc.gov.in",
        "icon": "📋",
    },
    {
        "id": "DLTC",
        "name_en": "District Labour & Training Centre",
        "name_te": "జిల్లా కార్మిక శిక్షణ కేంద్రం",
        "name_hi": "जिला श्रम एवं प्रशिक्षण केंद्र",
        "helpline": "1800-425-2929",
        "portal_url": "https://labour.telangana.gov.in",
        "icon": "🔧",
    },
    {
        "id": "TGPSC",
        "name_en": "Telangana Government Pensions",
        "name_te": "తెలంగాణ ప్రభుత్వ పెన్షన్లు",
        "name_hi": "तेलंगाना सरकार पेंशन",
        "helpline": "040-23450985",
        "portal_url": "https://treasury.telangana.gov.in",
        "icon": "🏦",
    },
    {
        "id": "FOOD",
        "name_en": "Food Safety Authority of Telangana",
        "name_te": "తెలంగాణ ఆహార భద్రతా సంస్థ",
        "name_hi": "तेलंगाना खाद्य सुरक्षा प्राधिकरण",
        "helpline": "1800-425-1125",
        "portal_url": "https://fssai.gov.in",
        "icon": "🍽️",
    },
]

# required_fields keys:
#   "location"       → text: area / colony / ward
#   "ward_number"    → text: ward / door number
#   "sc_number"      → text: service connection number
#   "wc_number"      → text: water connection number
#   "route_number"   → text: bus route number
#   "bus_stop"       → text: bus stop name
#   "aadhar_last4"   → text (4 digits): last 4 of Aadhaar
#   "description"    → textarea: problem details

_COMPLAINTS = [
    # ── GHMC ──────────────────────────────────────────────────────────────
    {
        "dept_id": "GHMC",
        "category_en": "Pothole / Road Damage",
        "category_te": "గుంత / రోడ్డు నష్టం",
        "category_hi": "गड्ढा / सड़क क्षति",
        "keywords_en": "pothole,road,damage,broken,street,tarmac,asphalt,footpath,pavement,sidewalk",
        "keywords_te": "గుంత,రోడ్డు,నష్టం,వీధి,పాద మార్గం,రహదారి,తెగిపోయింది",
        "keywords_hi": "गड्ढा,सड़क,क्षति,टूटी,फुटपाथ,रास्ता,खराब",
        "required_fields": json.dumps(["location", "ward_number", "description"]),
    },
    {
        "dept_id": "GHMC",
        "category_en": "Garbage / Waste Not Collected",
        "category_te": "చెత్త తీయలేదు",
        "category_hi": "कचरा नहीं उठाया",
        "keywords_en": "garbage,trash,waste,rubbish,dump,litter,dustbin,sanitation,smell,stench",
        "keywords_te": "చెత్త,వ్యర్థాలు,డంప్,దుర్గంధం,చెత్త బుట్ట,పారిశుధ్యం",
        "keywords_hi": "कचरा,कूड़ा,गंदगी,बदबू,सफाई,डस्टबिन,सड़ांध",
        "required_fields": json.dumps(["location", "description"]),
    },
    {
        "dept_id": "GHMC",
        "category_en": "Drainage / Sewage Overflow",
        "category_te": "మురుగు నీరు నిండుట",
        "category_hi": "नाली / सीवर ओवरफ्लो",
        "keywords_en": "drainage,drain,sewage,overflow,flooding,stagnant,waterlogging,nala",
        "keywords_te": "మురుగు,డ్రెయిన్,వరదలు,నీరు నిలవడం,కాలువ",
        "keywords_hi": "नाली,सीवर,बाढ़,जलजमाव,ओवरफ्लो,नाला",
        "required_fields": json.dumps(["location", "ward_number", "description"]),
    },
    {
        "dept_id": "GHMC",
        "category_en": "Street Light Not Working",
        "category_te": "వీధి దీపం పని చేయటం లేదు",
        "category_hi": "स्ट्रीट लाइट काम नहीं कर रही",
        "keywords_en": "street light,streetlight,lamp,dark,no light,pole light,lighting",
        "keywords_te": "వీధి దీపం,లైటు,చీకటి,కాంతి లేదు",
        "keywords_hi": "स्ट्रीट लाइट,खंभा,अंधेरा,लाइट नहीं,बल्ब",
        "required_fields": json.dumps(["location", "ward_number", "description"]),
    },
    # ── TSSPDCL ───────────────────────────────────────────────────────────
    {
        "dept_id": "TSSPDCL",
        "category_en": "Power Cut / Outage",
        "category_te": "కరెంట్ పోయింది",
        "category_hi": "बिजली कटौती",
        "keywords_en": "power cut,outage,no electricity,blackout,load shedding,no power,electricity gone",
        "keywords_te": "కరెంట్,విద్యుత్,లైటు పోయింది,అవుటేజ్,పవర్ కట్",
        "keywords_hi": "बिजली,करंट,कटौती,आउटेज,बिजली नहीं,पावर",
        "required_fields": json.dumps(["sc_number", "location", "description"]),
    },
    {
        "dept_id": "TSSPDCL",
        "category_en": "Transformer Fault",
        "category_te": "ట్రాన్స్‌ఫార్మర్ పాడైంది",
        "category_hi": "ट्रांसफार्मर खराब",
        "keywords_en": "transformer,blown,burnt,exploded,substation,electrical fault",
        "keywords_te": "ట్రాన్స్‌ఫార్మర్,పాడైంది,కాలిపోయింది,సబ్‌స్టేషన్",
        "keywords_hi": "ट्रांसफार्मर,खराब,जला,सबस्टेशन,फॉल्ट",
        "required_fields": json.dumps(["sc_number", "location", "description"]),
    },
    {
        "dept_id": "TSSPDCL",
        "category_en": "Electricity Bill Dispute",
        "category_te": "కరెంట్ బిల్లు వివాదం",
        "category_hi": "बिजली बिल विवाद",
        "keywords_en": "electricity bill,high bill,wrong bill,billing error,meter reading,overcharge",
        "keywords_te": "కరెంట్ బిల్లు,అధిక బిల్లు,మీటర్ రీడింగ్,బిల్లు తప్పు",
        "keywords_hi": "बिजली बिल,ज्यादा बिल,मीटर,बिलिंग,गलत बिल",
        "required_fields": json.dumps(["sc_number", "aadhar_last4", "description"]),
    },
    # ── HMWSSB ────────────────────────────────────────────────────────────
    {
        "dept_id": "HMWSSB",
        "category_en": "No Water Supply",
        "category_te": "నీళ్ళు రావడం లేదు",
        "category_hi": "पानी की आपूर्ति नहीं",
        "keywords_en": "no water,water supply,water not coming,tap dry,pipeline,water shortage",
        "keywords_te": "నీళ్ళు,సరఫరా,నీళ్ళు రావట్లేదు,పైపులైన్,కొళాయి",
        "keywords_hi": "पानी नहीं,जल आपूर्ति,नल बंद,पाइपलाइन,पानी की कमी",
        "required_fields": json.dumps(["wc_number", "location", "description"]),
    },
    {
        "dept_id": "HMWSSB",
        "category_en": "Pipe Burst / Water Leakage",
        "category_te": "పైపు పగిలింది / నీళ్ళు లీకేజీ",
        "category_hi": "पाइप फटना / पानी का रिसाव",
        "keywords_en": "pipe burst,leakage,leak,broken pipe,water leak,flooding road,water waste",
        "keywords_te": "పైపు,పగిలింది,లీకేజీ,నీళ్ళు వృథా,వరదలు",
        "keywords_hi": "पाइप,फटा,रिसाव,लीकेज,पानी बर्बाद,बाढ़",
        "required_fields": json.dumps(["wc_number", "location", "description"]),
    },
    {
        "dept_id": "HMWSSB",
        "category_en": "Contaminated / Dirty Water",
        "category_te": "మురికి నీళ్ళు",
        "category_hi": "गंदा / दूषित पानी",
        "keywords_en": "dirty water,contaminated,muddy,smelly water,unclean,polluted water",
        "keywords_te": "మురికి నీళ్ళు,కలుషిత,వాసన,అపరిశుభ్రమైన",
        "keywords_hi": "गंदा पानी,दूषित,बदबूदार,मटमैला,प्रदूषित",
        "required_fields": json.dumps(["wc_number", "location", "description"]),
    },
    # ── TSRTC ─────────────────────────────────────────────────────────────
    {
        "dept_id": "TSRTC",
        "category_en": "Bus Not on Route / Missed",
        "category_te": "బస్సు రాలేదు",
        "category_hi": "बस नहीं आई",
        "keywords_en": "bus,no bus,bus not coming,route,missed bus,bus late,frequency",
        "keywords_te": "బస్సు,రూట్,బస్సు రాలేదు,ఆలస్యం",
        "keywords_hi": "बस,रूट,बस नहीं आई,देरी,बस लेट",
        "required_fields": json.dumps(["route_number", "bus_stop", "description"]),
    },
    {
        "dept_id": "TSRTC",
        "category_en": "Driver / Conductor Misconduct",
        "category_te": "డ్రైవర్ / కండక్టర్ దుర్వినియోగం",
        "category_hi": "चालक / कंडक्टर का दुर्व्यवहार",
        "keywords_en": "driver,conductor,rash driving,misbehavior,rude,abusive,overcharge ticket",
        "keywords_te": "డ్రైవర్,కండక్టర్,దుర్వర్తన,మొరటుగా,అతి వేగం",
        "keywords_hi": "चालक,कंडक्टर,दुर्व्यवहार,बदतमीजी,तेज गाड़ी",
        "required_fields": json.dumps(["route_number", "bus_stop", "aadhar_last4", "description"]),
    },
    {
        "dept_id": "TSRTC",
        "category_en": "Bus Stop Damaged / Missing",
        "category_te": "బస్ స్టాప్ పాడైంది",
        "category_hi": "बस स्टॉप टूटा / नहीं है",
        "keywords_en": "bus stop,shelter,broken,no shelter,damaged stop,missing stop",
        "keywords_te": "బస్ స్టాప్,షెల్టర్,పాడైంది,లేదు",
        "keywords_hi": "बस स्टॉप,शेल्टर,टूटा,नहीं है",
        "required_fields": json.dumps(["route_number", "bus_stop", "description"]),
    },
    # ── TSPSC ─────────────────────────────────────────────────────────────
    {
        "dept_id": "TSPSC",
        "category_en": "Hall Ticket / Admit Card Issue",
        "category_te": "హాల్ టికెట్ సమస్య",
        "category_hi": "हॉल टिकट / एडमिट कार्ड समस्या",
        "keywords_en": "hall ticket,admit card,exam,not received,download,tspsc exam,certificate",
        "keywords_te": "హాల్ టికెట్,పరీక్ష,అడ్మిట్ కార్డ్,డౌన్లోడ్,అందలేదు",
        "keywords_hi": "हॉल टिकट,एडमिट कार्ड,परीक्षा,नहीं मिला,डाउनलोड",
        "required_fields": json.dumps(["aadhar_last4", "description"]),
    },
    {
        "dept_id": "TSPSC",
        "category_en": "Result / Merit List Dispute",
        "category_te": "ఫలితాల వివాదం",
        "category_hi": "परिणाम / मेरिट सूची विवाद",
        "keywords_en": "result,merit list,marks,rank,wrong result,objection,answer key",
        "keywords_te": "ఫలితాలు,మెరిట్ లిస్ట్,మార్కులు,ర్యాంక్,తప్పు",
        "keywords_hi": "परिणाम,मेरिट,अंक,रैंक,गलत,आपत्ति",
        "required_fields": json.dumps(["aadhar_last4", "description"]),
    },
    # ── DLTC ──────────────────────────────────────────────────────────────
    {
        "dept_id": "DLTC",
        "category_en": "Wage Theft / Unpaid Salary",
        "category_te": "జీతం చెల్లించలేదు",
        "category_hi": "वेतन चोरी / बकाया वेतन",
        "keywords_en": "salary,wage,unpaid,not paid,labour,dues,employer,payslip",
        "keywords_te": "జీతం,వేతనం,చెల్లించలేదు,కార్మికుడు,యజమాని",
        "keywords_hi": "वेतन,तनख्वाह,नहीं मिला,मजदूरी,नियोक्ता",
        "required_fields": json.dumps(["aadhar_last4", "description"]),
    },
    {
        "dept_id": "DLTC",
        "category_en": "PF / ESI Dispute",
        "category_te": "పీఎఫ్ / ఈఎస్‌ఐ వివాదం",
        "category_hi": "पीएफ / ईएसआई विवाद",
        "keywords_en": "pf,provident fund,epf,esi,esic,deduction,not deposited",
        "keywords_te": "పీఎఫ్,ప్రావిడెంట్ ఫండ్,ఈఎస్‌ఐ,కోత",
        "keywords_hi": "पीएफ,भविष्य निधि,ईएसआई,कटौती,जमा नहीं",
        "required_fields": json.dumps(["aadhar_last4", "description"]),
    },
    # ── TGPSC ─────────────────────────────────────────────────────────────
    {
        "dept_id": "TGPSC",
        "category_en": "Pension Not Received",
        "category_te": "పెన్షన్ రాలేదు",
        "category_hi": "पेंशन नहीं मिली",
        "keywords_en": "pension,old age,widow,disability,not received,delay,pension amount",
        "keywords_te": "పెన్షన్,వృద్ధాప్యం,వితంతువు,వికలాంగులు,రాలేదు,జాప్యం",
        "keywords_hi": "पेंशन,बुढ़ापा,विधवा,विकलांग,नहीं मिली,देरी",
        "required_fields": json.dumps(["aadhar_last4", "description"]),
    },
    # ── FOOD ──────────────────────────────────────────────────────────────
    {
        "dept_id": "FOOD",
        "category_en": "Adulterated / Expired Food",
        "category_te": "కల్తీ / గడువు తీరిన ఆహారం",
        "category_hi": "मिलावटी / एक्सपायर्ड खाना",
        "keywords_en": "adulterated,expired,food,spoiled,contaminated food,fake,mislabeled",
        "keywords_te": "కల్తీ,ఆహారం,చెడిపోయింది,నకిలీ,గడువు",
        "keywords_hi": "मिलावट,खाना,एक्सपायर,खराब,नकली,लेबल",
        "required_fields": json.dumps(["location", "aadhar_last4", "description"]),
    },
    {
        "dept_id": "FOOD",
        "category_en": "Restaurant / Hotel Hygiene",
        "category_te": "హోటల్ పరిశుభ్రత సమస్య",
        "category_hi": "रेस्तरां / होटल स्वच्छता",
        "keywords_en": "restaurant,hotel,hygiene,dirty,cockroach,flies,unhygienic,kitchen",
        "keywords_te": "హోటల్,రెస్టారెంట్,పరిశుభ్రత,బొద్దింక,ఈగలు,అపరిశుభ్రమైన",
        "keywords_hi": "रेस्तरां,होटल,स्वच्छता,गंदगी,कॉकरोच,मक्खी",
        "required_fields": json.dumps(["location", "aadhar_last4", "description"]),
    },
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db():
    """Supabase tables are managed externally."""
    pass


def _seed(conn: sqlite3.Connection) -> None:
    conn.executemany(
        """INSERT OR IGNORE INTO departments
           (id, name_en, name_te, name_hi, helpline, portal_url, icon)
           VALUES (:id, :name_en, :name_te, :name_hi, :helpline, :portal_url, :icon)""",
        _DEPARTMENTS,
    )
    conn.executemany(
        """INSERT INTO complaints
           (dept_id, category_en, category_te, category_hi,
            keywords_en, keywords_te, keywords_hi, required_fields)
           VALUES (:dept_id, :category_en, :category_te, :category_hi,
                   :keywords_en, :keywords_te, :keywords_hi, :required_fields)""",
        _COMPLAINTS,
    )


def _stem(word: str) -> str:
    """
    Minimal English stemmer: strips common suffixes so that
    'potholes' matches 'pothole', 'leaking' matches 'leak', etc.
    Also works as a no-op for Telugu/Hindi (non-ASCII passes through).
    """
    if not word.isascii():
        return word
    for suffix in ("ing", "tion", "ed", "es", "s", "er", "ly"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


# ---------------------------------------------------------------------------
# Private-issue detection
# Each entry: keywords that signal a PRIVATE problem (not government's job),
# plus advice on who to actually contact.
# ---------------------------------------------------------------------------

_PRIVATE_ISSUES = [
    {
        "keywords_en": ["my house", "my home", "my flat", "my apartment", "my room",
                        "inside house", "inside home", "indoor", "internal", "my bathroom",
                        "my kitchen", "my wall", "my roof", "my tap", "my pipe",
                        "my wiring", "my meter box", "my socket", "my switch"],
        "keywords_te": ["మా ఇంట్లో", "నా ఇంట్లో", "ఇంటి లోపల", "మా ఇల్లు", "నా ఇల్లు",
                        "మా బాత్రూమ్", "మా కిచెన్", "నా గది"],
        "keywords_hi": ["मेरे घर", "मेरे मकान", "मेरे फ्लैट", "घर के अंदर",
                        "अंदर की", "मेरे बाथरूम", "मेरी रसोई", "मेरे कमरे"],
        "issue_en":   "leakage,pipe,tap,water,seepage,damp,wet,dripping",
        "issue_te":   "లీకేజీ,పైపు,కొళాయి,నీళ్ళు,తేమ,లీక్",
        "issue_hi":   "रिसाव,पाइप,नल,पानी,सीलन,गीला",
        "advice": {
            "en": {
                "title":   "This looks like a private plumbing issue",
                "body":    "Leakage or pipe problems **inside your home** are the responsibility of the building owner, not the government. HMWSSB only handles leaks on public water mains and street pipelines.",
                "actions": [
                    ("🔧", "Call a licensed plumber",          "Search 'plumber near me' on Google Maps or JustDial"),
                    ("🏢", "Contact your landlord / builder",  "If renting, your landlord is legally responsible for internal plumbing"),
                    ("💧", "Contact HMWSSB only if…",         "The leak is from the public pipe on the street, or your water connection meter is faulty"),
                ],
                "helpline_label": "HMWSSB (public mains only)",
                "helpline":       "155313",
                "portal":         "https://hmwssb.gov.in",
            },
            "te": {
                "title":   "ఇది వ్యక్తిగత ప్లంబింగ్ సమస్య అని కనిపిస్తోంది",
                "body":    "మీ **ఇంటి లోపల** నీళ్ళ లీకేజీ లేదా పైపు సమస్య భవన యజమాని బాధ్యత — ప్రభుత్వం కాదు. HMWSSB వీధిలోని పబ్లిక్ పైపులైన్ సమస్యలు మాత్రమే పరిష్కరిస్తుంది.",
                "actions": [
                    ("🔧", "లైసెన్స్ పొందిన ప్లంబర్‌ను పిలవండి", "Google Maps లేదా JustDial లో 'plumber near me' వెతకండి"),
                    ("🏢", "మీ యజమాని / బిల్డర్‌ని సంప్రదించండి", "అద్దెకు ఉంటే, అంతర్గత పైప్ లైన్ యజమాని బాధ్యత"),
                    ("💧", "HMWSSB ని మాత్రమే సంప్రదించండి…",      "వీధిలో పబ్లిక్ పైపు నుండి లీకేజీ అయితే లేదా మీటర్ లోపం అయితే"),
                ],
                "helpline_label": "HMWSSB (పబ్లిక్ పైపులైన్ మాత్రమే)",
                "helpline":       "155313",
                "portal":         "https://hmwssb.gov.in",
            },
            "hi": {
                "title":   "यह एक निजी प्लंबिंग समस्या लगती है",
                "body":    "**घर के अंदर** पानी का रिसाव या पाइप की समस्या मकान मालिक की जिम्मेदारी है — सरकार की नहीं। HMWSSB केवल सड़क पर सार्वजनिक पाइपलाइन की समस्याएं देखती है।",
                "actions": [
                    ("🔧", "लाइसेंसी प्लंबर बुलाएं",         "Google Maps या JustDial पर 'plumber near me' खोजें"),
                    ("🏢", "मकान मालिक / बिल्डर से बात करें", "किराए पर रहते हैं तो अंदरूनी प्लंबिंग मालिक की जिम्मेदारी है"),
                    ("💧", "HMWSSB से तभी संपर्क करें जब…",   "सड़क पर सार्वजनिक पाइप से रिसाव हो, या मीटर में खराबी हो"),
                ],
                "helpline_label": "HMWSSB (सार्वजनिक पाइप मात्र)",
                "helpline":       "155313",
                "portal":         "https://hmwssb.gov.in",
            },
        },
    },
    {
        "keywords_en": ["my house", "my home", "my flat", "my apartment",
                        "inside house", "indoor", "internal", "my room"],
        "keywords_te": ["మా ఇంట్లో", "నా ఇంట్లో", "ఇంటి లోపల"],
        "keywords_hi": ["मेरे घर", "घर के अंदर", "अंदर की"],
        "issue_en":   "power cut,electricity,no power,no light,wiring,short circuit,trip,fuse",
        "issue_te":   "కరెంట్,విద్యుత్,లైటు,వైరింగ్,ట్రిప్",
        "issue_hi":   "बिजली,करंट,वायरिंग,शॉर्ट सर्किट,फ्यूज",
        "advice": {
            "en": {
                "title":   "This sounds like an internal electrical issue",
                "body":    "Electrical faults **inside your home** (wiring, switches, fuse box) are the responsibility of a licensed electrician or your building owner — not TSSPDCL. TSSPDCL handles street transformers and public supply lines.",
                "actions": [
                    ("⚡", "Call a licensed electrician",       "Search 'electrician near me' on Google Maps or JustDial"),
                    ("🏢", "Contact your landlord / builder",   "For rented property, internal wiring faults are the landlord's responsibility"),
                    ("🔌", "Contact TSSPDCL only if…",         "The entire street has no power, or the transformer/main line outside is faulty"),
                ],
                "helpline_label": "TSSPDCL (street/transformer faults only)",
                "helpline":       "1912",
                "portal":         "https://tssouthernpower.com",
            },
            "te": {
                "title":   "ఇది అంతర్గత విద్యుత్ సమస్య అని కనిపిస్తోంది",
                "body":    "మీ **ఇంటి లోపల** వైరింగ్, స్విచ్, ఫ్యూజ్ సమస్యలు లైసెన్స్ పొందిన ఎలక్ట్రీషియన్ లేదా యజమాని బాధ్యత — TSSPDCL కాదు.",
                "actions": [
                    ("⚡", "లైసెన్స్ పొందిన ఎలక్ట్రీషియన్‌ను పిలవండి", "Google Maps లో 'electrician near me' వెతకండి"),
                    ("🏢", "యజమాని / బిల్డర్‌ని సంప్రదించండి",           "అద్దె ఇంటికి అంతర్గత వైరింగ్ యజమాని బాధ్యత"),
                    ("🔌", "TSSPDCL ని మాత్రమే సంప్రదించండి…",           "మొత్తం వీధికి కరెంట్ లేకపోతే లేదా ట్రాన్స్‌ఫార్మర్ పాడైతే"),
                ],
                "helpline_label": "TSSPDCL (ట్రాన్స్‌ఫార్మర్ / వీధి మాత్రమే)",
                "helpline":       "1912",
                "portal":         "https://tssouthernpower.com",
            },
            "hi": {
                "title":   "यह घर की आंतरिक बिजली समस्या लगती है",
                "body":    "**घर के अंदर** वायरिंग, स्विच, फ्यूज की समस्या लाइसेंसी इलेक्ट्रीशियन या मकान मालिक की जिम्मेदारी है — TSSPDCL की नहीं।",
                "actions": [
                    ("⚡", "लाइसेंसी इलेक्ट्रीशियन बुलाएं",    "Google Maps पर 'electrician near me' खोजें"),
                    ("🏢", "मकान मालिक से बात करें",              "किराए की संपत्ति में अंदरूनी वायरिंग मालिक की जिम्मेदारी"),
                    ("🔌", "TSSPDCL से तभी संपर्क करें जब…",     "पूरी गली में बिजली न हो या बाहर ट्रांसफार्मर खराब हो"),
                ],
                "helpline_label": "TSSPDCL (ट्रांसफार्मर / सड़क मात्र)",
                "helpline":       "1912",
                "portal":         "https://tssouthernpower.com",
            },
        },
    },
]


def check_private_issue(query: str, lang: str = "en") -> dict | None:
    """
    Check if the query describes a private (non-government) issue.
    Returns an advice dict if matched, else None.

    Logic: query must contain BOTH a location-ownership signal
    (e.g. 'my house') AND a relevant issue keyword.
    """
    # For non-ASCII scripts, skip the punctuation-strip so Unicode is preserved
    if lang == "en":
        clean = re.sub(r"[^\w\s]", " ", query.lower())
    else:
        clean = query.lower()

    kw_key    = f"keywords_{lang}"
    issue_key = f"issue_{lang}"

    for entry in _PRIVATE_ISSUES:
        # Check location-ownership signal
        loc_keywords = entry.get(kw_key, [])
        has_location = any(kw in clean for kw in loc_keywords)
        if not has_location:
            continue

        # Check issue type keywords
        issue_kws = [k.strip() for k in entry.get(issue_key, "").split(",") if k.strip()]
        has_issue = any(kw in clean for kw in issue_kws)
        if not has_issue:
            continue

        return entry["advice"][lang]

    return None


def route_query(query: str, lang: str = "en") -> list[dict]:
    """
    Score all complaint rows against the search query using keyword overlap.

    Matching layers (each adds to the score):
      3 pts — exact keyword phrase found inside query string
      2 pts — stemmed query token matches stemmed keyword token
      1 pt  — query token is a substring of any keyword (catches typos/partials)

    Args:
        query: Raw user input string (any language).
        lang:  One of 'en', 'te', 'hi'.
    """
    if not query or not query.strip():
        return []

    # Normalise query
    clean = re.sub(r"[^\w\s]", " ", query.lower().strip())
    query_tokens = [t for t in clean.split() if len(t) >= 2]
    query_stemmed = {_stem(t) for t in query_tokens}
    query_joined = " ".join(query_tokens)   # for phrase matching

    # Stop-words to ignore (English only — location names, prepositions)
    stopwords = {
        "in", "at", "on", "the", "my", "a", "an", "is", "are", "not",
        "no", "i", "we", "have", "has", "there", "near", "here", "our",
        "this", "that", "and", "or", "of", "for", "to", "it"
    }
    query_tokens_filtered = [t for t in query_tokens if t not in stopwords]
    query_stemmed_filtered = {_stem(t) for t in query_tokens_filtered}

    kw_col = f"keywords_{lang}"
    cat_col = f"category_{lang}"

    complaints = supabase.table("complaints").select("*").execute().data
    departments = supabase.table("departments").select("*").execute().data

    dept_lookup = {d["id"]: d for d in departments}

    rows = []

    for c in complaints:
        dept = dept_lookup.get(c["dept_id"])
        if not dept: # skip if department info is missing
            continue

            import json
        rows.append({
            "id": c["id"],
            "dept_id": c["dept_id"],
            "category_en": c["category_en"],
            "category_local": c[cat_col],
            "keywords": c[kw_col],
            "required_fields": c["required_fields"],
            "name_en": dept["name_en"],
            "name_te": dept["name_te"],
            "name_hi": dept["name_hi"],
            "helpline": dept["helpline"],
            "portal_url": dept["portal_url"],
            "icon": dept["icon"],
        })

    results = []
    for row in rows:
        raw_kw = re.sub(r"[^\w\s,]", " ", row["keywords"].lower())
        # keyword phrases (comma-separated entries)
        kw_phrases = [p.strip() for p in raw_kw.split(",") if p.strip()]
        # individual keyword tokens
        kw_tokens_flat = set()
        for phrase in kw_phrases:
            kw_tokens_flat.update(phrase.split())
        kw_stemmed = {_stem(t) for t in kw_tokens_flat}

        score = 0

        # Layer 1: exact phrase match (highest confidence)
        for phrase in kw_phrases:
            if phrase and phrase in query_joined:
                score += 3

        # Layer 2: stemmed token overlap
        score += len(query_stemmed_filtered & kw_stemmed) * 2

        # Layer 3: substring match — query token appears inside any keyword
        for qt in query_tokens_filtered:
            if len(qt) >= 3:
                for kw in kw_tokens_flat:
                    if qt in kw or kw in qt:
                        score += 1
                        break

        if score > 0:
            results.append({
                "score": score,
                "complaint_id": row["id"],
                "dept_id": row["dept_id"],
                "category_en": row["category_en"],
                "category_local": row["category_local"],
                "required_fields": row["required_fields"],
                "dept_name_en": row["name_en"],
                "dept_name_te": row["name_te"],
                "dept_name_hi": row["name_hi"],
                "helpline": row["helpline"],
                "portal_url": row["portal_url"],
                "icon": row["icon"],
            })

    results.sort(key=lambda x: -x["score"])
    return results


def save_grievance(
    dept_id: str,
    category_en: str,
    fields: dict,
    language: str,
):
    result = (
        supabase.table("grievances")
        .insert({
            "dept_id": dept_id,
            "category_en": category_en,
            "fields_json": json.dumps(fields, ensure_ascii=False),
            "language": language,
        })
        .execute()
    )

    return result.data[0]["id"]


def get_grievance_history(limit=50):

    grievances = (
        supabase.table("grievances")
        .select("*")
        .order("id", desc=True)
        .limit(limit)
        .execute()
        .data
    )

    departments = (
        supabase.table("departments")
        .select("*")
        .execute()
        .data
    )

    dept_lookup = {
        d["id"]: d["name_en"]
        for d in departments
    }

    history = []

    for row in grievances:
        fields = json.loads(row["fields_json"])

        history.append({
            "ID": row["id"],
            "Submitted": row["created_at"],
            "Department": dept_lookup.get(
                row["dept_id"],
                row["dept_id"]
            ),
            "Category": row["category_en"],
            "Language": row["language"].upper(),
            "Details": ", ".join(
                f"{k}: {v}"
                for k, v in fields.items()
                if v
            ),
        })

    return history


def get_all_departments() -> list[dict]:
    """Return all department rows from Supabase."""
    result = supabase.table("departments").select("*").execute()
    return result.data

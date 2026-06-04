"""
app.py
======
Telangana Citizen Grievance Router — Streamlit UI

What this does:
  1. Citizen types their problem in English / Telugu / Hindi
  2. App routes to the correct department
  3. Shows: what to bring, official portal link, helpline
  4. Generates a ready-to-copy draft complaint letter

No form submission. No database writes. Pure information + draft generator.
Run with:  uv run streamlit run app.py
"""

import streamlit as st
from database import init_db, route_query, check_private_issue, get_all_departments

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Telangana Grievance Router",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ---------------------------------------------------------------------------
# CSS — Glassmorphic green/gold theme
# ---------------------------------------------------------------------------

def inject_css() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Telugu:wght@300;400;600;700&family=Noto+Sans:wght@300;400;600;700&display=swap');

    :root {
        --green-dark:   #0d2b17;
        --green-mid:    #1a472a;
        --green-light:  #2d6a4f;
        --gold:         #c9a84c;
        --gold-light:   #e8c96e;
        --glass-bg:     rgba(255,255,255,0.06);
        --glass-border: rgba(201,168,76,0.30);
        --text-primary: #f0ece0;
        --text-muted:   #b0aa94;
        --radius:       14px;
    }

    .stApp {
        background: linear-gradient(135deg, #0d2b17 0%, #1a3a28 45%, #0f2d1e 100%);
        font-family: 'Noto Sans', 'Noto Sans Telugu', sans-serif;
        color: var(--text-primary);
    }

    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1.5rem; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a2212 0%, #0d2b17 100%) !important;
        border-right: 1px solid var(--glass-border);
    }
    [data-testid="stSidebar"] * { color: var(--text-primary) !important; }

    .glass-card {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius);
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.2rem;
        backdrop-filter: blur(14px);
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    }

    .hero-banner {
        background: linear-gradient(135deg, rgba(201,168,76,0.15) 0%, rgba(45,106,79,0.20) 100%);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius);
        padding: 2rem 2.4rem 1.6rem;
        margin-bottom: 1.6rem;
        text-align: center;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: var(--gold-light);
        margin: 0 0 0.3rem;
    }
    .hero-sub { font-size: 1rem; color: var(--text-muted); margin: 0; }

    .dept-card {
        background: linear-gradient(135deg, rgba(201,168,76,0.12) 0%, rgba(26,71,42,0.25) 100%);
        border: 1.5px solid var(--gold);
        border-radius: var(--radius);
        padding: 1.4rem 1.8rem;
        margin-bottom: 1rem;
    }
    .dept-icon   { font-size: 2.4rem; margin-bottom: 0.4rem; }
    .dept-name   { font-size: 1.25rem; font-weight: 700; color: var(--gold-light); margin: 0 0 0.2rem; }
    .dept-cat    { font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.9rem; }
    .dept-meta   { display:flex; gap:1.4rem; flex-wrap:wrap; font-size:0.85rem; color:var(--text-muted); }
    .dept-meta a { color: var(--gold-light) !important; text-decoration: none; }
    .dept-meta a:hover { text-decoration: underline; }

    .badge {
        display: inline-block;
        background: rgba(201,168,76,0.18);
        border: 1px solid rgba(201,168,76,0.4);
        color: var(--gold-light);
        border-radius: 20px;
        padding: 2px 12px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 6px;
    }

    .section-heading {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--gold);
        margin-bottom: 0.7rem;
    }

    .checklist-item {
        display: flex;
        align-items: flex-start;
        gap: 0.7rem;
        padding: 0.6rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        font-size: 0.9rem;
        color: var(--text-primary);
    }
    .checklist-item:last-child { border-bottom: none; }
    .check-icon { color: var(--gold-light); font-size: 1rem; margin-top: 1px; min-width: 18px; }

    .draft-box {
        background: rgba(0,0,0,0.3);
        border: 1px solid var(--glass-border);
        border-radius: 10px;
        padding: 1.2rem 1.4rem;
        font-size: 0.88rem;
        line-height: 1.7;
        color: var(--text-primary);
        white-space: pre-wrap;
        font-family: 'Noto Sans', monospace;
    }

    .alt-row {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(201,168,76,0.15);
        border-radius: 10px;
        padding: 0.65rem 1rem;
        margin-bottom: 0.45rem;
        font-size: 0.85rem;
        color: var(--text-muted);
    }
    .alt-row strong { color: var(--gold-light); }

    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--gold) !important;
        box-shadow: 0 0 0 2px rgba(201,168,76,0.25) !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%);
        color: #0d2b17 !important;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 0.55rem 2rem;
        font-size: 0.95rem;
        width: 100%;
    }
    .stButton > button:hover { opacity: 0.88; }

    .private-card {
        background: linear-gradient(135deg, rgba(180,90,30,0.18) 0%, rgba(26,71,42,0.20) 100%);
        border: 1.5px solid #c97a3a;
        border-radius: var(--radius);
        padding: 1.4rem 1.8rem;
        margin-bottom: 1rem;
    }
    .private-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f0a955;
        margin-bottom: 0.5rem;
    }
    .private-body {
        font-size: 0.88rem;
        color: var(--text-muted);
        margin-bottom: 1rem;
        line-height: 1.6;
    }
    .action-row {
        display: flex;
        align-items: flex-start;
        gap: 0.8rem;
        padding: 0.65rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .action-row:last-child { border-bottom: none; }
    .action-icon { font-size: 1.2rem; min-width: 22px; }
    .action-label { font-weight: 600; color: #f0ece0; font-size: 0.88rem; }
    .action-sub   { font-size: 0.78rem; color: var(--text-muted); margin-top: 1px; }
    .govt-note {
        margin-top: 0.9rem;
        font-size: 0.78rem;
        color: #b0aa94;
        border-top: 1px solid rgba(255,255,255,0.07);
        padding-top: 0.7rem;
    }
    .govt-note a { color: #e8c96e !important; }

    .dir-row {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.45rem 0.2rem;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        font-size: 0.82rem;
    }
    .dir-code { font-weight: 700; color: var(--gold-light); min-width: 70px; }
    </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------

T = {
    "en": {
        "app_title":        "Telangana Citizen Grievance Router",
        "app_subtitle":     "Find the right department · Know what to bring · Get a draft complaint",
        "search_label":     "Describe your problem",
        "search_placeholder": "e.g.  pothole on my road,  power cut,  no water,  bus not coming...",
        "search_btn":       "🔍  Find Department",
        "no_match_title":   "No department matched",
        "no_match_body":    "Try different words. Examples: 'pothole', 'power cut', 'water leak', 'bus', 'pension', 'garbage'.",
        "dept_matched":     "Department Matched",
        "complaint_type":   "Complaint type",
        "helpline":         "Helpline",
        "portal":           "Official Portal",
        "what_to_bring":    "What to bring / have ready",
        "draft_heading":    "Draft Complaint — copy & paste this",
        "draft_tip":        "✏️  Fill in the blanks marked with [ ] before submitting.",
        "alt_matches":      "Other departments that might help",
        "sidebar_lang":     "Language",
        "sidebar_dir":      "Department Directory",
        "sidebar_tip":      "💡 How to use",
        "sidebar_tip_body": "Type your problem in any language. We'll find the right department and tell you exactly what to do next.",
    },
    "te": {
        "app_title":        "తెలంగాణ పౌర ఫిర్యాదు రౌటర్",
        "app_subtitle":     "సరైన శాఖ కనుగొనండి · ఏమి తీసుకెళ్ళాలో తెలుసుకోండి · ఫిర్యాదు ముసాయిదా పొందండి",
        "search_label":     "మీ సమస్యను వివరించండి",
        "search_placeholder": "ఉదా: రోడ్డు గుంత, కరెంట్ పోయింది, నీళ్ళు రావట్లేదు...",
        "search_btn":       "🔍  శాఖను కనుగొనండి",
        "no_match_title":   "సరిపోలిక కనుగొనబడలేదు",
        "no_match_body":    "వేరే మాటలు ప్రయత్నించండి: 'గుంత', 'కరెంట్', 'నీళ్ళు', 'బస్సు', 'పెన్షన్'.",
        "dept_matched":     "శాఖ సరిపోలింది",
        "complaint_type":   "ఫిర్యాదు రకం",
        "helpline":         "హెల్ప్‌లైన్",
        "portal":           "అధికారిక పోర్టల్",
        "what_to_bring":    "తీసుకెళ్ళాల్సిన పత్రాలు / సమాచారం",
        "draft_heading":    "ఫిర్యాదు ముసాయిదా — కాపీ చేసి సమర్పించండి",
        "draft_tip":        "✏️  సమర్పించే ముందు [ ] గుర్తున్న ఖాళీలు పూరించండి.",
        "alt_matches":      "సహాయపడగల ఇతర శాఖలు",
        "sidebar_lang":     "భాష",
        "sidebar_dir":      "శాఖల డైరెక్టరీ",
        "sidebar_tip":      "💡 వినియోగం",
        "sidebar_tip_body": "ఏ భాషలో అయినా మీ సమస్యను టైప్ చేయండి. మేము సరైన శాఖను కనుగొని తదుపరి చేయవలసిన పనిని చెప్తాం.",
    },
    "hi": {
        "app_title":        "तेलंगाना नागरिक शिकायत राउटर",
        "app_subtitle":     "सही विभाग खोजें · क्या लाना है जानें · शिकायत का मसौदा पाएं",
        "search_label":     "अपनी समस्या बताएं",
        "search_placeholder": "जैसे: सड़क में गड्ढा, बिजली नहीं, पानी नहीं, बस नहीं आई...",
        "search_btn":       "🔍  विभाग खोजें",
        "no_match_title":   "कोई विभाग नहीं मिला",
        "no_match_body":    "अलग शब्द आज़माएं: 'गड्ढा', 'बिजली', 'पानी', 'बस', 'पेंशन', 'कचरा'।",
        "dept_matched":     "विभाग मिला",
        "complaint_type":   "शिकायत प्रकार",
        "helpline":         "हेल्पलाइन",
        "portal":           "आधिकारिक पोर्टल",
        "what_to_bring":    "क्या लाएं / क्या तैयार रखें",
        "draft_heading":    "शिकायत का मसौदा — कॉपी करके जमा करें",
        "draft_tip":        "✏️  जमा करने से पहले [ ] वाली जगहें भरें।",
        "alt_matches":      "अन्य संभावित विभाग",
        "sidebar_lang":     "भाषा",
        "sidebar_dir":      "विभाग निर्देशिका",
        "sidebar_tip":      "💡 कैसे उपयोग करें",
        "sidebar_tip_body": "किसी भी भाषा में अपनी समस्या टाइप करें। हम सही विभाग और अगला कदम बताएंगे।",
    },
}

LANG_OPTIONS = {"English": "en", "తెలుగు": "te", "हिंदी": "hi"}


# ---------------------------------------------------------------------------
# What-to-bring checklist  (keyed by required_field id from DB)
# ---------------------------------------------------------------------------

FIELD_INFO = {
    "en": {
        "location":     "Your full address / colony / locality name",
        "ward_number":  "Ward number or door number (check your property tax receipt)",
        "sc_number":    "Service Connection Number (on your electricity bill)",
        "wc_number":    "Water Connection Number (on your water bill)",
        "route_number": "Bus route number (shown on the bus or bus stop board)",
        "bus_stop":     "Nearest bus stop name",
        "aadhar_last4": "Aadhaar card (last 4 digits needed for verification)",
        "description":  "Clear description of the problem with date it started",
    },
    "te": {
        "location":     "మీ పూర్తి చిరునామా / కాలనీ పేరు",
        "ward_number":  "వార్డు నంబర్ లేదా ఇంటి నంబర్ (ఆస్తి పన్ను రసీదు చూడండి)",
        "sc_number":    "సర్వీస్ కనెక్షన్ నంబర్ (కరెంట్ బిల్లు పై ఉంటుంది)",
        "wc_number":    "వాటర్ కనెక్షన్ నంబర్ (నీళ్ళ బిల్లు పై ఉంటుంది)",
        "route_number": "బస్సు రూట్ నంబర్ (బస్సుపై లేదా స్టాప్ బోర్డుపై చూడండి)",
        "bus_stop":     "సమీప బస్ స్టాప్ పేరు",
        "aadhar_last4": "ఆధార్ కార్డు (ధృవీకరణకు చివరి 4 అంకెలు అవసరం)",
        "description":  "సమస్య ప్రారంభమైన తేదీతో స్పష్టమైన వివరణ",
    },
    "hi": {
        "location":     "आपका पूरा पता / कॉलोनी / मोहल्ले का नाम",
        "ward_number":  "वार्ड नंबर या घर नंबर (संपत्ति कर रसीद देखें)",
        "sc_number":    "सेवा कनेक्शन नंबर (बिजली बिल पर होता है)",
        "wc_number":    "जल कनेक्शन नंबर (पानी के बिल पर होता है)",
        "route_number": "बस रूट नंबर (बस पर या बस स्टॉप बोर्ड पर देखें)",
        "bus_stop":     "नज़दीकी बस स्टॉप का नाम",
        "aadhar_last4": "आधार कार्ड (सत्यापन के लिए अंतिम 4 अंक)",
        "description":  "समस्या कब शुरू हुई — स्पष्ट विवरण के साथ",
    },
}

FIELD_ICONS = {
    "location":     "📍",
    "ward_number":  "🏠",
    "sc_number":    "⚡",
    "wc_number":    "💧",
    "route_number": "🚌",
    "bus_stop":     "🛑",
    "aadhar_last4": "🪪",
    "description":  "📝",
}


# ---------------------------------------------------------------------------
# Draft complaint generator
# ---------------------------------------------------------------------------

DRAFT_TEMPLATES = {
    "en": """\
To,
The {dept_name},
Telangana Government

Subject: Complaint regarding {category} — {location_hint}

Respected Sir/Madam,

I, [Your Full Name], residing at [Your Full Address, Colony, Hyderabad — PIN],
wish to bring to your kind attention the following issue:

Problem: {category}
Location of issue: [Street / Area / Colony name]
Date the problem started: [DD/MM/YYYY]
Details: [Describe the problem clearly in 2–3 sentences]

I kindly request you to take immediate action to resolve this issue at the earliest.

Thanking you,

[Your Full Name]
[Your Mobile Number]
[Your Email Address (optional)]
[Date: {today}]

Reference documents to attach:
{docs_hint}
""",
    "te": """\
సేవలో,
{dept_name},
తెలంగాణ ప్రభుత్వం

విషయం: {category} — {location_hint} కు సంబంధించిన ఫిర్యాదు

అయ్యా/అమ్మా,

నేను [మీ పూర్తి పేరు], [మీ పూర్తి చిరునామా, కాలనీ, హైదరాబాద్ — పిన్]లో నివసిస్తున్నాను.
క్రింది సమస్యను మీ దృష్టికి తీసుకొస్తున్నాను:

సమస్య: {category}
సమస్య ఉన్న ప్రదేశం: [వీధి / ప్రాంతం / కాలనీ పేరు]
సమస్య ప్రారంభమైన తేదీ: [DD/MM/YYYY]
వివరాలు: [సమస్యను స్పష్టంగా 2–3 వాక్యాల్లో వివరించండి]

వీలైనంత త్వరగా చర్యలు తీసుకోవాలని మనవి చేసుకుంటున్నాను.

మీ విశ్వాసపాత్రుడు/విశ్వాసపాత్రురాలు,

[మీ పూర్తి పేరు]
[మీ మొబైల్ నంబర్]
[తేదీ: {today}]

జత చేయవలసిన పత్రాలు:
{docs_hint}
""",
    "hi": """\
सेवा में,
{dept_name},
तेलंगाना सरकार

विषय: {category} — {location_hint} के संबंध में शिकायत

महोदय/महोदया,

मैं [आपका पूरा नाम], [पूरा पता, कॉलोनी, हैदराबाद — पिन] का निवासी हूँ।
निम्नलिखित समस्या आपके संज्ञान में लाना चाहता/चाहती हूँ:

समस्या: {category}
समस्या का स्थान: [गली / क्षेत्र / कॉलोनी का नाम]
समस्या शुरू होने की तारीख: [DD/MM/YYYY]
विवरण: [2–3 वाक्यों में स्पष्ट रूप से समस्या बताएं]

कृपया जल्द से जल्द आवश्यक कार्रवाई करें।

आपका/आपकी विश्वासपात्र,

[आपका पूरा नाम]
[आपका मोबाइल नंबर]
[तारीख: {today}]

संलग्न दस्तावेज़:
{docs_hint}
""",
}


def build_draft(result: dict, lang: str) -> str:
    from datetime import date

    dept_name_key = f"dept_name_{lang}"
    dept_name = result[dept_name_key]
    category  = result["category_local"]

    # Build docs hint from required fields
    field_info = FIELD_INFO[lang]
    docs_list  = []
    for f in result["required_fields"]:
        if f != "description":
            docs_list.append(f"  • {field_info.get(f, f)}")
    docs_hint = "\n".join(docs_list) if docs_list else "  • Photo of the problem (if applicable)"

    template = DRAFT_TEMPLATES[lang]
    return template.format(
        dept_name     = dept_name,
        category      = category,
        location_hint = "[Your Area]",
        today         = date.today().strftime("%d/%m/%Y"),
        docs_hint     = docs_hint,
    )


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def _init_session() -> None:
    for k, v in {
        "lang": "en",
        "search_query": "",
        "matched_results": [],
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar() -> None:
    t = T[st.session_state["lang"]]
    with st.sidebar:
        st.markdown("""
            <div style="text-align:center; padding:1rem 0 1.4rem;">
                <div style="font-size:2.8rem;">🏛️</div>
                <div style="font-size:1rem; font-weight:700; color:#e8c96e; margin-top:0.3rem;">Telangana Gov</div>
                <div style="font-size:0.72rem; color:#b0aa94;">Grievance Router</div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f'<div class="section-heading">{t["sidebar_lang"]}</div>', unsafe_allow_html=True)
        lang_pick = st.radio("lang", list(LANG_OPTIONS.keys()),
                             index=list(LANG_OPTIONS.values()).index(st.session_state["lang"]),
                             label_visibility="collapsed")
        st.session_state["lang"] = LANG_OPTIONS[lang_pick]

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(f'<div class="section-heading">{t["sidebar_dir"]}</div>', unsafe_allow_html=True)

        lang = st.session_state["lang"]
        for dept in get_all_departments():
            st.markdown(
                f'<div class="dir-row"><span class="dir-code">{dept["icon"]} {dept["id"]}</span>'
                f'<span style="color:#c8c2ae;">{dept[f"name_{lang}"]}</span></div>',
                unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            f'<div class="glass-card" style="font-size:0.82rem;">'
            f'<strong style="color:#e8c96e;">{t["sidebar_tip"]}</strong><br>'
            f'<span style="color:#b0aa94;">{t["sidebar_tip_body"]}</span></div>',
            unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

def render_hero(t: dict) -> None:
    lang = st.session_state["lang"]
    tag  = {"en": "English · తెలుగు · हिंदी", "te": "ఇంగ్లీష్ · తెలుగు · హిందీ", "hi": "अंग्रेजी · तेलुगु · हिंदी"}[lang]
    st.markdown(
        f'<div class="hero-banner">'
        f'<div class="hero-title">🏛️ {t["app_title"]}</div>'
        f'<div class="hero-sub">{t["app_subtitle"]}</div>'
        f'<div style="margin-top:0.6rem;font-size:0.78rem;color:#c9a84c;letter-spacing:1px;">{tag}</div>'
        f'</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def render_search(t: dict) -> None:
    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input(t["search_label"], value=st.session_state["search_query"],
                              placeholder=t["search_placeholder"], key="search_input")
    with col2:
        st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
        clicked = st.button(t["search_btn"], key="search_btn")

    if clicked or (query and query != st.session_state["search_query"]):
        st.session_state["search_query"]   = query
        st.session_state["matched_results"] = route_query(query, st.session_state["lang"])


# ---------------------------------------------------------------------------
# Department card
# ---------------------------------------------------------------------------

def render_dept_card(result: dict, t: dict) -> None:
    lang      = st.session_state["lang"]
    dept_name = result[f"dept_name_{lang}"]
    st.markdown(
        f'<div class="dept-card">'
        f'<div class="dept-icon">{result["icon"]}</div>'
        f'<div class="dept-name">{dept_name}</div>'
        f'<div class="dept-cat"><span class="badge">{t["complaint_type"]}</span>{result["category_local"]}</div>'
        f'<div class="dept-meta">'
        f'<span>📞 {t["helpline"]}: <strong>{result["helpline"]}</strong></span>'
        f'<span>🌐 <a href="{result["portal_url"]}" target="_blank">{t["portal"]} ↗</a></span>'
        f'</div></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# What to bring checklist
# ---------------------------------------------------------------------------

def render_checklist(result: dict, t: dict) -> None:
    lang       = st.session_state["lang"]
    field_info = FIELD_INFO[lang]

    st.markdown(f'<div class="section-heading" style="margin-top:1.2rem;">{t["what_to_bring"]}</div>',
                unsafe_allow_html=True)

    items_html = ""
    for field_id in result["required_fields"]:
        icon  = FIELD_ICONS.get(field_id, "📌")
        label = field_info.get(field_id, field_id.replace("_", " ").title())
        items_html += (
            f'<div class="checklist-item">'
            f'<span class="check-icon">{icon}</span>'
            f'<span>{label}</span>'
            f'</div>'
        )

    st.markdown(f'<div class="glass-card">{items_html}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Draft complaint
# ---------------------------------------------------------------------------

def render_draft(result: dict, t: dict) -> None:
    lang  = st.session_state["lang"]
    draft = build_draft(result, lang)

    st.markdown(f'<div class="section-heading" style="margin-top:1.2rem;">{t["draft_heading"]}</div>',
                unsafe_allow_html=True)
    st.info(t["draft_tip"])
    st.text_area("draft_area", value=draft, height=380, label_visibility="collapsed")


# ---------------------------------------------------------------------------
# Alternate matches
# ---------------------------------------------------------------------------

def render_alts(results: list[dict], t: dict) -> None:
    if len(results) <= 1:
        return
    lang = st.session_state["lang"]
    st.markdown(f'<div class="section-heading" style="margin-top:1.4rem;">{t["alt_matches"]}</div>',
                unsafe_allow_html=True)
    for res in results[1:5]:
        st.markdown(
            f'<div class="alt-row">{res["icon"]} <strong>{res[f"dept_name_{lang}"]}</strong>'
            f' — {res["category_local"]}'
            f' &nbsp;|&nbsp; 📞 {res["helpline"]}'
            f' &nbsp;|&nbsp; <a href="{res["portal_url"]}" target="_blank" style="color:#e8c96e;">Portal ↗</a>'
            f'</div>', unsafe_allow_html=True)


def render_private_issue(advice: dict) -> None:
    """Render the friendly 'not a government issue' advisory card."""
    import re as _re

    # Convert **bold** markdown in body to <strong> for HTML rendering
    body_html = _re.sub(r"\*\*(.+?)\*\*", r"<strong style='color:#f0a955;'>\1</strong>", advice["body"])

    actions_html = ""
    for icon, label, sub in advice["actions"]:
        actions_html += (
            f'<div class="action-row">'
            f'<span class="action-icon">{icon}</span>'
            f'<div><div class="action-label">{label}</div>'
            f'<div class="action-sub">{sub}</div></div>'
            f'</div>'
        )

    govt_note = (
        f'If you do need to contact the government department: '
        f'📞 <strong>{advice["helpline_label"]}</strong>: {advice["helpline"]} &nbsp;|&nbsp; '
        f'<a href="{advice["portal"]}" target="_blank">Official Portal ↗</a>'
    )

    st.markdown(
        f'<div class="private-card">'
        f'<div class="private-title">⚠️ {advice["title"]}</div>'
        f'<div class="private-body">{body_html}</div>'
        f'{actions_html}'
        f'<div class="govt-note">{govt_note}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    _init_session()
    inject_css()
    render_sidebar()

    t = T[st.session_state["lang"]]

    render_hero(t)
    render_search(t)

    results: list[dict] = st.session_state.get("matched_results", [])
    query:   str        = st.session_state.get("search_query", "")

    if query and not results:
        st.markdown(
            f'<div class="glass-card">'
            f'<strong style="color:#e8c96e;">🔍 {t["no_match_title"]}</strong><br>'
            f'<span style="color:#b0aa94;">{t["no_match_body"]}</span>'
            f'</div>', unsafe_allow_html=True)

    if results:
        # Check if this is actually a private issue before showing dept card
        private = check_private_issue(query, st.session_state["lang"])

        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            if private:
                st.markdown(f'<div class="section-heading">⚠️ BEFORE YOU CONTACT THE GOVERNMENT</div>',
                            unsafe_allow_html=True)
                render_private_issue(private)
            else:
                top = results[0]
                st.markdown(f'<div class="section-heading">{t["dept_matched"]}</div>',
                            unsafe_allow_html=True)
                render_dept_card(top, t)
                render_checklist(top, t)
                render_alts(results, t)

        with col_right:
            top = results[0]
            render_draft(top, t)


if __name__ == "__main__":
    main()

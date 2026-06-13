"""
Pratham Education Foundation — Impact Dashboard (Demo)
NSS Open Projects 2026 · Challenge 5.1

Backend: SQLite (dev) / PostgreSQL (prod) / Google Sheets (live field data)
To rebuild DB:   python setup_db.py
To connect Sheets: see sheets_connector.py
"""

from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sqlalchemy
from dash import Dash, Input, Output, State, callback, dcc, html
import dash_bootstrap_components as dbc
from dotenv import load_dotenv
import os

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────────────────────
_DATA_DIR    = r"C:\project\nss_dashboard\data"
SQLITE_PATH  = rf"{_DATA_DIR}\pratham.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{SQLITE_PATH}")

PRATHAM_STATES = [
    "Uttar Pradesh", "Bihar", "Rajasthan",
    "Maharashtra", "Gujarat", "Madhya Pradesh",
]

DEFAULT_TARGETS = {
    "gpi": 1.00, "retention": 90.0, "dropout": 10.0,
    "passrate": 85.0, "toilet": 95.0, "ptr": 30.0,
}

# National averages (UDISE 2019-20 / Census 2011 published figures)
NATIONAL_AVG = {
    "gpi":       1.01,
    "retention": 82.0,
    "dropout":   17.0,
    "passrate":  73.0,
    "ptr":       26.0,
    "toilet":    92.0,
    "literacy":  72.9,
    "female_lit":64.6,
}

C = {
    "primary": "#0052A5",
    "accent":  "#FF6B35",
    "success": "#198754",
    "danger":  "#dc3545",
    "muted":   "#6c757d",
    "warn":    "#fd7e14",
}

# ── DATA LOADING — SQLite / PostgreSQL / Google Sheets ───────────────────────
_engine = sqlalchemy.create_engine(DATABASE_URL)

def load_data():
    """Load from database. Swap DATABASE_URL in .env for PostgreSQL or any SQL backend."""
    boys_cols  = [f"class_{i}_boys"  for i in range(1, 13)]
    girls_cols = [f"class_{i}_girls" for i in range(1, 13)]

    df       = pd.read_sql("SELECT * FROM enrollment",       _engine)
    dist_df  = pd.read_sql("SELECT * FROM district_quality", _engine)
    sec_df   = pd.read_sql("SELECT * FROM secondary_results",_engine)

    # Rename district_quality column to match app expectations
    if "population" in dist_df.columns:
        dist_df = dist_df.rename(columns={"population": "population_k"})

    return df, dist_df, sec_df, boys_cols, girls_cols

def load_field_data_kpis():
    """Load live field data KPIs from Google Sheets or demo CSV."""
    try:
        from sheets_connector import load_field_data, compute_field_kpis
        return compute_field_kpis(load_field_data())
    except Exception:
        return {}

def load_predicted_impacts():
    """Load activity log and compute predicted KPI impacts via lag model."""
    try:
        from sheets_connector import load_activity_data
        from activity_impact import compute_predicted_impacts
        return compute_predicted_impacts(load_activity_data())
    except Exception:
        return []

df, dist_df, sec_df, BOYS_COLS, GIRLS_COLS = load_data()
FIELD_KPIS        = load_field_data_kpis()
PREDICTED_IMPACTS = load_predicted_impacts()
YEARS  = sorted(df["ac_year"].unique())
STATES = sorted(df["state_name"].unique())
_last_refresh = [datetime.now()]

# Data quality summary (shown in header)
DQ_ANOMALIES = int(df.get("dq_retention_anomaly", pd.Series([0])).sum() +
                   df.get("dq_dropout_anomaly", pd.Series([0])).sum())

# ── HELPERS ───────────────────────────────────────────────────────────────────
def fmt_lakh(n):
    if pd.isna(n) or n == 0: return "—"
    if n >= 1e7: return f"{n/1e7:.2f} Cr"
    if n >= 1e5: return f"{n/1e5:.1f} L"
    return f"{int(n):,}"

def filter_df(years, states, districts):
    return df[df["ac_year"].isin(years) & df["state_name"].isin(states) & df["district_name"].isin(districts)]

def progress_color(pct):
    if pct >= 90: return "success"
    if pct >= 70: return "warning"
    return "danger"

def kpi_card(title, value, subtitle, color, delta=None, benchmark=None):
    delta_el = html.Span(
        f" {delta}",
        style={"fontSize":"0.75rem","color": C["success"] if "▲" in str(delta) else C["danger"]}
    ) if delta else None
    bench_el = html.Span(
        f"  ·  National avg: {benchmark}",
        style={"fontSize":"0.68rem","color":C["muted"]}
    ) if benchmark else None
    return dbc.Card(dbc.CardBody([
        html.P(title, className="text-muted mb-1",
               style={"fontSize":"0.72rem","fontWeight":600,"letterSpacing":"0.05em","textTransform":"uppercase"}),
        html.Div([
            html.H3(value, style={"color":color,"fontWeight":700,"margin":"0","display":"inline"}),
            delta_el,
        ]),
        html.P([subtitle, bench_el], className="text-muted mt-1 mb-0", style={"fontSize":"0.70rem"}),
    ]), className="shadow-sm h-100", style={"borderTop":f"4px solid {color}","borderRadius":"8px"})

def cost_card(title, value, incremental, subtitle, icon):
    return dbc.Card(dbc.CardBody([
        html.Div([html.Span(icon, style={"fontSize":"1.4rem"}),
                  html.P(title, className="text-muted mb-0 ms-2",
                         style={"fontSize":"0.72rem","fontWeight":600,"textTransform":"uppercase","letterSpacing":"0.05em"})],
                 className="d-flex align-items-center mb-1"),
        html.H4(value, style={"color":C["accent"],"fontWeight":700,"margin":"0"}),
        html.P(incremental, className="mb-0 mt-1",
               style={"fontSize":"0.72rem","color":C["success"],"fontWeight":600}),
        html.P(subtitle, className="text-muted mb-0", style={"fontSize":"0.68rem"}),
    ]), className="shadow-sm h-100 border-0",
       style={"borderLeft":f"5px solid {C['accent']}","borderRadius":"8px","background":"#fff8f5"})

def progress_row(label, current, target, unit="", invert=False, national=None):
    if current is None or (isinstance(current, float) and np.isnan(current)):
        return html.Div()
    pct = (current/target*100) if not invert else ((2*target-current)/target*100)
    pct = max(0, min(100, pct))
    gap = current - target
    ok  = (gap > 0 and not invert) or (gap < 0 and invert)
    gap_str   = f"{'▲' if gap>0 else '▼'} {abs(gap):.1f}{unit} {'above' if gap>0 else 'below'} target"
    nat_str   = f"  ·  national avg {national}{unit}" if national else ""
    return html.Div([
        html.Div([
            html.Span(label, className="small fw-semibold"),
            html.Span(f"{current:.1f}{unit}  /  target {target:.0f}{unit}{nat_str}",
                      className="small text-muted ms-2"),
            html.Span(gap_str, className="small ms-2 fw-semibold",
                      style={"color": C["success"] if ok else C["danger"]}),
        ], className="d-flex justify-content-between flex-wrap mb-1"),
        dbc.Progress(value=pct, color=progress_color(pct), style={"height":"10px"}, className="mb-2"),
    ])

# ── APP ───────────────────────────────────────────────────────────────────────
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], title="Pratham Impact Dashboard")
S = {"background":"#ffffff","padding":"14px 16px","borderRadius":"10px",
     "marginBottom":"14px","boxShadow":"0 1px 4px rgba(0,0,0,0.07)"}

app.layout = dbc.Container(fluid=True,
    style={"backgroundColor":"#f0f2f5","paddingBottom":"40px"}, children=[

    dcc.Interval(id="refresh-interval", interval=60_000, n_intervals=0),
    dcc.Store(id="last-refresh-store"),

    # ── HEADER ────────────────────────────────────────────────────────────────
    dbc.Row(dbc.Col(html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span("P", style={"background":C["primary"],"color":"#fff","fontWeight":900,
                                         "fontSize":"1.4rem","padding":"4px 10px","borderRadius":"6px","marginRight":"10px"}),
                    html.Span("PRATHAM", style={"fontWeight":800,"fontSize":"1.2rem",
                                                "color":C["primary"],"letterSpacing":"0.1em"}),
                    html.Span(" Education Foundation", style={"color":"#555","fontSize":"0.95rem"}),
                    dbc.Badge("DEMO", color="warning", className="ms-2 align-middle", style={"fontSize":"0.6rem"}),
                ], className="d-flex align-items-center"),
                html.Small("Every child in school and learning well  ·  Primary & foundational literacy  ·  India",
                           className="text-muted mt-1 d-block"),
            ], md=8),
            dbc.Col(html.Div([
                html.Small("Last refreshed: ", className="text-muted"),
                html.Small(id="last-refresh-display",
                           children=datetime.now().strftime("%d %b %Y, %H:%M:%S"),
                           style={"color":C["primary"],"fontWeight":600}),
                html.Br(),
                html.Small(
                    f"Backend: SQLite  ·  Data quality: {DQ_ANOMALIES} anomalies flagged  ·  "
                    "Set DATABASE_URL in .env for PostgreSQL",
                    className="text-muted fst-italic", style={"fontSize":"0.68rem"}),
            ], className="text-end"), md=4, className="d-flex align-items-center justify-content-end"),
        ]),
    ], className="py-3 px-3")), className="bg-white border-bottom mb-3 shadow-sm"),

    # ── THEORY OF CHANGE ──────────────────────────────────────────────────────
    html.Div([
        dbc.Row([
            dbc.Col(html.H6("🔗 Theory of Change — How our work creates impact",
                            className="fw-bold mb-3", style={"color":C["primary"]}), md=9),
            dbc.Col(html.Small("Values update with filters below",
                               className="text-muted fst-italic float-end"), md=3),
        ]),
        html.Div(id="toc-section"),
    ], style=S),

    # ── LIVE FIELD DATA (Google Sheets / demo) ───────────────────────────────
    html.Div([
        dbc.Row([
            dbc.Col(html.H6("📡 Live Field Data — Weekly Field Reports",
                            className="fw-bold mb-0", style={"color":C["success"]}), md=8),
            dbc.Col(html.Small(
                f"Source: {FIELD_KPIS.get('field_data_source','none')}  ·  "
                f"{FIELD_KPIS.get('weeks_of_data',0)} weeks  ·  "
                f"as of {FIELD_KPIS.get('field_as_of','—')}",
                className="text-muted fst-italic float-end small"), md=4),
        ], className="mb-2"),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.P("Field Enrollment", className="text-muted mb-1",
                       style={"fontSize":"0.7rem","fontWeight":600,"textTransform":"uppercase"}),
                html.H4(f"{FIELD_KPIS.get('field_enrollment',0):,}",
                        style={"color":C["success"],"fontWeight":700,"margin":0}),
                html.Small("Children in weekly field reports", className="text-muted"),
            ])), md=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.P("Field GPI", className="text-muted mb-1",
                       style={"fontSize":"0.7rem","fontWeight":600,"textTransform":"uppercase"}),
                html.H4(f"{FIELD_KPIS.get('field_gpi',0):.2f}",
                        style={"color":C["success"],"fontWeight":700,"margin":0}),
                html.Small("Girls/boys ratio this week", className="text-muted"),
            ])), md=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.P("Teacher Attendance", className="text-muted mb-1",
                       style={"fontSize":"0.7rem","fontWeight":600,"textTransform":"uppercase"}),
                html.H4(f"{FIELD_KPIS.get('field_teacher_att',0):.1f}%",
                        style={"color":C["warn"],"fontWeight":700,"margin":0}),
                html.Small("% of school visits — teacher present", className="text-muted"),
            ])), md=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.P("MDM Coverage", className="text-muted mb-1",
                       style={"fontSize":"0.7rem","fontWeight":600,"textTransform":"uppercase"}),
                html.H4(f"{FIELD_KPIS.get('field_mdm_coverage',0):.1f}%",
                        style={"color":C["success"],"fontWeight":700,"margin":0}),
                html.Small("% schools serving mid-day meal", className="text-muted"),
            ])), md=3),
        ], className="g-3"),
        html.Div(
            html.Small(
                "To connect your Google Sheet: set GOOGLE_SHEET_ID in .env and add google_credentials.json — see sheets_connector.py",
                className="text-muted fst-italic mt-2 d-block", style={"fontSize":"0.68rem"}
            ) if FIELD_KPIS.get("field_data_source") == "demo_generated" else html.Span()
        ),
    ], style={**S, "borderLeft":f"4px solid {C['success']}"}),

    # ── PREDICTED KPI IMPACT (Activity → Outcome translation layer) ──────────
    html.Div(id="predicted-impact-section"),

    # ── INSIGHT ALERTS ────────────────────────────────────────────────────────
    html.Div(id="alert-panel"),

    # ── FILTERS ───────────────────────────────────────────────────────────────
    html.Div([
        dbc.Row([
            dbc.Col([html.Label("Academic Years", className="fw-semibold small"),
                     dcc.Dropdown(id="filter-year", options=[{"label":y,"value":y} for y in YEARS],
                                  value=YEARS, multi=True, clearable=False)], md=3),
            dbc.Col([html.Label("State / Programme Area", className="fw-semibold small"),
                     dcc.Dropdown(id="filter-state", options=[{"label":s,"value":s} for s in STATES],
                                  value=PRATHAM_STATES, multi=True, clearable=False)], md=4),
            dbc.Col([html.Label("District", className="fw-semibold small"),
                     dcc.Dropdown(id="filter-district", multi=True, clearable=False)], md=3),
            dbc.Col([
                html.Label("Annual Budget (₹ Crore)", className="fw-semibold small"),
                dbc.InputGroup([
                    dbc.InputGroupText("₹"),
                    dbc.Input(id="budget-input", type="number", value=500, min=1, max=10000, step=10),
                    dbc.InputGroupText("Cr"),
                ], size="sm"),
            ], md=2),
        ]),
    ], style={**S, "marginBottom":"10px"}),

    # ── PROGRAMME TARGETS ─────────────────────────────────────────────────────
    html.Div([
        dbc.Row([
            dbc.Col(html.H6("⚙ Programme Targets", className="mb-0 fw-bold",
                            style={"color":C["primary"]}), md=10),
            dbc.Col(dbc.Button("Edit Targets", id="toggle-targets", size="sm",
                               outline=True, color="primary", className="float-end"), md=2),
        ], className="mb-2"),
        dbc.Collapse(id="targets-collapse", is_open=False, children=[
            dbc.Row([
                dbc.Col([html.Label("GPI Target", className="small fw-semibold"),
                         dbc.Input(id="t-gpi", type="number", value=DEFAULT_TARGETS["gpi"], step=0.01, min=0.8, max=1.2, size="sm")], md=2),
                dbc.Col([html.Label("Retention % Target", className="small fw-semibold"),
                         dbc.Input(id="t-retention", type="number", value=DEFAULT_TARGETS["retention"], step=1, min=50, max=100, size="sm")], md=2),
                dbc.Col([html.Label("Dropout % Target (max)", className="small fw-semibold"),
                         dbc.Input(id="t-dropout", type="number", value=DEFAULT_TARGETS["dropout"], step=1, min=0, max=50, size="sm")], md=2),
                dbc.Col([html.Label("Pass Rate % Target", className="small fw-semibold"),
                         dbc.Input(id="t-passrate", type="number", value=DEFAULT_TARGETS["passrate"], step=1, min=50, max=100, size="sm")], md=2),
                dbc.Col([html.Label("Girls Toilet % Target", className="small fw-semibold"),
                         dbc.Input(id="t-toilet", type="number", value=DEFAULT_TARGETS["toilet"], step=1, min=50, max=100, size="sm")], md=2),
                dbc.Col([html.Label("PTR Target (max)", className="small fw-semibold"),
                         dbc.Input(id="t-ptr", type="number", value=DEFAULT_TARGETS["ptr"], step=1, min=10, max=60, size="sm")], md=2),
            ], className="mt-2"),
        ]),
    ], style=S),

    # ── PROGRAMME PROGRESS ────────────────────────────────────────────────────
    html.Div([
        html.H6("📊 Programme Progress — Current vs Targets vs National Average",
                className="fw-bold mb-3", style={"color":C["primary"]}),
        html.Div(id="progress-section"),
    ], style=S),

    # ── COST-PER-IMPACT ───────────────────────────────────────────────────────
    html.Div([
        html.H6("💰 Cost-per-Impact", className="fw-bold mb-1", style={"color":C["accent"]}),
        html.P("Gross cost (budget ÷ total) and incremental cost (budget ÷ children above national baseline)",
               className="text-muted mb-3", style={"fontSize":"0.75rem"}),
        dbc.Row(id="cost-cards", className="g-3"),
    ], style=S),

    # ── OUTPUT KPIs ───────────────────────────────────────────────────────────
    html.Div([
        html.P("OUTPUT — Enrollment & Reach", className="small fw-bold text-muted mb-2",
               style={"textTransform":"uppercase","letterSpacing":"0.06em"}),
        dbc.Row([
            dbc.Col(id="kpi-enrollment", md=3), dbc.Col(id="kpi-gpi",       md=3),
            dbc.Col(id="kpi-retention",  md=3), dbc.Col(id="kpi-dropout",   md=3),
        ], className="g-3"),
    ], style=S),

    # ── OUTCOME KPIs ──────────────────────────────────────────────────────────
    html.Div([
        html.P("OUTCOME — Quality & Learning Results (2015-16)", className="small fw-bold text-muted mb-2",
               style={"textTransform":"uppercase","letterSpacing":"0.06em"}),
        dbc.Row([
            dbc.Col(id="kpi-passrate", md=3), dbc.Col(id="kpi-ptr",    md=3),
            dbc.Col(id="kpi-mdm",      md=3), dbc.Col(id="kpi-toilet", md=3),
        ], className="g-3"),
    ], style=S),

    # ── IMPACT KPIs ───────────────────────────────────────────────────────────
    html.Div([
        html.P("IMPACT — Structural & Equity Indicators", className="small fw-bold text-muted mb-2",
               style={"textTransform":"uppercase","letterSpacing":"0.06em"}),
        dbc.Row([
            dbc.Col(id="kpi-literacy",  md=3), dbc.Col(id="kpi-fem-lit",   md=3),
            dbc.Col(id="kpi-repeater",  md=3), dbc.Col(id="kpi-singletch", md=3),
        ], className="g-3"),
    ], style=S),

    # ── CHARTS ────────────────────────────────────────────────────────────────
    dbc.Row([
        dbc.Col(dcc.Graph(id="chart-trend"),        md=7),
        dbc.Col(dcc.Graph(id="chart-gender-class"), md=5),
    ], className="mb-3"),
    dbc.Row([
        dbc.Col(dcc.Graph(id="chart-top-districts"), md=5),
        dbc.Col(dcc.Graph(id="chart-funnel"),         md=4),
        dbc.Col(dcc.Graph(id="chart-hs-transition"),  md=3),
    ], className="mb-3"),
    dbc.Row([
        dbc.Col(dcc.Graph(id="chart-passrate"),    md=6),
        dbc.Col(dcc.Graph(id="chart-passrate-eq"), md=6),
    ], className="mb-3"),
    dbc.Row([
        dbc.Col(dcc.Graph(id="chart-ptr"),    md=6),
        dbc.Col(dcc.Graph(id="chart-equity"), md=6),
    ], className="mb-3"),

    # ── FOOTER ────────────────────────────────────────────────────────────────
    dbc.Row(dbc.Col(html.Div([
        html.Small("Pratham Education Foundation — Impact Dashboard (Demo)  ·  "),
        html.Small("Data: UDISE 2012-20 · Education in India Dataset (Kaggle) · Census 2011  ·  "),
        html.Small("NSS Open Projects 2026 — Challenge 5.1", className="fst-italic"),
    ], className="text-muted"), className="text-center py-3 border-top bg-white")),
])

# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS
# ═══════════════════════════════════════════════════════════════════════════════

@callback(Output("last-refresh-display","children"), Input("refresh-interval","n_intervals"))
def tick(n):
    _last_refresh[0] = datetime.now()
    return _last_refresh[0].strftime("%d %b %Y, %H:%M:%S")

@callback(Output("targets-collapse","is_open"), Input("toggle-targets","n_clicks"),
          State("targets-collapse","is_open"), prevent_initial_call=True)
def toggle_targets(n, is_open): return not is_open

@callback(Output("filter-district","options"), Output("filter-district","value"),
          Input("filter-state","value"))
def update_districts(states):
    districts = sorted(df[df["state_name"].isin(states)]["district_name"].unique())
    return [{"label":d,"value":d} for d in districts], districts[:40]


# ── THEORY OF CHANGE ──────────────────────────────────────────────────────────
@callback(Output("toc-section","children"),
          Input("filter-year","value"), Input("filter-state","value"), Input("filter-district","value"))
def update_toc(years, states, districts):
    if not districts: return html.P("Select districts to populate.", className="text-muted small")

    d        = filter_df(years, states, districts)
    states_t = [s.strip().title() for s in states]
    sec_sub  = sec_df[sec_df["statname"].isin(states_t)]
    dist_sub = dist_df[dist_df["district_name"].isin(districts)]

    enroll    = int(d["total_enrollment"].sum())
    girls     = int(d["total_girls"].sum())
    gpi       = float(d["gpi"].median())
    ret       = float(d["primary_retention_pct"].median())
    drop      = float(d["sec_dropout_pct"].median())
    pr        = float(sec_sub["pass_rate"].mean())   if not sec_sub.empty  else None
    ptr       = float(dist_sub["ptr"].median())      if not dist_sub.empty else None
    lit       = float(dist_sub["literacy_rate"].median()) if not dist_sub.empty else None

    def node(stage, label, value, color, nat=None):
        nat_row = html.Div(f"national: {nat}", style={"fontSize":"0.65rem","color":"#888"}) if nat else None
        return html.Div([
            html.Div(stage, style={"fontSize":"0.6rem","fontWeight":700,"letterSpacing":"0.08em",
                                   "textTransform":"uppercase","color":color,"marginBottom":"2px"}),
            html.Div(value, style={"fontSize":"1.05rem","fontWeight":800,"color":color}),
            html.Div(label, style={"fontSize":"0.68rem","color":"#555"}),
            nat_row,
        ], style={"textAlign":"center","padding":"10px 6px","background":"#f8f9fa",
                  "borderRadius":"8px","borderTop":f"3px solid {color}","minWidth":"110px"})

    def arrow():
        return html.Div("→", style={"fontSize":"1.4rem","color":"#aaa","alignSelf":"center","padding":"0 4px"})

    pr_val  = f"{pr:.1f}%"  if pr  else "—"
    ptr_val = f"{ptr:.0f}:1" if ptr else "—"
    lit_val = f"{lit:.1f}%" if lit else "—"

    return html.Div([
        node("Activity",  "Schools reached",        f"{len(districts):,} districts", "#6c757d"),
        arrow(),
        node("Output",    "Children enrolled",      fmt_lakh(enroll),               C["primary"],  f"{NATIONAL_AVG['gpi']:.2f} GPI"),
        arrow(),
        node("Output",    "Gender parity (GPI)",    f"{gpi:.2f}",                   C["primary"],  f"{NATIONAL_AVG['gpi']:.2f}"),
        arrow(),
        node("Outcome",   "Primary retention",      f"{ret:.1f}%",                  C["success"],  f"{NATIONAL_AVG['retention']:.0f}%"),
        arrow(),
        node("Outcome",   "Secondary dropout",      f"{drop:.1f}%",                 C["warn"],     f"{NATIONAL_AVG['dropout']:.0f}%"),
        arrow(),
        node("Outcome",   "Class 10 pass rate",     pr_val,                         C["success"],  f"{NATIONAL_AVG['passrate']:.0f}%"),
        arrow(),
        node("Impact",    "District literacy",      lit_val,                        C["primary"],  f"{NATIONAL_AVG['literacy']:.1f}%"),
    ], style={"display":"flex","flexWrap":"wrap","gap":"4px","alignItems":"stretch"})


# ── PREDICTED KPI IMPACT ──────────────────────────────────────────────────────
@callback(Output("predicted-impact-section","children"), Input("refresh-interval","n_intervals"))
def update_predicted_impacts(n):
    from activity_impact import CONFIDENCE_COLOR, monday_summary

    preds = PREDICTED_IMPACTS
    if not preds:
        return html.Div()

    mon = monday_summary(preds)

    def pred_card(p):
        sign      = "+" if p["direction"] == "up" else ""
        col       = CONFIDENCE_COLOR[p["confidence"]]
        arrow_str = "▲" if p["direction"] == "up" else "▼"
        fitted    = p.get("fitted", False)
        r2        = p.get("r2")
        ci_low    = p.get("ci_low")
        ci_high   = p.get("ci_high")
        n_obs     = p.get("n_obs")

        r2_el = html.Small(
            f"R²={r2:.3f}  n={n_obs:,}  95%CI [{ci_low:+.3f}, {ci_high:+.3f}]",
            className="d-block",
            style={"fontSize":"0.62rem","color":"#888","fontFamily":"monospace"}
        ) if (fitted and r2 is not None) else None

        source_badge = dbc.Badge(
            "OLS fitted" if fitted else "estimated",
            color="info" if fitted else "secondary",
            className="ms-1", style={"fontSize":"0.55rem"}
        )

        return dbc.Col(dbc.Card(dbc.CardBody([
            html.Div([
                html.Span(p["emoji"], style={"fontSize":"1.1rem"}),
                html.Span(f"  {p['label']}",
                          style={"fontWeight":700,"fontSize":"0.82rem","marginLeft":"4px"}),
                source_badge,
            ], className="d-flex align-items-center mb-1"),
            html.Div([
                html.Span(f"{arrow_str} {sign}{abs(p['predicted_delta']):.2f} {p['unit']}",
                          style={"fontSize":"1.1rem","fontWeight":800,"color":col}),
            ]),
            html.Small(f"→ {p['kpi']}", className="text-muted d-block"),
            html.Small(f"Expected by {p['due_date']}  ({p['lag_weeks']}w lag)",
                       className="d-block", style={"fontSize":"0.65rem","color":"#888"}),
            html.Small(f"{p['sessions_total']} sessions  ·  {p['children_reached']:,} children",
                       className="d-block", style={"fontSize":"0.65rem","color":"#888"}),
            r2_el,
            dbc.Badge(p["confidence"], color={
                "high":"success","medium":"warning","low":"secondary"
            }[p["confidence"]], className="mt-1", style={"fontSize":"0.6rem"}),
        ]), className="shadow-sm h-100",
           style={"borderTop":f"3px solid {col}","borderRadius":"8px"}),
        md=3, className="mb-2")

    # Monday check callout
    monday_el = html.Div()
    if mon:
        sign = "+" if mon["direction"] == "up" else ""
        monday_el = dbc.Alert([
            html.Strong("Monday Check — "),
            html.Span(f"{mon['emoji']} {mon['label']}"),
            html.Span(f" will move "),
            html.Strong(f"{sign}{abs(mon['predicted_delta']):.2f} {mon['unit']}",
                        style={"color": CONFIDENCE_COLOR[mon["confidence"]]}),
            html.Span(f" on {mon['kpi']} by {mon['due_date']}  "),
            dbc.Badge(f"{mon['confidence']} confidence", color={
                "high":"success","medium":"warning","low":"secondary"
            }[mon["confidence"]], className="align-middle"),
        ], color="light", className="py-2 px-3 mb-2 border",
           style={"fontSize":"0.82rem","borderLeft":f"4px solid {CONFIDENCE_COLOR[mon['confidence']]} !important"})

    return html.Div([
        dbc.Row([
            dbc.Col(html.H6("🔮 Predicted KPI Impact — Activities This Month",
                            className="fw-bold mb-0",
                            style={"color":"#6f42c1"}), md=9),
            dbc.Col(html.Small("Based on activity logs + lag model  ·  see activity_impact.py",
                               className="text-muted fst-italic float-end small"), md=3),
        ], className="mb-2"),
        monday_el,
        html.P(
            "Each row in your field log maps to a KPI that should move in 2–16 weeks. "
            "Confidence = how well the effect is documented.",
            className="text-muted mb-2", style={"fontSize":"0.72rem"}
        ),
        dbc.Row([pred_card(p) for p in preds], className="g-2"),
    ], style={**S, "borderLeft":"4px solid #6f42c1"})


# ── INSIGHT ALERTS ────────────────────────────────────────────────────────────
@callback(Output("alert-panel","children"),
          Input("filter-year","value"), Input("filter-state","value"), Input("filter-district","value"),
          Input("t-gpi","value"), Input("t-retention","value"), Input("t-dropout","value"),
          Input("t-passrate","value"), Input("t-toilet","value"), Input("t-ptr","value"))
def update_alerts(years, states, districts, t_gpi, t_ret, t_drop, t_pass, t_toilet, t_ptr):
    if not districts: return html.Div()

    d        = filter_df(years, states, districts)
    states_t = [s.strip().title() for s in states]
    sec_sub  = sec_df[sec_df["statname"].isin(states_t)]
    dist_sub = dist_df[dist_df["district_name"].isin(districts)]

    tg   = t_gpi     or DEFAULT_TARGETS["gpi"]
    tr   = t_ret     or DEFAULT_TARGETS["retention"]
    td   = t_drop    or DEFAULT_TARGETS["dropout"]
    tp   = t_pass    or DEFAULT_TARGETS["passrate"]
    tto  = t_toilet  or DEFAULT_TARGETS["toilet"]
    tptr = t_ptr     or DEFAULT_TARGETS["ptr"]

    gpi  = float(d["gpi"].median())
    ret  = float(d["primary_retention_pct"].median())
    drop = float(d["sec_dropout_pct"].median())
    pr   = float(sec_sub["pass_rate"].mean())          if not sec_sub.empty  else None
    tlt  = float(dist_sub["girls_toilet_pct"].median()) if not dist_sub.empty else None
    ptr  = float(dist_sub["ptr"].median())              if not dist_sub.empty else None

    # Worst-offending districts for drill-down alerts
    worst_ret  = (d.groupby(["state_name","district_name"])["primary_retention_pct"]
                   .median().reset_index().nsmallest(3,"primary_retention_pct"))
    worst_drop = (d.groupby(["state_name","district_name"])["sec_dropout_pct"]
                   .median().reset_index().nlargest(3,"sec_dropout_pct"))

    alerts = []

    def pct_off(curr, target, invert=False):
        if curr is None: return 0
        return abs(curr - target) / target * 100

    # Critical alerts (>20% off target)
    if gpi < tg and pct_off(gpi, tg) > 5:
        alerts.append(("danger", "⚠ Gender Parity Below Target",
                        f"GPI is {gpi:.2f} vs target {tg:.2f} — "
                        f"{(tg-gpi)/tg*100:.0f}% gap. National average is {NATIONAL_AVG['gpi']:.2f}. "
                        f"Girls enrollment needs urgent attention."))

    if ret < tr:
        gap = tr - ret
        bottom = ", ".join(f"{r['district_name'].title()} ({r['primary_retention_pct']:.0f}%)"
                           for _, r in worst_ret.iterrows())
        sev = "danger" if gap > 15 else "warning"
        alerts.append((sev, "⚠ Primary Retention Below Target",
                        f"Retention is {ret:.1f}% vs target {tr:.0f}% — "
                        f"{gap:.1f} pp gap. Worst districts: {bottom}. "
                        f"National average: {NATIONAL_AVG['retention']:.0f}%."))

    if drop > td:
        gap = drop - td
        top = ", ".join(f"{r['district_name'].title()} ({r['sec_dropout_pct']:.0f}%)"
                        for _, r in worst_drop.iterrows())
        sev = "danger" if gap > 10 else "warning"
        alerts.append((sev, "⚠ Secondary Dropout Exceeds Target",
                        f"Dropout rate is {drop:.1f}% vs max target {td:.0f}% — "
                        f"{gap:.1f} pp above threshold. High-risk districts: {top}."))

    if pr is not None and pr < tp:
        gap = tp - pr
        sev = "danger" if gap > 15 else "warning"
        alerts.append((sev, "⚠ Class 10 Pass Rate Below Target",
                        f"Pass rate is {pr:.1f}% vs target {tp:.0f}% — "
                        f"{gap:.1f} pp gap. National average: {NATIONAL_AVG['passrate']:.0f}%. "
                        f"Consider remedial programme intensification."))

    if tlt is not None and tlt < tto:
        alerts.append(("warning", "⚠ Girls Toilet Coverage Gap",
                        f"Coverage at {tlt:.1f}% vs target {tto:.0f}%. "
                        f"Absence of toilets is a leading cause of girl dropout at secondary level."))

    if ptr is not None and ptr > tptr:
        alerts.append(("warning", "⚠ High Pupil-Teacher Ratio",
                        f"Median PTR is {ptr:.0f}:1 vs target {tptr:.0f}:1. "
                        f"National average: {NATIONAL_AVG['ptr']:.0f}:1. Affects learning outcomes directly."))

    # Positive alerts
    if gpi >= tg:
        alerts.append(("success", "✓ Gender Parity Achieved",
                        f"GPI {gpi:.2f} meets or exceeds target {tg:.2f}. "
                        f"Above national average of {NATIONAL_AVG['gpi']:.2f}."))

    if pr is not None and pr >= NATIONAL_AVG["passrate"]:
        alerts.append(("success", "✓ Pass Rate Above National Average",
                        f"Class 10 pass rate {pr:.1f}% exceeds national average of {NATIONAL_AVG['passrate']:.0f}%."))

    if not alerts:
        return html.Div([
            dbc.Alert("✓ All monitored KPIs are within acceptable range of targets.",
                      color="success", className="mb-2", style={"fontSize":"0.85rem"})
        ], style={"marginBottom":"14px"})

    # Sort: danger first, then warning, then success
    order = {"danger":0,"warning":1,"success":2}
    alerts.sort(key=lambda x: order.get(x[0],3))

    return html.Div([
        html.Div([
            html.H6("🔔 Insight Alerts — Action Required",
                    className="fw-bold mb-2", style={"color":C["danger"]}),
            html.Small(f"{sum(1 for a in alerts if a[0]=='danger')} critical  ·  "
                       f"{sum(1 for a in alerts if a[0]=='warning')} warnings  ·  "
                       f"{sum(1 for a in alerts if a[0]=='success')} on track",
                       className="text-muted"),
        ], className="mb-2"),
        *[dbc.Alert([html.Strong(title + "  "), msg],
                    color=sev, className="mb-2 py-2", style={"fontSize":"0.82rem"})
          for sev, title, msg in alerts],
    ], style=S)


# ── PROGRAMME PROGRESS ────────────────────────────────────────────────────────
@callback(Output("progress-section","children"),
          Input("filter-year","value"), Input("filter-state","value"), Input("filter-district","value"),
          Input("t-gpi","value"), Input("t-retention","value"), Input("t-dropout","value"),
          Input("t-passrate","value"), Input("t-toilet","value"), Input("t-ptr","value"))
def update_progress(years, states, districts, t_gpi, t_ret, t_drop, t_pass, t_toilet, t_ptr):
    if not districts: return html.P("Select districts.", className="text-muted small")

    d        = filter_df(years, states, districts)
    states_t = [s.strip().title() for s in states]
    dist_sub = dist_df[dist_df["district_name"].isin(districts)]
    sec_sub  = sec_df[sec_df["statname"].isin(states_t)]

    gpi  = float(d["gpi"].median())
    ret  = float(d["primary_retention_pct"].median())
    drop = float(d["sec_dropout_pct"].median())
    pr   = float(sec_sub["pass_rate"].mean())           if not sec_sub.empty  else None
    tlt  = float(dist_sub["girls_toilet_pct"].median()) if not dist_sub.empty else None
    ptr  = float(dist_sub["ptr"].median())              if not dist_sub.empty else None

    tg=t_gpi or DEFAULT_TARGETS["gpi"]; tr=t_ret or DEFAULT_TARGETS["retention"]
    td=t_drop or DEFAULT_TARGETS["dropout"]; tp=t_pass or DEFAULT_TARGETS["passrate"]
    tto=t_toilet or DEFAULT_TARGETS["toilet"]; tptr=t_ptr or DEFAULT_TARGETS["ptr"]

    return dbc.Row([
        dbc.Col([
            progress_row("Gender Parity Index (GPI)",   gpi,  tg,   "",  False, NATIONAL_AVG["gpi"]),
            progress_row("Primary Retention Rate",      ret,  tr,   "%", False, NATIONAL_AVG["retention"]),
            progress_row("Secondary Dropout Rate",      drop, td,   "%", True,  NATIONAL_AVG["dropout"]),
        ], md=6),
        dbc.Col([
            progress_row("Class 10 Pass Rate",          pr,   tp,   "%", False, NATIONAL_AVG["passrate"]),
            progress_row("Girls Toilet Coverage",       tlt,  tto,  "%", False, NATIONAL_AVG["toilet"]),
            progress_row("Pupil-Teacher Ratio",         ptr,  tptr, "",  True,  NATIONAL_AVG["ptr"]),
        ], md=6),
    ])


# ── COST-PER-IMPACT ───────────────────────────────────────────────────────────
@callback(Output("cost-cards","children"),
          Input("filter-year","value"), Input("filter-state","value"), Input("filter-district","value"),
          Input("budget-input","value"))
def update_cost(years, states, districts, budget_cr):
    if not districts or not budget_cr:
        return dbc.Col(html.P("Enter a budget and select districts.", className="text-muted small"))

    d        = filter_df(years, states, districts)
    states_t = [s.strip().title() for s in states]
    sec_sub  = sec_df[sec_df["statname"].isin(states_t)]
    budget   = float(budget_cr) * 1e7

    total   = int(d["total_enrollment"].sum())
    girls   = int(d["total_girls"].sum())
    ret_pct = float(d["primary_retention_pct"].median())
    retained = int(total * ret_pct / 100)

    # Incremental = children above national baseline
    incr_retained = max(0, int(total * (ret_pct - NATIONAL_AVG["retention"]) / 100))

    pr     = float(sec_sub["pass_rate"].mean()) if not sec_sub.empty else None
    appeared = int(sec_sub["appeared"].sum())   if not sec_sub.empty else 0
    passers  = int(appeared * (pr/100))         if pr else 0
    incr_passers = max(0, int(appeared * (((pr or 0) - NATIONAL_AVG["passrate"])/100)))

    def fmt(n):
        if n <= 0: return "—"
        v = budget / n
        return f"₹{v/1000:.1f}K" if v >= 1000 else f"₹{int(v)}"

    def incr_str(n, label):
        if n <= 0: return f"0 {label} above national baseline"
        v = budget / n
        s = f"₹{v/1000:.1f}K" if v >= 1000 else f"₹{int(v)}"
        return f"Incremental: {s} per {label} above national avg"

    return [
        dbc.Col(cost_card("Cost per Child Enrolled",
                          fmt(total),
                          f"Budget ÷ {fmt_lakh(total)} enrolled  ·  gross",
                          f"National baseline: enroll more to lower this", "👤"), md=3),
        dbc.Col(cost_card("Cost per Child Retained",
                          fmt(retained),
                          incr_str(incr_retained, "retained child"),
                          f"{fmt_lakh(retained)} retained to Cl 5  (ret {ret_pct:.1f}%)", "📚"), md=3),
        dbc.Col(cost_card("Cost per Girl Enrolled",
                          fmt(girls),
                          f"GPI programme efficiency",
                          f"{fmt_lakh(girls)} girls  ·  focus on parity states", "👧"), md=3),
        dbc.Col(cost_card("Cost per Class 10 Passer",
                          fmt(passers),
                          incr_str(incr_passers, "additional passer"),
                          f"{fmt_lakh(passers)} passed board  ·  {pr:.1f}% pass rate" if pr else "—", "🎓"), md=3),
    ]


# ── OUTPUT KPIs ───────────────────────────────────────────────────────────────
@callback(
    Output("kpi-enrollment","children"), Output("kpi-gpi","children"),
    Output("kpi-retention","children"),  Output("kpi-dropout","children"),
    Input("filter-year","value"), Input("filter-state","value"), Input("filter-district","value"),
    Input("t-gpi","value"), Input("t-retention","value"), Input("t-dropout","value"))
def kpis_output(years, states, districts, t_gpi, t_ret, t_drop):
    empty = kpi_card("—","—","No data","#aaa")
    if not districts: return empty, empty, empty, empty
    d = filter_df(years, states, districts)

    # YoY delta: latest year vs previous year
    yrs = sorted(d["ac_year"].unique())
    if len(yrs) >= 2:
        cur = d[d["ac_year"]==yrs[-1]]["total_enrollment"].sum()
        prv = d[d["ac_year"]==yrs[-2]]["total_enrollment"].sum()
        enroll_delta = f"{'▲' if cur>=prv else '▼'} {abs(cur-prv)/prv*100:.1f}% vs {yrs[-2]}"
    else:
        enroll_delta = None

    gpi  = float(d["gpi"].median())
    ret  = float(d["primary_retention_pct"].median())
    drop = float(d["sec_dropout_pct"].median())
    tg=t_gpi or DEFAULT_TARGETS["gpi"]; tr=t_ret or DEFAULT_TARGETS["retention"]; td=t_drop or DEFAULT_TARGETS["dropout"]

    return (
        kpi_card("Total Enrollment",   fmt_lakh(d["total_enrollment"].sum()),
                 f"{fmt_lakh(d['total_girls'].sum())} girls  ·  {fmt_lakh(d['total_boys'].sum())} boys",
                 C["primary"], enroll_delta),
        kpi_card("Gender Parity Index",f"{gpi:.2f}", "Girls / Boys  (1.0 = equal)",
                 C["primary"], f"{'▲' if gpi>=tg else '▼'} vs target {tg:.2f}",
                 benchmark=f"{NATIONAL_AVG['gpi']:.2f}"),
        kpi_card("Primary Retention",  f"{ret:.1f}%", "Class 5 vs Class 1",
                 C["success"], f"{'▲' if ret>=tr else '▼'} vs target {tr:.0f}%",
                 benchmark=f"{NATIONAL_AVG['retention']:.0f}%"),
        kpi_card("Secondary Dropout",  f"{drop:.1f}%", "Lost between Class 6 & 8",
                 C["danger"],  f"{'▼' if drop<=td else '▲'} vs target {td:.0f}%",
                 benchmark=f"{NATIONAL_AVG['dropout']:.0f}%"),
    )


# ── OUTCOME KPIs ──────────────────────────────────────────────────────────────
@callback(
    Output("kpi-passrate","children"), Output("kpi-ptr","children"),
    Output("kpi-mdm","children"),      Output("kpi-toilet","children"),
    Input("filter-state","value"), Input("filter-district","value"),
    Input("t-passrate","value"), Input("t-ptr","value"), Input("t-toilet","value"))
def kpis_outcome(states, districts, t_pass, t_ptr, t_toilet):
    empty = kpi_card("—","—","No data","#aaa")
    if not states: return empty, empty, empty, empty
    states_t = [s.strip().title() for s in states]
    sec_sub  = sec_df[sec_df["statname"].isin(states_t)]
    dist_sub = dist_df[dist_df["district_name"].isin(districts)] if districts else dist_df[dist_df["state_name"].isin(states_t)]

    pr  = float(sec_sub["pass_rate"].mean())           if not sec_sub.empty  else None
    ptr = float(dist_sub["ptr"].median())              if not dist_sub.empty else None
    mdm = float(dist_sub["mdm_pct"].median())          if not dist_sub.empty else None
    tlt = float(dist_sub["girls_toilet_pct"].median()) if not dist_sub.empty else None

    def v(x, s=""): return f"{x:.1f}{s}" if x is not None and not np.isnan(x) else "—"
    tp=t_pass or 85; tptr=t_ptr or 30; tto=t_toilet or 95

    return (
        kpi_card("Class 10 Pass Rate",    v(pr,"%"),   "Board exam — 2014-15",
                 "#0d6efd", f"{'▲' if (pr or 0)>=tp else '▼'} vs target {tp}%",
                 benchmark=f"{NATIONAL_AVG['passrate']:.0f}%"),
        kpi_card("Pupil-Teacher Ratio",   v(ptr,":1"), "Median district",
                 C["warn"],  f"{'▼' if (ptr or 99)<=tptr else '▲'} vs target {tptr}:1",
                 benchmark=f"{NATIONAL_AVG['ptr']:.0f}:1"),
        kpi_card("Mid-Day Meal Coverage", v(mdm,"%"),  "% schools with MDM",  C["success"]),
        kpi_card("Girls Toilet Coverage", v(tlt,"%"),  "% schools with toilet",
                 "#6f42c1", f"{'▲' if (tlt or 0)>=tto else '▼'} vs target {tto}%",
                 benchmark=f"{NATIONAL_AVG['toilet']:.0f}%"),
    )


# ── IMPACT KPIs ───────────────────────────────────────────────────────────────
@callback(
    Output("kpi-literacy","children"),  Output("kpi-fem-lit","children"),
    Output("kpi-repeater","children"),  Output("kpi-singletch","children"),
    Input("filter-state","value"), Input("filter-district","value"))
def kpis_impact(states, districts):
    empty = kpi_card("—","—","No data","#aaa")
    if not states: return empty, empty, empty, empty
    states_t = [s.strip().title() for s in states]
    dist_sub = dist_df[dist_df["district_name"].isin(districts)] if districts else dist_df[dist_df["state_name"].isin(states_t)]

    def v(x, s=""): return f"{x:.1f}{s}" if x is not None and not np.isnan(float(x)) else "—"

    lit  = dist_sub["literacy_rate"].median()     if not dist_sub.empty else None
    flit = dist_sub["female_lit"].median()         if not dist_sub.empty else None
    rep  = dist_sub["repeater_rate_pct"].median()  if not dist_sub.empty else None
    stch = dist_sub["single_tch_pct"].median()    if not dist_sub.empty else None

    return (
        kpi_card("Overall Literacy",       v(lit,"%"),  "Census 2011",  "#0dcaf0",
                 benchmark=f"{NATIONAL_AVG['literacy']:.1f}%"),
        kpi_card("Female Literacy",        v(flit,"%"), "Census 2011",  "#6f42c1",
                 benchmark=f"{NATIONAL_AVG['female_lit']:.1f}%"),
        kpi_card("Primary Repeater Rate",  v(rep,"%"),  "Boys Gr 1-5",  C["danger"]),
        kpi_card("Single-Teacher Schools", v(stch,"%"), "Quality risk",  C["warn"]),
    )


# ── CHARTS ────────────────────────────────────────────────────────────────────
@callback(Output("chart-trend","figure"),
          Input("filter-year","value"), Input("filter-state","value"), Input("filter-district","value"))
def chart_trend(years, states, districts):
    if not districts: return go.Figure()
    d   = filter_df(years, states, districts)
    agg = d.groupby("ac_year")[["total_boys","total_girls"]].sum().reset_index()
    agg["total"] = agg["total_boys"] + agg["total_girls"]
    agg["yoy"]   = agg["total"].pct_change() * 100
    fig = go.Figure()
    fig.add_bar(x=agg["ac_year"], y=agg["total_boys"],  name="Boys",  marker_color="#4C9BE8")
    fig.add_bar(x=agg["ac_year"], y=agg["total_girls"], name="Girls", marker_color="#F06292")
    fig.add_scatter(x=agg["ac_year"], y=agg["yoy"], name="YoY %",
                    mode="lines+markers", yaxis="y2",
                    line=dict(color=C["success"], width=2.5, dash="dot"))
    fig.update_layout(title="Enrollment Trend + YoY Growth",barmode="stack",
                      yaxis=dict(title="Enrollment"),
                      yaxis2=dict(title="YoY %",overlaying="y",side="right",showgrid=False),
                      legend=dict(orientation="h",y=-0.18),
                      margin=dict(t=50,b=40),plot_bgcolor="white")
    return fig


@callback(Output("chart-gender-class","figure"),
          Input("filter-year","value"), Input("filter-state","value"), Input("filter-district","value"))
def chart_gender_class(years, states, districts):
    if not districts: return go.Figure()
    d = filter_df(years, states, districts)
    classes = [f"Cl {i}" for i in range(1, 13)]
    fig = go.Figure([
        go.Bar(name="Boys",  x=classes, y=d[BOYS_COLS].sum().values,  marker_color="#4C9BE8"),
        go.Bar(name="Girls", x=classes, y=d[GIRLS_COLS].sum().values, marker_color="#F06292"),
    ])
    fig.update_layout(title="Demographic Reach — Enrollment by Class & Gender",
                      barmode="group",legend=dict(orientation="h",y=-0.2),
                      margin=dict(t=50,b=40),plot_bgcolor="white",yaxis_title="Enrollment")
    return fig


@callback(Output("chart-top-districts","figure"),
          Input("filter-year","value"), Input("filter-state","value"), Input("filter-district","value"))
def chart_top_districts(years, states, districts):
    if not districts: return go.Figure()
    d   = filter_df(years, states, districts)
    top = (d.groupby("district_name")["total_enrollment"].sum()
            .nlargest(15).reset_index().sort_values("total_enrollment"))
    fig = px.bar(top, x="total_enrollment", y="district_name", orientation="h",
                 title="Demographic Reach — Top 15 Districts",
                 labels={"total_enrollment":"Enrollment","district_name":""},
                 color="total_enrollment", color_continuous_scale="Blues")
    fig.update_layout(margin=dict(t=50,b=30,l=120),plot_bgcolor="white",coloraxis_showscale=False)
    return fig


@callback(Output("chart-funnel","figure"),
          Input("filter-year","value"), Input("filter-state","value"), Input("filter-district","value"))
def chart_funnel(years, states, districts):
    if not districts: return go.Figure()
    d = filter_df(years, states, districts)
    stages = {f"Class {i}": int(d[f"class_{i}_boys"].sum()+d[f"class_{i}_girls"].sum())
              for i in range(1, 13)}
    fig = go.Figure(go.Funnel(
        y=list(stages.keys()), x=list(stages.values()),
        textposition="inside", textinfo="value+percent initial",
        marker={"color":["#0052A5","#1565C0","#1976D2","#1E88E5","#2196F3","#64B5F6",
                         "#EF6C00","#F57C00","#FB8C00","#FF6B35","#FFA726","#FFD54F"]},
    ))
    fig.update_layout(title="Programme Progress — Funnel Cl 1→12",
                      margin=dict(t=50,b=10,l=10,r=10))
    return fig


@callback(Output("chart-hs-transition","figure"),
          Input("filter-year","value"), Input("filter-state","value"), Input("filter-district","value"))
def chart_hs_transition(years, states, districts):
    if not districts: return go.Figure()
    d   = filter_df(years, states, districts).replace([np.inf,-np.inf], np.nan)
    agg = d.groupby("ac_year")["hs_transition_pct"].median().reset_index().dropna(subset=["hs_transition_pct"])
    if agg.empty:
        fig = go.Figure()
        fig.update_layout(title="Class 10-11 Transition % (No data)", margin=dict(t=60,b=30))
        return fig
    fig = px.line(agg, x="ac_year", y="hs_transition_pct", markers=True,
                  title="Class 10 to 11 Transition %",
                  labels={"hs_transition_pct":"%","ac_year":"Year"},
                  color_discrete_sequence=[C["primary"]])
    fig.update_layout(margin=dict(t=60,b=30),plot_bgcolor="white",yaxis_title="%")
    fig.add_hline(y=100, line_dash="dot", line_color="gray")
    return fig


@callback(Output("chart-passrate","figure"),
          Input("filter-state","value"), Input("t-passrate","value"))
def chart_passrate(states, t_pass):
    states_t = [s.strip().title() for s in (states or [])]
    sub = sec_df[sec_df["statname"].isin(states_t)].dropna(subset=["pass_rate"])
    if sub.empty: sub = sec_df.dropna(subset=["pass_rate"])
    sub = sub.sort_values("pass_rate")
    fig = go.Figure()
    fig.add_bar(y=sub["statname"], x=sub["pass_rate_boys"],  name="Boys",  orientation="h", marker_color="#4C9BE8")
    fig.add_bar(y=sub["statname"], x=sub["pass_rate_girls"], name="Girls", orientation="h", marker_color="#F06292")
    fig.add_vline(x=t_pass or 85, line_dash="dot", line_color="red",
                  annotation_text=f"Target {t_pass or 85}%")
    fig.add_vline(x=NATIONAL_AVG["passrate"], line_dash="dash", line_color="#aaa",
                  annotation_text=f"National {NATIONAL_AVG['passrate']:.0f}%", annotation_position="bottom right")
    fig.update_layout(title="Class 10 Pass Rate — Boys vs Girls",barmode="group",
                      xaxis_title="Pass Rate %",legend=dict(orientation="h",y=-0.15),
                      margin=dict(t=50,b=50,l=140),plot_bgcolor="white",xaxis=dict(range=[0,105]))
    return fig


@callback(Output("chart-passrate-eq","figure"), Input("filter-state","value"))
def chart_passrate_equity(states):
    states_t = [s.strip().title() for s in (states or [])]
    sub = sec_df[sec_df["statname"].isin(states_t)].dropna(subset=["pass_rate"])
    if sub.empty: sub = sec_df.dropna(subset=["pass_rate"])
    sub = sub.sort_values("pass_rate")
    fig = go.Figure()
    fig.add_bar(y=sub["statname"], x=sub["pass_rate"],    name="General", orientation="h", marker_color=C["primary"])
    fig.add_bar(y=sub["statname"], x=sub["pass_rate_sc"], name="SC",      orientation="h", marker_color="#fd7e14")
    fig.add_bar(y=sub["statname"], x=sub["pass_rate_st"], name="ST",      orientation="h", marker_color=C["danger"])
    fig.update_layout(title="Equity Gap — General vs SC vs ST",barmode="group",
                      xaxis_title="Pass Rate %",legend=dict(orientation="h",y=-0.15),
                      margin=dict(t=50,b=50,l=140),plot_bgcolor="white",xaxis=dict(range=[0,105]))
    return fig


@callback(Output("chart-ptr","figure"),
          Input("filter-state","value"), Input("filter-district","value"), Input("t-ptr","value"))
def chart_ptr(states, districts, t_ptr):
    states_t = [s.strip().title() for s in (states or [])]
    sub = dist_df[dist_df["state_name"].isin(states_t)].dropna(subset=["ptr","literacy_rate"])
    if sub.empty: return go.Figure()
    fig = px.scatter(sub, x="literacy_rate", y="ptr", color="state_name",
                     hover_name="district_name",
                     title="Pupil-Teacher Ratio vs Literacy Rate",
                     labels={"literacy_rate":"Literacy %","ptr":"PTR","state_name":"State"})
    fig.add_hline(y=t_ptr or 30, line_dash="dot", line_color="red",
                  annotation_text=f"Target PTR {t_ptr or 30}")
    fig.add_hline(y=NATIONAL_AVG["ptr"], line_dash="dash", line_color="#aaa",
                  annotation_text=f"National avg {int(NATIONAL_AVG['ptr'])}",
                  annotation_position="bottom right")
    fig.update_layout(margin=dict(t=50,b=40),plot_bgcolor="white")
    return fig


@callback(Output("chart-equity","figure"),
          Input("filter-state","value"), Input("filter-district","value"))
def chart_equity(states, districts):
    states_t = [s.strip().title() for s in (states or [])]
    dist_sub = dist_df[dist_df["state_name"].isin(states_t)].dropna(subset=["girls_toilet_pct"])
    gpi_dist = (df[df["ac_year"]==YEARS[-1]].groupby("district_name")["gpi"].median().reset_index())
    gpi_dist["district_name"] = gpi_dist["district_name"].str.strip().str.upper()
    merged = dist_sub.merge(gpi_dist, on="district_name", how="inner")
    merged = merged.dropna(subset=["girls_toilet_pct","gpi","population_k","mdm_pct"])
    merged = merged[merged["population_k"] > 0]
    if merged.empty: return go.Figure()
    fig = px.scatter(merged, x="girls_toilet_pct", y="gpi", color="mdm_pct", size="population_k",
                     hover_name="district_name", color_continuous_scale="Greens",
                     title="Equity: Girls Toilet Coverage vs GPI (bubble=population, color=MDM)",
                     labels={"girls_toilet_pct":"Girls Toilet %","gpi":"GPI","mdm_pct":"MDM %"})
    fig.add_hline(y=1.0, line_dash="dot", line_color="gray", annotation_text="GPI parity")
    fig.update_layout(margin=dict(t=70,b=40),plot_bgcolor="white")
    return fig


if __name__ == "__main__":
    app.run(debug=True)

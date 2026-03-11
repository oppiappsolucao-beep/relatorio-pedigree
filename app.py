# app.py
import os
import time
import re
import datetime as dt
import pandas as pd
import streamlit as st

AUTO_REFRESH_SECONDS = 60
CACHE_TTL_SECONDS = 60

st.set_page_config(page_title="Pedigree — Visão Geral (TV)", page_icon="🪪", layout="wide")

SHEET_ID = "1Q0mLvOBxEGCojUITBLxCXRtpXVMAHE3ngvGsa2Cgf9Q"
GID_COMISSAO_JULLIA = 583435424
GID_CLEAR = 1396326144

APP_BOOT = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
APP_VERSION = os.getenv("APP_VERSION", f"boot@{APP_BOOT}")

# -------------------------------
# AUTO REFRESH
# -------------------------------
st.markdown(
f"""
<script>
const refreshMs = {AUTO_REFRESH_SECONDS * 1000};
setTimeout(() => {{
const url = new URL(window.location.href);
url.searchParams.set("_tv", Date.now());
window.location.replace(url.toString());
}}, refreshMs);
</script>
""",
unsafe_allow_html=True,
)

# -------------------------------
# STYLE
# -------------------------------
st.markdown("""
<style>

.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px; }

[data-testid="stAppViewContainer"] { background: #f6f7fb; }

.tv-title { font-size: 46px; font-weight: 900; color: #111827; }

.tv-subtitle { font-size: 16px; color: #6b7280; margin-bottom: 1.2rem; }

.big-kpi {
background: white;
border-radius: 18px;
padding: 22px;
border: 1px solid #e5e7eb;
box-shadow: 0 8px 22px rgba(17,24,39,0.06);
margin-bottom: 1.2rem;
}

.big-kpi .value {
font-size: 60px;
font-weight: 900;
}

.kpi-card {
background: white;
border-radius: 18px;
padding: 18px;
border: 1px solid #e5e7eb;
box-shadow: 0 8px 22px rgba(17,24,39,0.06);
position: relative;
min-height: 112px;
}

.kpi-accent {
position: absolute;
left: 0;
top: 14px;
bottom: 14px;
width: 8px;
border-radius: 12px;
}

.kpi-title {
font-size: 15px;
font-weight: 800;
margin-left: 16px;
}

.kpi-sub {
font-size: 12px;
color: #6b7280;
margin-left: 16px;
}

.kpi-value {
font-size: 38px;
font-weight: 900;
margin-left: 16px;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------
# HELPERS
# -------------------------------

@st.cache_data(show_spinner=False, ttl=CACHE_TTL_SECONDS)
def load_gid(gid):

    bust = int(time.time()*1000)

    url=f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={gid}&_={bust}"

    df=pd.read_csv(url)

    df.columns=[c.strip() for c in df.columns]

    return df


def kpi_card(title,value,subtitle,accent="#6366f1"):

    st.markdown(f"""
<div class="kpi-card">
<div class="kpi-accent" style="background:{accent}"></div>
<div class="kpi-title">{title}</div>
<div class="kpi-value">{value}</div>
<div class="kpi-sub">{subtitle}</div>
</div>
""",unsafe_allow_html=True)


def detect_col(df,predicates):

    for c in df.columns:

        cl=c.strip().lower()

        if any(p(cl) for p in predicates):

            return c

    return None


# -------------------------------
# LOAD DATA
# -------------------------------
df = load_gid(GID_COMISSAO_JULLIA)
df_clear = load_gid(GID_CLEAR)

# -------------------------------
# FILHOTES KPI
# -------------------------------
filhotes_total = len(df_clear)

st.markdown('<div class="tv-title">Pedigree — Visão Geral</div>', unsafe_allow_html=True)

st.markdown(
f'<div class="tv-subtitle">Dashboard Pedigree • versão {APP_VERSION}</div>',
unsafe_allow_html=True
)

st.markdown(f"""
<div class="big-kpi">
<div>FILHOTES VENDIDOS</div>
<div class="value">{filhotes_total}</div>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# STATUS PEDIGREE
# -------------------------------

st.markdown("### Status Pedigree (aba Clear • total acumulado)")

CLEAR_COL_STATUS = detect_col(df_clear,[lambda s:"status pedigree" in s])

STATUS_LIST = [

"Fazer Pedigree Venda",
"Fazer Predigree s/ trans",
"Fazer RG/Certidão",
"Pendências / Problemas",
"Aprovação Cliente",
"Para Imprimir Pedigree",
"Imprimir Etiqueta",
"Imprimir RG + Certidão",
"Airtag",
"Envio Correio",
"Postado/Enviado Corr",
"Postado/ enviado loja",
"Pendencia Cliente",
"Sem Matriz",

]

def norm(v):

    s=str(v or "").strip()

    s=re.sub(r"\s+"," ",s)

    return s


if CLEAR_COL_STATUS:

    status_series=df_clear[CLEAR_COL_STATUS].fillna("").astype(str).map(norm)

    status_series=status_series[status_series!=""]

    counts=status_series.value_counts().to_dict()

    cols=4
    rows=(len(STATUS_LIST)+cols-1)//cols

    grid=[st.columns(cols) for _ in range(rows)]

    for i,status in enumerate(STATUS_LIST):

        r=i//cols
        c=i%cols

        val=int(counts.get(status,0))

        with grid[r][c]:

            kpi_card(status,val,"registros acumulados")

else:

    st.warning("Coluna 'Status Pedigree' não encontrada")

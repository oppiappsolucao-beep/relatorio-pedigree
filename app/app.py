# dashboard_sheets_versao2_fixed_v27_corrige_valores_remove_ticket_grafico.py
# Pedigree — Visão Geral (TV)
# - Pedigree (vendas/valores): gid 583435424 (Comissão Jullia)
# - Filhotes vendidos (KPI topo): aba Clear gid 1396326144

import streamlit as st
import pandas as pd
import datetime as dt
import re

st.set_page_config(page_title="Pedigree — Visão Geral (TV)", page_icon="🪪", layout="wide")

# -------------------------------
# IDs
# -------------------------------
SHEET_ID = "1Q0mLvOBxEGCojUITBLxCXRtpXVMAHE3ngvGsa2Cgf9Q"
GID_COMISSAO_JULLIA = 583435424
GID_CLEAR = 1396326144

# -------------------------------
# Style (TV / cards)
# -------------------------------
st.markdown(
    """
<style>
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px; }
[data-testid="stAppViewContainer"] { background: #f6f7fb; }

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.tv-title { font-size: 46px; font-weight: 900; letter-spacing: 0.5px; margin: 0.1rem 0 0.2rem 0; color: #111827; }
.tv-subtitle { font-size: 16px; color: #6b7280; margin-bottom: 1.2rem; }

.big-kpi { background: white; border-radius: 18px; padding: 22px 22px; border: 1px solid #e5e7eb;
           box-shadow: 0 8px 22px rgba(17,24,39,0.06); margin-bottom: 1.2rem; }
.big-kpi .label { font-size: 14px; color: #6b7280; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
.big-kpi .value { font-size: 60px; font-weight: 900; color: #111827; line-height: 1.05; margin-top: 6px; }

.kpi-card { background: white; border-radius: 18px; padding: 18px 18px; border: 1px solid #e5e7eb;
            box-shadow: 0 8px 22px rgba(17,24,39,0.06); position: relative; min-height: 112px; }
.kpi-accent { position: absolute; left: 0; top: 14px; bottom: 14px; width: 8px; border-radius: 12px; }
.kpi-title { font-size: 15px; font-weight: 800; color: #111827; margin-left: 16px; }
.kpi-sub { font-size: 12px; color: #6b7280; margin-left: 16px; margin-top: 4px; }
.kpi-value { font-size: 38px; font-weight: 900; color: #111827; margin-left: 16px; margin-top: 10px; line-height: 1.0; }

.pill { display: inline-block; padding: 6px 10px; border-radius: 999px; background: #eef2ff; border: 1px solid #e0e7ff;
        font-size: 12px; font-weight: 700; color: #3730a3; margin-right: 8px; }

.kpi-value { white-space: nowrap; }

.kpi-card.compact { min-height: 104px; padding: 14px 14px; }
.kpi-card.compact .kpi-title { font-size: 13px; margin-left: 14px; }
.kpi-card.compact .kpi-value { font-size: 24px; margin-left: 14px; margin-top: 8px; }
.kpi-card.compact .kpi-sub { font-size: 12px; margin-left: 14px; margin-top: 2px; }

</style>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# Helpers
# -------------------------------
@st.cache_data(show_spinner=False)
def load_gid(gid: int) -> pd.DataFrame:
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={gid}"
    df = pd.read_csv(url)
    df.columns = [c.strip() for c in df.columns]
    return df

def brl_to_float(v):
    if pd.isna(v):
        return 0.0
    s = str(v).strip()
    if not s:
        return 0.0
    s = s.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0

def money_br(v):
    try:
        v = float(v)
    except Exception:
        v = 0.0
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def parse_date_any(v):
    if pd.isna(v):
        return None
    s = str(v).strip()
    if not s:
        return None
    d = pd.to_datetime(s, dayfirst=True, errors="coerce")
    if pd.isna(d):
        return None
    return d.date()

def month_name_to_int(s: str):
    s = str(s).strip().lower()
    meses = {
        "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
        "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
        "outubro": 10, "novembro": 11, "dezembro": 12
    }
    for k, v in meses.items():
        if k in s:
            return v
    return None

def parse_mes(v, fallback_year=None):
    """Return (year, month) or None."""
    if pd.isna(v):
        return None
    s = str(v).strip().lower()
    if not s:
        return None

    mname = month_name_to_int(s)
    if mname:
        y = re.search(r"(20\d{2})", s)
        year = int(y.group(1)) if y else (fallback_year if fallback_year else dt.date.today().year)
        return (year, mname)

    m = re.search(r"(\d{1,2})/(20\d{2})", s)
    if m:
        return (int(m.group(2)), int(m.group(1)))

    m2 = re.search(r"(20\d{2})[-/](\d{1,2})", s)
    if m2:
        return (int(m2.group(1)), int(m2.group(2)))

    d = parse_date_any(s)
    if d:
        return (d.year, d.month)

    return None

def mes_label(ym):
    y, m = ym
    return f"{m:02d}/{y}"

def kpi_card(title, value, subtitle, accent="#4f46e5", compact: bool = False):
    klass = "kpi-card compact" if compact else "kpi-card"
    st.markdown(
        f"""
<div class=\"{klass}\">
  <div class="kpi-accent" style="background:{accent};"></div>
  <div class="kpi-title">{title}</div>
  <div class="kpi-value">{value}</div>
  <div class="kpi-sub">{subtitle}</div>
</div>
        """,
        unsafe_allow_html=True
    )

def soma_coluna(df_part: pd.DataFrame, col: str) -> float:
    if col and col in df_part.columns:
        return df_part[col].apply(brl_to_float).sum()
    return 0.0

def detect_col(df, predicates):
    for c in df.columns:
        cl = c.strip().lower()
        if any(p(cl) for p in predicates):
            return c
    return None

# -------------------------------
# Load data
# -------------------------------
df = load_gid(GID_COMISSAO_JULLIA)
df_clear = load_gid(GID_CLEAR)

# Columns (Comissão Jullia)
COL_UNIDADE = detect_col(df, [lambda s: "unidade" in s, lambda s: "loja" in s])
COL_MES_VENDA = detect_col(df, [lambda s: "mês da venda" in s, lambda s: "mes da venda" in s,
                               lambda s: "mês venda" in s, lambda s: "mes venda" in s,
                               lambda s: "mês de venda" in s, lambda s: "mes de venda" in s])
COL_MES_COMPRA = detect_col(df, [lambda s: "mês da compra do cliente" in s, lambda s: "mes da compra do cliente" in s,
                                lambda s: "mês de compra" in s, lambda s: "mes de compra" in s,
                                lambda s: "compra do cliente" in s])
COL_DATA = detect_col(df, [lambda s: s in ["vendas", "data", "data venda", "data da venda"],
                           lambda s: ("data" in s and "venda" in s)])

# Valor: SEMPRE preferir a coluna "Valor" (para não somar componentes e duplicar)
COL_VALOR = detect_col(df, [lambda s: s == "valor", lambda s: s.startswith("valor ")])

# Produto (coluna D na sua planilha: "Produtos")
COL_PRODUTO = detect_col(df, [lambda s: s == "produtos", lambda s: s == "produto", lambda s: "produto" in s,
                              lambda s: s == "pedigree", lambda s: s.startswith("pedigree")])

def row_fallback_year(row):
    if COL_DATA and COL_DATA in row:
        d = parse_date_any(row[COL_DATA])
        if d:
            return d.year
    return dt.date.today().year

def get_mes_venda_key(row):
    fy = row_fallback_year(row)
    if COL_MES_VENDA and COL_MES_VENDA in row and pd.notna(row[COL_MES_VENDA]):
        mk = parse_mes(row[COL_MES_VENDA], fallback_year=fy)
        if mk:
            return mk
    if COL_DATA and COL_DATA in row and pd.notna(row[COL_DATA]):
        mk2 = parse_mes(row[COL_DATA], fallback_year=fy)
        if mk2:
            return mk2
    return None

def get_mes_compra_key(row):
    # usar o MESMO ano do mês da venda como fallback
    mv = get_mes_venda_key(row)
    fy = mv[0] if mv else row_fallback_year(row)
    if COL_MES_COMPRA and COL_MES_COMPRA in row and pd.notna(row[COL_MES_COMPRA]):
        mk = parse_mes(row[COL_MES_COMPRA], fallback_year=fy)
        if mk:
            return mk
    return None

df["_mes_venda_key"] = df.apply(get_mes_venda_key, axis=1)
df["_mes_compra_key"] = df.apply(get_mes_compra_key, axis=1)

df_valid = df[df["_mes_venda_key"].notna()].copy()

# Dropdown options: todos os meses presentes
def _collect_mes_venda_options(dframe):
    """Collect ALL month options present in the sheet.
    Sources:
      - computed _mes_venda_key
      - raw month column (Mês da Venda)
      - sale date column (Data da Venda / Vendas)
    """
    opts = set()

    # 1) from computed key (already robust)
    if "_mes_venda_key" in dframe.columns:
        for v in dframe["_mes_venda_key"].dropna().unique():
            try:
                opts.add(tuple(v))
            except Exception:
                pass

    # 2) from raw month column (handles month name without year)
    if COL_MES_VENDA and COL_MES_VENDA in dframe.columns:
        for _, row in dframe.iterrows():
            raw = row.get(COL_MES_VENDA, None)
            if pd.isna(raw):
                continue
            fy = row_fallback_year(row)
            mk = parse_mes(raw, fallback_year=fy)
            if mk:
                opts.add(mk)

    # 3) from sale date column (guarantees months like Fevereiro appear even if month text is inconsistent)
    if COL_DATA and COL_DATA in dframe.columns:
        for v in dframe[COL_DATA].dropna().tolist():
            mk = parse_mes(v, fallback_year=dt.date.today().year)
            if mk:
                opts.add(mk)

    return sorted(list(opts), key=lambda x: (x[0], x[1]))

all_mes_venda = _collect_mes_venda_options(df)

default_month = all_mes_venda[-1] if all_mes_venda else (dt.date.today().year, dt.date.today().month)

# -------------------------------
# Filters row (separado, modo TV)
# -------------------------------
st.markdown(
    """<style>
    .filter-wrap { background: rgba(255,255,255,0.0); padding: 0.2rem 0 0.6rem 0; }
    .stSelectbox > div { min-width: 220px; }
    </style>""",
    unsafe_allow_html=True
)

f1, f2, f3 = st.columns([1.0, 1.2, 1.2])

with f1:
    st.markdown('<span class="pill">🪪 Setor: Pedigree</span>', unsafe_allow_html=True)

with f2:
    selected_mes_venda = st.selectbox(
        "Mês da Venda",
        options=all_mes_venda,
        index=all_mes_venda.index(st.session_state.get("mes_venda_sel", default_month)) if st.session_state.get("mes_venda_sel", default_month) in all_mes_venda else 0,
        format_func=mes_label,
        key="mes_venda_sel",
    )

with f3:
    if COL_UNIDADE:
        unidades = ["Todas"] + sorted([
            u for u in df_valid[COL_UNIDADE].dropna().astype(str).unique()
            if str(u).strip() != ""
        ])
        unidade = st.selectbox("Unidade", options=unidades, index=0)
    else:
        unidade = "Todas"
        st.markdown('<span class="pill">🏬 Unidade: (não encontrada)</span>', unsafe_allow_html=True)

if COL_UNIDADE and unidade != "Todas":
    df_valid = df_valid[df_valid[COL_UNIDADE].astype(str).str.strip() == str(unidade).strip()].copy()

# -------------------------------
# KPI topo: Filhotes vendidos (aba Clear)
# -------------------------------
def _detect_mes_col_clear(dfc):
    # na sua aba Clear: coluna "Mês"
    for c in dfc.columns:
        cl = c.strip().lower()
        if cl in ["mês", "mes"]:
            return c
    for c in dfc.columns:
        if "mês" in c.strip().lower() or "mes" in c.strip().lower():
            return c
    return None

CLEAR_COL_MES = _detect_mes_col_clear(df_clear)
CLEAR_COL_ID = detect_col(df_clear, [lambda s: s == "nome", lambda s: "cpf" in s, lambda s: "cliente" in s]) or (df_clear.columns[0] if len(df_clear.columns) else None)

filhotes_mes = 0
if CLEAR_COL_MES:
    tmp = df_clear.copy()
    tmp["_mk"] = tmp[CLEAR_COL_MES].apply(lambda v: parse_mes(v, fallback_year=selected_mes_venda[0]))
    tmp = tmp[tmp["_mk"].notna()]
    tmp_mes = tmp[tmp["_mk"] == selected_mes_venda]
    if CLEAR_COL_ID and CLEAR_COL_ID in tmp_mes.columns:
        filhotes_mes = tmp_mes[CLEAR_COL_ID].astype(str).str.strip().ne("").sum()
    else:
        filhotes_mes = len(tmp_mes)

# -------------------------------
# Core logic (Comissão Jullia)
# -------------------------------
df_mes_venda = df_valid[df_valid["_mes_venda_key"] == selected_mes_venda].copy()
df_mesmo_mes = df_mes_venda[df_mes_venda["_mes_compra_key"] == selected_mes_venda].copy()
df_outros_meses = df_mes_venda[df_mes_venda["_mes_compra_key"] != selected_mes_venda].copy()

q_total_mes_venda = len(df_mes_venda)
q_mesmo = len(df_mesmo_mes)
q_outros = len(df_outros_meses)

def soma_valor(df_part):
    # Preferir SEMPRE a coluna Valor (evita somar Clear/Silmario/etc e duplicar)
    if COL_VALOR and COL_VALOR in df_part.columns:
        return df_part[COL_VALOR].apply(brl_to_float).sum()
    # fallback: se não existir Valor, soma qualquer coluna numérica BRL conhecida
    total = 0.0
    for c in df_part.columns:
        cl = c.strip().lower()
        if cl in ["silmario", "correios", "airtag", "certidão", "certidao", "jullia", "julia", "clear"]:
            total += df_part[c].apply(brl_to_float).sum()
    return total

v_total_mes_venda = soma_valor(df_mes_venda)
v_mesmo = soma_valor(df_mesmo_mes)
v_outros = soma_valor(df_outros_meses)

# -------------------------------
# Header
# -------------------------------
st.markdown('<div class="tv-title">Pedigree — Visão Geral</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="tv-subtitle">Filtro por <b>Mês da Venda</b> • Comissão Jullia (gid {GID_COMISSAO_JULLIA}) • Mês selecionado: <b>{mes_label(selected_mes_venda)}</b> • Unidade: <b>{unidade}</b></div>',
    unsafe_allow_html=True
)

# Big KPI (filhotes)
st.markdown(
    f"""
<div class="big-kpi">
  <div class="label">FILHOTES VENDIDOS (aba Clear)</div>
  <div class="value">{filhotes_mes}</div>
</div>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# Cards row 1 (SEM ticket médio)
# -------------------------------
c1, c2, c3 = st.columns(3)
with c1:
    kpi_card("Vendas registradas no mês", f"{q_total_mes_venda}", f"Mês Venda: {mes_label(selected_mes_venda)}", accent="#f59e0b")
with c2:
    kpi_card("Compras no mesmo mês", f"{q_mesmo}", "Mês Compra = Mês Venda", accent="#10b981")
with c3:
    kpi_card("Compras de outros meses", f"{q_outros}", "Mês Compra ≠ Mês Venda", accent="#ef4444")

# -------------------------------
# Cards row 2 (3 quadrados lado a lado)
# -------------------------------
c4, c5, c6 = st.columns(3)
with c4:
    kpi_card("Faturamento do mês (registrado)", money_br(v_total_mes_venda), "somatório do mês selecionado", accent="#6366f1")
with c5:
    kpi_card("R$ mesmo mês", money_br(v_mesmo), "valor das compras no mesmo mês", accent="#059669")
with c6:
    kpi_card("R$ outros meses", money_br(v_outros), "valor das compras de outros meses", accent="#b91c1c")

st.markdown("<div class='tv-subtitle' style='margin-top:10px;'>*Obs.: se “Mês de Compra” estiver vazio, entra em “outros meses”.*</div>", unsafe_allow_html=True)

# -------------------------------
# Gráfico – Quantidade de produtos (mês selecionado)
# (horizontal, estilo BI / TV — sem libs extras)
# -------------------------------
st.markdown("### Quantidade de produtos (mês selecionado)")

if COL_PRODUTO and COL_PRODUTO in df_mes_venda.columns:
    prod_counts = (
        df_mes_venda[COL_PRODUTO]
        .astype(str)
        .str.strip()
        .replace("", "Não informado")
        .value_counts()
        .sort_values(ascending=True)
    )

    if not prod_counts.empty:
        import plotly.express as px

        chart_df = prod_counts.reset_index()
        chart_df.columns = ["Produto", "Quantidade"]

        fig = px.bar(
            chart_df,
            x="Quantidade",
            y="Produto",
            orientation="h",
            text="Quantidade",
            height=max(320, 45 * len(chart_df)),
        )

        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis_title="Quantidade",
            yaxis_title="",
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum produto encontrado para o mês selecionado.")
else:
    st.info("Coluna de produtos não encontrada (esperado: coluna D / 'Produtos').")

# -------------------------------
# Totais por componente (mês selecionado) — abaixo de tudo
# -------------------------------
st.markdown("### Totais por componente (mês selecionado)")

COL_SILMARIO = detect_col(df, [lambda s: s == "silmario"])
COL_CLEAR_CMP = detect_col(df, [lambda s: s == "clear"])
COL_CORREIOS = detect_col(df, [lambda s: s == "correios"])
COL_AIRTAG = detect_col(df, [lambda s: s in ["airtag", "air tag"]])
COL_CERTIDAO = detect_col(df, [lambda s: s in ["certidão", "certidao"]])
COL_JULLIA = detect_col(df, [lambda s: s in ["jullia", "julia"]])

v_silmario = soma_coluna(df_mes_venda, COL_SILMARIO)
v_clear_cmp = soma_coluna(df_mes_venda, COL_CLEAR_CMP)
v_correios = soma_coluna(df_mes_venda, COL_CORREIOS)
v_airtag = soma_coluna(df_mes_venda, COL_AIRTAG)
v_certidao = soma_coluna(df_mes_venda, COL_CERTIDAO)
v_jullia = soma_coluna(df_mes_venda, COL_JULLIA)

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    kpi_card("Silmario", money_br(v_silmario), "total no mês", accent="#0ea5e9", compact=True)
with k2:
    kpi_card("Clear", money_br(v_clear_cmp), "total no mês", accent="#f97316", compact=True)
with k3:
    kpi_card("Correios", money_br(v_correios), "total no mês", accent="#2563eb", compact=True)
with k4:
    kpi_card("AirTag", money_br(v_airtag), "total no mês", accent="#f59e0b", compact=True)
with k5:
    kpi_card("Certidão", money_br(v_certidao), "total no mês", accent="#16a34a", compact=True)
with k6:
    kpi_card("Jullia", money_br(v_jullia), "total no mês", accent="#7c3aed", compact=True)


# -------------------------------
# Status Pedigree (aba Clear) — abaixo de tudo
# -------------------------------
st.markdown("### Status Pedigree (aba Clear • mês selecionado)")

# Detect column "Status Pedigree" inside Clear sheet
CLEAR_COL_STATUS = detect_col(
    df_clear,
    [
        lambda s: s == "status pedigree",
        lambda s: "status pedigree" in s,
    ]
)

# Lista fixa (12) — exatamente como no dropdown da planilha
STATUS_LIST = [
    "Fazer Pedigree Venda",
    "Fazer Pedigree s/ trans",
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
]

def _norm_status(v: str) -> str:
    s = str(v or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

if not CLEAR_COL_MES:
    st.warning("Na aba Clear não foi encontrada a coluna 'Mês' para filtrar por mês.")
elif not CLEAR_COL_STATUS or CLEAR_COL_STATUS not in df_clear.columns:
    st.warning("Na aba Clear não foi encontrada a coluna 'Status Pedigree'.")
else:
    clear_tmp = df_clear.copy()
    clear_tmp["_mk"] = clear_tmp[CLEAR_COL_MES].apply(lambda v: parse_mes(v, fallback_year=selected_mes_venda[0]))
    clear_tmp = clear_tmp[clear_tmp["_mk"].notna()]
    clear_mes = clear_tmp[clear_tmp["_mk"] == selected_mes_venda].copy()

    if clear_mes.empty:
        st.info("Ainda não há registros na aba Clear para o mês selecionado.")
    else:
        # Conta por status (ignorando vazios)
        col_series = clear_mes[CLEAR_COL_STATUS].fillna("").astype(str).str.strip()
        col_series = col_series[col_series.ne("")]

        counts_map = {}
        if not col_series.empty:
            vc = col_series.map(_norm_status).value_counts()
            counts_map = vc.to_dict()

        # Render 12 cards fixos (4 colunas x 3 linhas)
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        rows = [st.columns(4), st.columns(4), st.columns(4)]

        for idx, status in enumerate(STATUS_LIST):
            r = idx // 4
            c = idx % 4
            val = int(counts_map.get(_norm_status(status), 0))

            # Cores (só para diferenciar visualmente)
            stl = status.lower()
            if "pend" in stl or "proble" in stl:
                accent = "#ef4444"
            elif "aprova" in stl:
                accent = "#10b981"
            elif "imprimir" in stl:
                accent = "#2563eb"
            elif "postado" in stl or "envio" in stl or "correio" in stl:
                accent = "#f59e0b"
            else:
                accent = "#6366f1"

            with rows[r][c]:
                kpi_card(status, f"{val}", "registros no mês", accent=accent, compact=True)

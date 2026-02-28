import os
import streamlit as st

# ============================================================
# CONFIG & INIT
# ============================================================
st.set_page_config(
    page_title="VinoLogix | Simulador Logístico",
    layout="wide",
    page_icon="🍷"
)

# ============================================================
# LOGIN DE USUARIO (Debe ir justo después de la configuración)
# ============================================================
from utils.auth import check_login
check_login()

from utils.config import CATALOGOS, DATA_DIR
from utils.state import init_session_state, get_inputs, apply_scenario
from utils.io_data import load_parametros_base
from utils.calculos_costos import (
    convertir_volumen,
    calcular_costos_operacion,
    calcular_tributos
)
from utils.checklist import (
    load_checklist_csv,
    filtrar_por_modalidad,
    calcular_cumplimiento
)
from utils.graficas import (
    fig_costos_donut,
    fig_costos_waterfall,
    fig_cumplimiento_gauge
)

init_session_state()

# ============================================================
# STYLE (CSS) - Sidebar Blanco
# ============================================================
st.markdown("""
<style>
.block-container { padding-top: 1.0rem; padding-bottom: 1.5rem; }
section[data-testid="stSidebar"] { background-color: #FFFFFF !important; }
div[data-testid="stExpander"] details { border-radius: 10px; }
div[data-testid="stMetric"] { padding: 0.2rem 0.2rem; }
button[data-baseweb="tab"] { font-size: 0.95rem; }
div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
h1, h2, h3 { margin-bottom: 0.3rem; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOADERS (Aquí estaba el error de 'base', ya está corregido)
# ============================================================
@st.cache_data(show_spinner=False)
def _load_base():
    param_path = DATA_DIR / "parametros_base.csv"
    return load_parametros_base(str(param_path))


def _load_checklist_all():
    check_path = DATA_DIR / "checklist_normativo.csv"
    if check_path.exists():
        return load_checklist_csv(str(check_path))
    return None

base = _load_base()
check_df_all = _load_checklist_all()

# ============================================================
# UI HELPERS 
# ============================================================
def _render_brand_header():
    left, right = st.columns([0.75, 0.25], vertical_alignment="center")
    with left:
        st.title("VinoLogix")
        st.caption(f"👤 Analista en sesión: **{st.session_state.usuario}** | Importación Francia → Colombia")
    with right:
        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            st.image(logo_path, width=140)

def _render_quick_guide():
    with st.expander("📘 Guía rápida (para usuarios no técnicos)", expanded=False):
        st.markdown(
            """
            **Cómo usar la app**
            1) Configura el escenario en la **barra lateral**.  
            2) Presiona **Actualizar análisis**.  
            3) Revisa los KPIs en Home y luego valida requisitos en **Checklist Normativo**.  
            4) Exporta en **Reporte** (PDF/Excel).
            """
        )

def _render_assumptions_box():
    with st.expander("🧾 Supuestos TDG y rangos esperados (para validar coherencia)", expanded=False):
        st.markdown(
            """
            Referencias típicas (pueden variar por operador/mercado):
            - **Embotellado 750 ml**: ~11.250 L ≈ 15.000 botellas por contenedor 40 ft.  
            - **Flexitank/Granel**: ~24.000 L por contenedor 40 ft.  
            - **Seguro**: se modela como % (p.ej. 1%) o valor fijo en USD.  
            - **EUR.1 válido**: suele implicar **arancel 0%** (según regla del modelo).  
            """
        )

def _sanity_checks(modalidad: str, cantidad: float, litros: float, eur1: bool):
    msgs = []
    mod = (modalidad or "").lower()

    if mod.startswith("embot"):
        if litros > 18000: msgs.append("⚠️ Litros altos para **Embotellado**. Revisa unidad/cantidad.")
        if 0 < litros < 5000: msgs.append("⚠️ Litros bajos para un escenario típico de contenedor. Revisa unidad/cantidad.")
    elif mod.startswith("granel") or "flex" in mod:
        if 0 < litros < 15000: msgs.append("⚠️ Litros bajos para **Flexitank/Granel**. Revisa unidad/cantidad.")
        if litros > 30000: msgs.append("⚠️ Litros altos para **Flexitank**. Revisa unidad/cantidad.")

    if cantidad == 0 or litros == 0: msgs.append("⚠️ Cantidad/volumen en cero: costos unitarios no interpretables.")
    if not eur1: msgs.append("ℹ️ EUR.1 no válido: revisa impacto en arancel (Costos y Tributos).")

    if msgs:
        for m in msgs: st.warning(m)
    else:
        st.success("Chequeos de coherencia: OK (escenario consistente).")

def _render_kpis(kpis_costos, params_sim, cumpl_pct, riesgo):
    st.subheader("📌 Indicadores clave (KPIs)")
    row1 = st.columns(3)
    row1[0].metric("Costo total (COP)", f"{kpis_costos['costo_total_cop']:,.0f}")
    row1[1].metric("Costo / L (COP/L)", f"{kpis_costos['costo_litro_cop']:,.0f}")
    row1[2].metric("Costo / botella (COP)", f"{kpis_costos['costo_botella_cop']:,.0f}")

    row2 = st.columns(3)
    row2[0].metric("TRM", f"{params_sim['trm']:,.0f}")
    row2[1].metric("Cumplimiento", f"{cumpl_pct:.1f}%")
    row2[2].metric("Riesgo", riesgo)

def _render_dashboard(costos_df, cumpl_pct, res_trib):
    st.subheader("📊 Dashboard (interactivo)")
    g1, g2 = st.columns([1.35, 1.0], vertical_alignment="top")

    with g1:
        st.markdown("**Estructura de costos**")
        t1, t2 = st.tabs(["Donut (participación)", "Waterfall (cascada)"])
        with t1: st.plotly_chart(fig_costos_donut(costos_df), use_container_width=True)
        with t2: st.plotly_chart(fig_costos_waterfall(costos_df), use_container_width=True)

    with g2:
        st.markdown("**Cumplimiento / Riesgo**")
        st.plotly_chart(fig_cumplimiento_gauge(cumpl_pct), use_container_width=True)
        st.caption(f"Arancel (modelo): {res_trib.get('arancel_pct', 0)*100:.1f}%")

        if cumpl_pct >= 85: st.success("Cumplimiento alto: el riesgo tiende a ser bajo.")
        elif cumpl_pct >= 60: st.warning("Cumplimiento medio: revisa pendientes para evitar reprocesos.")
        else: st.error("Cumplimiento bajo: alto riesgo de bloqueos/reprocesos. Revisa checklist.")

def _render_top_actions(check_filtrado, params_sim):
    st.subheader("🧩 Acciones sugeridas (Top pendientes)")
    if check_filtrado is None or len(check_filtrado) == 0:
        st.info("No hay checklist cargado para esta modalidad.")
        return

    pend = check_filtrado.copy()
    pend["estado"] = pend["estado"].astype(str)
    pend = pend[pend["estado"].str.upper() != "OK"]

    if len(pend) == 0:
        st.success("✅ Todo OK. No hay pendientes normativos para este escenario.")
        return

    cols_show = [c for c in ["requisito", "responsable", "evidencia", "observacion"] if c in pend.columns]
    left, right = st.columns([2, 1], vertical_alignment="top")

    with left: st.dataframe(pend.head(7)[cols_show], use_container_width=True, hide_index=True)
    with right:
        st.warning(f"Pendientes: {len(pend)}")
        st.info("👉 Ve a **Checklist Normativo** y marca OK lo soportado.")
        if not bool(params_sim.get("eur1", True)):
            st.info("👉 EUR.1 no válido: revisa el **arancel** en Costos y Tributos.")

def _render_interpretation(res_trib):
    st.subheader("🧠 Interpretación rápida")
    st.markdown(
        f"""
        - Si el **flete internacional** domina la torta, entonces el costo unitario será **muy sensible** a TRM/flete.  
        - Con EUR.1 **no válido**, el **arancel** puede incrementar el costo (en el modelo: **{res_trib.get('arancel_pct',0)*100:.1f}%**).  
        - Un cumplimiento bajo implica riesgo de demoras o retenciones documentales.
        """
    )

def _render_debug(params_sim, litros, botellas, costos_df, trib_df, res_trib):
    with st.expander("🔎 Auditoría / Validación (para sustentar y revisar valores)", expanded=False):
        st.write("**Parámetros simulados**")
        st.json(params_sim)
        st.write("**Volumen calculado**")
        c1, c2 = st.columns(2)
        c1.metric("Litros", f"{litros:,.2f}")
        c2.metric("Botellas (est.)", f"{botellas:,.0f}")
        st.write("**Tabla de costos**")
        st.dataframe(costos_df, use_container_width=True, hide_index=True)
        st.write("**Tabla de tributos**")
        st.dataframe(trib_df, use_container_width=True, hide_index=True)

# ============================================================
# SIDEBAR 
# ============================================================
with st.sidebar:
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=160)

    st.markdown("## Configuración")
    st.caption("Define el escenario y actualiza el análisis.")

    with st.form("form_inputs", border=False):
        st.subheader("Operación")
        st.session_state.modalidad = st.selectbox("Modalidad", CATALOGOS["modalidad"], index=CATALOGOS["modalidad"].index(st.session_state.modalidad))
        st.session_state.incoterm = st.selectbox("Incoterm", CATALOGOS["incoterm"], index=CATALOGOS["incoterm"].index(st.session_state.incoterm))
        st.session_state.puerto = st.selectbox("Puerto ingreso", CATALOGOS["puerto"], index=CATALOGOS["puerto"].index(st.session_state.puerto))
        st.session_state.ciudad = st.selectbox("Ciudad destino", CATALOGOS["ciudad"], index=CATALOGOS["ciudad"].index(st.session_state.ciudad))
        st.session_state.unidad_vol = st.selectbox("Unidad volumen", CATALOGOS["unidad_vol"], index=CATALOGOS["unidad_vol"].index(st.session_state.unidad_vol))
        st.session_state.cantidad = st.number_input("Cantidad", min_value=0.0, value=float(st.session_state.cantidad), step=1.0)

        st.divider()
        st.subheader("Escenario de costos")
        st.session_state.trm = st.number_input("TRM (COP/USD)", min_value=0.0, value=float(st.session_state.trm))
        st.session_state.flete_usd = st.number_input("Flete internacional (USD)", min_value=0.0, value=float(st.session_state.flete_usd))
        st.session_state.seguro_modo = st.selectbox("Seguro", ["pct", "usd"], index=0 if st.session_state.seguro_modo == "pct" else 1)
        st.session_state.seguro_val = st.number_input("Valor seguro", min_value=0.0, value=float(st.session_state.seguro_val))
        st.session_state.bodegaje_cop = st.number_input("Bodegaje/almacenamiento (COP)", min_value=0.0, value=float(st.session_state.bodegaje_cop))
        st.session_state.transporte_interno_cop = st.number_input("Transporte interno (COP)", min_value=0.0, value=float(st.session_state.transporte_interno_cop))
        st.session_state.eur1 = st.checkbox("Certificado EUR.1 válido", value=bool(st.session_state.eur1))

        st.divider()
        st.subheader("Escenario rápido")
        st.session_state.escenario = st.selectbox("Escenario", CATALOGOS["escenario"], index=CATALOGOS["escenario"].index(st.session_state.escenario))
        st.form_submit_button("Actualizar análisis", type="primary")

# ============================================================
# MAIN 
# ============================================================
_render_brand_header()
_render_quick_guide()
_render_assumptions_box()

params = get_inputs()
params_sim = apply_scenario(params)

litros, botellas = convertir_volumen(params_sim["unidad_vol"], float(params_sim["cantidad"]), base, params_sim["modalidad"])
params_sim["litros"] = litros

kpis_costos, costos_df = calcular_costos_operacion(params_sim, base)
res_trib, trib_df = calcular_tributos(params_sim, base)

cumpl_pct, riesgo = 0.0, "N/D"
check_filtrado = None
if check_df_all is not None:
    check_filtrado = filtrar_por_modalidad(check_df_all, params_sim["modalidad"]).copy().fillna("")
    if "estado" not in check_filtrado.columns: check_filtrado["estado"] = check_filtrado.get("estado_default", "Pendiente")
    if len(check_filtrado) > 0: cumpl_pct, riesgo = calcular_cumplimiento(check_filtrado)

_render_kpis(kpis_costos, params_sim, cumpl_pct, riesgo)
st.divider()
st.subheader("✅ Validación rápida del escenario")
_sanity_checks(modalidad=params_sim["modalidad"], cantidad=float(params_sim["cantidad"]), litros=float(litros), eur1=bool(params_sim.get("eur1", True)))
st.divider()
_render_dashboard(costos_df, cumpl_pct, res_trib)
st.divider()
_render_interpretation(res_trib)
st.divider()
_render_top_actions(check_filtrado, params_sim)
_render_debug(params_sim, litros, botellas, costos_df, trib_df, res_trib)
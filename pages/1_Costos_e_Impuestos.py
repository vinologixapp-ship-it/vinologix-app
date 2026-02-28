# pages/1_Costos_e_Impuestos.py
import streamlit as st

from utils.config import DATA_DIR
from utils.state import init_session_state, get_inputs, apply_scenario
from utils.io_data import load_parametros_base
from utils.calculos_costos import convertir_volumen, calcular_costos_operacion, calcular_impuestos
from utils.graficas import fig_costos_donut, fig_costos_waterfall
from utils.ui import set_page_config, apply_global_style, render_sidebar_brand


# 0) Config SIEMPRE primero
set_page_config("Costos e Impuestos", layout="wide")
apply_global_style()
render_sidebar_brand()

# 1) Estado + datos base
init_session_state()
base = load_parametros_base(str(DATA_DIR / "parametros_base.csv"))

# 2) UI
st.title("Costos e Impuestos")
st.caption("Desglose de costos logísticos + cálculo de impuestos. Útil para validar el escenario y comparar alternativas.")

params = get_inputs()
params_sim = apply_scenario(params)

with st.expander("📌 Opcional: FOB (USD) para CIF más exacto", expanded=False):
    fob_default = float(params_sim.get("fob_usd", 0.0) or 0.0)
    fob = st.number_input("FOB (USD)", min_value=0.0, value=fob_default)
    params_sim["fob_usd"] = float(fob)

# Volumen
unidad_vol = params_sim.get("unidad_vol", "Botellas")
cantidad = float(params_sim.get("cantidad", 0.0) or 0.0)
modalidad = params_sim.get("modalidad", "Embotellado")

litros, botellas = convertir_volumen(unidad_vol, cantidad, base, modalidad)
params_sim["litros"] = float(litros)

# Costos e impuestos
kpis_costos, costos_df = calcular_costos_operacion(params_sim, base)
res_trib, trib_df = calcular_impuestos(params_sim, base)

# KPIs cabecera
trm_val = float(params_sim.get("trm", 0.0) or 0.0)
total_impuestos = float(res_trib.get("total_impuestos_cop", 0.0) or 0.0)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Litros estimados", f"{litros:,.2f}")
c2.metric("Botellas 750cc (est.)", f"{botellas:,.0f}")
c3.metric("TRM aplicada", f"{trm_val:,.0f}")
c4.metric("Total impuestos (COP)", f"{total_impuestos:,.0f}")

st.divider()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Costo total operación (COP)", f"{float(kpis_costos.get('costo_total_cop', 0.0)):,.0f}")
k2.metric("Costo por litro (COP/L)", f"{float(kpis_costos.get('costo_litro_cop', 0.0)):,.0f}")
k3.metric("Costo por botella 750cc (COP)", f"{float(kpis_costos.get('costo_botella_cop', 0.0)):,.0f}")
k4.metric("Arancel aplicado", f"{float(res_trib.get('arancel_pct', 0.0))*100:.1f}%")

st.divider()

# Dashboard
left, right = st.columns([1.3, 1.0])

with left:
    st.subheader("Visualización de costos")
    t1, t2 = st.tabs(["Participación (donut)", "Cascada (waterfall)"])
    with t1:
        st.plotly_chart(fig_costos_donut(costos_df), use_container_width=True)
    with t2:
        st.plotly_chart(fig_costos_waterfall(costos_df), use_container_width=True)

with right:
    st.subheader("Lectura rápida")
    st.info(
        "📌 Si el **flete internacional** domina el total, el costo unitario será muy sensible a TRM y flete.\n\n"
        "📌 Si **EUR.1** no está válido, revisa el efecto en **arancel**.\n\n"
        "📌 Si el costo por litro se sale de rango esperado, valida **unidad/cantidad** y modalidad."
    )
    st.caption(
        f"IVA: {float(res_trib.get('iva_pct', 0.0))*100:.1f}% | "
        f"Consumo: {float(res_trib.get('consumo_pct', 0.0))*100:.1f}%"
    )

st.divider()

# Tablas
colA, colB = st.columns(2)
with colA:
    st.subheader("Tabla de costos (operación)")
    st.dataframe(costos_df, use_container_width=True, hide_index=True)

with colB:
    st.subheader("Tabla de impuestos")
    st.caption(
        f"Arancel: {float(res_trib.get('arancel_pct', 0.0))*100:.1f}% | "
        f"IVA: {float(res_trib.get('iva_pct', 0.0))*100:.1f}% | "
        f"Consumo: {float(res_trib.get('consumo_pct', 0.0))*100:.1f}%"
    )
    st.dataframe(trib_df, use_container_width=True, hide_index=True)

with st.expander("🧪 Validación (para sustentación)", expanded=False):
    st.json(params_sim)
# pages/3_Reporte.py
import streamlit as st
import pandas as pd

from utils.config import DATA_DIR
from utils.state import init_session_state, get_inputs, apply_scenario
from utils.io_data import load_parametros_base
from utils.calculos_costos import convertir_volumen, calcular_costos_operacion, calcular_tributos
from utils.checklist import load_checklist_csv, filtrar_por_modalidad, calcular_cumplimiento
from utils.exportables import generar_pdf_bytes
from utils.graficas import fig_costos_donut
from utils.auth import check_login
from utils.ui import set_page_config, apply_global_style, render_sidebar_brand


set_page_config("Reporte", layout="wide")
apply_global_style()
render_sidebar_brand(show_nav_hint=False)

init_session_state()
check_login()

st.title("Reporte del escenario")
st.caption("Visualiza la información relevante del escenario actual y genera un reporte en PDF.")

param_path = DATA_DIR / "parametros_base.csv"
base = load_parametros_base(str(param_path))

params = get_inputs()
params_sim = apply_scenario(params)

litros, botellas = convertir_volumen(
    params_sim.get("unidad_vol", "Botellas"),
    float(params_sim.get("cantidad", 0.0) or 0.0),
    base,
    params_sim.get("modalidad", "Embotellado"),
)
params_sim["litros"] = float(litros)
params_sim["botellas_estimadas"] = float(botellas)

kpis_costos, costos_df = calcular_costos_operacion(params_sim, base)
_, trib_df = calcular_tributos(params_sim, base)

fig_donut = fig_costos_donut(costos_df)
fig_donut.update_layout(
    template="plotly_white",
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(color="black"),
)

check_path = DATA_DIR / "checklist_normativo.csv"
check_filtrado = None
cumpl_pct, riesgo = 0.0, "N/D"

if check_path.exists():
    check_df = load_checklist_csv(str(check_path))
    check_filtrado = filtrar_por_modalidad(
        check_df,
        params_sim.get("modalidad", "Embotellado")
    ).copy()

    if "estado" not in check_filtrado.columns:
        check_filtrado["estado"] = "Pendiente"

    check_filtrado["estado"] = check_filtrado["estado"].fillna("Pendiente").astype(str)
    cumpl_pct, riesgo = calcular_cumplimiento(check_filtrado)

pendientes_df = pd.DataFrame()
if check_filtrado is not None and not check_filtrado.empty and "estado" in check_filtrado.columns:
    pendientes_df = check_filtrado[check_filtrado["estado"].str.upper() != "OK"].copy()

st.subheader("Secciones visibles en pantalla")
colA, colB, colC, colD = st.columns(4)

inc_inputs = colA.checkbox("Parámetros del escenario", value=True)
inc_costos = colB.checkbox("Costos logísticos", value=True)
inc_trib = colC.checkbox("Impuestos y tributos", value=True)
inc_check = colD.checkbox("Checklist normativo", value=True)

st.divider()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Costo total (COP)", f"{float(kpis_costos.get('costo_total_cop', 0.0)):,.0f}")
c2.metric("Litros estimados", f"{float(params_sim.get('litros', 0.0)):,.2f}")
c3.metric("Cumplimiento (%)", f"{float(cumpl_pct):.1f}")
c4.metric("Riesgo", str(riesgo))

st.divider()

if inc_inputs:
    st.subheader("Parámetros del escenario")
    df_inputs = pd.DataFrame(
        [{"Parámetro": k, "Valor": v} for k, v in params_sim.items()]
    )
    st.dataframe(df_inputs, width="stretch", hide_index=True)

if inc_costos:
    st.subheader("Costos logísticos")
    if costos_df is not None and not costos_df.empty:
        st.dataframe(costos_df, width="stretch", hide_index=True)
        st.plotly_chart(fig_donut, width="stretch")
    else:
        st.info("No hay datos de costos para mostrar.")

if inc_trib:
    st.subheader("Impuestos y tributos")
    if trib_df is not None and not trib_df.empty:
        st.dataframe(trib_df, width="stretch", hide_index=True)
    else:
        st.info("No hay datos tributarios para mostrar.")

if inc_check:
    st.subheader("Checklist normativo")
    if check_filtrado is not None and not check_filtrado.empty:
        st.dataframe(check_filtrado, width="stretch", hide_index=True)

        st.markdown("**Pendientes identificados**")
        if not pendientes_df.empty:
            st.dataframe(pendientes_df, width="stretch", hide_index=True)
        else:
            st.success("No hay pendientes. El checklist está completo.")
    else:
        st.info("No se encontró información del checklist normativo.")

st.divider()

inputs_out = params_sim if inc_inputs else {}
costos_out = costos_df if inc_costos else pd.DataFrame()
trib_out = trib_df if inc_trib else pd.DataFrame()

st.subheader("Exportación")
usuario = st.session_state.get("usuario", "Usuario")

if st.button("Generar PDF", type="primary"):
    try:
        pbytes = generar_pdf_bytes(
            titulo="Reporte VinoLogix - Escenario Logístico",
            usuario=usuario,
            kpis=kpis_costos,
            inputs=inputs_out,
            costos_df=costos_out,
            trib_df=trib_out,
            cumplimiento_pct=cumpl_pct,
            riesgo=riesgo,
            top_pendientes_df=pendientes_df,
            fig_costos=fig_donut,
        )

        st.download_button(
            "Descargar PDF",
            data=pbytes,
            file_name="reporte_vinologix.pdf",
            mime="application/pdf",
        )
        st.success("PDF generado correctamente.")

    except Exception as e:
        st.error(f"No fue posible generar el PDF: {e}")
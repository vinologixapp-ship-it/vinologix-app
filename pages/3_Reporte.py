# pages/3_Reporte.py
import streamlit as st
import pandas as pd

from utils.config import DATA_DIR
from utils.state import init_session_state, get_inputs, apply_scenario
from utils.io_data import load_parametros_base
from utils.calculos_costos import convertir_volumen, calcular_costos_operacion, calcular_tributos
from utils.checklist import load_checklist_csv, filtrar_por_modalidad, calcular_cumplimiento
from utils.exportables import exportar_excel_bytes, generar_pdf_bytes
from utils.graficas import fig_costos_donut
from utils.auth import check_login
from utils.ui import set_page_config, apply_global_style, render_sidebar_brand


# 0) Config + estilos + logo (UNA SOLA VEZ)
set_page_config("Reporte", layout="wide")
apply_global_style()
render_sidebar_brand(show_nav_hint=False)

# 1) Estado + login
init_session_state()
check_login()

st.title("Reporte (PDF / Excel)")
st.caption("Genera un reporte resumido del escenario actual con gráficas y checklist normativo incluido.")

# 2) Cargar base
param_path = DATA_DIR / "parametros_base.csv"
base = load_parametros_base(str(param_path))

# 3) Parámetros del escenario
params = get_inputs()
params_sim = apply_scenario(params)

# 4) Volumen
litros, botellas = convertir_volumen(
    params_sim.get("unidad_vol", "Botellas"),
    float(params_sim.get("cantidad", 0.0) or 0.0),
    base,
    params_sim.get("modalidad", "Embotellado"),
)
params_sim["litros"] = float(litros)

# 5) Cálculos
kpis_costos, costos_df = calcular_costos_operacion(params_sim, base)
res_trib, trib_df = calcular_tributos(params_sim, base)

# 6) Gráfica costos
fig_donut = fig_costos_donut(costos_df)
# Fondo blanco para exportación (PDF/Excel)
fig_donut.update_layout(
    template="plotly_white",
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(color="black"),
)

# 7) Checklist + cumplimiento
check_path = DATA_DIR / "checklist_normativo.csv"
check_df = None
check_filtrado = None
cumpl_pct, riesgo = 0.0, "N/D"

if check_path.exists():
    check_df = load_checklist_csv(str(check_path))
    check_filtrado = filtrar_por_modalidad(check_df, params_sim.get("modalidad", "Embotellado")).copy()

    if "estado" not in check_filtrado.columns:
        check_filtrado["estado"] = check_filtrado.get("estado_default", "Pendiente")

    check_filtrado["estado"] = check_filtrado["estado"].fillna("Pendiente").astype(str)
    cumpl_pct, riesgo = calcular_cumplimiento(check_filtrado)

# 8) Pendientes completos para PDF
pendientes_df = pd.DataFrame()
if check_filtrado is not None and len(check_filtrado) > 0 and "estado" in check_filtrado.columns:
    pendientes_df = check_filtrado[check_filtrado["estado"].str.upper() != "OK"]

# 9) Selector de secciones del reporte
st.subheader("Qué incluir en el reporte")
colA, colB, colC, colD = st.columns(4)

inc_inputs = colA.checkbox("Parámetros", value=True)
inc_costos = colB.checkbox("Costos Logísticos", value=True)
inc_trib = colC.checkbox("Impuestos", value=True)
inc_check = colD.checkbox("Checklist Normativo", value=True)

st.divider()

# 10) KPIs resumen
c1, c2, c3 = st.columns(3)
c1.metric("Costo total (COP)", f"{float(kpis_costos.get('costo_total_cop', 0.0)):,.0f}")
c2.metric("Cumplimiento Normativo (%)", f"{float(cumpl_pct):.1f}")
c3.metric("Nivel de Riesgo", str(riesgo))

# 11) Outputs según selección
inputs_out = params_sim if inc_inputs else {}
costos_out = costos_df if inc_costos else pd.DataFrame()
trib_out = trib_df if inc_trib else pd.DataFrame()
check_out = check_filtrado if (inc_check and check_filtrado is not None) else None

# 12) Botones exportación
col1, col2 = st.columns(2)

with col1:
    if st.button("Generar Excel", type="primary"):
        xbytes = exportar_excel_bytes(
            inputs_out,
            costos_out,
            trib_out,
            check_out,
            fig_costos=fig_donut,
        )
        st.download_button(
            "Descargar Excel",
            data=xbytes,
            file_name="reporte_vinologix.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

with col2:
    if st.button("Generar PDF", type="primary"):
        # usuario seguro
        usuario = st.session_state.get("usuario", "Usuario")

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
# pages/2_Checklist_Normativo.py
import streamlit as st
import pandas as pd

from utils.config import DATA_DIR
from utils.state import init_session_state, get_inputs
from utils.checklist import (
    load_checklist_csv,
    filtrar_por_modalidad,
    calcular_cumplimiento,
    save_checklist_csv,
)
from utils.ui import set_page_config, apply_global_style, render_sidebar_brand


# 0) Config + estilos + logo (UNA SOLA VEZ)
set_page_config("Checklist Normativo", layout="wide")
apply_global_style()
render_sidebar_brand()


# 1) Estado
init_session_state()

st.title("Checklist Normativo")
st.caption("Marca **OK/Pendiente**. Guarda y el Home actualizará el cumplimiento y el riesgo.")

params = get_inputs()
modalidad = params.get("modalidad", "Embotellado")

path = DATA_DIR / "checklist_normativo.csv"
df_all = load_checklist_csv(str(path)).fillna("")


# 2) Estado default
if "estado" not in df_all.columns:
    df_all["estado"] = df_all.get("estado_default", "Pendiente")


# 3) Vista filtrada
df_view = filtrar_por_modalidad(df_all, modalidad).copy().fillna("")
if "observacion" not in df_view.columns:
    df_view["observacion"] = ""

st.markdown(f"**Modalidad activa:** `{modalidad}`")


# 4) Editor
edited = st.data_editor(
    df_view[["requisito", "aplica_a", "responsable", "evidencia", "estado", "observacion"]],
    use_container_width=True,
    num_rows="fixed",
    column_config={
        "estado": st.column_config.SelectboxColumn("Estado", options=["OK", "Pendiente"]),
        "observacion": st.column_config.TextColumn("Observación", help="Notas internas o evidencia faltante"),
    },
)

cumpl_pct, riesgo = calcular_cumplimiento(edited)

c1, c2, c3 = st.columns([1, 1, 2])
c1.metric("Cumplimiento (%)", f"{cumpl_pct:.1f}")
c2.metric("Riesgo (derivado)", riesgo)
with c3:
    st.progress(min(max(cumpl_pct / 100, 0), 1))

st.divider()


# 5) Guardar cambios
if st.button("Guardar cambios", type="primary"):
    upd = edited[["requisito", "estado", "observacion"]].copy()
    upd["requisito"] = upd["requisito"].astype(str)

    df_all["requisito"] = df_all["requisito"].astype(str)

    df_all = df_all.merge(
        upd,
        on="requisito",
        how="left",
        suffixes=("", "_new"),
    )

    df_all["estado"] = df_all["estado_new"].fillna(df_all["estado"])

    if "observacion" in df_all.columns:
        df_all["observacion"] = df_all["observacion_new"].fillna(df_all["observacion"])
    else:
        df_all["observacion"] = df_all["observacion_new"].fillna("")

    df_all = df_all.drop(columns=[c for c in ["estado_new", "observacion_new"] if c in df_all.columns])

    save_checklist_csv(df_all, str(path))
    st.success("✅ Checklist guardado. Ve a Home: el % y el riesgo se actualizarán.")
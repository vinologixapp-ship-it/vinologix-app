# pages/0_Guia_de_Uso.py

import streamlit as st
from utils.ui import set_page_config, apply_global_style, render_sidebar_brand

set_page_config("Guía de Uso", layout="wide")
apply_global_style()
render_sidebar_brand()

st.title("🧸 Guía de Uso: Importar vino como si fuera un juego")

st.markdown("""
¿Primera vez usando VinoLogix?  
No te preocupes. Aquí lo entenderás como si tuvieras 10 años.
""")

st.divider()

# =========================================================
# 1. HISTORIA SIMPLE
# =========================================================

st.header("🍇 1. La historia sencilla")

st.info("""
Imagina que compras vino en Francia y quieres traerlo a Colombia para venderlo.

Pero traerlo no es solo pagar el vino.

Debes pagar:
- 🚢 El barco
- 🛡 El seguro
- 🏢 La aduana
- 📦 El transporte en Colombia
- 💰 Los impuestos

Esta app te dice:
👉 ¿Cuánto te cuesta realmente?
👉 ¿Vas a ganar o perder dinero?
👉 ¿Te falta algún permiso?
""")

st.divider()

# =========================================================
# 2. DICCIONARIO SUPER FACIL
# =========================================================

st.header("📘 2. Diccionario fácil (sin palabras raras)")

st.markdown("""
🔹 **Embotellado**  
El vino ya viene en botellas listas para vender.

🔹 **Flexitank**  
Es como una piscina gigante dentro del contenedor. Luego tú lo embotellas aquí.

🔹 **FOB**  
Es lo que pagas al vendedor en Francia. Hasta que el vino sube al barco.

🔹 **Flete internacional**  
Lo que cuesta el viaje en barco.

🔹 **Seguro**  
Si algo pasa en el viaje, esto protege tu dinero.

🔹 **TRM**  
Es cuánto vale un dólar en pesos colombianos.

🔹 **EUR.1**  
Es un papel especial que puede hacer que no pagues arancel.
""")

st.divider()

# =========================================================
# 3. COMO SABER SI VAS BIEN
# =========================================================

st.header("🚦 3. ¿Cómo saber si vas ganando o perdiendo?")

col1, col2 = st.columns(2)

with col1:
    st.success("""
    🟢 Vas bien cuando:
    - El costo por botella es bajo
    - El cumplimiento está cerca de 100%
    - El riesgo dice "Bajo"
    """)

with col2:
    st.error("""
    🔴 Cuidado cuando:
    - El costo por botella es muy alto
    - El cumplimiento está bajo
    - El riesgo dice "Alto"
    """)

st.divider()

# =========================================================
# 4. HAZ TU PRIMERA PRUEBA
# =========================================================

st.header("🎮 4. Haz tu primera prueba (modo tutorial)")

st.markdown("""
Ve al menú izquierdo y coloca estos datos:
""")

st.code("""
Modalidad: Embotellado
Unidad volumen: Botellas
Cantidad: 15000
TRM: 4000
Flete internacional: 3500
Seguro: 2%
EUR.1: Activado
""")

st.markdown("""
Luego ve a:

👉 Costos e Impuestos  
👉 Checklist Normativo  
👉 Reporte  

Mira cómo cambian los números.
""")

st.divider()

# =========================================================
# 5. REGLA DE ORO
# =========================================================

st.header("🧠 5. La regla de oro")

st.warning("""
Si el flete internacional es muy alto y traes pocas botellas,
cada botella será carísima.

Entre más volumen traigas, más barato sale cada litro.
""")

st.divider()

st.success("Ahora ya sabes usar VinoLogix como un experto 🚀")
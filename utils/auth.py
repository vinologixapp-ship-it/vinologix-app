import streamlit as st

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        # Pantalla de Login
        st.markdown("<h1 style='text-align: center;'>VinoLogix 🍷</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Simulador Logístico–Económico (Francia → Colombia)</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info("Por favor, identifícate para personalizar tus reportes.")
            with st.form("login_form"):
                usuario = st.text_input("Tu Nombre (Aparecerá en los reportes como analista/cliente)")
                empresa = st.text_input("Empresa o Proyecto (Opcional)")
                submit = st.form_submit_button("Ingresar al Simulador", type="primary")
                
                if submit and usuario:
                    st.session_state.logged_in = True
                    st.session_state.usuario = usuario
                    st.session_state.empresa = empresa
                    st.rerun()
                elif submit and not usuario:
                    st.error("⚠️ Debes ingresar tu nombre para continuar.")
        
        # Detiene la carga del resto de la página hasta que se inicie sesión
        st.stop()
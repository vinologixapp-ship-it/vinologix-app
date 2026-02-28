import streamlit as st

def init_session_state():
    defaults = {
        "modalidad": "Embotellado",
        "incoterm": "FOB",
        "puerto": "Cartagena",
        "ciudad": "Bogotá",
        "unidad_vol": "Contenedor 40ft",
        "cantidad": 1.0,

        "trm": 4000.0,
        "flete_usd": 4500.0,
        "seguro_modo": "pct",
        "seguro_val": 0.01,
        "bodegaje_cop": 0.0,
        "transporte_interno_cop": 0.0,

        "escenario": "Base",
        "eur1": True,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_inputs() -> dict:
    keys = [
        "modalidad","incoterm","puerto","ciudad",
        "unidad_vol","cantidad",
        "trm","flete_usd","seguro_modo","seguro_val",
        "bodegaje_cop","transporte_interno_cop",
        "escenario","eur1"
    ]
    return {k: st.session_state[k] for k in keys}


def apply_scenario(params: dict) -> dict:
    p = params.copy()
    scen = p["escenario"]

    if scen == "+10% TRM":
        p["trm"] *= 1.10
    elif scen == "+15% Flete":
        p["flete_usd"] *= 1.15
    elif scen == "Worst-case":
        p["trm"] *= 1.10
        p["flete_usd"] *= 1.15

    return p
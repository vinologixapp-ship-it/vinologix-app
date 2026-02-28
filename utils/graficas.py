# utils/graficas.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _normalize_cost_df(costos_df: pd.DataFrame):
    """
    Normaliza DataFrame para asegurar columnas:
    - componente
    - valor_cop
    """
    if costos_df is None or len(costos_df) == 0:
        return pd.DataFrame(columns=["componente", "valor_cop"])

    df = costos_df.copy()

    # Normalizar nombres
    if "componente" not in df.columns:
        df = df.rename(columns={df.columns[0]: "componente"})

    if "valor_cop" not in df.columns:
        for c in df.columns[::-1]:
            if c != "componente":
                df = df.rename(columns={c: "valor_cop"})
                break

    df["valor_cop"] = pd.to_numeric(df["valor_cop"], errors="coerce").fillna(0.0)
    df["componente"] = df["componente"].astype(str)

    return df


# --------------------------------------------------
# DONUT DE COSTOS
# --------------------------------------------------
def fig_costos_donut(costos_df: pd.DataFrame):

    df = _normalize_cost_df(costos_df)
    df = df[df["valor_cop"] > 0]

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            annotations=[dict(text="Sin datos", showarrow=False, font_size=16)],
            margin=dict(l=10, r=10, t=10, b=10)
        )
        return fig

    fig = px.pie(
        df,
        names="componente",
        values="valor_cop",
        hole=0.55,
    )

    fig.update_traces(
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>COP %{value:,.0f}<extra></extra>"
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        legend_title_text="Componente",
        showlegend=True,
    )

    return fig


# --------------------------------------------------
# WATERFALL DE COSTOS
# --------------------------------------------------
def fig_costos_waterfall(costos_df: pd.DataFrame):

    df = _normalize_cost_df(costos_df)

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            annotations=[dict(text="Sin datos", showarrow=False, font_size=16)],
            margin=dict(l=10, r=10, t=10, b=10)
        )
        return fig

    valores = df["valor_cop"].tolist()
    componentes = df["componente"].tolist()

    # Agregar total automático al final
    componentes.append("Total")
    valores.append(sum(valores))

    fig = go.Figure(go.Waterfall(
        orientation="v",
        x=componentes,
        y=valores,
        measure=["relative"] * (len(valores) - 1) + ["total"],
        connector={"line": {"width": 1}},
    ))

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis_title="COP",
    )

    fig.update_yaxes(tickformat=",.0f")

    return fig


# --------------------------------------------------
# GAUGE DE CUMPLIMIENTO
# --------------------------------------------------
def fig_cumplimiento_gauge(pct: float):

    pct = max(0, min(100, float(pct)))  # limitar entre 0-100

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={"suffix": "%"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"thickness": 0.25},
            "steps": [
                {"range": [0, 60], "color": "#FDEDEC"},
                {"range": [60, 85], "color": "#FCF3CF"},
                {"range": [85, 100], "color": "#E8F8F5"},
            ],
        },
    ))

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=230
    )

    return fig
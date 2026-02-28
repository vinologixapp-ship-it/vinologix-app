import pandas as pd

def load_checklist_csv(path_csv: str) -> pd.DataFrame:
    df = pd.read_csv(path_csv)

    for col in ["requisito", "aplica_a", "responsable",
                "evidencia", "estado_default", "observacion"]:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna("").str.strip()

    return df


def filtrar_por_modalidad(df: pd.DataFrame, modalidad: str) -> pd.DataFrame:
    if "aplica_a" not in df.columns:
        return df.copy()

    aplica = df["aplica_a"].str.lower().isin([modalidad.lower(), "ambos"])
    return df[aplica].copy()


def calcular_cumplimiento(df: pd.DataFrame) -> tuple[float, str]:
    d = df.copy()

    if "estado" not in d.columns:
        d["estado"] = d["estado_default"]

    ok = (d["estado"].str.upper() == "OK").sum()
    total = len(d)
    pct = 100 * ok / total if total else 0.0

    if pct < 70:
        riesgo = "Alto"
    elif pct < 90:
        riesgo = "Medio"
    else:
        riesgo = "Bajo"

    return pct, riesgo


def save_checklist_csv(df: pd.DataFrame, path_csv: str) -> None:
    df.to_csv(path_csv, index=False)
    df = df.fillna("")
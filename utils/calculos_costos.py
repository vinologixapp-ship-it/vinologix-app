# utils/calculos_costos.py
import pandas as pd


def convertir_volumen(unidad: str, cantidad: float, base: dict, modalidad: str):
    """
    Convierte a litros y botellas estimadas (750cc por defecto).
    Espera en base:
      - botella_l (default 0.75)
      - litros_contenedor_flexitank
      - litros_contenedor_embotellado
    """
    botella_l = float(base.get("botella_l", 0.75))
    unidad = (unidad or "").strip()

    if unidad == "Botellas":
        litros = float(cantidad) * botella_l
        botellas = float(cantidad)

    elif unidad == "Litros":
        litros = float(cantidad)
        botellas = litros / botella_l if botella_l > 0 else 0.0

    else:  # Contenedor 40ft (o cualquier otro texto)
        if (modalidad or "").strip() == "Flexitank":
            litros = float(cantidad) * float(base.get("litros_contenedor_flexitank", 24000))
        else:
            litros = float(cantidad) * float(base.get("litros_contenedor_embotellado", 12000))
        botellas = litros / botella_l if botella_l > 0 else 0.0

    return float(litros), float(botellas)


def calcular_costos_operacion(params: dict, base: dict):
    """
    MVP defendible:
    - Flete internacional (USD -> COP)
    - Seguro internacional (USD -> COP)
    - Bodegaje (COP)
    - Transporte interno (COP)

    Requiere en params:
      - trm, flete_usd, bodegaje_cop, transporte_interno_cop
      - seguro_modo ('pct' o 'abs'), seguro_val
      - litros (para KPIs)
    """
    # lecturas seguras
    trm = float(params.get("trm", 0.0))
    flete_usd = float(params.get("flete_usd", 0.0))
    bodegaje = float(params.get("bodegaje_cop", 0.0))
    transporte = float(params.get("transporte_interno_cop", 0.0))

    seguro_modo = str(params.get("seguro_modo", "pct")).strip().lower()
    seguro_val = float(params.get("seguro_val", 0.0))
    fob_usd = float(params.get("fob_usd", 0.0))

    # Seguro
    if seguro_modo == "pct":
        # Base mínima para evitar 0 cuando FOB está vacío
        base_seguro = (fob_usd + flete_usd) if (fob_usd + flete_usd) > 0 else flete_usd
        seguro_usd = seguro_val * base_seguro
    else:
        seguro_usd = seguro_val

    df = pd.DataFrame(
        [
            ("Flete internacional", flete_usd, "USD"),
            ("Seguro internacional", seguro_usd, "USD"),
            ("Bodegaje / almacenamiento", bodegaje, "COP"),
            ("Transporte interno", transporte, "COP"),
        ],
        columns=["componente", "valor", "moneda"],
    )

    def _to_cop(row):
        return float(row["valor"]) * trm if row["moneda"] == "USD" else float(row["valor"])

    df["valor_cop"] = df.apply(_to_cop, axis=1)

    total_cop = float(df["valor_cop"].sum())
    litros = float(params.get("litros", 0.0))
    botella_l = float(base.get("botella_l", 0.75))

    kpis = {
        "costo_total_cop": total_cop,
        "costo_litro_cop": (total_cop / litros) if litros > 0 else 0.0,
        "costo_botella_cop": ((total_cop / litros) * botella_l) if litros > 0 else 0.0,
    }
    return kpis, df


def calcular_tributos(params: dict, base: dict):
    """
    MVP defendible:
    - CIF = (FOB + flete + seguro) * TRM
    - Arancel depende de EUR.1
    - Consumo ad valorem (%)
    - IVA (%), calculado sobre (CIF + arancel + consumo)

    Requiere en base:
      - iva_pct (default 0.05)
      - consumo_adval_pct (default 0.20)
      - arancel_pref_eur1 (default 0.0)
      - arancel_sin_eur1 (default 0.15)
    """
    trm = float(params.get("trm", 0.0))
    fob_usd = float(params.get("fob_usd", 0.0))
    flete_usd = float(params.get("flete_usd", 0.0))

    seguro_modo = str(params.get("seguro_modo", "pct")).strip().lower()
    seguro_val = float(params.get("seguro_val", 0.0))

    if seguro_modo == "pct":
        base_seguro = (fob_usd + flete_usd) if (fob_usd + flete_usd) > 0 else flete_usd
        seguro_usd = seguro_val * base_seguro
    else:
        seguro_usd = seguro_val

    cif_usd = fob_usd + flete_usd + seguro_usd
    cif_cop = float(cif_usd * trm)

    iva_pct = float(base.get("iva_pct", 0.05))
    consumo_pct = float(base.get("consumo_adval_pct", 0.20))

    eur1 = bool(params.get("eur1", False))
    arancel_pct = float(base.get("arancel_pref_eur1", 0.0)) if eur1 else float(base.get("arancel_sin_eur1", 0.15))

    arancel_cop = float(cif_cop * arancel_pct)
    consumo_cop = float(cif_cop * consumo_pct)
    iva_cop = float((cif_cop + arancel_cop + consumo_cop) * iva_pct)

    df = pd.DataFrame(
        [
            ("CIF (base)", cif_cop),
            ("Arancel", arancel_cop),
            ("Impuesto al consumo (ad valorem)", consumo_cop),
            ("IVA", iva_cop),
        ],
        columns=["tributo", "valor_cop"],
    )

    total = arancel_cop + consumo_cop + iva_cop

    resumen = {
        "cif_cop": cif_cop,

        # Compatibilidad (tu página hoy imprime total_impuestos_cop)
        "total_impuestos_cop": total,

        # También dejo el nombre anterior por si lo usas en otros lados
        "total_tributos_cop": total,

        "arancel_pct": arancel_pct,
        "iva_pct": iva_pct,
        "consumo_pct": consumo_pct,
    }
    return resumen, df


def calcular_impuestos(params: dict, base: dict):
    """
    Alias para evitar ImportError en las páginas.
    Mantiene naming 'impuestos' para UI / reporte.
    """
    return calcular_tributos(params, base)
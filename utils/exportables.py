from __future__ import annotations
import io
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def generar_pdf_bytes(
    titulo: str,
    usuario: str,
    kpis: dict,
    inputs: dict,
    costos_df: pd.DataFrame,
    trib_df: pd.DataFrame,
    cumplimiento_pct: float,
    riesgo: str,
    top_pendientes_df: pd.DataFrame | None = None,
    fig_costos=None
) -> bytes:

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 2.5 * cm

    def dibujar_membrete(canvas_obj):
        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            canvas_obj.drawImage(
                logo_path,
                width - 4.5 * cm,
                height - 2.0 * cm,
                width=3 * cm,
                preserveAspectRatio=True,
                mask="auto",
            )

        canvas_obj.setStrokeColorRGB(0.47, 0.11, 0.22)
        canvas_obj.setLineWidth(2)
        canvas_obj.line(2 * cm, height - 2.2 * cm, width - 2 * cm, height - 2.2 * cm)

    def salto_de_pagina_si_es_necesario(espacio_requerido):
        nonlocal y
        if y < espacio_requerido:
            c.showPage()
            y = height - 3.0 * cm
            dibujar_membrete(c)
            return True
        return False

    def dibujar_titulo_seccion(texto):
        nonlocal y
        salto_de_pagina_si_es_necesario(3 * cm)
        c.setFillColorRGB(0.47, 0.11, 0.22)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2 * cm, y, texto)
        y -= 0.6 * cm
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 10)

    def safe_str(value):
        return "N/D" if value is None else str(value)

    dibujar_membrete(c)
    y -= 0.5 * cm

    c.setFillColorRGB(0.47, 0.11, 0.22)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(2 * cm, y, titulo)
    y -= 0.7 * cm

    fecha_actual = datetime.now(ZoneInfo("America/Bogota")).strftime("%Y-%m-%d %H:%M")

    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Generado por: {safe_str(usuario)} | Empresa/Cliente: Analista Interno")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Fecha de impresión: {fecha_actual} (Hora Bogotá)")
    y -= 1.2 * cm

    c.setFillColorRGB(0, 0, 0)

    dibujar_titulo_seccion("1. Indicadores Clave (KPIs)")
    kpi_lines = [
        f"- Costo total (COP): $ {float(kpis.get('costo_total_cop', 0) or 0):,.0f}",
        f"- Costo por litro (COP/L): $ {float(kpis.get('costo_litro_cop', 0) or 0):,.0f}",
        f"- Costo por botella 750cc: $ {float(kpis.get('costo_botella_cop', 0) or 0):,.0f}",
        f"- Cumplimiento normativo: {float(cumplimiento_pct or 0):.1f} %",
        f"- Nivel de riesgo logístico: {safe_str(riesgo)}",
    ]

    for line in kpi_lines:
        salto_de_pagina_si_es_necesario(1.2 * cm)
        c.drawString(2.5 * cm, y, line)
        y -= 0.5 * cm
    y -= 0.4 * cm

    if fig_costos is not None:
        try:
            img_bytes = fig_costos.to_image(format="png", scale=2)
            img_buffer = io.BytesIO(img_bytes)
            img_reader = ImageReader(img_buffer)

            dibujar_titulo_seccion("2. Distribución de Costos")
            alto_img = 7.5 * cm
            salto_de_pagina_si_es_necesario(alto_img + 2 * cm)
            c.drawImage(
                img_reader,
                4 * cm,
                y - alto_img,
                width=13 * cm,
                height=alto_img,
                preserveAspectRatio=True,
            )
            y -= (alto_img + 1.0 * cm)
        except Exception:
            dibujar_titulo_seccion("2. Distribución de Costos")
            c.drawString(2.5 * cm, y, "No fue posible incrustar la gráfica en el PDF.")
            y -= 0.7 * cm

    dibujar_titulo_seccion("3. Parámetros del Escenario")
    keys_labels = {
        "modalidad": "Modalidad",
        "incoterm": "Incoterm",
        "puerto": "Puerto",
        "ciudad": "Ciudad destino",
        "unidad_vol": "Unidad de volumen",
        "cantidad": "Cantidad",
        "trm": "TRM",
        "flete_usd": "Flete internacional (USD)",
        "litros": "Litros estimados",
        "botellas_estimadas": "Botellas estimadas",
    }

    for key, label in keys_labels.items():
        salto_de_pagina_si_es_necesario(1.0 * cm)
        c.drawString(2.5 * cm, y, f"{label}: {safe_str(inputs.get(key, 'N/D'))}")
        y -= 0.45 * cm
    y -= 0.5 * cm

    dibujar_titulo_seccion("4. Costos Principales")
    if costos_df is not None and not costos_df.empty and {"componente", "valor_cop"}.issubset(costos_df.columns):
        top_costos = costos_df.sort_values("valor_cop", ascending=False)
        for _, r in top_costos.iterrows():
            salto_de_pagina_si_es_necesario(1.0 * cm)
            c.drawString(2.5 * cm, y, f"- {safe_str(r['componente'])}: $ {float(r['valor_cop'] or 0):,.0f} COP")
            y -= 0.45 * cm
    else:
        c.drawString(2.5 * cm, y, "No hay información de costos para este escenario.")
        y -= 0.45 * cm
    y -= 0.5 * cm

    dibujar_titulo_seccion("5. Impuestos y Tributos")
    if trib_df is not None and not trib_df.empty and {"tributo", "valor_cop"}.issubset(trib_df.columns):
        for _, r in trib_df.iterrows():
            salto_de_pagina_si_es_necesario(1.0 * cm)
            c.drawString(2.5 * cm, y, f"- {safe_str(r['tributo'])}: $ {float(r['valor_cop'] or 0):,.0f} COP")
            y -= 0.45 * cm
    else:
        c.drawString(2.5 * cm, y, "No hay información tributaria para este escenario.")
        y -= 0.45 * cm
    y -= 0.5 * cm

    dibujar_titulo_seccion("6. Checklist Normativo")
    if top_pendientes_df is not None and not top_pendientes_df.empty:
        c.drawString(2.5 * cm, y, "Pendientes identificados para este escenario:")
        y -= 0.6 * cm

        for _, r in top_pendientes_df.iterrows():
            salto_de_pagina_si_es_necesario(1.5 * cm)
            requisito = safe_str(r.get("requisito", "Requisito no especificado"))
            responsable = safe_str(r.get("responsable", "N/A"))

            c.setFont("Helvetica-Bold", 10)
            c.drawString(3.0 * cm, y, f"- {requisito}")
            y -= 0.4 * cm
            c.setFont("Helvetica", 9)
            c.drawString(3.5 * cm, y, f"Responsable: {responsable}")
            y -= 0.6 * cm
    else:
        c.drawString(2.5 * cm, y, "Todo en regla. No hay documentos pendientes para este escenario.")
        y -= 0.5 * cm

    c.save()
    return buffer.getvalue()
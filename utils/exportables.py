from __future__ import annotations
import io
import os
from datetime import datetime

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from openpyxl.drawing.image import Image as XLImage


def exportar_excel_bytes(inputs: dict,
                         costos_df: pd.DataFrame,
                         trib_df: pd.DataFrame,
                         checklist_df: pd.DataFrame | None = None,
                         fig_costos=None) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([inputs]).T.reset_index().rename(columns={"index": "parametro", 0: "valor"}) \
            .to_excel(writer, sheet_name="Inputs", index=False)
        costos_df.to_excel(writer, sheet_name="Costos", index=False)
        trib_df.to_excel(writer, sheet_name="Impuestos", index=False) # Cambio a Impuestos

        if checklist_df is not None:
            checklist_df.to_excel(writer, sheet_name="Checklist", index=False)

        if fig_costos is not None:
            img_bytes = fig_costos.to_image(format="png", scale=2)
            img_buffer = io.BytesIO(img_bytes)
            workbook = writer.book
            ws_chart = workbook.create_sheet("Dashboard")
            xl_img = XLImage(img_buffer)
            ws_chart.add_image(xl_img, "B2")

    return output.getvalue()


def generar_pdf_bytes(titulo: str,
                      usuario: str, 
                      kpis: dict,
                      inputs: dict,
                      costos_df: pd.DataFrame,
                      trib_df: pd.DataFrame,
                      cumplimiento_pct: float,
                      riesgo: str,
                      top_pendientes_df: pd.DataFrame | None = None,
                      fig_costos=None) -> bytes:
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 2.5 * cm

    # ==========================================
    # FUNCIÓN AUXILIAR: DIBUJAR LOGO EN CADA HOJA
    # ==========================================
    def dibujar_membrete(canvas_obj):
        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            canvas_obj.drawImage(logo_path, width - 4.5 * cm, height - 2.0 * cm, width=3 * cm, preserveAspectRatio=True, mask='auto')
        
        # Línea decorativa color vino tinto arriba
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

    # Dibujar membrete en la PRIMERA hoja
    dibujar_membrete(c)
    y -= 0.5 * cm

    # ==========================================
    # CABECERA Y DATOS DEL REPORTE
    # ==========================================
    c.setFillColorRGB(0.47, 0.11, 0.22)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(2 * cm, y, titulo)
    y -= 0.7 * cm

    import pytz 
    tz = pytz.timezone('America/Bogota')
    fecha_actual = datetime.now(tz).strftime('%Y-%m-%d %H:%M')
    
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Generado por: {usuario} | Empresa/Cliente: Analista Interno")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Fecha de impresión: {fecha_actual} (Hora Bogotá)")
    y -= 1.2 * cm

    c.setFillColorRGB(0, 0, 0)

    # ==========================================
    # 1. KPIs
    # ==========================================
    salto_de_pagina_si_es_necesario(5 * cm)
    c.setFillColorRGB(0.47, 0.11, 0.22)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "1. Indicadores Clave (KPIs)")
    y -= 0.6 * cm

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 11)
    kpi_lines = [
        f"• Costo total (COP): $ {kpis.get('costo_total_cop', 0):,.0f}",
        f"• Costo por litro (COP/L): $ {kpis.get('costo_litro_cop', 0):,.0f}",
        f"• Costo por botella 750cc: $ {kpis.get('costo_botella_cop', 0):,.0f}",
        f"• Cumplimiento normativo: {cumplimiento_pct:.1f} %",
        f"• Nivel de riesgo logístico: {riesgo}",
    ]
    for line in kpi_lines:
        c.drawString(2.5 * cm, y, line)
        y -= 0.5 * cm
    y -= 0.5 * cm

    # ==========================================
    # 2. GRÁFICA VISUAL
    # ==========================================
    if fig_costos is not None:
        salto_de_pagina_si_es_necesario(10 * cm)
        c.setFillColorRGB(0.47, 0.11, 0.22)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2 * cm, y, "2. Distribución de Costos")
        y -= 0.3 * cm
        
        img_bytes = fig_costos.to_image(format="png", scale=2)
        img_buffer = io.BytesIO(img_bytes)
        img_reader = ImageReader(img_buffer)
        
        alto_img = 7.5 * cm
        c.drawImage(img_reader, 4 * cm, y - alto_img, width=13 * cm, height=alto_img, preserveAspectRatio=True)
        y -= (alto_img + 1.2 * cm)

    # ==========================================
    # 3. INPUTS DEL ESCENARIO
    # ==========================================
    salto_de_pagina_si_es_necesario(4 * cm)
    c.setFillColorRGB(0.47, 0.11, 0.22)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "3. Parámetros del Escenario")
    y -= 0.6 * cm
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 10)
    keys = ["modalidad", "incoterm", "puerto", "ciudad", "unidad_vol", "cantidad", "trm", "flete_usd"]
    for i, k in enumerate(keys):
        salto_de_pagina_si_es_necesario(1.5 * cm)
        if i % 2 == 0:
            x_pos = 2 * cm
            y -= 0.45 * cm
        else:
            x_pos = 10 * cm
        c.drawString(x_pos, y, f"{k.capitalize()}: {inputs.get(k)}")
    y -= 1.0 * cm

    # ==========================================
    # 4. TABLAS DE COSTOS E IMPUESTOS
    # ==========================================
    def dibujar_titulo_seccion(texto):
        nonlocal y
        salto_de_pagina_si_es_necesario(3 * cm)
        c.setFillColorRGB(0.47, 0.11, 0.22)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2 * cm, y, texto)
        y -= 0.6 * cm
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 10)

    # Costos
    dibujar_titulo_seccion("4. Costos Principales (Top 5)")
    top_costos = costos_df.sort_values("valor_cop", ascending=False).head(5)
    for _, r in top_costos.iterrows():
        salto_de_pagina_si_es_necesario(1 * cm)
        c.drawString(2.5 * cm, y, f"• {r['componente']}: $ {float(r['valor_cop']):,.0f} COP")
        y -= 0.45 * cm
    y -= 0.5 * cm

    # Impuestos
    dibujar_titulo_seccion("5. Impuestos de Nacionalización")
    for _, r in trib_df.iterrows():
        salto_de_pagina_si_es_necesario(1 * cm)
        c.drawString(2.5 * cm, y, f"• {r['tributo']}: $ {float(r['valor_cop']):,.0f} COP")
        y -= 0.45 * cm
    y -= 0.5 * cm

    # ==========================================
    # 6. CHECKLIST NORMATIVO
    # ==========================================
    dibujar_titulo_seccion("6. Checklist Normativo (Requisitos Pendientes)")
    if top_pendientes_df is not None and not top_pendientes_df.empty:
        c.drawString(2.5 * cm, y, "Atención: Los siguientes documentos aún no han sido gestionados:")
        y -= 0.6 * cm
        for _, r in top_pendientes_df.iterrows():
            salto_de_pagina_si_es_necesario(1 * cm)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(3 * cm, y, f"- {r['requisito']}")
            y -= 0.4 * cm 
            c.setFont("Helvetica", 9)
            c.drawString(3.5 * cm, y, f"Resp: {r.get('responsable', 'N/A')}")
            y -= 0.6 * cm
    else:
        c.setFillColorRGB(0.1, 0.6, 0.1) # Verde oscuro
        c.drawString(2.5 * cm, y, "✅ Todo en regla. No hay documentos pendientes para este escenario.")
        y -= 0.5 * cm

    c.showPage()
    c.save()
    return buffer.getvalue()
from django.conf import settings
from django.core.files.base import ContentFile
from io import BytesIO
import os

def generar_contrato_pdf(contrato):
    """
    Genera un PDF del contrato de adopción.
    Usa reportlab para crear el PDF.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
        
        # Crear buffer en memoria
        buffer = BytesIO()
        
        # Crear el documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Estilos
        styles = getSampleStyleSheet()
        titulo_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#009688'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
        
        # Contenido del contrato
        story = []
        
        # Título
        story.append(Paragraph("CONTRATO DE ADOPCIÓN", titulo_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Información del contrato
        story.append(Paragraph(f"<b>N° de Contrato:</b> {contrato.id}", normal_style))
        story.append(Paragraph(f"<b>Fecha:</b> {contrato.fecha_generacion.strftime('%d de %B de %Y')}", normal_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Datos del adoptante
        adoptante = contrato.id_adoptante
        story.append(Paragraph("<b>DATOS DEL ADOPTANTE:</b>", styles['Heading2']))
        
        datos_adoptante = [
            ['Nombre Completo:', adoptante.nombre],
            ['Dirección:', adoptante.direccion],
            ['Teléfono:', adoptante.telefono],
            ['Email:', adoptante.email]
        ]
        
        tabla_adoptante = Table(datos_adoptante, colWidths=[2*inch, 4*inch])
        tabla_adoptante.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E0F2F1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        story.append(tabla_adoptante)
        story.append(Spacer(1, 0.2*inch))
        
        # Datos del animal
        animal = contrato.id_adopcion.id_animal
        story.append(Paragraph("<b>DATOS DEL ANIMAL ADOPTADO:</b>", styles['Heading2']))
        
        datos_animal = [
            ['Nombre:', animal.nombre],
            ['Especie:', animal.especie],
            ['Edad:', f'{animal.edad} años'],
            ['Sexo:', animal.sexo],
            ['Estado de Salud:', animal.estado_salud]
        ]
        
        tabla_animal = Table(datos_animal, colWidths=[2*inch, 4*inch])
        tabla_animal.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E0F2F1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        story.append(tabla_animal)
        story.append(Spacer(1, 0.3*inch))
        
        # Cláusulas del contrato
        story.append(Paragraph("<b>CLÁUSULAS:</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        clausulas = [
            "El adoptante se compromete a proporcionar al animal alimentación adecuada, atención veterinaria cuando sea necesaria y un ambiente seguro y amoroso.",
            "El adoptante acepta que RescatandoAndo Stgo realice seguimientos periódicos para verificar el bienestar del animal adoptado.",
            "El adoptante se compromete a no abandonar, maltratar o descuidar al animal bajo ninguna circunstancia.",
            "En caso de no poder continuar con el cuidado del animal, el adoptante se compromete a notificar inmediatamente a RescatandoAndo Stgo para coordinar su devolución.",
            "El adoptante reconoce que cualquier incumplimiento de estas cláusulas puede resultar en la recuperación del animal por parte de RescatandoAndo Stgo.",
        ]
        
        for i, clausula in enumerate(clausulas, 1):
            story.append(Paragraph(f"<b>{i}.</b> {clausula}", normal_style))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Aceptación
        story.append(Paragraph(
            "El adoptante declara haber leído y aceptado todas las cláusulas de este contrato, "
            "comprometiéndose a cumplirlas en su totalidad.",
            normal_style
        ))
        
        story.append(Spacer(1, 0.5*inch))
        
        # Firmas
        firmas_data = [
            ['_______________________', '_______________________'],
            ['Firma del Adoptante', 'Firma RescatandoAndo Stgo'],
            [adoptante.nombre, 'Representante Legal']
        ]
        
        tabla_firmas = Table(firmas_data, colWidths=[3*inch, 3*inch])
        tabla_firmas.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 20),
        ]))
        
        story.append(tabla_firmas)
        
        # Construir PDF
        doc.build(story)
        
        # Guardar el PDF en el modelo
        pdf_content = buffer.getvalue()
        buffer.close()
        
        filename = f"contrato_{contrato.id}_{adoptante.nombre.replace(' ', '_')}.pdf"
        contrato.archivo_pdf.save(filename, ContentFile(pdf_content), save=True)
        
        return True
        
    except ImportError:
        print("Error: reportlab no está instalado. Ejecuta: pip install reportlab")
        return False
    except Exception as e:
        print(f"Error al generar PDF: {str(e)}")
        return False

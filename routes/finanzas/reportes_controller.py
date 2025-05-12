from flask import request, redirect, url_for, flash, send_file, render_template
from datetime import datetime, timedelta
import os
import csv
import calendar

from models import db, Usuario, PagoMensualidad, VentaProducto, Producto
from models import datetime_colombia, date_colombia
from .utils import obtener_periodo_actual, sanitizar_valor_numerico

# Importar el blueprint directamente desde el paquete finanzas
from routes.finanzas import bp

@bp.route('/pagos')
def pagos():
    pagos = PagoMensualidad.query.order_by(PagoMensualidad.fecha_pago.desc()).all()
    return render_template('finanzas/pagos.html', pagos=pagos, now=datetime.now())

@bp.route('/exportar', methods=['POST'])
def exportar_finanzas():
    """
    Exporta los datos financieros en diferentes formatos.
    Implementa manejo inteligente de dependencias opcionales.
    
    Formatos soportados:
    - CSV: Formato básico sin dependencias adicionales
    - Excel: Requiere pandas, openpyxl y xlsxwriter
    - PDF: Requiere reportlab
    
    Implementado por: YEIFRAN HERNANDEZ (NEURALJIRA_DEV)
    """
    try:
        # Obtener parámetros del formulario
        formato = request.form.get('formato', 'csv')  # Formato por defecto: CSV
        periodo = request.form.get('periodo', 'actual')
        incluir_resumen = 'incluirResumen' in request.form
        incluir_graficos = 'incluirGraficos' in request.form
        incluir_detalles = 'incluirDetalles' in request.form
        
        # Determinar fechas según el período
        hoy = date_colombia()
        periodo_actual = obtener_periodo_actual()
        
        # Calcular fechas de inicio y fin según el período seleccionado
        if periodo == 'actual':
            inicio_periodo = periodo_actual['inicio_mes']
            fin_periodo = periodo_actual['fin_mes']
            titulo_periodo = f"{periodo_actual['nombre_mes']} {periodo_actual['año']}"
        elif periodo == 'anterior':
            mes_anterior = hoy.month - 1
            año_anterior = hoy.year
            if mes_anterior <= 0:
                mes_anterior = 12
                año_anterior -= 1
            ultimo_dia = calendar.monthrange(año_anterior, mes_anterior)[1]
            inicio_periodo = datetime(año_anterior, mes_anterior, 1).date()
            fin_periodo = datetime(año_anterior, mes_anterior, ultimo_dia).date()
            titulo_periodo = f"{calendar.month_name[mes_anterior]} {año_anterior}"
        elif periodo == 'trimestre':
            inicio_periodo = (hoy.replace(day=1) - timedelta(days=90))
            fin_periodo = hoy
            titulo_periodo = f"Último Trimestre ({inicio_periodo.strftime('%d/%m/%Y')} - {fin_periodo.strftime('%d/%m/%Y')})"
        elif periodo == 'anual':
            inicio_periodo = datetime(hoy.year, 1, 1).date()
            fin_periodo = datetime(hoy.year, 12, 31).date()
            titulo_periodo = f"Año {hoy.year}"
        else:
            inicio_periodo = periodo_actual['inicio_mes']
            fin_periodo = periodo_actual['fin_mes']
            titulo_periodo = f"{periodo_actual['nombre_mes']} {periodo_actual['año']}"
        
        # Convertir a datetime para consultas
        inicio_periodo = datetime.combine(inicio_periodo, datetime.min.time())
        fin_periodo = datetime.combine(fin_periodo, datetime.max.time())
        
        # Preparar la carpeta de exportación
        export_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exports')
        os.makedirs(export_folder, exist_ok=True)
        fecha_actual = datetime_colombia().strftime('%Y%m%d_%H%M%S')
        
        # Obtener datos básicos
        # Pagos de membresías
        pagos = db.session.query(
            PagoMensualidad, Usuario
        ).join(Usuario).filter(
            PagoMensualidad.fecha_pago >= inicio_periodo,
            PagoMensualidad.fecha_pago <= fin_periodo
        ).all()
        
        # Ventas de productos
        ventas = db.session.query(
            VentaProducto, Producto, Usuario
        ).join(Producto).outerjoin(Usuario, VentaProducto.usuario_id == Usuario.id).filter(
            VentaProducto.fecha >= inicio_periodo,
            VentaProducto.fecha <= fin_periodo
        ).all()
        
        # Obtener datos de resumen
        total_pagos = sum(p.monto for p, _ in pagos)
        total_ventas = sum(v.total for v, _, _ in ventas)
        total_ingresos = total_pagos + total_ventas
        
        # Exportar según el formato seleccionado
        if formato == 'csv':
            # Exportación CSV (sin dependencias adicionales)
            filename = f'finanzas_{periodo}_{fecha_actual}.csv'
            filepath = os.path.join(export_folder, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Escribir encabezado del reporte
                writer.writerow(['INFORME FINANCIERO', titulo_periodo])
                writer.writerow(['Fecha de generación:', datetime_colombia().strftime('%d/%m/%Y %H:%M:%S')])
                writer.writerow([])
                
                # Escribir resumen si se solicitó
                if incluir_resumen:
                    writer.writerow(['RESUMEN FINANCIERO'])
                    writer.writerow(['Total Ingresos:', f"{total_ingresos:,.2f}"])
                    writer.writerow(['Ingresos por Membresías:', f"{total_pagos:,.2f}"])
                    writer.writerow(['Ingresos por Productos:', f"{total_ventas:,.2f}"])
                    writer.writerow([])
                
                # Escribir detalles de pagos si se solicitó
                if incluir_detalles:
                    writer.writerow(['DETALLE DE PAGOS DE MEMBRESÍAS'])
                    writer.writerow(['ID', 'Fecha', 'Usuario', 'Plan', 'Monto', 'Método de Pago'])
                    for pago, usuario in pagos:
                        writer.writerow([
                            pago.id,
                            pago.fecha_pago.strftime('%d/%m/%Y') if pago.fecha_pago else '',
                            usuario.nombre,
                            pago.plan,
                            f"{pago.monto:,.2f}",
                            pago.metodo_pago
                        ])
                    writer.writerow([])
                    
                    writer.writerow(['DETALLE DE VENTAS DE PRODUCTOS'])
                    writer.writerow(['ID', 'Fecha', 'Producto', 'Usuario', 'Cantidad', 'Precio Unitario', 'Total', 'Método de Pago'])
                    for venta, producto, usuario in ventas:
                        writer.writerow([
                            venta.id,
                            venta.fecha.strftime('%d/%m/%Y') if venta.fecha else '',
                            producto.nombre,
                            usuario.nombre if usuario else 'Cliente no registrado',
                            venta.cantidad,
                            f"{venta.precio_unitario:,.2f}",
                            f"{venta.total:,.2f}",
                            venta.metodo_pago
                        ])
            
            # Retornar el archivo para descarga
            return send_file(filepath, as_attachment=True, download_name=filename)
        
        elif formato == 'excel':
            # Verificar si pandas y xlsxwriter están instalados
            try:
                import pandas as pd
                import xlsxwriter
                from openpyxl import Workbook
            except ImportError:
                instrucciones = (
                    "Para exportar a Excel se requieren bibliotecas adicionales. "
                    "Puede instalarlas con uno de estos comandos:\n\n"
                    "1) pip install -r exportacion-requirements.txt\n"
                    "2) pip install pandas xlsxwriter openpyxl"
                )
                flash(instrucciones, 'warning')
                return redirect(url_for('main.finanzas.index'))
            
            # Nombre del archivo
            filename = f'finanzas_{periodo}_{fecha_actual}.xlsx'
            filepath = os.path.join(export_folder, filename)
            
            # Crear un ExcelWriter
            writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
            workbook = writer.book
            
            # Formato para títulos
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#4F81BD',
                'font_color': 'white'
            })
            
            # Formato para encabezados
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D0E5FF',
                'border': 1
            })
            
            # Formato para moneda
            money_format = workbook.add_format({
                'num_format': '_($* #,##0.00_)',
                'border': 1
            })
            
            # Hoja de resumen
            if incluir_resumen:
                # Crear DataFrame para el resumen
                resumen_data = {
                    'Concepto': ['Ingresos Totales', 'Ingresos por Membresías', 'Ingresos por Productos',
                                'Cantidad de Pagos', 'Cantidad de Ventas'],
                    'Valor': [total_ingresos, total_pagos, total_ventas, len(pagos), len(ventas)]
                }
                df_resumen = pd.DataFrame(resumen_data)
                
                # Escribir el DataFrame a Excel
                df_resumen.to_excel(writer, sheet_name='Resumen', index=False, startrow=2)
                
                # Obtener la hoja de trabajo
                worksheet = writer.sheets['Resumen']
                worksheet.set_column('A:A', 25)
                worksheet.set_column('B:B', 15)
                
                # Agregar título
                worksheet.merge_range('A1:B1', f'RESUMEN FINANCIERO - {titulo_periodo}', title_format)
                
                # Aplicar formato a encabezados
                for col_num, value in enumerate(df_resumen.columns.values):
                    worksheet.write(2, col_num, value, header_format)
            
            # Hoja de pagos de membresías
            if incluir_detalles:
                # Crear DataFrame para pagos
                pagos_data = []
                for pago, usuario in pagos:
                    pagos_data.append({
                        'ID': pago.id,
                        'Fecha': pago.fecha_pago,
                        'Usuario': usuario.nombre,
                        'Plan': pago.plan,
                        'Monto': float(pago.monto),
                        'Método de Pago': pago.metodo_pago
                    })
                
                if pagos_data:
                    df_pagos = pd.DataFrame(pagos_data)
                    df_pagos.to_excel(writer, sheet_name='Pagos_Membresías', index=False, startrow=2)
                    
                    worksheet = writer.sheets['Pagos_Membresías']
                    worksheet.set_column('A:A', 5)   # ID
                    worksheet.set_column('B:B', 15)  # Fecha
                    worksheet.set_column('C:C', 25)  # Usuario
                    worksheet.set_column('D:D', 15)  # Plan
                    worksheet.set_column('E:E', 12)  # Monto
                    worksheet.set_column('F:F', 15)  # Método de Pago
                    
                    # Aplicar formato a los encabezados
                    worksheet.merge_range('A1:F1', 'DETALLE DE PAGOS DE MEMBRESÍAS', title_format)
                    for col_num, value in enumerate(df_pagos.columns.values):
                        worksheet.write(2, col_num, value, header_format)
                
                # Crear DataFrame para ventas
                ventas_data = []
                for venta, producto, usuario in ventas:
                    ventas_data.append({
                        'ID': venta.id,
                        'Fecha': venta.fecha,
                        'Producto': producto.nombre,
                        'Usuario': usuario.nombre if usuario else 'Cliente no registrado',
                        'Cantidad': venta.cantidad,
                        'Precio Unitario': float(venta.precio_unitario),
                        'Total': float(venta.total),
                        'Método de Pago': venta.metodo_pago
                    })
                
                if ventas_data:
                    df_ventas = pd.DataFrame(ventas_data)
                    df_ventas.to_excel(writer, sheet_name='Ventas_Productos', index=False, startrow=2)
                    
                    worksheet = writer.sheets['Ventas_Productos']
                    worksheet.set_column('A:A', 5)   # ID
                    worksheet.set_column('B:B', 15)  # Fecha
                    worksheet.set_column('C:C', 25)  # Producto
                    worksheet.set_column('D:D', 25)  # Usuario
                    worksheet.set_column('E:E', 10)  # Cantidad
                    worksheet.set_column('F:F', 15)  # Precio Unitario
                    worksheet.set_column('G:G', 15)  # Total
                    worksheet.set_column('H:H', 15)  # Método de Pago
                    
                    # Aplicar formato a los encabezados
                    worksheet.merge_range('A1:H1', 'DETALLE DE VENTAS DE PRODUCTOS', title_format)
                    for col_num, value in enumerate(df_ventas.columns.values):
                        worksheet.write(2, col_num, value, header_format)
            
            # Agregar hoja de gráficos si se solicitó
            if incluir_graficos:
                worksheet = workbook.add_worksheet('Gráficos')
                worksheet.merge_range('A1:F1', f'ANÁLISIS GRÁFICO - {titulo_periodo}', title_format)
                
                # Datos para el gráfico de ingresos
                chart_data = {
                    'Categoría': ['Membresías', 'Productos'],
                    'Ingresos': [float(total_pagos), float(total_ventas)]
                }
                df_chart = pd.DataFrame(chart_data)
                df_chart.to_excel(writer, sheet_name='Gráficos', index=False, startrow=3)
                
                # Crear gráfico circular
                chart1 = workbook.add_chart({'type': 'pie'})
                chart1.add_series({
                    'name': 'Distribución de Ingresos',
                    'categories': ['Gráficos', 4, 0, 5, 0],
                    'values': ['Gráficos', 4, 1, 5, 1],
                    'data_labels': {'percentage': True}
                })
                
                chart1.set_title({'name': 'Distribución de Ingresos'})
                chart1.set_style(10)
                worksheet.insert_chart('A8', chart1, {'x_offset': 25, 'y_offset': 10, 'x_scale': 1.5, 'y_scale': 1.5})
            
            # Guardar el libro
            writer.close()
            
            # Retornar el archivo para descarga
            return send_file(filepath, as_attachment=True, download_name=filename)
        
        elif formato == 'pdf':
            # Verificar si reportlab está instalado
            try:
                import reportlab
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import letter, landscape
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.graphics.shapes import Drawing
                from reportlab.graphics.charts.piecharts import Pie
                from reportlab.lib.units import inch
            except ImportError:
                instrucciones = (
                    "Para exportar a PDF se requiere reportlab. "
                    "Puede instalarlo con uno de estos comandos:\n\n"
                    "1) pip install -r exportacion-requirements.txt\n"
                    "2) pip install reportlab"
                )
                flash(instrucciones, 'warning')
                return redirect(url_for('main.finanzas.index'))
            
            # Nombre del archivo
            filename = f'finanzas_{periodo}_{fecha_actual}.pdf'
            filepath = os.path.join(export_folder, filename)
            
            # Crear el documento PDF
            doc = SimpleDocTemplate(filepath, pagesize=landscape(letter))
            elements = []
            
            # Estilos para el documento
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            subtitle_style = styles['Heading2']
            normal_style = styles['Normal']
            
            # Crear título y subtítulo
            elements.append(Paragraph(f"INFORME FINANCIERO - {titulo_periodo}", title_style))
            elements.append(Paragraph(f"Generado el {datetime_colombia().strftime('%d/%m/%Y %H:%M:%S')}", subtitle_style))
            elements.append(Spacer(1, 20))
            
            # Agregar resumen financiero si se solicitó
            if incluir_resumen:
                elements.append(Paragraph("RESUMEN FINANCIERO", subtitle_style))
                
                # Tabla de resumen
                data = [
                    ['Concepto', 'Valor'],
                    ['Ingresos Totales', f"${total_ingresos:,.2f}"],
                    ['Ingresos por Membresías', f"${total_pagos:,.2f}"],
                    ['Ingresos por Productos', f"${total_ventas:,.2f}"],
                    ['Cantidad de Pagos', str(len(pagos))],
                    ['Cantidad de Ventas', str(len(ventas))]
                ]
                
                table = Table(data, colWidths=[4*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ]))
                
                elements.append(table)
                elements.append(Spacer(1, 20))
            
            # Agregar gráficos si se solicitó
            if incluir_graficos:
                elements.append(Paragraph("ANÁLISIS GRÁFICO", subtitle_style))
                
                # Crear un gráfico circular para la distribución de ingresos
                if total_ingresos > 0:
                    drawing = Drawing(400, 200)
                    pie = Pie()
                    pie.x = 150
                    pie.y = 50
                    pie.width = 150
                    pie.height = 150
                    pie.data = [float(total_pagos), float(total_ventas)]
                    pie.labels = ['Membresías', 'Productos']
                    pie.slices.strokeWidth = 0.5
                    
                    # Colores para las secciones del gráfico
                    pie.slices[0].fillColor = colors.lightblue
                    pie.slices[1].fillColor = colors.lightgreen
                    
                    drawing.add(pie)
                    # Añadir el título como un párrafo separado en vez de dentro del drawing
                    elements.append(drawing)
                    elements.append(Paragraph("Distribución de Ingresos", subtitle_style))
                    elements.append(Spacer(1, 20))
            
            # Agregar detalles si se solicitó
            if incluir_detalles:
                # Detalles de pagos de membresías
                if pagos:
                    elements.append(Paragraph("DETALLE DE PAGOS DE MEMBRESÍAS", subtitle_style))
                    
                    # Crear tabla de pagos
                    pagos_data = [['ID', 'Fecha', 'Usuario', 'Plan', 'Monto', 'Método de Pago']]
                    
                    for pago, usuario in pagos:
                        pagos_data.append([
                            str(pago.id),
                            pago.fecha_pago.strftime('%d/%m/%Y') if pago.fecha_pago else '',
                            usuario.nombre,
                            pago.plan,
                            f"${pago.monto:,.2f}",
                            pago.metodo_pago
                        ])
                    
                    pagos_table = Table(pagos_data, colWidths=[0.5*inch, 1*inch, 2.5*inch, 1.5*inch, 1*inch, 1.5*inch])
                    pagos_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ]))
                    
                    elements.append(pagos_table)
                    elements.append(Spacer(1, 20))
                
                # Detalles de ventas de productos
                if ventas:
                    elements.append(Paragraph("DETALLE DE VENTAS DE PRODUCTOS", subtitle_style))
                    
                    # Crear tabla de ventas
                    ventas_data = [['ID', 'Fecha', 'Producto', 'Usuario', 'Cant.', 'P. Unit.', 'Total', 'Método Pago']]
                    
                    for venta, producto, usuario in ventas:
                        ventas_data.append([
                            str(venta.id),
                            venta.fecha.strftime('%d/%m/%Y') if venta.fecha else '',
                            producto.nombre,
                            usuario.nombre if usuario else 'Cliente no registrado',
                            str(venta.cantidad),
                            f"${venta.precio_unitario:,.2f}",
                            f"${venta.total:,.2f}",
                            venta.metodo_pago
                        ])
                    
                    ventas_table = Table(ventas_data, colWidths=[0.5*inch, 1*inch, 2*inch, 2*inch, 0.5*inch, 1*inch, 1*inch, 1*inch])
                    ventas_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ]))
                    
                    elements.append(ventas_table)
            
            # Construir el PDF
            doc.build(elements)
            
            # Retornar el archivo para descarga
            return send_file(filepath, as_attachment=True, download_name=filename)
        
        else:
            flash('Formato de exportación no válido', 'danger')
            return redirect(url_for('main.finanzas.index'))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error al exportar datos financieros: {str(e)}', 'danger')
        return redirect(url_for('main.finanzas.index')) 
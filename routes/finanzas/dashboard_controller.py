"""
Módulo de Finanzas - Dashboard Controller
=========================================

Controlador para el dashboard principal de finanzas que muestra los indicadores
clave de desempeño (KPIs), gráficos de rendimiento y análisis financiero.

Desarrollado por: YEIFRAN HERNANDEZ
NEURALJIRA_DEV - Visión inteligente para gestión de gimnasios
"""

from flask import Blueprint, render_template, redirect, url_for, flash
from sqlalchemy import func, desc, extract, and_
from datetime import datetime, timedelta
import json
from decimal import Decimal

from models import db, Usuario, Asistencia, PagoMensualidad, VentaProducto, Producto
from models import datetime_colombia, date_colombia
from .utils import (sanitizar_valor_numerico, obtener_periodo_actual, 
                    obtener_periodos_anteriores, json_seguro, 
                    IMPUESTO_IVA, COSTO_OPERATIVO_PORCENTAJE, MARGEN_BRUTO_OBJETIVO)

# El blueprint se importa desde __init__.py
from routes.finanzas import bp

@bp.route('/')
def index():
    """
    Vista principal de finanzas que muestra un dashboard con indicadores clave
    y gráficos de rendimiento financiero según estándares contables profesionales.
    
    Implementado por: YEIFRAN HERNANDEZ (NEURALJIRA_DEV)
    """
    try:
        periodo_actual = obtener_periodo_actual()
        periodos = obtener_periodos_anteriores(6)  # Últimos 6 meses
        
        # Fechas clave para los cálculos
        hoy = date_colombia()
        inicio_dia = datetime.combine(hoy, datetime.min.time())
        inicio_semana = inicio_dia - timedelta(days=hoy.weekday())
        inicio_mes = datetime.combine(periodo_actual['inicio_mes'], datetime.min.time())
        fin_mes = datetime.combine(periodo_actual['fin_mes'], datetime.max.time())
        
        # SECCIÓN 2: MÉTRICAS DE USUARIOS Y ASISTENCIA
        # -----------------------------------------------------------
        # Obtener estadísticas de usuarios
        usuarios_activos = Usuario.query.count()
        usuarios_con_plan_vigente = Usuario.query.filter(
            Usuario.fecha_vencimiento_plan >= hoy
        ).count()
        
        # Calcular asistencias del mes actual (datos reales)
        asistencias_mes = Asistencia.query.filter(Asistencia.fecha >= inicio_mes).count()
        asistencias_promedio = sanitizar_valor_numerico(0.00)
        if usuarios_activos > 0:
            asistencias_promedio = sanitizar_valor_numerico(asistencias_mes / usuarios_activos)
        
        # SECCIÓN 3: CÁLCULO DE INGRESOS MENSUALES POR CATEGORÍA
        # -----------------------------------------------------------
        # Ingresos por membresías (mes actual)
        pagos_mes = db.session.query(func.sum(PagoMensualidad.monto)).\
            filter(PagoMensualidad.fecha_pago >= inicio_mes).scalar() or 0
        ingresos_mensual_membresias = sanitizar_valor_numerico(pagos_mes)
        
        # Ingresos por ventas de productos (mes actual)
        ventas_mes = db.session.query(func.sum(VentaProducto.total)).\
            filter(VentaProducto.fecha >= inicio_mes).scalar() or 0
        ingresos_mensual_productos = sanitizar_valor_numerico(ventas_mes)
        
        # Ingresos totales mensuales
        ingresos_mensual_total = ingresos_mensual_membresias + ingresos_mensual_productos
        
        # SECCIÓN 4: CÁLCULO DE INGRESOS DIARIOS Y SEMANALES
        # -----------------------------------------------------------
        # Ingresos diarios (hoy) con detalle por categoría
        pagos_dia = db.session.query(func.sum(PagoMensualidad.monto)).\
            filter(PagoMensualidad.fecha_pago >= inicio_dia).scalar() or 0
        ventas_dia = db.session.query(func.sum(VentaProducto.total)).\
            filter(VentaProducto.fecha >= inicio_dia).scalar() or 0
        
        ingresos_diarios_membresias = sanitizar_valor_numerico(pagos_dia)
        ingresos_diarios_productos = sanitizar_valor_numerico(ventas_dia)
        ingresos_diarios_total = ingresos_diarios_membresias + ingresos_diarios_productos
        
        # Ingresos semanales con detalle por categoría
        pagos_semana = db.session.query(func.sum(PagoMensualidad.monto)).\
            filter(PagoMensualidad.fecha_pago >= inicio_semana).scalar() or 0
        ventas_semana = db.session.query(func.sum(VentaProducto.total)).\
            filter(VentaProducto.fecha >= inicio_semana).scalar() or 0
        
        ingresos_semanales_membresias = sanitizar_valor_numerico(pagos_semana)
        ingresos_semanales_productos = sanitizar_valor_numerico(ventas_semana)
        ingresos_semanales_total = ingresos_semanales_membresias + ingresos_semanales_productos
        
        # SECCIÓN 5: CÁLCULO DE MÁRGENES DE GANANCIA E INDICADORES FINANCIEROS
        # -----------------------------------------------------------
        # Cálculo de márgenes de ganancia basado en costos estándar
        margen_bruto_diario = ingresos_diarios_total * MARGEN_BRUTO_OBJETIVO
        margen_bruto_semanal = ingresos_semanales_total * MARGEN_BRUTO_OBJETIVO
        margen_bruto_mensual = ingresos_mensual_total * MARGEN_BRUTO_OBJETIVO
        
        # Cálculo de impuestos (IVA)
        iva_diario = Decimal('0.00')
        iva_semanal = Decimal('0.00')
        iva_mensual = Decimal('0.00')
        
        # Solo calcular IVA si hay ingresos
        if ingresos_diarios_total > Decimal('0.00'):
            iva_diario = ingresos_diarios_total * IMPUESTO_IVA / (Decimal('1.00') + IMPUESTO_IVA)
        
        if ingresos_semanales_total > Decimal('0.00'):    
            iva_semanal = ingresos_semanales_total * IMPUESTO_IVA / (Decimal('1.00') + IMPUESTO_IVA)
        
        if ingresos_mensual_total > Decimal('0.00'):
            iva_mensual = ingresos_mensual_total * IMPUESTO_IVA / (Decimal('1.00') + IMPUESTO_IVA)
        
        # Cálculo de ingresos netos (después de impuestos)
        ingresos_netos_diarios = ingresos_diarios_total - iva_diario
        ingresos_netos_semanales = ingresos_semanales_total - iva_semanal
        ingresos_netos_mensuales = ingresos_mensual_total - iva_mensual
        
        # Cálculo de costos operativos
        costos_operativos_mensuales = ingresos_mensual_total * COSTO_OPERATIVO_PORCENTAJE
        
        # Cálculo de margen neto
        margen_neto_mensual = ingresos_netos_mensuales - costos_operativos_mensuales
        
        # SECCIÓN 6: DATOS PARA GRÁFICOS MENSUALES HISTÓRICOS
        # -----------------------------------------------------------
        # Preparar arrays para almacenar datos históricos
        meses = []
        datos_ingresos_membresias = []
        datos_ingresos_productos = []
        datos_margenes = []
        datos_ingresos_netos = []
        
        # Iterar por cada período para obtener datos históricos
        for periodo in periodos:
            try:
                # Fechas del período
                inicio_periodo = datetime.combine(periodo['inicio_mes'], datetime.min.time())
                fin_periodo = datetime.combine(periodo['fin_mes'], datetime.max.time())
                
                # Añadir nombre del mes al array
                nombre_mes = periodo['nombre_mes'][:3]  # Abreviatura del mes
                meses.append(f"{nombre_mes} {periodo['año']}")
                
                # Ingresos por membresías en el período
                pagos_periodo = db.session.query(func.sum(PagoMensualidad.monto)).\
                    filter(and_(
                        PagoMensualidad.fecha_pago >= inicio_periodo,
                        PagoMensualidad.fecha_pago <= fin_periodo
                    )).scalar() or 0
                ingresos_membresias = sanitizar_valor_numerico(pagos_periodo)
                datos_ingresos_membresias.append(float(ingresos_membresias))
                
                # Ingresos por productos en el período
                ventas_periodo = db.session.query(func.sum(VentaProducto.total)).\
                    filter(and_(
                        VentaProducto.fecha >= inicio_periodo,
                        VentaProducto.fecha <= fin_periodo
                    )).scalar() or 0
                ingresos_productos = sanitizar_valor_numerico(ventas_periodo)
                datos_ingresos_productos.append(float(ingresos_productos))
                
                # Cálculo del ingreso total y margen para el período
                ingresos_total_periodo = ingresos_membresias + ingresos_productos
                
                # Cálculos financieros para el período
                iva_periodo = ingresos_total_periodo * IMPUESTO_IVA / (Decimal('1.00') + IMPUESTO_IVA)
                ingresos_netos_periodo = ingresos_total_periodo - iva_periodo
                margen_periodo = ingresos_netos_periodo * MARGEN_BRUTO_OBJETIVO
                
                # Almacenar resultados
                datos_margenes.append(float(margen_periodo))
                datos_ingresos_netos.append(float(ingresos_netos_periodo))
                
            except Exception as e:
                # Registrar error y usar valores predeterminados
                print(f'Error en cálculo para período {periodo["mes"]}/{periodo["año"]}: {str(e)}')
                
                # Si ya tenemos el mes en la lista pero faltan los datos, añadir ceros
                if len(meses) > len(datos_ingresos_membresias):
                    datos_ingresos_membresias.append(0)
                if len(meses) > len(datos_ingresos_productos):
                    datos_ingresos_productos.append(0)
                if len(meses) > len(datos_margenes):
                    datos_margenes.append(0)
                if len(meses) > len(datos_ingresos_netos):
                    datos_ingresos_netos.append(0)
        
        # Verificar que tenemos datos para los gráficos
        if not meses:
            # Si no hay datos, usar valores predeterminados
            meses = [f"{periodo['nombre_mes'][:3]} {periodo['año']}" for periodo in periodos]
            datos_ingresos_membresias = [0] * len(meses)
            datos_ingresos_productos = [0] * len(meses)
            datos_margenes = [0] * len(meses)
            datos_ingresos_netos = [0] * len(meses)
        
        # SECCIÓN 7: DATOS PARA GRÁFICO DE DISTRIBUCIÓN DE PLANES
        # -----------------------------------------------------------
        # Obtener distribución de planes de membresía
        planes_count = db.session.query(
            Usuario.plan, func.count(Usuario.id)
        ).group_by(Usuario.plan).all()
        
        # Definir planes estándar y sus tarifas
        planes_estandar = {
            'Diario': Usuario.PRECIO_DIARIO,
            'Quincenal': Usuario.PRECIO_QUINCENAL,
            'Mensual': Usuario.PRECIO_MENSUAL,
            'Estudiantil': Usuario.PRECIO_ESTUDIANTIL,
            'Dirigido': Usuario.PRECIO_DIRIGIDO,
            'Personalizado': Usuario.PRECIO_PERSONALIZADO
        }
        
        # Inicializar con ceros para todos los planes posibles
        planes_nombres = list(planes_estandar.keys())
        datos_planes = [0] * len(planes_nombres)
        ingresos_potenciales_por_plan = [0] * len(planes_nombres)
        
        # Llenar con datos reales
        for plan, count in planes_count:
            if plan in planes_nombres:
                index = planes_nombres.index(plan)
                datos_planes[index] = count
                # Calcular ingreso potencial mensual por tipo de plan
                if plan in planes_estandar:
                    if plan == 'Diario':
                        # Para plan diario estimar 20 días al mes
                        ingresos_potenciales_por_plan[index] = planes_estandar[plan] * 20 * count
                    elif plan == 'Quincenal':
                        # Para plan quincenal estimar 2 pagos al mes
                        ingresos_potenciales_por_plan[index] = planes_estandar[plan] * 2 * count
                    else:
                        # Para otros planes, un pago mensual
                        ingresos_potenciales_por_plan[index] = planes_estandar[plan] * count
        
        # SECCIÓN 8: ANÁLISIS DE PRODUCTOS Y VENTAS
        # -----------------------------------------------------------
        # Datos para productos más vendidos (top 5)
        productos_vendidos = db.session.query(
            Producto.nombre,
            Producto.precio,
            func.sum(VentaProducto.cantidad).label('cantidad_vendida'),
            func.sum(VentaProducto.total).label('total_vendido')
        ).join(VentaProducto).\
         filter(VentaProducto.fecha >= inicio_mes).\
         group_by(Producto.id).\
         order_by(desc('cantidad_vendida')).\
         limit(5).all()
        
        # Calcular métricas de margen por producto
        if productos_vendidos:
            # Preparar arrays para los gráficos
            productos_nombres = [str(p[0]) for p in productos_vendidos]
            productos_cantidades = [int(sanitizar_valor_numerico(p[2])) for p in productos_vendidos]
            productos_ingresos = [float(sanitizar_valor_numerico(p[3])) for p in productos_vendidos]
            
            # Calcular margen de ganancia por producto (asumiendo un costo del 60%)
            productos_margenes = []
            for nombre, precio, cantidad, total in productos_vendidos:
                costo = sanitizar_valor_numerico(total) * COSTO_OPERATIVO_PORCENTAJE
                margen = sanitizar_valor_numerico(total) - costo
                productos_margenes.append(float(margen))
        else:
            productos_nombres = ["Sin ventas en este período"]
            productos_cantidades = [0]
            productos_ingresos = [0.0]
            productos_margenes = [0.0]
        
        # SECCIÓN 9: HISTORIAL DE TRANSACCIONES RECIENTES
        # -----------------------------------------------------------
        # Obtener los últimos pagos de membresías
        pagos_membresias = PagoMensualidad.query.order_by(PagoMensualidad.fecha_pago.desc()).limit(10).all()
        
        # Obtener las últimas ventas de productos
        ultimas_ventas = db.session.query(VentaProducto, Producto, Usuario).\
            join(Producto).\
            outerjoin(Usuario).\
            order_by(VentaProducto.fecha.desc()).limit(10).all()
        
        # Convertir ventas a formato para mostrar
        pagos_productos = []
        for venta, producto, usuario in ultimas_ventas:
            monto = sanitizar_valor_numerico(venta.total)
            pago = type('Pago', (), {
                'usuario': usuario,
                'monto': float(monto),
                'fecha': venta.fecha,
                'tipo': 'Producto',
                'metodo_pago': venta.metodo_pago,
                'detalle': producto.nombre,
                'categoria': producto.categoria if hasattr(producto, 'categoria') else 'General'
            })
            pagos_productos.append(pago)
        
        # Convertir pagos de membresías a formato similar
        pagos_memb_formateados = []
        for pago in pagos_membresias:
            monto = sanitizar_valor_numerico(pago.monto)
            pago_obj = type('Pago', (), {
                'usuario': pago.usuario,
                'monto': float(monto),
                'fecha': pago.fecha_pago,
                'tipo': 'Membresía',
                'metodo_pago': pago.metodo_pago,
                'detalle': pago.plan,
                'categoria': 'Mensualidad'
            })
            pagos_memb_formateados.append(pago_obj)
        
        # Combinar todos los pagos
        pagos = pagos_memb_formateados + pagos_productos
        pagos.sort(key=lambda x: x.fecha, reverse=True)
        
        # SECCIÓN 10: INDICADORES CLAVE DE DESEMPEÑO (KPIs)
        # -----------------------------------------------------------
        # KPI: Valor promedio de transacción
        valor_promedio_transaccion = sanitizar_valor_numerico(0.00)
        if pagos:
            total_transacciones = sum(p.monto for p in pagos)
            valor_promedio_transaccion = sanitizar_valor_numerico(total_transacciones / len(pagos))
        else:
            # Calcular directamente de la base de datos
            total_pagos = db.session.query(func.sum(PagoMensualidad.monto)).scalar() or 0
            total_ventas = db.session.query(func.sum(VentaProducto.total)).scalar() or 0
            count_pagos = db.session.query(func.count(PagoMensualidad.id)).scalar() or 0
            count_ventas = db.session.query(func.count(VentaProducto.id)).scalar() or 0
            
            total_transacciones = total_pagos + total_ventas
            total_count = count_pagos + count_ventas
            
            if total_count > 0:
                valor_promedio_transaccion = sanitizar_valor_numerico(total_transacciones / total_count)
        
        # KPI: Ingresos por usuario activo
        ingresos_por_usuario = sanitizar_valor_numerico(0.00)
        if usuarios_activos > 0:
            ingresos_por_usuario = sanitizar_valor_numerico(ingresos_mensual_total / usuarios_activos)
        else:
            # Calcular utilizando todos los ingresos históricos divididos por usuarios
            total_pagos = db.session.query(func.sum(PagoMensualidad.monto)).scalar() or 0
            total_ventas = db.session.query(func.sum(VentaProducto.total)).scalar() or 0
            total_ingresos = total_pagos + total_ventas
            
            if usuarios_activos > 0 and total_ingresos > 0:
                ingresos_por_usuario = sanitizar_valor_numerico(total_ingresos / usuarios_activos)
        
        # KPI: Ratio de conversión (usuarios con plan vigente vs total)
        ratio_conversion = sanitizar_valor_numerico(0.00)
        if usuarios_activos > 0:
            ratio_conversion = sanitizar_valor_numerico((usuarios_con_plan_vigente / usuarios_activos) * 100)
        
        # KPI: Asistencias promedio por usuario
        asistencias_promedio = sanitizar_valor_numerico(0.00)
        if usuarios_activos > 0:
            asistencias_promedio = sanitizar_valor_numerico(asistencias_mes / usuarios_activos)
        
        # Obtener fecha actual para la plantilla
        fecha_actual = datetime.now()
        
        # SECCIÓN 11: PREPARACIÓN DE DATOS PARA VISUALIZACIÓN
        # -----------------------------------------------------------
        
        # SECCIÓN 12: RENDERIZADO DE LA PLANTILLA CON TODOS LOS DATOS
        # -----------------------------------------------------------
        # SECCIÓN FINAL: ASEGURAR QUE TODAS LAS VARIABLES TIENEN VALORES PREDETERMINADOS SEGUROS
        # -----------------------------------------------------------
        # Variables para la sección de márgenes de ganancia (tarjetas de color)
        # Estas anteriormente se pasaban con otro nombre y causaban el error
        margen_diario = margen_bruto_diario  # Asegurar compatibilidad con la plantilla
        margen_semanal = margen_bruto_semanal
        margen_mensual = margen_bruto_mensual
        
        # Comprobar y asignar valores predeterminados para evitar errores de formateo
        valores_predeterminados = {
            # KPIs financieros
            'ingresos_por_usuario': sanitizar_valor_numerico(0.00),
            'valor_promedio_transaccion': sanitizar_valor_numerico(0.00),
            'ratio_conversion': sanitizar_valor_numerico(0.00),
            'asistencias_promedio': sanitizar_valor_numerico(0.00),
            
            # Ingresos por período
            'ingresos_mensual_total': sanitizar_valor_numerico(0.00),
            'ingresos_mensual_membresias': sanitizar_valor_numerico(0.00),
            'ingresos_mensual_productos': sanitizar_valor_numerico(0.00),
            'ingresos_diarios_total': sanitizar_valor_numerico(0.00),
            'ingresos_semanales_total': sanitizar_valor_numerico(0.00),
            
            # Márgenes y costos
            'margen_bruto_diario': sanitizar_valor_numerico(0.00),
            'margen_bruto_semanal': sanitizar_valor_numerico(0.00),
            'margen_bruto_mensual': sanitizar_valor_numerico(0.00),
            'margen_neto_mensual': sanitizar_valor_numerico(0.00),
            'costos_operativos_mensuales': sanitizar_valor_numerico(0.00),
            'iva_mensual': sanitizar_valor_numerico(0.00),
            'ingresos_netos_mensuales': sanitizar_valor_numerico(0.00),
            
            # Compatibilidad con nombres anteriores
            'margen_diario': margen_diario,
            'margen_semanal': margen_semanal,
            'margen_mensual': margen_mensual,
            
            # Datos para gráficos
            'meses': json_seguro(meses),
            'datos_ingresos_membresias': json_seguro(datos_ingresos_membresias),
            'datos_ingresos_productos': json_seguro(datos_ingresos_productos),
            'datos_margenes': json_seguro(datos_margenes),
            'datos_ingresos_netos': json_seguro(datos_ingresos_netos),
            'planes_nombres': json_seguro(planes_nombres),
            'datos_planes': json_seguro(datos_planes),
            'ingresos_potenciales_por_plan': json_seguro(ingresos_potenciales_por_plan),
            'productos_nombres': json_seguro(productos_nombres),
            'productos_cantidades': json_seguro(productos_cantidades),
            'productos_ingresos': json_seguro(productos_ingresos),
            'productos_margenes': json_seguro(productos_margenes),
            
            # Datos adicionales
            'fecha_actual': fecha_actual,
            'periodo_actual': periodo_actual,
            'pagos': pagos,
            
            # Datos sobre impuestos
            'iva_mensual': float(iva_mensual),
            'ingresos_netos_mensuales': float(ingresos_netos_mensuales),
            
            # Añadir el módulo json para la plantilla
            'json': json
        }
        
        # Asegurar que todas las variables tienen valores predeterminados si son None
        template_vars = valores_predeterminados.copy()
        for key, default_value in valores_predeterminados.items():
            if key not in template_vars or template_vars[key] is None:
                if hasattr(default_value, '__float__'):
                    template_vars[key] = float(default_value)
                else:
                    template_vars[key] = default_value
        
        return render_template('finanzas/finanzas.html', **template_vars)
                            
    except Exception as e:
        flash(f'Error al cargar finanzas: {str(e)}', 'danger')
        return redirect(url_for('main.finanzas.index')) 
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from models import db, Usuario, Asistencia, PagoMensualidad, VentaProducto, Producto
from models import datetime_colombia, date_colombia  # Importar las funciones de zona horaria
from sqlalchemy import func, desc, extract, and_
from datetime import datetime, timedelta, date
import json
import math
import calendar
from decimal import Decimal, ROUND_HALF_UP
import os
import csv

"""
Módulo de Finanzas del Sistema GymTrack
Desarrollado por: YEIFRAN HERNANDEZ
NEURALJIRA_DEV - Visión inteligente para gestión de gimnasios

ESTÁNDARES CONTABLES IMPLEMENTADOS:
- Categorización precisa de ingresos por origen
- Períodos fiscales estandarizados
- Consistencia en presentación de datos financieros
- Cálculos de márgenes e indicadores clave de negocio (KPIs)
- Tratamiento correcto de valores monetarios usando Decimal
"""

# Crear blueprint para finanzas
bp = Blueprint('finanzas', __name__, url_prefix='/finanzas')

# Función auxiliar para sanitizar valores
def sanitizar_valor_numerico(valor):
    """Convierte valores None, NaN o infinitos a 0 con precisión contable"""
    if valor is None or isinstance(valor, (float, int)) and (math.isnan(valor) or math.isinf(valor)):
        return Decimal('0.00')
    
    # Convertir a Decimal con precisión de 2 decimales para valores monetarios
    if isinstance(valor, (float, int)):
        return Decimal(str(valor)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    return valor

# Constantes financieras
IMPUESTO_IVA = Decimal('0.19')  # 19% - IVA estándar en Colombia
COSTO_OPERATIVO_PORCENTAJE = Decimal('0.60')  # 60% - Costo operativo estimado
MARGEN_BRUTO_OBJETIVO = Decimal('0.40')  # 40% - Objetivo de margen bruto

# Definición de períodos fiscales
def obtener_periodo_actual():
    """Obtiene el período fiscal actual (mes y año)"""
    hoy = date_colombia()
    return {
        'mes': hoy.month,
        'año': hoy.year,
        'nombre_mes': calendar.month_name[hoy.month],
        'inicio_mes': date(hoy.year, hoy.month, 1),
        'fin_mes': date(hoy.year, hoy.month, calendar.monthrange(hoy.year, hoy.month)[1])
    }

def obtener_periodos_anteriores(cantidad=6):
    """Obtiene los períodos fiscales anteriores al actual"""
    periodos = []
    periodo_actual = obtener_periodo_actual()
    
    # Añadir el período actual
    periodos.append(periodo_actual)
    
    # Añadir períodos anteriores
    for i in range(1, cantidad):
        # Calcular mes y año para el período anterior
        mes = periodo_actual['mes'] - i
        año = periodo_actual['año']
        
        # Ajustar si el mes es anterior a enero
        if mes <= 0:
            mes = 12 + mes
            año -= 1
        
        # Crear datos del período
        ultimo_dia = calendar.monthrange(año, mes)[1]
        periodo = {
            'mes': mes,
            'año': año,
            'nombre_mes': calendar.month_name[mes],
            'inicio_mes': date(año, mes, 1),
            'fin_mes': date(año, mes, ultimo_dia)
        }
        periodos.append(periodo)
    
    # Invertir para tener orden cronológico
    periodos.reverse()
    return periodos

@bp.route('/')
def index():
    """
    Vista principal de finanzas que muestra un dashboard con indicadores clave
    y gráficos de rendimiento financiero según estándares contables profesionales.
    
    Implementado por: YEIFRAN HERNANDEZ (NEURALJIRA_DEV)
    """
    try:
        # SECCIÓN 1: INICIALIZACIÓN DE FECHAS Y PERÍODOS FISCALES
        # -----------------------------------------------------------
        # Obtener período fiscal actual y anteriores
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
        asistencias_promedio = Decimal('0.00')
        if usuarios_activos > 0:
            asistencias_promedio = Decimal(str(asistencias_mes / usuarios_activos)).quantize(Decimal('0.01'))
        
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
        iva_diario = ingresos_diarios_total * IMPUESTO_IVA / (Decimal('1.00') + IMPUESTO_IVA)
        iva_semanal = ingresos_semanales_total * IMPUESTO_IVA / (Decimal('1.00') + IMPUESTO_IVA)
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
        valor_promedio_transaccion = Decimal('0.00')
        if pagos:
            total_transacciones = sum(p.monto for p in pagos)
            valor_promedio_transaccion = Decimal(str(total_transacciones / len(pagos))).quantize(Decimal('0.01'))
        
        # KPI: Ingresos por usuario activo
        ingresos_por_usuario = Decimal('0.00')
        if usuarios_activos > 0:
            ingresos_por_usuario = (ingresos_mensual_total / Decimal(str(usuarios_activos))).quantize(Decimal('0.01'))
        
        # KPI: Ratio de conversión (usuarios con plan vigente vs total)
        ratio_conversion = Decimal('0.00')
        if usuarios_activos > 0:
            ratio_conversion = (Decimal(str(usuarios_con_plan_vigente)) / Decimal(str(usuarios_activos)) * Decimal('100')).quantize(Decimal('0.01'))
        
        # Obtener fecha actual para la plantilla
        fecha_actual = datetime.now()
        
        # SECCIÓN 11: PREPARACIÓN DE DATOS PARA VISUALIZACIÓN
        # -----------------------------------------------------------
        # Convertir datos a JSON de forma segura
        def json_seguro(datos):
            """Convierte datos a JSON escapando valores problemáticos"""
            try:
                # Manejar casos especiales como NaN, Infinity, etc.
                if isinstance(datos, (list, tuple)):
                    datos = [0 if isinstance(x, (float, int)) and (math.isnan(x) or math.isinf(x)) else x for x in datos]
                return json.dumps(datos)
            except (TypeError, ValueError, OverflowError) as e:
                print(f"Error al convertir a JSON: {str(e)}")
                if isinstance(datos, (list, tuple)):
                    return json.dumps([0] * len(datos))
                return json.dumps([])
        
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
            'ingresos_por_usuario': Decimal('0.00'),
            'valor_promedio_transaccion': Decimal('0.00'),
            'ratio_conversion': Decimal('0.00'),
            'asistencias_promedio': Decimal('0.00'),
            
            # Ingresos por período
            'ingresos_mensual_total': Decimal('0.00'),
            'ingresos_mensual_membresias': Decimal('0.00'),
            'ingresos_mensual_productos': Decimal('0.00'),
            'ingresos_diarios_total': Decimal('0.00'),
            'ingresos_semanales_total': Decimal('0.00'),
            
            # Márgenes y costos
            'margen_bruto_diario': Decimal('0.00'),
            'margen_bruto_semanal': Decimal('0.00'),
            'margen_bruto_mensual': Decimal('0.00'),
            'margen_neto_mensual': Decimal('0.00'),
            'costos_operativos_mensuales': Decimal('0.00'),
            'iva_mensual': Decimal('0.00'),
            'ingresos_netos_mensuales': Decimal('0.00'),
            
            # Compatibilidad con nombres anteriores
            'margen_diario': Decimal('0.00'),
            'margen_semanal': Decimal('0.00'),
            'margen_mensual': Decimal('0.00')
        }
        
        # Crear un diccionario con todas las variables a pasar a la plantilla
        template_vars = {
            # Datos de usuarios y actividad
            'usuarios_activos': usuarios_activos,
            'usuarios_con_plan_vigente': usuarios_con_plan_vigente,
            'asistencias_mes': asistencias_mes,
            'asistencias_promedio': float(asistencias_promedio),
            
            # Datos de ingresos periódicos
            'ingresos_mensual_membresias': float(ingresos_mensual_membresias),
            'ingresos_mensual_productos': float(ingresos_mensual_productos),
            'ingresos_mensual_total': float(ingresos_mensual_total),
            'ingresos_diarios_total': float(ingresos_diarios_total),
            'ingresos_semanales_total': float(ingresos_semanales_total),
            
            # Datos de márgenes e indicadores financieros
            'margen_bruto_diario': float(margen_bruto_diario),
            'margen_bruto_semanal': float(margen_bruto_semanal),
            'margen_bruto_mensual': float(margen_bruto_mensual),
            'margen_neto_mensual': float(margen_neto_mensual),
            'costos_operativos_mensuales': float(costos_operativos_mensuales),
            
            # Compatibilidad con nombres anteriores
            'margen_diario': float(margen_diario),
            'margen_semanal': float(margen_semanal),
            'margen_mensual': float(margen_mensual),
            
            # KPIs importantes
            'valor_promedio_transaccion': float(valor_promedio_transaccion),
            'ingresos_por_usuario': float(ingresos_por_usuario),
            'ratio_conversion': float(ratio_conversion),
            
            # Datos para gráficos históricos
            'meses': json_seguro(meses),
            'datos_ingresos_membresias': json_seguro(datos_ingresos_membresias),
            'datos_ingresos_productos': json_seguro(datos_ingresos_productos),
            'datos_margenes': json_seguro(datos_margenes),
            'datos_ingresos_netos': json_seguro(datos_ingresos_netos),
            
            # Datos para gráficos de planes
            'planes_nombres': json_seguro(planes_nombres),
            'datos_planes': json_seguro(datos_planes),
            'ingresos_potenciales_por_plan': json_seguro(ingresos_potenciales_por_plan),
            
            # Datos para gráficos de productos
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
        for key, default_value in valores_predeterminados.items():
            if key not in template_vars or template_vars[key] is None:
                if isinstance(default_value, Decimal):
                    template_vars[key] = float(default_value)
                else:
                    template_vars[key] = default_value
        
        return render_template('finanzas/finanzas.html', **template_vars)
                            
    except Exception as e:
        flash(f'Error al cargar finanzas: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@bp.route('/pagos')
def pagos():
    pagos = PagoMensualidad.query.order_by(PagoMensualidad.fecha_pago.desc()).all()
    return render_template('pagos/pagos.html', pagos=pagos)

@bp.route('/diarias')
def finanzas_diarias():
    """
    Análisis financiero diario con desglose detallado de ingresos,
    ventas y métricas de rendimiento.
    
    Implementado por: YEIFRAN HERNANDEZ (NEURALJIRA_DEV)
    """
    try:
        # Obtener la fecha para el análisis (hoy por defecto)
        fecha_str = request.args.get('fecha')
        
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                fecha = date_colombia()
        else:
            fecha = date_colombia()
        
        # Inicio y fin del día
        inicio_dia = datetime.combine(fecha, datetime.min.time())
        fin_dia = datetime.combine(fecha, datetime.max.time())
        
        # 1. Obtener ingresos por membresías del día
        pagos_membresia = PagoMensualidad.query.filter(
            PagoMensualidad.fecha_pago >= inicio_dia,
            PagoMensualidad.fecha_pago <= fin_dia
        ).all()
        
        total_membresias = sum(pago.monto for pago in pagos_membresia)
        
        # Agrupar por tipo de plan
        ingresos_por_plan = {}
        for pago in pagos_membresia:
            if pago.plan in ingresos_por_plan:
                ingresos_por_plan[pago.plan] += pago.monto
            else:
                ingresos_por_plan[pago.plan] = pago.monto
        
        # 2. Obtener ingresos por ventas de productos del día
        ventas_productos = VentaProducto.query.filter(
            VentaProducto.fecha >= inicio_dia,
            VentaProducto.fecha <= fin_dia
        ).all()
        
        total_productos = sum(venta.total for venta in ventas_productos)
        
        # Agrupar por categoría
        productos_por_categoria = {}
        for venta in ventas_productos:
            producto = venta.producto
            if producto.categoria in productos_por_categoria:
                productos_por_categoria[producto.categoria] += venta.total
            else:
                productos_por_categoria[producto.categoria] = venta.total
        
        # Detalle de productos vendidos
        detalle_productos = {}
        for venta in ventas_productos:
            nombre_producto = venta.producto.nombre
            if nombre_producto in detalle_productos:
                detalle_productos[nombre_producto]['cantidad'] += venta.cantidad
                detalle_productos[nombre_producto]['total'] += venta.total
            else:
                detalle_productos[nombre_producto] = {
                    'cantidad': venta.cantidad,
                    'precio_unitario': venta.precio_unitario,
                    'total': venta.total
                }
        
        # 3. Calcular totales
        total_ingresos = total_membresias + total_productos
        
        # 4. Método de pago
        ingresos_por_metodo = {}
        
        # Métodos de pago de membresías
        for pago in pagos_membresia:
            if pago.metodo_pago in ingresos_por_metodo:
                ingresos_por_metodo[pago.metodo_pago] += pago.monto
            else:
                ingresos_por_metodo[pago.metodo_pago] = pago.monto
        
        # Métodos de pago de productos
        for venta in ventas_productos:
            if venta.metodo_pago in ingresos_por_metodo:
                ingresos_por_metodo[venta.metodo_pago] += venta.total
            else:
                ingresos_por_metodo[venta.metodo_pago] = venta.total
        
        # 5. Obtener asistencias del día
        asistencias = Asistencia.query.filter(
            Asistencia.fecha >= inicio_dia,
            Asistencia.fecha <= fin_dia
        ).count()
        
        return render_template('finanzas/finanzas_diarias.html',
                              fecha=fecha,
                              pagos_membresia=pagos_membresia,
                              ventas_productos=ventas_productos,
                              total_membresias=total_membresias,
                              total_productos=total_productos,
                              total_ingresos=total_ingresos,
                              ingresos_por_plan=ingresos_por_plan,
                              productos_por_categoria=productos_por_categoria,
                              detalle_productos=detalle_productos,
                              ingresos_por_metodo=ingresos_por_metodo,
                              asistencias=asistencias)
    except Exception as e:
        flash(f'Error al cargar finanzas diarias: {str(e)}', 'danger')
        return redirect(url_for('main.finanzas.index'))

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
            inicio_periodo = date(año_anterior, mes_anterior, 1)
            fin_periodo = date(año_anterior, mes_anterior, ultimo_dia)
            titulo_periodo = f"{calendar.month_name[mes_anterior]} {año_anterior}"
        elif periodo == 'trimestre':
            inicio_periodo = (hoy.replace(day=1) - timedelta(days=90))
            fin_periodo = hoy
            titulo_periodo = f"Último Trimestre ({inicio_periodo.strftime('%d/%m/%Y')} - {fin_periodo.strftime('%d/%m/%Y')})"
        elif periodo == 'anual':
            inicio_periodo = date(hoy.year, 1, 1)
            fin_periodo = date(hoy.year, 12, 31)
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
        ).join(Producto).outerjoin(Usuario).filter(
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

"""
Sistema de análisis financiero para GymTrack
Copyright © NEURALJIRA_DEV - YEIFRAN HERNANDEZ
Todos los derechos reservados.
""" 
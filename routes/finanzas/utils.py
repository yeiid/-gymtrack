from decimal import Decimal, ROUND_HALF_UP
import math
import calendar
from datetime import datetime, date, timedelta
from models import datetime_colombia, date_colombia

# Constantes financieras
IMPUESTO_IVA = Decimal('0.19')  # 19% - IVA estándar en Colombia
COSTO_OPERATIVO_PORCENTAJE = Decimal('0.60')  # 60% - Costo operativo estimado
MARGEN_BRUTO_OBJETIVO = Decimal('0.40')  # 40% - Objetivo de margen bruto

# Función auxiliar para sanitizar valores
def sanitizar_valor_numerico(valor):
    """Convierte valores None, NaN o infinitos a 0 con precisión contable"""
    if valor is None or isinstance(valor, (float, int)) and (math.isnan(valor) or math.isinf(valor)):
        return Decimal('0.00')
    
    # Convertir a Decimal con precisión de 2 decimales para valores monetarios
    if isinstance(valor, (float, int)):
        return Decimal(str(valor)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    return valor

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

def json_seguro(datos):
    """Convierte datos a JSON escapando valores problemáticos"""
    import json
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
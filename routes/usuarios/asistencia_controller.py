from flask import render_template, request, redirect, url_for, flash
from models import db, Usuario, Asistencia
from models import datetime_colombia, date_colombia
from datetime import datetime, timedelta
from sqlalchemy import func
import calendar
from routes.usuarios.routes import bp

@bp.route('/asistencia')
def asistencia():
    try:
        # Obtener parámetros de filtro
        mes_str = request.args.get('mes')
        ano_str = request.args.get('ano')
        usuario_id = request.args.get('usuario_id')
        
        # Obtener fecha actual en Colombia
        fecha_actual = date_colombia()
        
        # Si no se especifica mes o año, usar el actual
        mes = int(mes_str) if mes_str else fecha_actual.month
        ano = int(ano_str) if ano_str else fecha_actual.year
        
        # Construir filtro de fecha
        primer_dia = datetime(ano, mes, 1)
        
        # Último día del mes
        if mes == 12:
            ultimo_dia = datetime(ano + 1, 1, 1)
        else:
            ultimo_dia = datetime(ano, mes + 1, 1)
        
        # Consulta base de asistencias - IMPORTANTE: Hacer join con Usuario
        query = db.session.query(Asistencia, Usuario).join(
            Usuario, Asistencia.usuario_id == Usuario.id
        ).filter(
            Asistencia.fecha >= primer_dia,
            Asistencia.fecha < ultimo_dia
        )
        
        # Filtrar por usuario si se especifica
        if usuario_id:
            query = query.filter(Asistencia.usuario_id == int(usuario_id))
        
        # Obtener estadísticas por día
        stats_query = db.session.query(
            func.strftime('%d', Asistencia.fecha).label('dia'),
            func.count().label('cantidad')
        ).filter(
            Asistencia.fecha >= primer_dia,
            Asistencia.fecha < ultimo_dia
        )
        
        if usuario_id:
            stats_query = stats_query.filter(Asistencia.usuario_id == int(usuario_id))
            
        # Agrupar por día
        stats_query = stats_query.group_by(func.strftime('%d', Asistencia.fecha))
        
        # Estadísticas de asistencia por día
        asistencias_por_dia = stats_query.all()
        
        # Estadísticas para gráfico
        datos_grafico = {int(item.dia): item.cantidad for item in asistencias_por_dia}
        
        # Días del mes para el calendario
        dias_mes = calendar.monthrange(ano, mes)[1]
        
        # Generar calendario con datos de asistencia
        calendario = []
        for dia in range(1, dias_mes + 1):
            asistencias = datos_grafico.get(dia, 0)
            calendario.append({'dia': dia, 'asistencias': asistencias})
        
        # Obtener todos los usuarios con información de días restantes para el filtro
        usuarios_query = Usuario.query.all()
        usuarios_con_info = []
        for usuario in usuarios_query:
            # Calcular días restantes del plan
            dias_restantes = None
            if usuario.fecha_vencimiento_plan:
                dias_restantes = (usuario.fecha_vencimiento_plan - fecha_actual).days
                
            estado = 'vencido' if dias_restantes is not None and dias_restantes < 0 else \
                    'proximo' if dias_restantes is not None and dias_restantes <= 3 else \
                    'activo' if dias_restantes is not None else 'sin_fecha'
                    
            usuarios_con_info.append({
                'usuario': usuario,
                'dias_restantes': dias_restantes,
                'estado': estado
            })
        
        # Obtener todas las asistencias del período filtrado
        asistencias_result = query.order_by(Asistencia.fecha.desc()).all()
        
        # Formatear asistencias con usuario incluido
        asistencias_formateadas = []
        for asistencia, usuario in asistencias_result:
            asistencias_formateadas.append({
                'id': asistencia.id,
                'fecha': asistencia.fecha,
                'usuario': usuario  # Objeto usuario completo
            })
        
        # Contar asistencias de hoy
        hoy = fecha_actual
        inicio_hoy = datetime.combine(hoy, datetime.min.time())
        fin_hoy = datetime.combine(hoy, datetime.max.time())
        asistencias_hoy = Asistencia.query.filter(
            Asistencia.fecha >= inicio_hoy,
            Asistencia.fecha <= fin_hoy
        ).count()
        
        # Contar asistencias del mes actual
        primer_dia_mes = datetime(fecha_actual.year, fecha_actual.month, 1)
        if fecha_actual.month == 12:
            primer_dia_sig_mes = datetime(fecha_actual.year + 1, 1, 1)
        else:
            primer_dia_sig_mes = datetime(fecha_actual.year, fecha_actual.month + 1, 1)
            
        asistencias_mes = Asistencia.query.filter(
            Asistencia.fecha >= primer_dia_mes,
            Asistencia.fecha < primer_dia_sig_mes
        ).count()
        
        # Nombres de los meses para el selector
        nombres_meses = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        
        # Obtener próximos vencimientos (usuarios con planes que vencen en los próximos 3 días)
        proximos_vencimientos = []
        for usuario in Usuario.query.filter(
            Usuario.fecha_vencimiento_plan.isnot(None)
        ).all():
            if usuario.fecha_vencimiento_plan:
                dias = (usuario.fecha_vencimiento_plan - fecha_actual).days
                if 0 <= dias <= 3:
                    proximos_vencimientos.append({
                        'id': usuario.id,
                        'nombre': usuario.nombre,
                        'plan': usuario.plan,
                        'fecha_vencimiento': usuario.fecha_vencimiento_plan.strftime('%d/%m/%Y'),
                        'dias': dias
                    })
        
        # Añadir fecha actual para la plantilla
        today = datetime.now()
        
        return render_template('asistencia/asistencia.html', 
                              asistencias=asistencias_formateadas,
                              calendario=calendario,
                              usuarios=usuarios_con_info,
                              usuario_seleccionado=int(usuario_id) if usuario_id else None,
                              mes_actual=mes,
                              ano_actual=ano,
                              mes_nombre=nombres_meses[mes-1],
                              meses=[(i+1, nombre) for i, nombre in enumerate(nombres_meses)],
                              asistencias_hoy=asistencias_hoy,
                              asistencias_mes=asistencias_mes,
                              proximos_vencimientos=proximos_vencimientos,
                              limite_asistencias=len(asistencias_formateadas),
                              today=today)
    except Exception as e:
        print(f"Error en la página de asistencia: {str(e)}")
        flash(f"Error al mostrar la página de asistencia: {str(e)}", "danger")
        return redirect(url_for('main.index'))

@bp.route('/marcar_asistencia/<int:usuario_id>')
def marcar_asistencia(usuario_id):
    try:
        # Verificar si el usuario existe
        usuario = Usuario.query.get_or_404(usuario_id)
        
        # Verificar si ya tiene una asistencia hoy
        hoy = date_colombia()
        inicio_hoy = datetime.combine(hoy, datetime.min.time())
        fin_hoy = datetime.combine(hoy, datetime.max.time()) 
        
        asistencia_existente = Asistencia.query.filter(
            Asistencia.usuario_id == usuario_id,
            Asistencia.fecha >= inicio_hoy,
            Asistencia.fecha <= fin_hoy
        ).first()
        
        # Si ya existe una asistencia hoy, mostrar mensaje
        if asistencia_existente:
            flash(f"{usuario.nombre} ya tiene registrada su asistencia hoy ({asistencia_existente.fecha.strftime('%Y-%m-%d %H:%M')})", "info")
            return redirect(request.referrer or url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))
        
        # Registrar nueva asistencia
        asistencia = Asistencia(
            usuario_id=usuario_id,
            fecha=datetime_colombia()
        )
        
        db.session.add(asistencia)
        db.session.commit()
        
        flash(f"Asistencia registrada para {usuario.nombre}", "success")
        
        # Redireccionar a la página anterior o a la ficha del usuario
        return redirect(request.referrer or url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al registrar asistencia: {str(e)}", "danger")
        return redirect(url_for('main.usuarios.index')) 
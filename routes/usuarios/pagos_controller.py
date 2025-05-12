from flask import render_template, request, redirect, url_for, flash
from models import db, Usuario, PagoMensualidad
from models import datetime_colombia, date_colombia
from datetime import datetime
from routes.usuarios.usuario_controller import calcular_fecha_vencimiento
from routes.usuarios.routes import bp

@bp.route('/renovar_plan/<int:usuario_id>', methods=['GET', 'POST'])
def renovar_plan(usuario_id):
    try:
        usuario = Usuario.query.get_or_404(usuario_id)
        
        if request.method == 'POST':
            # Obtener datos del formulario
            plan = request.form['plan']
            metodo_pago = request.form['metodo_pago']
            fecha_pago_str = request.form.get('fecha_pago')
            
            # Convertir fecha si se proporciona, o usar la actual
            if fecha_pago_str:
                fecha_pago = datetime.strptime(fecha_pago_str, '%Y-%m-%d').date()
            else:
                fecha_pago = date_colombia()
            
            # Calcular fecha de vencimiento
            fecha_vencimiento = calcular_fecha_vencimiento(fecha_pago, plan)
            
            # Calcular precio según el plan seleccionado
            if plan == 'Diario':
                precio_plan = Usuario.PRECIO_DIARIO
            elif plan == 'Quincenal':
                precio_plan = Usuario.PRECIO_QUINCENAL
            elif plan == 'Mensual':
                precio_plan = Usuario.PRECIO_MENSUAL
            elif plan == 'Estudiantil':
                precio_plan = Usuario.PRECIO_ESTUDIANTIL
            elif plan == 'Dirigido':
                precio_plan = Usuario.PRECIO_DIRIGIDO
            elif plan == 'Personalizado':
                precio_plan = Usuario.PRECIO_PERSONALIZADO
            else:
                precio_plan = 0
            
            # Actualizar información del usuario
            usuario.plan = plan
            usuario.metodo_pago = metodo_pago
            usuario.fecha_vencimiento_plan = fecha_vencimiento
            usuario.precio_plan = precio_plan
            
            # Registrar el pago
            pago = PagoMensualidad(
                usuario_id=usuario_id,
                monto=precio_plan,
                metodo_pago=metodo_pago,
                plan=plan,
                fecha_inicio=fecha_pago,
                fecha_fin=fecha_vencimiento
            )
            
            db.session.add(pago)
            db.session.commit()
            
            flash("Plan renovado correctamente", "success")
            return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))
        
        # GET request
        # Obtener la fecha actual
        fecha_actual = date_colombia()
        # Formato para el input de fecha
        hoy_str = fecha_actual.strftime('%Y-%m-%d')
        
        return render_template('pagos/renovar_plan.html', 
                              usuario=usuario,
                              hoy=hoy_str,
                              fecha_actual=fecha_actual)
    except Exception as e:
        db.session.rollback()
        flash(f"Error al renovar plan: {str(e)}", "danger")
        return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id)) 
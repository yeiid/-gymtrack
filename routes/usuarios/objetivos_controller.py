from flask import render_template, request, redirect, url_for, flash
from models import db, Usuario, ObjetivoPersonal
from models import date_colombia
from datetime import datetime
from routes.usuarios.routes import bp

@bp.route('/objetivos/<int:usuario_id>', methods=['GET', 'POST'])
def objetivos(usuario_id):
    try:
        usuario = Usuario.query.get_or_404(usuario_id)
        
        if request.method == 'POST':
            descripcion = request.form.get('descripcion', '').strip()
            
            if not descripcion:
                flash("La descripción del objetivo es obligatoria", "danger")
                return redirect(url_for('main.usuarios.objetivos', usuario_id=usuario_id))
            
            # Convertir fecha si se proporciona
            fecha_objetivo_str = request.form.get('fecha_objetivo')
            fecha_objetivo = None
            if fecha_objetivo_str:
                fecha_objetivo = datetime.strptime(fecha_objetivo_str, '%Y-%m-%d').date()
            
            # Crear el objetivo
            objetivo = ObjetivoPersonal(
                usuario_id=usuario_id,
                descripcion=descripcion,
                fecha_objetivo=fecha_objetivo,
                progreso=0,
                estado='En progreso'
            )
            
            db.session.add(objetivo)
            db.session.commit()
            
            flash("Objetivo registrado correctamente", "success")
            return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))
        
        # Obtener los objetivos del usuario
        objetivos = ObjetivoPersonal.query.filter_by(usuario_id=usuario_id).order_by(
            ObjetivoPersonal.completado,
            ObjetivoPersonal.fecha_creacion.desc()
        ).all()
        
        return render_template('usuarios/objetivos.html', 
                              usuario=usuario,
                              objetivos=objetivos,
                              hoy=date_colombia().strftime('%Y-%m-%d'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al procesar objetivos: {str(e)}", "danger")
        return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))

@bp.route('/actualizar_objetivo/<int:objetivo_id>', methods=['POST'])
def actualizar_objetivo(objetivo_id):
    try:
        objetivo = ObjetivoPersonal.query.get_or_404(objetivo_id)
        usuario_id = objetivo.usuario_id
        
        # Obtener datos del formulario
        progreso = int(request.form.get('progreso', 0))
        estado = request.form.get('estado', 'En progreso')
        
        # Actualizar objetivo
        objetivo.progreso = progreso
        objetivo.estado = estado
        
        # Si se marca como completado, actualizar fecha de completado
        if estado == 'Completado':
            objetivo.completado = True
            objetivo.fecha_completado = date_colombia()
        else:
            objetivo.completado = False
            objetivo.fecha_completado = None
        
        db.session.commit()
        
        flash("Objetivo actualizado correctamente", "success")
        return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar objetivo: {str(e)}", "danger")
        
        # Redireccionar al perfil del usuario si conocemos su ID
        try:
            return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))
        except:
            return redirect(url_for('main.usuarios.index')) 
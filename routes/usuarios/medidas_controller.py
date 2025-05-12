from flask import render_template, request, redirect, url_for, flash
from models import db, Usuario, MedidasCorporales
from models import date_colombia
from datetime import datetime
from routes.usuarios.routes import bp

@bp.route('/medidas/<int:usuario_id>', methods=['GET', 'POST'])
def medidas(usuario_id):
    try:
        usuario = Usuario.query.get_or_404(usuario_id)
        
        if request.method == 'POST':
            # Convertir campos a flotantes, manejando entradas vacías
            peso = float(request.form['peso']) if request.form['peso'] else None
            altura = float(request.form['altura']) if request.form['altura'] else None
            pecho = float(request.form['pecho']) if request.form['pecho'] else None
            cintura = float(request.form['cintura']) if request.form['cintura'] else None
            cadera = float(request.form['cadera']) if request.form['cadera'] else None
            brazo_izquierdo = float(request.form['brazo_izquierdo']) if request.form['brazo_izquierdo'] else None
            brazo_derecho = float(request.form['brazo_derecho']) if request.form['brazo_derecho'] else None
            pierna_izquierda = float(request.form['pierna_izquierda']) if request.form['pierna_izquierda'] else None
            pierna_derecha = float(request.form['pierna_derecha']) if request.form['pierna_derecha'] else None
            fecha_str = request.form.get('fecha')
            
            # Calcular IMC si hay peso y altura
            imc = None
            if peso is not None and altura is not None and altura > 0:
                # Altura en metros para el cálculo del IMC
                altura_metros = altura / 100
                imc = peso / (altura_metros * altura_metros)
            
            # Convertir fecha si se proporciona
            if fecha_str:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            else:
                fecha = date_colombia()
            
            # Crear o actualizar medida
            medida_id = request.form.get('medida_id')
            if medida_id:
                # Actualizar medida existente
                medida = MedidasCorporales.query.get(medida_id)
                if not medida or medida.usuario_id != usuario_id:
                    flash("No se encontró la medida a actualizar", "danger")
                    return redirect(url_for('main.usuarios.medidas', usuario_id=usuario_id))
            else:
                # Crear nueva medida
                medida = MedidasCorporales(usuario_id=usuario_id)
            
            # Actualizar datos de la medida
            medida.fecha = fecha
            medida.peso = peso
            medida.altura = altura
            medida.imc = imc
            medida.pecho = pecho
            medida.cintura = cintura
            medida.cadera = cadera
            medida.brazo_izquierdo = brazo_izquierdo
            medida.brazo_derecho = brazo_derecho
            medida.pierna_izquierda = pierna_izquierda
            medida.pierna_derecha = pierna_derecha
            medida.notas = request.form.get('notas', '')
            
            # Guardar en la base de datos
            if not medida_id:
                db.session.add(medida)
            db.session.commit()
            
            flash("Medidas guardadas correctamente", "success")
            return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))
        
        # GET request
        # Obtener todas las medidas ordenadas por fecha descendente
        medidas = MedidasCorporales.query.filter_by(usuario_id=usuario_id).order_by(MedidasCorporales.fecha.desc()).all()
        
        # Obtener la medida a editar si se especifica
        medida_id = request.args.get('editar')
        medida_editar = None
        if medida_id:
            medida_editar = MedidasCorporales.query.get(medida_id)
            if not medida_editar or medida_editar.usuario_id != usuario_id:
                flash("No se encontró la medida a editar", "danger")
                return redirect(url_for('main.usuarios.medidas', usuario_id=usuario_id))
        
        return render_template('usuarios/medidas.html', 
                              usuario=usuario, 
                              medidas=medidas,
                              medida_editar=medida_editar,
                              hoy=date_colombia().strftime('%Y-%m-%d'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al procesar medidas: {str(e)}", "danger")
        return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id)) 
from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from sqlalchemy.orm import joinedload
from models import DatabaseManager, ModelFactory, Client, Vehicle, Service, Part, ServicePart
import datetime
import re

app = Flask(__name__)
@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    return f"<pre>{traceback.format_exc()}</pre>", 500
app.config.from_object(Config)

# Inicializa o gerenciador de banco de dados (Singleton)
db_manager = DatabaseManager(app.config["SQLALCHEMY_DATABASE_URI"])

# ===================================
# ROTAS
# ===================================

# Página inicial
@app.route('/')
def index():
    return render_template('index.html')


# -------------------
# Clientes
# -------------------
@app.route('/clients')
def clients():
    session = db_manager.get_session()
    try:
        all_clients = session.query(Client).all()
        return render_template('clients.html', clients=all_clients)
    finally:
        session.close()


@app.route('/client/new', methods=['GET', 'POST'])
def new_client():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']

        session = db_manager.get_session()
        try:
            client = ModelFactory.create_model('Client', name=name, address=address, phone=phone, email=email)
            session.add(client)
            session.commit()
            flash('Cliente adicionado com sucesso', 'success')
            return redirect(url_for('clients'))
        except Exception as e:
            session.rollback()
            flash(f'Erro ao adicionar cliente: {str(e)}', 'danger')
        finally:
            session.close()

    return render_template('new_client.html')


@app.route('/client/edit/<int:client_id>', methods=['GET', 'POST'])
def edit_client(client_id):
    session = db_manager.get_session()
    try:
        client = session.get(Client, client_id)
        if not client:
            flash('Cliente não encontrado!', 'danger')
            return redirect(url_for('clients'))

        if request.method == 'POST':
            client.name = request.form['name']
            client.address = request.form['address']
            client.phone = request.form['phone']
            client.email = request.form['email']
            session.commit()
            flash('Cliente atualizado com sucesso', 'success')
            return redirect(url_for('clients'))

        return render_template('edit_client.html', client=client)
    except Exception as e:
        session.rollback()
        flash(f'Erro ao editar cliente: {str(e)}', 'danger')
        return redirect(url_for('clients'))
    finally:
        session.close()


@app.route('/client/delete/<int:client_id>', methods=['POST'])
def delete_client(client_id):
    session = db_manager.get_session()
    try:
        client = session.get(Client, client_id)
        if not client:
            flash('Cliente não encontrado!', 'danger')
            return redirect(url_for('clients'))

        session.delete(client)
        session.commit()
        flash('Cliente excluído com sucesso', 'success')
        return redirect(url_for('clients'))
    except Exception as e:
        session.rollback()
        flash(f'Erro ao excluir cliente: {str(e)}', 'danger')
        return redirect(url_for('clients'))
    finally:
        session.close()


# -------------------
# Veículos
# -------------------
@app.route('/vehicles')
def vehicles():
    session = db_manager.get_session()
    try:
        all_vehicles = session.query(Vehicle).options(joinedload(Vehicle.client)).all()
        return render_template('vehicles.html', vehicles=all_vehicles)
    finally:
        session.close()


@app.route('/vehicle/new', methods=['GET', 'POST'])
def new_vehicle():
    session = db_manager.get_session()
    try:
        if request.method == 'POST':
            make = request.form['make']
            model = request.form['model']
            year_str = request.form['year']
            license_plate = request.form['license_plate']

            # Validação do ano
            if not year_str.isdigit() or len(year_str) > 4:
                flash('O campo Ano deve conter apenas números e ter no máximo 4 dígitos.', 'danger')
                clients = session.query(Client).all()
                return render_template('new_vehicle.html', clients=clients)
            year = int(year_str)

            # Validação da placa
            if len(license_plate) > 7 or not re.match(r'^[A-Z0-9]+$', license_plate):
                flash('O campo Placa deve ter no máximo 7 caracteres, contendo apenas letras maiúsculas e números.', 'danger')
                clients = session.query(Client).all()
                return render_template('new_vehicle.html', clients=clients)

            client_id = int(request.form['client_id'])
            vehicle = ModelFactory.create_model('Vehicle', make=make, model=model, year=year,
                                                license_plate=license_plate, client_id=client_id)
            session.add(vehicle)
            session.commit()
            flash('Veículo adicionado com sucesso', 'success')
            return redirect(url_for('vehicles'))

        clients = session.query(Client).all()
        return render_template('new_vehicle.html', clients=clients)
    except Exception as e:
        session.rollback()
        flash(f'Erro ao adicionar veículo: {str(e)}', 'danger')
        return redirect(url_for('vehicles'))
    finally:
        session.close()


@app.route('/vehicle/edit/<int:vehicle_id>', methods=['GET', 'POST'])
def edit_vehicle(vehicle_id):
    session = db_manager.get_session()
    try:
        vehicle = session.get(Vehicle, vehicle_id)
        if not vehicle:
            flash('Veículo não encontrado!', 'danger')
            return redirect(url_for('vehicles'))

        if request.method == 'POST':
            vehicle.make = request.form['make']
            vehicle.model = request.form['model']
            year_str = request.form['year']
            license_plate = request.form['license_plate']
            vehicle.client_id = int(request.form['client_id'])

            # Validação do ano
            if not year_str.isdigit() or len(year_str) > 4:
                flash('O campo Ano deve conter apenas números e ter no máximo 4 dígitos.', 'danger')
                clients = session.query(Client).all()
                return render_template('edit_vehicle.html', vehicle=vehicle, clients=clients)
            vehicle.year = int(year_str)

            # Validação da placa
            if len(license_plate) > 7 or not re.match(r'^[A-Z0-9]+$', license_plate):
                flash('O campo Placa deve ter no máximo 7 caracteres, contendo apenas letras maiúsculas e números.', 'danger')
                clients = session.query(Client).all()
                return render_template('edit_vehicle.html', vehicle=vehicle, clients=clients)
            vehicle.license_plate = license_plate

            session.commit()
            flash('Veículo atualizado com sucesso', 'success')
            return redirect(url_for('vehicles'))

        clients = session.query(Client).all()
        return render_template('edit_vehicle.html', vehicle=vehicle, clients=clients)
    except Exception as e:
        session.rollback()
        flash(f'Erro ao editar veículo: {str(e)}', 'danger')
        return redirect(url_for('vehicles'))
    finally:
        session.close()


@app.route('/vehicle/delete/<int:vehicle_id>', methods=['POST'])
def delete_vehicle(vehicle_id):
    session = db_manager.get_session()
    try:
        vehicle = session.get(Vehicle, vehicle_id)
        if not vehicle:
            flash('Veículo não encontrado!', 'danger')
            return redirect(url_for('vehicles'))

        session.delete(vehicle)
        session.commit()
        flash('Veículo excluído com sucesso', 'success')
        return redirect(url_for('vehicles'))
    except Exception as e:
        session.rollback()
        flash(f'Erro ao excluir veículo: {str(e)}', 'danger')
        return redirect(url_for('vehicles'))
    finally:
        session.close()


# -------------------
# Serviços
# -------------------
@app.route('/services')
def services():
    session = db_manager.get_session()
    try:
        all_services = session.query(Service).options(joinedload(Service.vehicle)).all()
        return render_template('services.html', services=all_services)
    finally:
        session.close()


@app.route('/service/new', methods=['GET', 'POST'])
def new_service():
    session = db_manager.get_session()
    try:
        if request.method == 'POST':
            description = request.form['description']
            cost_str = request.form['cost']
            vehicle_id = int(request.form['vehicle_id'])

            # Validação
            if len(description) > 400:
                flash('Descrição deve ter no máximo 400 caracteres.', 'danger')
                vehicles = session.query(Vehicle).all()
                return render_template('new_service.html', vehicles=vehicles)

            try:
                cost = float(cost_str)
                if len(str(int(cost))) > 6:
                    flash('Custo deve ter no máximo 6 dígitos.', 'danger')
                    vehicles = session.query(Vehicle).all()
                    return render_template('new_service.html', vehicles=vehicles)
            except ValueError:
                flash('Custo deve ser numérico.', 'danger')
                vehicles = session.query(Vehicle).all()
                return render_template('new_service.html', vehicles=vehicles)

            service = ModelFactory.create_model('Service', description=description, cost=cost,
                                                vehicle_id=vehicle_id, date=datetime.datetime.now())
            session.add(service)
            session.commit()
            flash('Serviço adicionado com sucesso', 'success')
            return redirect(url_for('services'))

        vehicles = session.query(Vehicle).all()
        return render_template('new_service.html', vehicles=vehicles)
    except Exception as e:
        session.rollback()
        flash(f'Erro ao adicionar serviço: {str(e)}', 'danger')
        return redirect(url_for('services'))
    finally:
        session.close()


# -------------------
# Peças
# -------------------
@app.route('/parts')
def parts():
    session = db_manager.get_session()
    try:
        all_parts = session.query(Part).all()
        return render_template('parts.html', parts=all_parts)
    finally:
        session.close()


@app.route('/part/new', methods=['GET', 'POST'])
def new_part():
    session = db_manager.get_session()
    try:
        if request.method == 'POST':
            name = request.form['name']
            price = float(request.form['price'])
            stock = int(request.form['stock'])

            part = ModelFactory.create_model('Part', name=name, price=price, stock=stock)
            session.add(part)
            session.commit()
            flash('Peça adicionada com sucesso', 'success')
            return redirect(url_for('parts'))

        return render_template('new_part.html')
    except Exception as e:
        session.rollback()
        flash(f'Erro ao adicionar peça: {str(e)}', 'danger')
        return redirect(url_for('parts'))
    finally:
        session.close()


@app.route('/part/edit/<int:part_id>', methods=['GET', 'POST'])
def edit_part(part_id):
    session = db_manager.get_session()
    try:
        part = session.get(Part, part_id)
        if not part:
            flash('Peça não encontrada!', 'danger')
            return redirect(url_for('parts'))

        if request.method == 'POST':
            part.name = request.form['name']
            part.price = float(request.form['price'])
            part.stock = int(request.form['stock'])
            session.commit()
            flash('Peça atualizada com sucesso', 'success')
            return redirect(url_for('parts'))

        return render_template('edit_part.html', part=part)
    except Exception as e:
        session.rollback()
        flash(f'Erro ao editar peça: {str(e)}', 'danger')
        return redirect(url_for('parts'))
    finally:
        session.close()


@app.route('/part/delete', methods=['POST'])
@app.route('/part/delete/<int:part_id>', methods=['POST'])
def delete_part(part_id=None):
    if part_id is None:
        try:
            part_id = int(request.form.get('part_id', 0))
        except (TypeError, ValueError):
            part_id = None

    if not part_id:
        flash('ID da peça não informado.', 'warning')
        return redirect(url_for('parts'))

    session = db_manager.get_session()
    try:
        part = session.get(Part, part_id)
        if not part:
            flash('Peça não encontrada!', 'danger')
            return redirect(url_for('parts'))

        session.query(ServicePart).filter(ServicePart.part_id == part_id).delete(synchronize_session=False)
        session.delete(part)
        session.commit()
        flash('Peça excluída com sucesso', 'success')
        return redirect(url_for('parts'))
    except Exception as e:
        session.rollback()
        app.logger.exception(f'Erro ao excluir peça {part_id}')
        flash(f'Erro ao excluir peça: {str(e)}', 'danger')
        return redirect(url_for('parts'))
    finally:
        session.close()


@app.route('/part/delete/', methods=['GET'])
def delete_part_missing_id():
    flash('ID da peça não informado.', 'warning')
    return redirect(url_for('parts'))


# ===================================
# EXECUÇÃO DO FLASK
# ===================================
# Nenhum app.run() aqui, use "flask run"



@app.route('/service/edit/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    session = db_manager.get_session()
    try:
        service = session.get(Service, service_id)
        if not service:
            flash('Serviço não encontrado!', 'danger')
            return redirect(url_for('services'))

        if request.method == 'POST':
            description = request.form['description']
            cost_str = request.form['cost']
            vehicle_id = int(request.form['vehicle_id'])

            if len(description) > 400:
                flash('Descrição deve ter no máximo 400 caracteres.', 'danger')
                vehicles = session.query(Vehicle).all()
                return render_template('edit_service.html', service=service, vehicles=vehicles)

            try:
                cost = float(cost_str)
                if len(str(int(cost))) > 6:
                    flash('Custo deve ter no máximo 6 dígitos.', 'danger')
                    vehicles = session.query(Vehicle).all()
                    return render_template('edit_service.html', service=service, vehicles=vehicles)
            except ValueError:
                flash('Custo deve ser numérico.', 'danger')
                vehicles = session.query(Vehicle).all()
                return render_template('edit_service.html', service=service, vehicles=vehicles)

            service.description = description
            service.cost = cost
            service.vehicle_id = vehicle_id
            session.commit()

            flash('Serviço atualizado com sucesso!', 'success')
            return redirect(url_for('services'))

        vehicles = session.query(Vehicle).all()
        return render_template('edit_service.html', service=service, vehicles=vehicles)

    except Exception as e:
        session.rollback()
        flash(f'Erro ao editar serviço: {str(e)}', 'danger')
        return redirect(url_for('services'))
    finally:
        session.close()


@app.route('/service/delete/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    session = db_manager.get_session()
    try:
        service = session.get(Service, service_id)
        if not service:
            flash('Serviço não encontrado!', 'danger')
            return redirect(url_for('services'))

        session.delete(service)
        session.commit()
        flash('Serviço excluído com sucesso!', 'success')
        return redirect(url_for('services'))

    except Exception as e:
        session.rollback()
        flash(f'Erro ao excluir serviço: {str(e)}', 'danger')
        return redirect(url_for('services'))
    finally:
        session.close()

"""
SISBOV - Versão Web (Flask)
Funciona no navegador do celular e pode ser instalada como PWA
"""
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.exceptions import BadRequest
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

# Importar serviços existentes
from src.services.database import init_database, get_connection
from src.services.property_service import (
    get_all_properties, create_property, get_property,
    update_property, delete_property
)
from src.services.animal_service import (
    get_animals_by_property, create_animal_group, update_animal_quantity,
    register_birth, register_death, get_total_animals
)
from src.services.movement_service import (
    register_sale, register_purchase, get_sales_by_property, get_purchases_by_property
)
from src.services.health_service import (
    register_health_procedure, get_health_procedures_by_property
)
from src.services.gta_service import (
    register_gta, get_gtas_by_property
)
from src.services.other_animals_service import (
    create_other_animal_group, get_other_animals_by_property
)
from src.services.report_service import generate_annual_report
from src.services.user_service import UserService, authenticate_user, get_user, update_password
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'sisbov-secret-key-change-in-production')

# Inicializar banco de dados na primeira execução
try:
    init_database()
except Exception as e:
    print(f"⚠️ Aviso ao inicializar banco: {e}")
    print("(O banco será inicializado quando necessário)")

# ==================== DECORADOR DE AUTENTICAÇÃO ====================

def login_required(f):
    """Decorador para exigir autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== ROTAS DE AUTENTICAÇÃO ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Tela de login"""
    # Se já estiver logado, redireciona para a página inicial
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Preencha todos os campos!', 'error')
            return render_template('login.html')
        
        try:
            user = authenticate_user(username, password)
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['name'] = user['name']
                flash(f'Bem-vindo, {user["name"]}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Usuário ou senha incorretos!', 'error')
        except Exception as e:
            flash('Erro ao fazer login. Tente novamente.', 'error')
            print(f"Erro no login: {e}")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Faz logout do usuário"""
    session.clear()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Tela de perfil do usuário"""
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not old_password or not new_password or not confirm_password:
            flash('Preencha todos os campos!', 'error')
            user = get_user(session['user_id'])
            return render_template('profile.html', user=user)
        
        if new_password != confirm_password:
            flash('As novas senhas não coincidem!', 'error')
            user = get_user(session['user_id'])
            return render_template('profile.html', user=user)
        
        if len(new_password) < 6:
            flash('A nova senha deve ter pelo menos 6 caracteres!', 'error')
            user = get_user(session['user_id'])
            return render_template('profile.html', user=user)
        
        if update_password(session['user_id'], old_password, new_password):
            flash('Senha alterada com sucesso!', 'success')
        else:
            flash('Senha atual incorreta!', 'error')
    
    user = get_user(session['user_id'])
    return render_template('profile.html', user=user)

# ==================== ROTAS PRINCIPAIS ====================

@app.route('/')
@login_required
def index():
    """Página inicial - lista de propriedades"""
    try:
        properties = get_all_properties()
        return render_template('index.html', properties=properties)
    except Exception as e:
        flash(f'Erro ao carregar propriedades: {str(e)}', 'error')
        return render_template('index.html', properties=[])

@app.route('/property/<int:property_id>')
@login_required
def property_detail(property_id):
    """Dashboard da propriedade"""
    try:
        property_data = get_property(property_id)
        if not property_data:
            flash('Propriedade não encontrada', 'error')
            return redirect(url_for('index'))
        
        total_animals = get_total_animals(property_id)
        
        return render_template('property_dashboard.html', 
                             property=property_data, 
                             total_animals=total_animals)
    except Exception as e:
        flash(f'Erro ao carregar propriedade: {str(e)}', 'error')
        return redirect(url_for('index'))

# ==================== API - PROPRIEDADES ====================

@app.route('/api/properties', methods=['GET'])
def api_get_properties():
    """API: Lista todas as propriedades"""
    try:
        properties = get_all_properties()
        return jsonify([dict(p) for p in properties])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/properties', methods=['POST'])
def api_create_property():
    """API: Cria nova propriedade"""
    try:
        data = request.get_json()
        property_id = create_property(
            name=data['name'],
            owner_name=data['owner_name'],
            city=data['city'],
            state=data['state'],
            cpf_cnpj=data.get('cpf_cnpj'),
            address=data.get('address'),
            area=float(data['area']) if data.get('area') else None,
            natural_pasture_area=float(data['natural_pasture_area']) if data.get('natural_pasture_area') else None,
            cultivated_pasture_area=float(data['cultivated_pasture_area']) if data.get('cultivated_pasture_area') else None,
            notes=data.get('notes')
        )
        return jsonify({'id': property_id, 'success': True}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/properties/<int:property_id>', methods=['GET'])
def api_get_property(property_id):
    """API: Obtém uma propriedade"""
    try:
        property_data = get_property(property_id)
        if not property_data:
            return jsonify({'error': 'Propriedade não encontrada'}), 404
        return jsonify(dict(property_data))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/properties/<int:property_id>', methods=['PUT'])
def api_update_property(property_id):
    """API: Atualiza propriedade"""
    try:
        data = request.get_json()
        update_property(
            property_id=property_id,
            name=data.get('name'),
            owner_name=data.get('owner_name'),
            city=data.get('city'),
            state=data.get('state'),
            cpf_cnpj=data.get('cpf_cnpj'),
            address=data.get('address'),
            area=float(data['area']) if data.get('area') else None,
            natural_pasture_area=float(data['natural_pasture_area']) if data.get('natural_pasture_area') else None,
            cultivated_pasture_area=float(data['cultivated_pasture_area']) if data.get('cultivated_pasture_area') else None,
            notes=data.get('notes')
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/properties/<int:property_id>', methods=['DELETE'])
def api_delete_property(property_id):
    """API: Deleta propriedade"""
    try:
        delete_property(property_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ==================== API - ANIMAIS ====================

@app.route('/api/properties/<int:property_id>/animals', methods=['GET'])
def api_get_animals(property_id):
    """API: Lista animais de uma propriedade"""
    try:
        animals = get_animals_by_property(property_id)
        return jsonify(animals)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/properties/<int:property_id>/animals', methods=['POST'])
def api_create_animal(property_id):
    """API: Cria registro de animais"""
    try:
        data = request.get_json()
        create_animal_group(
            property_id=property_id,
            purpose=data['purpose'],
            category=data['category'],
            sex=data['sex'],
            quantity=int(data['quantity']),
            age_range=data.get('age_range'),
            classification=data.get('classification')
        )
        return jsonify({'success': True}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ==================== API - MOVIMENTOS ====================

@app.route('/api/properties/<int:property_id>/movements', methods=['GET'])
def api_get_movements(property_id):
    """API: Lista movimentos de uma propriedade"""
    try:
        sales = get_sales_by_property(property_id)
        purchases = get_purchases_by_property(property_id)
        movements = {
            'sales': sales,
            'purchases': purchases
        }
        return jsonify(movements)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/properties/<int:property_id>/births', methods=['POST'])
def api_register_birth(property_id):
    """API: Registra nascimento"""
    try:
        data = request.get_json()
        register_birth(
            property_id=property_id,
            date=data['date'],
            sex=data['sex'],
            age_range=data['age_range'],
            quantity=int(data['quantity']),
            notes=data.get('notes')
        )
        return jsonify({'success': True}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/properties/<int:property_id>/deaths', methods=['POST'])
def api_register_death(property_id):
    """API: Registra morte"""
    try:
        data = request.get_json()
        register_death(
            property_id=property_id,
            date=data['date'],
            category=data['category'],
            sex=data['sex'],
            age_range=data['age_range'],
            quantity=int(data['quantity']),
            cause=data.get('cause')
        )
        return jsonify({'success': True}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/properties/<int:property_id>/sales', methods=['POST'])
def api_register_sale(property_id):
    """API: Registra venda"""
    try:
        data = request.get_json()
        register_sale(
            property_id=property_id,
            date=data['date'],
            category=data.get('category', 'Bezerro'),
            sex=data.get('sex', 'Macho'),
            age_range=data.get('age_range'),
            quantity=int(data['quantity']),
            has_gta=data.get('has_gta', False),
            gta_number=data.get('gta_number'),
            destination=data.get('destination')
        )
        return jsonify({'success': True}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/properties/<int:property_id>/purchases', methods=['POST'])
def api_register_purchase(property_id):
    """API: Registra compra"""
    try:
        data = request.get_json()
        register_purchase(
            property_id=property_id,
            date=data['date'],
            origin=data.get('origin'),
            category=data.get('category', 'Bezerro'),
            sex=data.get('sex', 'Macho'),
            age_range=data.get('age_range'),
            quantity=int(data['quantity']),
            has_gta=data.get('has_gta', False),
            gta_number=data.get('gta_number')
        )
        return jsonify({'success': True}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ==================== API - SANITÁRIO ====================

@app.route('/api/properties/<int:property_id>/health', methods=['GET'])
def api_get_health(property_id):
    """API: Lista procedimentos sanitários"""
    try:
        procedures = get_health_procedures_by_property(property_id)
        return jsonify(procedures)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/properties/<int:property_id>/health', methods=['POST'])
def api_register_health(property_id):
    """API: Registra procedimento sanitário"""
    try:
        data = request.get_json()
        register_health_procedure(
            property_id=property_id,
            procedure_type=data.get('procedure_type', 'Vacinação'),
            vaccination_type=data.get('vaccination_type'),
            purpose_disease=data.get('purpose_disease'),
            product=data['product'],
            application_date=data['date'],
            category=data.get('category', 'Bezerro'),
            sex=data.get('sex', 'Macho'),
            age_range=data.get('age_range'),
            quantity=int(data['quantity']),
            next_application_date=data.get('next_date'),
            notes=data.get('notes')
        )
        return jsonify({'success': True}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ==================== ROTAS DE FUNCIONALIDADES ====================

@app.route('/property/<int:property_id>/animals')
@login_required
def show_animals(property_id):
    """Tela de cadastro de animais"""
    try:
        property_data = get_property(property_id)
        if not property_data:
            flash('Propriedade não encontrada', 'error')
            return redirect(url_for('index'))
        animals = get_animals_by_property(property_id)
        return render_template('animals.html', property=property_data, animals=animals)
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('property_detail', property_id=property_id))

@app.route('/property/<int:property_id>/births')
@login_required
def show_births(property_id):
    """Tela de nascimentos"""
    try:
        from src.services.animal_service import get_births_by_property
        property_data = get_property(property_id)
        if not property_data:
            flash('Propriedade não encontrada', 'error')
            return redirect(url_for('index'))
        births = get_births_by_property(property_id)
        return render_template('births.html', property=property_data, births=births)
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('property_detail', property_id=property_id))

@app.route('/property/<int:property_id>/sales')
@login_required
def show_sales(property_id):
    """Tela de vendas"""
    try:
        property_data = get_property(property_id)
        if not property_data:
            flash('Propriedade não encontrada', 'error')
            return redirect(url_for('index'))
        sales = get_sales_by_property(property_id)
        return render_template('sales.html', property=property_data, sales=sales)
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('property_detail', property_id=property_id))

@app.route('/property/<int:property_id>/purchases')
@login_required
def show_purchases(property_id):
    """Tela de compras"""
    try:
        property_data = get_property(property_id)
        if not property_data:
            flash('Propriedade não encontrada', 'error')
            return redirect(url_for('index'))
        purchases = get_purchases_by_property(property_id)
        return render_template('purchases.html', property=property_data, purchases=purchases)
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('property_detail', property_id=property_id))

@app.route('/property/<int:property_id>/deaths')
@login_required
def show_deaths(property_id):
    """Tela de mortes"""
    try:
        from src.services.animal_service import get_deaths_by_property
        property_data = get_property(property_id)
        if not property_data:
            flash('Propriedade não encontrada', 'error')
            return redirect(url_for('index'))
        deaths = get_deaths_by_property(property_id)
        return render_template('deaths.html', property=property_data, deaths=deaths)
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('property_detail', property_id=property_id))

@app.route('/property/<int:property_id>/health')
@login_required
def show_health(property_id):
    """Tela de controle sanitário"""
    try:
        property_data = get_property(property_id)
        if not property_data:
            flash('Propriedade não encontrada', 'error')
            return redirect(url_for('index'))
        procedures = get_health_procedures_by_property(property_id)
        return render_template('health.html', property=property_data, procedures=procedures)
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('property_detail', property_id=property_id))

@app.route('/property/<int:property_id>/gta')
@login_required
def show_gta(property_id):
    """Tela de controle de GTA"""
    try:
        property_data = get_property(property_id)
        if not property_data:
            flash('Propriedade não encontrada', 'error')
            return redirect(url_for('index'))
        gtas = get_gtas_by_property(property_id)
        return render_template('gta.html', property=property_data, gtas=gtas)
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('property_detail', property_id=property_id))

@app.route('/property/<int:property_id>/other_animals')
@login_required
def show_other_animals(property_id):
    """Tela de outros animais"""
    try:
        property_data = get_property(property_id)
        if not property_data:
            flash('Propriedade não encontrada', 'error')
            return redirect(url_for('index'))
        other_animals = get_other_animals_by_property(property_id)
        return render_template('other_animals.html', property=property_data, other_animals=other_animals)
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('property_detail', property_id=property_id))

@app.route('/property/<int:property_id>/reports')
@login_required
def show_reports(property_id):
    """Tela de relatórios"""
    try:
        property_data = get_property(property_id)
        if not property_data:
            flash('Propriedade não encontrada', 'error')
            return redirect(url_for('index'))
        return render_template('reports.html', property=property_data)
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('property_detail', property_id=property_id))

# ==================== API - GTA ====================

@app.route('/api/properties/<int:property_id>/gtas', methods=['GET'])
def api_get_gtas(property_id):
    """API: Lista GTAs de uma propriedade"""
    try:
        gtas = get_gtas_by_property(property_id)
        return jsonify(gtas)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/properties/<int:property_id>/gtas', methods=['POST'])
def api_register_gta(property_id):
    """API: Registra GTA"""
    try:
        data = request.get_json()
        register_gta(
            property_id=property_id,
            movement_type=data['movement_type'],
            gta_number=data['gta_number'],
            emission_date=data['emission_date'],
            quantity=int(data['quantity']),
            origin_destination=data['origin_destination'],
            age_range=data.get('age_range'),
            notes=data.get('notes')
        )
        return jsonify({'success': True}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ==================== API - OUTROS ANIMAIS ====================

@app.route('/api/properties/<int:property_id>/other_animals', methods=['GET'])
def api_get_other_animals(property_id):
    """API: Lista outros animais de uma propriedade"""
    try:
        animals = get_other_animals_by_property(property_id)
        return jsonify(animals)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/properties/<int:property_id>/other_animals', methods=['POST'])
def api_register_other_animal(property_id):
    """API: Registra outro animal"""
    try:
        data = request.get_json()
        create_other_animal_group(
            property_id=property_id,
            species=data['species'],
            sex=data['sex'],
            quantity=int(data['quantity']),
            classification=data.get('classification')
        )
        return jsonify({'success': True}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ==================== API - RELATÓRIOS ====================

@app.route('/api/properties/<int:property_id>/summary', methods=['GET'])
def api_get_summary(property_id):
    """API: Retorna resumo da propriedade"""
    try:
        from src.services.database import get_connection
        from psycopg2.extras import RealDictCursor
        
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        summary = {}
        
        # Total de animais
        cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM animals WHERE property_id = %s", (property_id,))
        result = cursor.fetchone()
        summary['total_animals'] = result['total'] if result else 0
        
        # Total de nascimentos
        cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM births WHERE property_id = %s", (property_id,))
        result = cursor.fetchone()
        summary['total_births'] = result['total'] if result else 0
        
        # Total de mortes
        cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM deaths WHERE property_id = %s", (property_id,))
        result = cursor.fetchone()
        summary['total_deaths'] = result['total'] if result else 0
        
        # Total de vendas
        cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM sales WHERE property_id = %s", (property_id,))
        result = cursor.fetchone()
        summary['total_sales'] = result['total'] if result else 0
        
        # Total de compras
        cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM purchases WHERE property_id = %s", (property_id,))
        result = cursor.fetchone()
        summary['total_purchases'] = result['total'] if result else 0
        
        # Total de procedimentos sanitários
        cursor.execute("SELECT COUNT(*) as total FROM health_procedures WHERE property_id = %s", (property_id,))
        result = cursor.fetchone()
        summary['total_health'] = result['total'] if result else 0
        
        # Total de outros animais
        cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM other_animals WHERE property_id = %s", (property_id,))
        result = cursor.fetchone()
        summary['total_other_animals'] = result['total'] if result else 0
        
        cursor.close()
        conn.close()
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/properties/<int:property_id>/reports/annual', methods=['GET'])
def api_get_annual_report(property_id):
    """API: Gera relatório anual"""
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        report = generate_annual_report(property_id, year)
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== HEALTH CHECK ====================

@app.route('/health')
@app.route('/healthz')
@app.route('/ping')
def health_check():
    """Health check endpoint para monitoramento (UptimeRobot, etc.)"""
    try:
        # Verificar conexão com o banco de dados
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        
        # Se chegou aqui, tudo está OK
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        # Se houver erro, retornar status não saudável
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

# ==================== STATIC ROUTES ====================

@app.route('/static/sw.js')
def service_worker():
    """Service Worker para PWA"""
    return app.send_static_file('sw.js'), 200, {'Content-Type': 'application/javascript'}

@app.route('/static/manifest.json')
def manifest():
    """Manifest para PWA"""
    return app.send_static_file('manifest.json'), 200, {'Content-Type': 'application/json'}

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handler para páginas não encontradas"""
    # Se o usuário estiver logado, redirecionar para a página inicial
    if 'user_id' in session:
        flash('Página não encontrada', 'error')
        return redirect(url_for('index'))
    # Caso contrário, redirecionar para login
    return redirect(url_for('login'))

# ==================== INICIAR SERVIDOR ====================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("=" * 50)
    print("🚀 SISBOV - Versão Web")
    print("=" * 50)
    print(f"📱 Acesse no celular: http://seu-ip:{port}")
    print(f"💻 Acesse no PC: http://localhost:{port}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=debug)


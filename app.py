import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-super-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(250), nullable=False)
    
    # Perfil
    name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    
    # Endereço
    cep = db.Column(db.String(20), nullable=True)
    street = db.Column(db.String(150), nullable=True)
    number = db.Column(db.String(20), nullable=True)
    complement = db.Column(db.String(100), nullable=True)
    neighborhood = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(20), nullable=True)

    tasks = db.relationship('Task', backref='user', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='pendente') # 'pendente', 'concluida'
    category = db.Column(db.String(50), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login inválido. Verifique seu e-mail e senha.')
    return render_template('login.html')

@app.route('/register/step1', methods=['GET', 'POST'])
def register_step1():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('E-mail já cadastrado.')
            return redirect(url_for('register_step1'))
        if password != confirm_password:
            flash('As senhas não conferem.')
            return redirect(url_for('register_step1'))
        
        session['reg_email'] = email
        session['reg_password'] = password
        return redirect(url_for('register_step2'))
        
    return render_template('register_step1.html')

@app.route('/register/step2', methods=['GET', 'POST'])
def register_step2():
    if 'reg_email' not in session:
        return redirect(url_for('register_step1'))
        
    if request.method == 'POST':
        session['reg_name'] = request.form.get('name')
        session['reg_phone'] = request.form.get('phone')
        session['reg_gender'] = request.form.get('gender')
        return redirect(url_for('register_step3'))
        
    return render_template('register_step2.html')

@app.route('/register/step3', methods=['GET', 'POST'])
def register_step3():
    if 'reg_email' not in session or 'reg_name' not in session:
        return redirect(url_for('register_step1'))
        
    if request.method == 'POST':
        cep = request.form.get('cep')
        street = request.form.get('street')
        number = request.form.get('number')
        complement = request.form.get('complement')
        neighborhood = request.form.get('neighborhood')
        city = request.form.get('city')
        state = request.form.get('state')
        
        new_user = User(
            email=session['reg_email'],
            password_hash=generate_password_hash(session['reg_password'], method='scrypt'),
            name=session['reg_name'],
            phone=session['reg_phone'],
            gender=session['reg_gender'],
            cep=cep, street=street, number=number, complement=complement,
            neighborhood=neighborhood, city=city, state=state
        )
        db.session.add(new_user)
        db.session.commit()
        
        session.pop('reg_email', None)
        session.pop('reg_password', None)
        session.pop('reg_name', None)
        session.pop('reg_phone', None)
        session.pop('reg_gender', None)
        
        login_user(new_user)
        return redirect(url_for('dashboard'))
        
    return render_template('register_step3.html')

@app.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.due_date).all()
    pendentes_count = Task.query.filter_by(user_id=current_user.id, status='pendente').count()
    concluidas_count = Task.query.filter_by(user_id=current_user.id, status='concluida').count()
    
    # Adding mock numbers just to match the cards in the screen
    matriculas_count = 0 
    habilidades_count = 0 

    return render_template('dashboard.html', tasks=tasks, 
                           pendentes=pendentes_count, concluidas=concluidas_count,
                           matriculas=matriculas_count, habilidades=habilidades_count)

@app.route('/tasks/add', methods=['POST'])
@login_required
def add_task():
    name = request.form.get('name')
    description = request.form.get('description')
    due_date_str = request.form.get('due_date')
    category = request.form.get('category')
    
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            pass
            
    if name:
        new_task = Task(
            user_id=current_user.id,
            name=name,
            description=description,
            due_date=due_date,
            category=category,
            status='pendente'
        )
        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/tasks/complete/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id == current_user.id:
        task.status = 'concluida' if task.status == 'pendente' else 'pendente'
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.phone = request.form.get('phone')
        current_user.gender = request.form.get('gender')
        
        current_user.cep = request.form.get('cep')
        current_user.street = request.form.get('street')
        current_user.number = request.form.get('number')
        current_user.complement = request.form.get('complement')
        current_user.neighborhood = request.form.get('neighborhood')
        current_user.city = request.form.get('city')
        current_user.state = request.form.get('state')
        
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('profile'))
        
    return render_template('profile.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)

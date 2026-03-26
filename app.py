from flask import Flask, render_template, redirect, url_for, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'your-secret-key-here-change-this'

db = SQLAlchemy(app)

# ========== ДЕКОРАТОР ДЛЯ ПРОВЕРКИ АДМИНА ==========
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ========== МОДЕЛИ ==========
class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    theme = db.Column(db.String(20), default='light')
    sound_enabled = db.Column(db.Boolean, default=True)
    notifications_enabled = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    avatar_url = db.Column(db.String(255))
    subgroup = db.Column(db.String(10), default='A')
    instructor_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=True)
    car = db.Column(db.String(100), nullable=True)
    car_type = db.Column(db.String(20), default='manual')
    role = db.Column(db.String(20), default='user')  # 'admin' или 'user'
    
    settings = db.relationship('UserSettings', backref='user', uselist=False, cascade='all, delete-orphan')
    instructor = db.relationship('Schedule', foreign_keys=[instructor_id])
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Schedule(db.Model):
    __tablename__ = 'schedule'
    
    id = db.Column(db.Integer, primary_key=True)
    group_type = db.Column(db.String(50), nullable=False)
    day = db.Column(db.String(20))
    time_start = db.Column(db.String(10))
    time_end = db.Column(db.String(10))
    title = db.Column(db.String(200))
    room = db.Column(db.String(20))
    instructor = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    whatsapp = db.Column(db.String(20))
    rating = db.Column(db.Float)
    experience = db.Column(db.Integer)
    car_type = db.Column(db.String(50))
    cars = db.Column(db.String(200))
    slots = db.Column(db.Integer, default=5)
    order_index = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Schedule {self.group_type}>'

# ========== СОЗДАНИЕ ТАБЛИЦ ==========
with app.app_context():
    db.create_all()
    print("✅ База данных 'asd' и таблицы созданы")
    
    # Создаем администратора, если его нет
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin_user = User(
            username='admin',
            email='admin@autoschool.ru',
            role='admin',
            is_active=True,
            subgroup='A'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.flush()
        
        admin_settings = UserSettings(
            user_id=admin_user.id,
            theme='dark',
            sound_enabled=True,
            notifications_enabled=True
        )
        db.session.add(admin_settings)
        db.session.commit()
        print("✅ Администратор создан: admin@autoschool.ru / admin123")

# ========== МАРШРУТЫ ==========
@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/programs')
def programs():
    """Страница программ обучения"""
    return render_template('programs.html')

@app.route('/exam')
def exam():
    """Страница с экзаменом (виджет ПДД)"""
    return render_template('ticket.html')

@app.route('/fleet')
def fleet():
    """Страница автопарка"""
    return render_template('fleet.html')

@app.route('/instructors')
def instructors():
    """Страница инструкторов"""
    return render_template('instructors.html')

@app.route('/schedule')
def schedule():
    """Страница расписания"""
    return render_template('schedule.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации"""
    if request.method == 'POST':
        data = request.get_json()
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        errors = {}
        
        # Валидация username
        if not username or len(username) < 3 or len(username) > 20:
            errors['username'] = 'Имя пользователя должно быть от 3 до 20 символов'
        elif not re.match(r'^[A-Za-zА-Яа-я0-9_]+$', username):
            errors['username'] = 'Только буквы, цифры и символ подчеркивания (_)'
        else:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                errors['username'] = 'Пользователь с таким именем уже существует'
        
        # Валидация email
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not email or not re.match(email_regex, email):
            errors['email'] = 'Введите корректный email адрес'
        else:
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                errors['email'] = 'Пользователь с таким email уже существует'
        
        # Валидация пароля
        password_regex = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{6,}$'
        if not password or not re.match(password_regex, password):
            errors['password'] = 'Пароль должен содержать минимум 6 символов, включая заглавные, строчные буквы и цифры'
        
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        
        try:
            new_user = User(
                username=username,
                email=email,
                is_active=True,
                role='user'
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.flush()
            
            settings = UserSettings(
                user_id=new_user.id,
                theme='light',
                sound_enabled=True,
                notifications_enabled=True
            )
            db.session.add(settings)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Регистрация успешна!',
                'redirect': url_for('login')
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'errors': {'server': 'Ошибка сервера. Попробуйте позже.'}
            }), 500
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if request.method == 'POST':
        data = request.get_json()
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'errors': {'form': 'Заполните все поля'}
            }), 400
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['logged_in'] = True
            session['is_admin'] = user.is_admin()
            session['role'] = user.role
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Вход выполнен успешно!',
                'redirect': url_for('index')
            })
        else:
            return jsonify({
                'success': False,
                'errors': {'form': 'Неверный email или пароль'}
            }), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Выход из системы"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/profile/<int:user_id>')
def profile(user_id):
    """Профиль пользователя"""
    if session.get('user_id') != user_id and not session.get('is_admin'):
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(user_id)
    instructor = None
    if user.instructor_id:
        instructor = Schedule.query.filter_by(id=user.instructor_id, group_type='instructor').first()
    
    instructors = Schedule.query.filter_by(group_type='instructor', is_active=True).order_by(Schedule.order_index).all()
    
    return render_template('profile.html', 
                         user=user, 
                         instructor=instructor, 
                         instructors=instructors,
                         is_admin=session.get('is_admin'))

# ========== АДМИН-МАРШРУТЫ (только для администратора) ==========
@app.route('/update_subgroup', methods=['POST'])
@admin_required
def update_subgroup():
    """Обновление подгруппы пользователя (только админ)"""
    user_id = request.form.get('user_id') or session.get('user_id')
    user = User.query.get(user_id)
    if user:
        user.subgroup = request.form.get('subgroup')
        db.session.commit()
    return redirect(url_for('profile', user_id=user_id))

@app.route('/update_instructor', methods=['POST'])
@admin_required
def update_instructor():
    """Обновление инструктора (только админ)"""
    user_id = request.form.get('user_id') or session.get('user_id')
    user = User.query.get(user_id)
    if user:
        instructor_id = request.form.get('instructor_id')
        user.instructor_id = int(instructor_id) if instructor_id else None
        user.car = None  # Сбрасываем автомобиль при смене инструктора
        db.session.commit()
    return redirect(url_for('profile', user_id=user_id))

@app.route('/update_car', methods=['POST'])
@admin_required
def update_car():
    """Обновление автомобиля (только админ)"""
    user_id = request.form.get('user_id') or session.get('user_id')
    user = User.query.get(user_id)
    if user:
        user.car = request.form.get('car')
        db.session.commit()
    return redirect(url_for('profile', user_id=user_id))

@app.route('/admin/users')
@admin_required
def admin_users():
    """Список всех пользователей (только админ)"""
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# ========== АДМИН-ПАНЕЛЬ РАСПИСАНИЯ ==========
@app.route('/admin/schedule')
@admin_required
def admin_schedule():
    """Админ-панель для редактирования расписания"""
    theory_a = Schedule.query.filter_by(group_type='theory_A', is_active=True).order_by(Schedule.order_index).all()
    theory_b = Schedule.query.filter_by(group_type='theory_B', is_active=True).order_by(Schedule.order_index).all()
    theory_c = Schedule.query.filter_by(group_type='theory_C', is_active=True).order_by(Schedule.order_index).all()
    instructors = Schedule.query.filter_by(group_type='instructor', is_active=True).order_by(Schedule.order_index).all()
    
    return render_template('admin/schedule.html', 
                         theory_a=theory_a, 
                         theory_b=theory_b, 
                         theory_c=theory_c, 
                         instructors=instructors)

@app.route('/admin/schedule/add', methods=['POST'])
@admin_required
def admin_schedule_add():
    """Добавление нового занятия"""
    data = request.form
    new_schedule = Schedule(
        group_type=data.get('group_type'),
        day=data.get('day'),
        time_start=data.get('time_start'),
        time_end=data.get('time_end'),
        title=data.get('title'),
        room=data.get('room'),
        instructor=data.get('instructor'),
        phone=data.get('phone'),
        whatsapp=data.get('whatsapp'),
        rating=float(data.get('rating')) if data.get('rating') else None,
        experience=int(data.get('experience')) if data.get('experience') else None,
        car_type=data.get('car_type'),
        cars=data.get('cars'),
        slots=int(data.get('slots')) if data.get('slots') else 5,
        order_index=int(data.get('order_index')) if data.get('order_index') else 0,
        is_active=True
    )
    db.session.add(new_schedule)
    db.session.commit()
    return redirect(url_for('admin_schedule'))

@app.route('/admin/schedule/edit/<int:id>', methods=['POST'])
@admin_required
def admin_schedule_edit(id):
    """Редактирование занятия"""
    schedule = Schedule.query.get_or_404(id)
    schedule.day = request.form.get('day', schedule.day)
    schedule.time_start = request.form.get('time_start', schedule.time_start)
    schedule.time_end = request.form.get('time_end', schedule.time_end)
    schedule.title = request.form.get('title', schedule.title)
    schedule.room = request.form.get('room', schedule.room)
    schedule.instructor = request.form.get('instructor', schedule.instructor)
    schedule.phone = request.form.get('phone', schedule.phone)
    schedule.whatsapp = request.form.get('whatsapp', schedule.whatsapp)
    schedule.rating = float(request.form.get('rating')) if request.form.get('rating') else schedule.rating
    schedule.experience = int(request.form.get('experience')) if request.form.get('experience') else schedule.experience
    schedule.car_type = request.form.get('car_type', schedule.car_type)
    schedule.cars = request.form.get('cars', schedule.cars)
    schedule.slots = int(request.form.get('slots')) if request.form.get('slots') else schedule.slots
    schedule.order_index = int(request.form.get('order_index')) if request.form.get('order_index') else schedule.order_index
    db.session.commit()
    return redirect(url_for('admin_schedule'))

@app.route('/admin/schedule/delete/<int:id>')
@admin_required
def admin_schedule_delete(id):
    """Удаление занятия"""
    schedule = Schedule.query.get_or_404(id)
    schedule.is_active = False
    db.session.commit()
    return redirect(url_for('admin_schedule'))

@app.route('/admin/schedule/init')
@admin_required
def admin_schedule_init():
    """Инициализация тестовых данных расписания"""
    Schedule.query.delete()
    
    # Теория A
    theory_a_data = [
        {'group_type': 'theory_A', 'day': 'Понедельник', 'time_start': '10:00', 'time_end': '12:00', 'title': 'ПДД: Общие положения', 'room': '101', 'order_index': 1},
        {'group_type': 'theory_A', 'day': 'Понедельник', 'time_start': '14:00', 'time_end': '16:00', 'title': 'ПДД: Дорожные знаки', 'room': '101', 'order_index': 2},
        {'group_type': 'theory_A', 'day': 'Среда', 'time_start': '10:00', 'time_end': '12:00', 'title': 'ПДД: Разметка и сигналы', 'room': '101', 'order_index': 3},
        {'group_type': 'theory_A', 'day': 'Среда', 'time_start': '14:00', 'time_end': '16:00', 'title': 'ПДД: Скорость и обгон', 'room': '101', 'order_index': 4},
        {'group_type': 'theory_A', 'day': 'Пятница', 'time_start': '10:00', 'time_end': '12:00', 'title': 'ПДД: Остановка и стоянка', 'room': '101', 'order_index': 5},
        {'group_type': 'theory_A', 'day': 'Пятница', 'time_start': '14:00', 'time_end': '16:00', 'title': 'ПДД: Проезд перекрестков', 'room': '101', 'order_index': 6},
    ]
    
    for data in theory_a_data:
        db.session.add(Schedule(**data))
    
    # Теория B
    theory_b_data = [
        {'group_type': 'theory_B', 'day': 'Вторник', 'time_start': '10:00', 'time_end': '12:00', 'title': 'ПДД: Общие положения', 'room': '102', 'order_index': 1},
        {'group_type': 'theory_B', 'day': 'Вторник', 'time_start': '14:00', 'time_end': '16:00', 'title': 'ПДД: Дорожные знаки', 'room': '102', 'order_index': 2},
        {'group_type': 'theory_B', 'day': 'Четверг', 'time_start': '10:00', 'time_end': '12:00', 'title': 'ПДД: Разметка и сигналы', 'room': '102', 'order_index': 3},
        {'group_type': 'theory_B', 'day': 'Четверг', 'time_start': '14:00', 'time_end': '16:00', 'title': 'ПДД: Скорость и обгон', 'room': '102', 'order_index': 4},
    ]
    
    for data in theory_b_data:
        db.session.add(Schedule(**data))
    
    # Теория C
    theory_c_data = [
        {'group_type': 'theory_C', 'day': 'Суббота', 'time_start': '10:00', 'time_end': '13:00', 'title': 'ПДД: Общие положения + знаки', 'room': '103', 'order_index': 1},
        {'group_type': 'theory_C', 'day': 'Суббота', 'time_start': '14:00', 'time_end': '17:00', 'title': 'ПДД: Разметка + сигналы', 'room': '103', 'order_index': 2},
    ]
    
    for data in theory_c_data:
        db.session.add(Schedule(**data))
    
    # Инструкторы
    instructors_data = [
        {'group_type': 'instructor', 'instructor': 'Александр Петров', 'car_type': 'Механика', 'rating': 4.9, 'experience': 8, 'phone': '+7 (800) 123-45-67', 'whatsapp': '78001234567', 'cars': 'Renault Logan, Lada Vesta', 'order_index': 1},
        {'group_type': 'instructor', 'instructor': 'Елена Смирнова', 'car_type': 'Автомат', 'rating': 5.0, 'experience': 6, 'phone': '+7 (800) 123-45-68', 'whatsapp': '78001234568', 'cars': 'Kia Rio, Hyundai Solaris', 'order_index': 2},
        {'group_type': 'instructor', 'instructor': 'Дмитрий Иванов', 'car_type': 'Механика/Автомат', 'rating': 4.8, 'experience': 10, 'phone': '+7 (800) 123-45-69', 'whatsapp': '78001234569', 'cars': 'Skoda Octavia, Tesla Model 3', 'order_index': 3},
        {'group_type': 'instructor', 'instructor': 'Мария Козлова', 'car_type': 'Автомат', 'rating': 4.9, 'experience': 5, 'phone': '+7 (800) 123-45-70', 'whatsapp': '78001234570', 'cars': 'Kia Rio, Hyundai Solaris', 'order_index': 4},
        {'group_type': 'instructor', 'instructor': 'Сергей Николаев', 'car_type': 'Механика', 'rating': 4.7, 'experience': 12, 'phone': '+7 (800) 123-45-71', 'whatsapp': '78001234571', 'cars': 'Renault Logan, Lada Vesta', 'order_index': 5},
        {'group_type': 'instructor', 'instructor': 'Анна Волкова', 'car_type': 'Автомат', 'rating': 5.0, 'experience': 4, 'phone': '+7 (800) 123-45-72', 'whatsapp': '78001234572', 'cars': 'Skoda Octavia, Tesla Model 3', 'order_index': 6},
    ]
    
    for data in instructors_data:
        db.session.add(Schedule(**data))
    
    db.session.commit()
    return redirect(url_for('admin_schedule'))

# ========== API ==========
@app.route('/api/schedule')
def api_schedule():
    """API для получения расписания"""
    theory_a = Schedule.query.filter_by(group_type='theory_A', is_active=True).order_by(Schedule.order_index).all()
    theory_b = Schedule.query.filter_by(group_type='theory_B', is_active=True).order_by(Schedule.order_index).all()
    theory_c = Schedule.query.filter_by(group_type='theory_C', is_active=True).order_by(Schedule.order_index).all()
    instructors = Schedule.query.filter_by(group_type='instructor', is_active=True).order_by(Schedule.order_index).all()
    
    def serialize(items):
        return [{
            'id': item.id,
            'day': item.day,
            'time_start': item.time_start,
            'time_end': item.time_end,
            'title': item.title,
            'room': item.room,
            'instructor': item.instructor,
            'phone': item.phone,
            'whatsapp': item.whatsapp,
            'rating': item.rating,
            'experience': item.experience,
            'car_type': item.car_type,
            'cars': item.cars,
            'slots': item.slots
        } for item in items]
    
    return jsonify({
        'theory': {
            'A': serialize(theory_a),
            'B': serialize(theory_b),
            'C': serialize(theory_c)
        },
        'instructors': serialize(instructors)
    })

@app.route('/api/users')
def api_users():
    """API для получения списка пользователей"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'role': u.role,
        'subgroup': u.subgroup,
        'car': u.car,
        'created_at': u.created_at.strftime('%Y-%m-%d %H:%M')
    } for u in users])

# ========== ОБРАБОТЧИКИ ОШИБОК ==========
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='127.0.0.1')
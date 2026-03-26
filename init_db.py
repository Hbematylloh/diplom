#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
from werkzeug.security import generate_password_hash

DB_CONFIG = {
    'dbname': 'asd',
    'user': 'postgres',
    'password': '123',
    'host': 'localhost',
    'port': '5432'
}

def create_database():
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'asd'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE asd")
            print("[OK] Database asd created")
        else:
            print("[OK] Database asd already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def create_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        return conn
    except psycopg2.Error as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

def create_tables(conn):
    cursor = conn.cursor()
    
    tables_sql = """
    -- Таблица пользователей
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(80) UNIQUE NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password_hash VARCHAR(200) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        last_login TIMESTAMP,
        avatar_url VARCHAR(255),
        subgroup VARCHAR(10) DEFAULT 'A',
        instructor_id INTEGER,
        car VARCHAR(100),
        car_type VARCHAR(20) DEFAULT 'manual',
        role VARCHAR(20) DEFAULT 'user'
    );

    -- Таблица настроек пользователей
    CREATE TABLE IF NOT EXISTS user_settings (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
        theme VARCHAR(20) DEFAULT 'light',
        sound_enabled BOOLEAN DEFAULT TRUE,
        notifications_enabled BOOLEAN DEFAULT TRUE,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Таблица расписания
    CREATE TABLE IF NOT EXISTS schedule (
        id SERIAL PRIMARY KEY,
        group_type VARCHAR(50) NOT NULL,
        day VARCHAR(20),
        time_start VARCHAR(10),
        time_end VARCHAR(10),
        title VARCHAR(200),
        room VARCHAR(20),
        instructor VARCHAR(100),
        phone VARCHAR(20),
        whatsapp VARCHAR(20),
        rating FLOAT,
        experience INTEGER,
        car_type VARCHAR(50),
        cars VARCHAR(200),
        slots INTEGER DEFAULT 5,
        order_index INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Индексы
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_schedule_group_type ON schedule(group_type);
    """
    
    try:
        cursor.execute(tables_sql)
        conn.commit()
        print("[OK] Tables created:")
        print("    - users (with subgroup, instructor_id, car, car_type, role)")
        print("    - user_settings")
        print("    - schedule (with cars field)")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"[ERROR] {e}")
        sys.exit(1)

def create_test_user(conn):
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print("[OK] Users already exist")
            return
        
        # Обычный тестовый пользователь
        user_password_hash = generate_password_hash('Test123')
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, created_at, is_active, subgroup, car_type, role) 
            VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s) RETURNING id
        """, ('test_user', 'test@example.com', user_password_hash, True, 'A', 'manual', 'user'))
        
        user_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO user_settings (user_id, theme, sound_enabled, notifications_enabled) 
            VALUES (%s, %s, %s, %s)
        """, (user_id, 'dark', True, True))
        
        # Администратор
        admin_password_hash = generate_password_hash('admin123')
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, created_at, is_active, subgroup, car_type, role) 
            VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s) RETURNING id
        """, ('admin', 'admin@autoschool.ru', admin_password_hash, True, 'A', 'manual', 'admin'))
        
        admin_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO user_settings (user_id, theme, sound_enabled, notifications_enabled) 
            VALUES (%s, %s, %s, %s)
        """, (admin_id, 'dark', True, True))
        
        conn.commit()
        print("[OK] Test users created:")
        print("    - User: test@example.com / Test123 (role: user)")
        print("    - Admin: admin@autoschool.ru / admin123 (role: admin)")
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"[ERROR] {e}")

def create_test_schedule(conn):
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM schedule")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print("[OK] Schedule data already exists")
            return
        
        print("[INFO] Creating test schedule data...")
        
        # Теория A
        theory_a = [
            ('theory_A', 'Понедельник', '10:00', '12:00', 'ПДД: Общие положения', '101'),
            ('theory_A', 'Понедельник', '14:00', '16:00', 'ПДД: Дорожные знаки', '101'),
            ('theory_A', 'Среда', '10:00', '12:00', 'ПДД: Разметка и сигналы', '101'),
            ('theory_A', 'Среда', '14:00', '16:00', 'ПДД: Скорость и обгон', '101'),
            ('theory_A', 'Пятница', '10:00', '12:00', 'ПДД: Остановка и стоянка', '101'),
            ('theory_A', 'Пятница', '14:00', '16:00', 'ПДД: Проезд перекрестков', '101'),
        ]
        
        # Теория B
        theory_b = [
            ('theory_B', 'Вторник', '10:00', '12:00', 'ПДД: Общие положения', '102'),
            ('theory_B', 'Вторник', '14:00', '16:00', 'ПДД: Дорожные знаки', '102'),
            ('theory_B', 'Четверг', '10:00', '12:00', 'ПДД: Разметка и сигналы', '102'),
            ('theory_B', 'Четверг', '14:00', '16:00', 'ПДД: Скорость и обгон', '102'),
        ]
        
        # Теория C
        theory_c = [
            ('theory_C', 'Суббота', '10:00', '13:00', 'ПДД: Общие положения + знаки', '103'),
            ('theory_C', 'Суббота', '14:00', '17:00', 'ПДД: Разметка + сигналы', '103'),
        ]
        
        # Инструкторы с автомобилями
        instructors = [
            ('instructor', 'Александр Петров', 'Механика', 4.9, 8, '+7 (800) 123-45-67', '78001234567', 'Renault Logan, Lada Vesta'),
            ('instructor', 'Елена Смирнова', 'Автомат', 5.0, 6, '+7 (800) 123-45-68', '78001234568', 'Kia Rio, Hyundai Solaris'),
            ('instructor', 'Дмитрий Иванов', 'Механика/Автомат', 4.8, 10, '+7 (800) 123-45-69', '78001234569', 'Skoda Octavia, Tesla Model 3'),
            ('instructor', 'Мария Козлова', 'Автомат', 4.9, 5, '+7 (800) 123-45-70', '78001234570', 'Kia Rio, Hyundai Solaris'),
            ('instructor', 'Сергей Николаев', 'Механика', 4.7, 12, '+7 (800) 123-45-71', '78001234571', 'Renault Logan, Lada Vesta'),
            ('instructor', 'Анна Волкова', 'Автомат', 5.0, 4, '+7 (800) 123-45-72', '78001234572', 'Skoda Octavia, Tesla Model 3'),
        ]
        
        # Вставка теории A
        for item in theory_a:
            cursor.execute("""
                INSERT INTO schedule (group_type, day, time_start, time_end, title, room, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, true)
            """, item)
        
        # Вставка теории B
        for item in theory_b:
            cursor.execute("""
                INSERT INTO schedule (group_type, day, time_start, time_end, title, room, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, true)
            """, item)
        
        # Вставка теории C
        for item in theory_c:
            cursor.execute("""
                INSERT INTO schedule (group_type, day, time_start, time_end, title, room, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, true)
            """, item)
        
        # Вставка инструкторов
        order = 1
        for item in instructors:
            cursor.execute("""
                INSERT INTO schedule (group_type, instructor, car_type, rating, experience, phone, whatsapp, cars, order_index, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true) RETURNING id
            """, (item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], order))
            order += 1
        
        conn.commit()
        total = len(theory_a) + len(theory_b) + len(theory_c) + len(instructors)
        print(f"[OK] Schedule data created: {total} records")
        print(f"    - Theory A: {len(theory_a)} lessons")
        print(f"    - Theory B: {len(theory_b)} lessons")
        print(f"    - Theory C: {len(theory_c)} lessons")
        print(f"    - Instructors: {len(instructors)}")
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"[ERROR] {e}")

def show_statistics(conn):
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)
    
    # Общая статистика
    for table in ['users', 'user_settings', 'schedule']:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()['count']
        print(f"{table:15}: {count}")
    
    # Статистика по ролям
    try:
        cursor.execute("""
            SELECT role, COUNT(*) as count 
            FROM users 
            GROUP BY role
        """)
        roles = cursor.fetchall()
        if roles:
            print("\n👥 Users by role:")
            for r in roles:
                print(f"  {r['role']:10}: {r['count']}")
    except Exception as e:
        print(f"\n  (role info: {e})")
    
    # Статистика по подгруппам
    try:
        cursor.execute("""
            SELECT subgroup, COUNT(*) as count 
            FROM users 
            WHERE subgroup IS NOT NULL 
            GROUP BY subgroup
        """)
        subgroups = cursor.fetchall()
        if subgroups:
            print("\n📚 Users by subgroup:")
            for s in subgroups:
                print(f"  Subgroup {s['subgroup']}: {s['count']}")
    except Exception as e:
        print(f"\n  (subgroup info: {e})")
    
    # Статистика по типу КПП
    try:
        cursor.execute("""
            SELECT car_type, COUNT(*) as count 
            FROM users 
            WHERE car_type IS NOT NULL 
            GROUP BY car_type
        """)
        car_types = cursor.fetchall()
        if car_types:
            print("\n🚗 Users by car type:")
            for c in car_types:
                type_name = "Механика" if c['car_type'] == 'manual' else "Автомат"
                print(f"  {type_name}: {c['count']}")
    except Exception as e:
        print(f"\n  (car type info: {e})")
    
    # Статистика по расписанию
    cursor.execute("""
        SELECT group_type, COUNT(*) as count 
        FROM schedule 
        WHERE is_active = true 
        GROUP BY group_type
        ORDER BY group_type
    """)
    schedule_stats = cursor.fetchall()
    
    if schedule_stats:
        print("\n📅 Schedule by type:")
        for s in schedule_stats:
            type_name = s['group_type'].replace('_', ' ')
            print(f"  {type_name:12}: {s['count']}")
    
    # Инструкторы
    cursor.execute("""
        SELECT instructor, car_type, rating, experience, phone, cars
        FROM schedule 
        WHERE group_type = 'instructor' AND is_active = true
        ORDER BY order_index
    """)
    instructors = cursor.fetchall()
    if instructors:
        print("\n👨‍🏫 Instructors:")
        for i in instructors:
            print(f"  • {i['instructor']}")
            print(f"    - Тип КПП: {i['car_type']} | ⭐ {i['rating']} | {i['experience']} лет")
            print(f"    - Телефон: {i['phone']}")
            print(f"    - Автомобили: {i['cars']}")
    
    # Теория
    cursor.execute("""
        SELECT group_type, COUNT(*) as count 
        FROM schedule 
        WHERE group_type LIKE 'theory_%' AND is_active = true 
        GROUP BY group_type
    """)
    theory = cursor.fetchall()
    if theory:
        print("\n📖 Theory lessons:")
        for t in theory:
            print(f"  {t['group_type']}: {t['count']} lessons")
    
    print("=" * 60)

def drop_all_tables(conn):
    confirm = input("\n⚠️ Delete ALL tables? (yes/no): ")
    if confirm.lower() == 'yes':
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS schedule CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS user_settings CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS users CASCADE;")
        conn.commit()
        print("[OK] All tables deleted")
        return True
    return False

def main():
    print("=" * 60)
    print("DATABASE INITIALIZATION")
    print("=" * 60)
    
    if not create_database():
        sys.exit(1)
    
    conn = create_connection()
    
    while True:
        print("\n📋 MENU:")
        print("1. Full initialization (all tables + test data)")
        print("2. Create tables only")
        print("3. Add schedule data")
        print("4. Add test users (user + admin)")
        print("5. Show statistics")
        print("6. Delete all tables")
        print("0. Exit")
        
        choice = input("\nChoose (0-6): ").strip()
        
        if choice == '1':
            create_tables(conn)
            create_test_schedule(conn)
            create_test_user(conn)
            show_statistics(conn)
            print("\n✅ Full initialization complete!")
        elif choice == '2':
            create_tables(conn)
        elif choice == '3':
            create_test_schedule(conn)
            show_statistics(conn)
        elif choice == '4':
            create_test_user(conn)
            show_statistics(conn)
        elif choice == '5':
            show_statistics(conn)
        elif choice == '6':
            drop_all_tables(conn)
        elif choice == '0':
            print("Goodbye!")
            break
        else:
            print("Invalid choice")
    
    conn.close()

def quick_init():
    print("🚀 Quick initialization...")
    print("=" * 40)
    
    create_database()
    conn = create_connection()
    create_tables(conn)
    create_test_schedule(conn)
    create_test_user(conn)
    show_statistics(conn)
    conn.close()
    
    print("\n" + "=" * 40)
    print("✅ DATABASE IS READY!")
    print("=" * 40)
    print("📊 Tables:")
    print("   - users (with subgroup, instructor_id, car, car_type, role)")
    print("   - user_settings")
    print("   - schedule (with cars field)")
    print("\n👤 Test users:")
    print("   User: test@example.com / Test123 (role: user)")
    print("   Admin: admin@autoschool.ru / admin123 (role: admin)")
    print("\n👨‍🏫 Instructors available: 6")
    print("   Each with multiple cars")
    print("=" * 40)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        quick_init()
    else:
        main()
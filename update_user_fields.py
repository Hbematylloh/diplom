from app import app, db

with app.app_context():
    # Добавляем новые поля в таблицу users
    try:
        db.session.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS subgroup VARCHAR(10) DEFAULT \'A\'')
        print("[OK] Added column: subgroup")
    except Exception as e:
        print(f"[ERROR] subgroup: {e}")
    
    try:
        db.session.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS instructor_id INTEGER')
        print("[OK] Added column: instructor_id")
    except Exception as e:
        print(f"[ERROR] instructor_id: {e}")
    
    try:
        db.session.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS car_type VARCHAR(20) DEFAULT \'manual\'')
        print("[OK] Added column: car_type")
    except Exception as e:
        print(f"[ERROR] car_type: {e}")
    
    db.session.commit()
    print("\n✅ Все поля добавлены в таблицу users")
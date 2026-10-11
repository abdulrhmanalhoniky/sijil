import os
import sqlite3
import uuid
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import shutil
import datetime

ph = PasswordHasher()

def init_db():
    conn = sqlite3.connect('sijil.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user', -- 'admin' أو 'user'
                backup_code TEXT UNIQUE)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Cases(
                case_number TEXT PRIMARY KEY,
                client_name TEXT NOT NULL,
                client_id TEXT NOT NULL,
                defendant_name TEXT NOT NULL,
                defendant_id TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(created_by) REFERENCES Users(id))''')
    
    conn.commit()
    conn.close()

def register_user(username, password, role="user"):
    try:
        conn = sqlite3.connect('sijil.db')
        c = conn.cursor()
        
        password_hash = ph.hash(password)
        
        raw_backup_code = None
        backup_code_hash = None
        
        if role == "admin":
            raw_backup_code = f"SIJIL-{uuid.uuid4().hex[:8].upper()}"
            backup_code_hash = ph.hash(raw_backup_code)
        
        c.execute('''INSERT INTO Users (username, password_hash, role, backup_code)
                    VALUES (?, ?, ?, ?)''', (username, password_hash, role, backup_code_hash))
        
        conn.commit()
        conn.close()
        
    
        if role == "admin":
            return f"Backup:{raw_backup_code.split('-')[1]}" 
        else:
            return "تم إنشاء الحساب بنجاح!"
        
    except sqlite3.IntegrityError:
        return "خطأ: اسم المستخدم موجود مسبقاً!"
    except Exception as e:
        return f"حدث خطأ: {e}"

def reset_password_with_backup_code(username, backup_code, new_password):

    try:
        conn = sqlite3.connect('sijil.db')
        c = conn.cursor()
        
        c.execute("SELECT id, backup_code FROM Users WHERE username=?", (username,))
        user = c.fetchone()
        
        if not user or not user[1]:
            conn.close()
            return "خطأ: اسم المستخدم أو مفتاح الطوارئ غير صحيح!"
            
        user_id, stored_backup_hash = user
        try:
            ph.verify(stored_backup_hash, backup_code)
        except VerifyMismatchError:
            conn.close()
            return "خطأ: مفتاح الطوارئ غير صحيح!"
            
    
        new_password_hash = ph.hash(new_password)
        
  
        c.execute("UPDATE Users SET password_hash=? WHERE id=?", (new_password_hash, user_id))
        
        conn.commit()
        conn.close()
        return "تم إعادة تعيين كلمة المرور بنجاح! يمكنك الآن تسجيل الدخول بها."
        
    except Exception as e:
        return f"حدث خطأ أثناء استعادة الحساب: {e}"

def verify_password(username, provided_password):
    conn = sqlite3.connect('sijil.db')
    c = conn.cursor()
    c.execute("SELECT password_hash FROM Users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result:
        stored_hash = result[0]
        try:
            ph.verify(stored_hash, provided_password)
            return True
        except VerifyMismatchError:
            return False
    return False

def get_all_cases():
    conn = sqlite3.connect('sijil.db')
    c = conn.cursor()
    c.execute("""
        SELECT Cases.case_number, Cases.client_name, Cases.client_id, 
               Cases.defendant_name, Cases.defendant_id, Cases.status, 
               Cases.notes, Users.username, Cases.created_at 
        FROM Cases 
        JOIN Users ON Cases.created_by = Users.id
        WHERE Cases.status != 'مؤرشف'
    """)
    cases = c.fetchall()
    conn.close()
    return cases

def add_case(case_num, client_name, client_id, def_name, def_id, status, notes, user_id):

    now = datetime.datetime.now()
    

    date_part = now.strftime("%Y-%m-%d")
    hour_24 = now.hour
    

    if hour_24 == 0:
        hour_12 = 12
        period = "صباحاً"
    elif hour_24 < 12:
        hour_12 = hour_24
        period = "صباحاً"
    elif hour_24 == 12:
        hour_12 = 12
        period = "مساءً"
    else:
        hour_12 = hour_24 - 12
        period = "مساءً"
        
    minute_sec = now.strftime("%M:%S")
    
    created_at_formatted = f"{date_part} {hour_12:02d}:{minute_sec} {period}"
    
    try:
        conn = sqlite3.connect('sijil.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO Cases (case_number, client_name, client_id, defendant_name, defendant_id, status, notes, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (case_num, client_name, client_id, def_name, def_id, status, notes, user_id, created_at_formatted))
        conn.commit()
        conn.close()
        return "تمت إضافة القضية بنجاح"
    except Exception as e:
        return f"حدث خطأ: {e}"
    
def get_employees_stats():

    conn = sqlite3.connect('sijil.db')
    c = conn.cursor()
    
    query = """
    SELECT Users.id, Users.username, Users.role, COUNT(Cases.case_number) as case_count
    FROM Users
    LEFT JOIN Cases ON Users.id = Cases.created_by
    GROUP BY Users.id
    """
    
    c.execute(query)
    results = c.fetchall()
    conn.close()
    return results

def update_case_details(case_number, new_status, new_notes):
    """تحديث حالة القضية والملاحظات في قاعدة البيانات"""
    try:
        conn = sqlite3.connect('sijil.db')
        c = conn.cursor()
        c.execute("""
            UPDATE Cases 
            SET status = ?, notes = ? 
            WHERE case_number = ?
        """, (new_status, new_notes, case_number))
        conn.commit()
        conn.close()
        return "تم تحديث بيانات القضية بنجاح!"
    except Exception as e:
        return f"حدث خطأ أثناء التحديث: {e}"
    
def generate_next_case_number():

    conn = sqlite3.connect('sijil.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM Cases")
    count = c.fetchone()[0]
    conn.close()
    year = datetime.datetime.now().year
    return f"CAS-{year}-{count + 1:03d}"

def search_cases(keyword):

    conn = sqlite3.connect('sijil.db')
    c = conn.cursor()
    query = """
        SELECT Cases.case_number, Cases.client_name, Cases.client_id, 
               Cases.defendant_name, Cases.defendant_id, Cases.status, 
               Cases.notes, Users.username, Cases.created_at 
        FROM Cases 
        JOIN Users ON Cases.created_by = Users.id
        WHERE Cases.case_number LIKE ? OR Cases.client_name LIKE ? OR Cases.client_id LIKE ?
        ORDER BY Cases.created_at DESC
    """
    pattern = f"%{keyword}%"
    c.execute(query, (pattern, pattern, pattern))
    results = c.fetchall()
    conn.close()
    return results

def get_dashboard_stats():

    conn = sqlite3.connect('sijil.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM Cases")
    total_cases = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM Cases WHERE status='جارية'")
    active_cases = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM Users")
    total_users = c.fetchone()[0]
    
    conn.close()
    return {"total": total_cases, "active": active_cases, "users": total_users}

def admin_update_user_password(user_id, new_password):
    try:
        conn = sqlite3.connect('sijil.db')
        c = conn.cursor()
        new_hash = ph.hash(new_password)
        c.execute("UPDATE Users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
        conn.commit()
        conn.close()
        return "تم تغيير كلمة المرور للموظف بنجاح!"
    except Exception as e:
        return f"حدث خطأ أثناء تغيير كلمة المرور: {e}"



def archive_case(case_num):
    """أرشفة القضية المحددة عن طريق تغيير حالتها إلى 'مؤرشف'"""
    try:
        conn = sqlite3.connect('sijil.db')
        c = conn.cursor()
        c.execute("UPDATE Cases SET status = 'مؤرشف' WHERE case_number = ?", (case_num,))
        conn.commit()
        conn.close()
        return "تمت أرشفة القضية بنجاح"
    except Exception as e:
        return f"حدث خطأ أثناء الأرشفة: {e}"


def backup_database(custom_path=None):
   
    try:
        db_file = 'sijil.db'
        if not os.path.exists(db_file):
            return "ملف قاعدة البيانات غير موجود!"

        if custom_path and os.path.exists(custom_path):
            backup_dir = custom_path
        else:
            backup_dir = 'backups'
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

    
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"sijil_backup_{timestamp}.db"
        destination_path = os.path.join(backup_dir, backup_filename)

        shutil.copy2(db_file, destination_path)
        return f"تم أخذ النسخة الاحتياطية بنجاح:\n{destination_path}"
    except Exception as e:
        return f"حدث خطأ أثناء النسخ الاحتياطي: {e}"
def delete_user(user_id):
    """حذف مستخدم من النظام (خاص بالآدمن)"""
    try:
        conn = sqlite3.connect('sijil.db')
        c = conn.cursor()
        
 
        c.execute("SELECT username, role FROM Users WHERE id = ?", (user_id,))
        user = c.fetchone()
        
        if user and user[0] == "admin":
            return "لا يمكن حذف حساب الآدمن الرئيسي للنظام!"
            
        c.execute("DELETE FROM Users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return "تم حذف المستخدم بنجاح"
    except Exception as e:
        return f"حدث خطأ أثناء الحذف: {e}"
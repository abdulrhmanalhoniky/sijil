import customtkinter as ctk
import sqlite3
from backend import sijil_db as database

class AuthManager:
    def __init__(self, root_app):
        self.app = root_app

    # ==================== 1. شاشة الإعداد الأولى (Setup Wizard) ====================
    def show_setup_wizard(self):
        self.app.clear_window()
        center_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        center_frame.pack(expand=True)
        
        ctk.CTkLabel(center_frame, text="إعداد النظام لأول مرة", font=("Arial", 26, "bold")).pack(pady=15)
        ctk.CTkLabel(center_frame, text="أنشئ حساب مسؤول النظام (Admin) أو تخطَّ لحساب مستخدم عادي", font=("Arial", 14), text_color="gray").pack(pady=5)
        
        self.user_entry = ctk.CTkEntry(center_frame, placeholder_text="اسم المستخدم", width=350, height=45, font=("Arial", 14))
        self.user_entry.pack(pady=12)
        
        self.pass_entry = ctk.CTkEntry(center_frame, placeholder_text="كلمة المرور", show="*", width=350, height=45, font=("Arial", 14))
        self.pass_entry.pack(pady=12)
        
        # رسالة التنبيه المباشرة (Inline Status Label)
        self.setup_status_label = ctk.CTkLabel(center_frame, text="", font=("Arial", 13, "bold"))
        self.setup_status_label.pack(pady=5)
        

        ctk.CTkButton(
            center_frame, 
            text="🛡️ إنشاء حساب مسؤول النظام (Admin)", 
            command=lambda: self.handle_setup(role="admin"), 
            width=350, height=45, 
            fg_color="#2b8a3e", hover_color="#237032", 
            font=("Arial", 14, "bold")
        ).pack(pady=10)

   
        ctk.CTkButton(
            center_frame, 
            text="➡️ تخطي وإنشاء حساب مستخدم عادي (User)", 
            command=lambda: self.handle_setup(role="user"), 
            width=350, height=40, 
            fg_color="transparent", border_width=1, border_color="#3b82f6", text_color="#3b82f6", hover_color="#1e293b", 
            font=("Arial", 13, "bold")
        ).pack(pady=5)

    def handle_setup(self, role="admin"):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        
        if not username or not password:
            self.setup_status_label.configure(text="الرجاء إدخال اسم المستخدم وكلمة المرور!", text_color="#ef4444")
            return
            
        result = database.register_user(username, password, role=role)
        
        if role == "admin" and "SIJIL" in result:
        
            self.show_backup_code_screen(result)
        elif "بنجاح" in result or "SIJIL" in result:
            # عند إنشاء حساب مستخدم عادي (تخطي)، ينتقل مباشرة لشاشة تسجيل الدخول تلقائياً
            self.setup_status_label.configure(text="تم إنشاء الحساب بنجاح! جاري الانتقال لشاشة تسجيل الدخول...", text_color="#16a34a")
            self.app.after(1200, self.show_login_screen)
        else:
            self.setup_status_label.configure(text=result, text_color="#ef4444")

    # ==================== شاشة عرض مفتاح الطوارئ (للآدمن) ====================
    def show_backup_code_screen(self, raw_code):
        self.app.clear_window()
        center_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        center_frame.pack(expand=True)
        
        ctk.CTkLabel(center_frame, text="تم إنشاء حساب الآدمن بنجاح!", font=("Arial", 24, "bold"), text_color="#2b8a3e").pack(pady=10)
        ctk.CTkLabel(center_frame, text="⚠️ هذا هو مفتاح الطوارئ (Backup Code) الخاص بك.\nاحتفظ به في مكان آمن لاستعادة الحساب:", font=("Arial", 14), text_color="#d97706", justify="center").pack(pady=15)
        
        code_box = ctk.CTkTextbox(center_frame, width=450, height=80, font=("Courier", 16, "bold"))
        code_box.pack(pady=15)
        code_box.insert("0.0", f"Backup:{raw_code}")
        code_box.configure(state="disabled")
        
        ctk.CTkButton(center_frame, text="موافق، الانتقال لتسجيل الدخول", command=self.show_login_screen, width=450, height=45, font=("Arial", 14, "bold")).pack(pady=25)


    def show_login_screen(self):
        self.app.clear_window()
        center_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        center_frame.pack(expand=True)
        
        ctk.CTkLabel(center_frame, text="تسجيل الدخول - سِجِل", font=("Arial", 26, "bold")).pack(pady=20)
        
        self.login_user_entry = ctk.CTkEntry(center_frame, placeholder_text="اسم المستخدم", width=350, height=45, font=("Arial", 14))
        self.login_user_entry.pack(pady=12)
        
        self.login_pass_entry = ctk.CTkEntry(center_frame, placeholder_text="كلمة المرور", show="*", width=350, height=45, font=("Arial", 14))
        self.login_pass_entry.pack(pady=12)
        
        self.login_status_label = ctk.CTkLabel(center_frame, text="", font=("Arial", 13, "bold"))
        self.login_status_label.pack(pady=5)
        
        ctk.CTkButton(center_frame, text="نسيت كلمة المرور؟", command=self.show_reset_password_screen, fg_color="transparent", text_color="#3b82f6", hover_color="#1e293b", font=("Arial", 13, "underline")).pack(pady=5, anchor="e")
        ctk.CTkButton(center_frame, text="دخول", command=self.handle_login, width=350, height=45, font=("Arial", 14, "bold")).pack(pady=15)

    def handle_login(self):
        username = self.login_user_entry.get().strip()
        password = self.login_pass_entry.get().strip()
        
        if not username or not password:
            self.login_status_label.configure(text="الرجاء إدخال الحقول المطلوبة!", text_color="#ef4444")
            return
            
        if database.verify_password(username, password):
            conn = sqlite3.connect('sijil.db')
            c = conn.cursor()
            c.execute("SELECT id, username, role FROM Users WHERE username=?", (username,))
            user_data = c.fetchone()
            conn.close()
            
            self.app.current_user = {"id": user_data[0], "username": user_data[1], "role": user_data[2]}
            self.app.show_dashboard()
        else:
            self.login_status_label.configure(text="اسم المستخدم أو كلمة المرور غير صحيحة!", text_color="#ef4444")

    # ==================== 3. شاشة استعادة كلمة المرور ====================
    def show_reset_password_screen(self):
        self.app.clear_window()
        center_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        center_frame.pack(expand=True)
        
        ctk.CTkLabel(center_frame, text="استعادة كلمة المرور", font=("Arial", 24, "bold")).pack(pady=15)
        
        self.reset_user_entry = ctk.CTkEntry(center_frame, placeholder_text="اسم المستخدم", width=350, height=45, font=("Arial", 14))
        self.reset_user_entry.pack(pady=10)
        
        self.reset_code_entry = ctk.CTkEntry(center_frame, placeholder_text="مفتاح الطوارئ (Backup Code)", width=350, height=45, font=("Arial", 14))
        self.reset_code_entry.pack(pady=10)
        
        self.reset_new_pass_entry = ctk.CTkEntry(center_frame, placeholder_text="كلمة المرور الجديدة", show="*", width=350, height=45, font=("Arial", 14))
        self.reset_new_pass_entry.pack(pady=10)
        
        self.reset_status_label = ctk.CTkLabel(center_frame, text="", font=("Arial", 13, "bold"))
        self.reset_status_label.pack(pady=5)
        
        ctk.CTkButton(center_frame, text="تغيير كلمة المرور", command=self.handle_reset_password, width=350, height=45, fg_color="#d97706", hover_color="#b45309", font=("Arial", 14, "bold")).pack(pady=15)
        ctk.CTkButton(center_frame, text="الرجوع", command=self.show_login_screen, fg_color="transparent", text_color="gray", font=("Arial", 13)).pack(pady=5)

    def handle_reset_password(self):
        u = self.reset_user_entry.get().strip()
        code = self.reset_code_entry.get().strip()
        new_p = self.reset_new_pass_entry.get().strip()
        
        if not u or not code or not new_p:
            self.reset_status_label.configure(text="يرجى تعبئة جميع الحقول المطلوبة!", text_color="#ef4444")
            return
            
        res = database.reset_password_with_backup_code(u, code, new_p)
        if "بنجاح" in res:
            self.reset_status_label.configure(text=res, text_color="#16a34a")
            self.app.after(1500, self.show_login_screen)
        else:
            self.reset_status_label.configure(text=res, text_color="#ef4444")
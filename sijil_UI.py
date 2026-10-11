import customtkinter as ctk
from tkinter import filedialog, messagebox
import sqlite3
from backend import sijil_db as database
from views import sijil_auth_view
from views import admin_views
from views import reports

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class SijilApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("سِجِل - نظام إدارة القضايا القانونية")
        
        
        self.current_user = None
        self.auth = sijil_auth_view.AuthManager(self)
        
        database.init_db()
        
        if self.is_database_empty():
            self.auth.show_setup_wizard()
        else:
            self.auth.show_login_screen()

    def is_database_empty(self):
        conn = sqlite3.connect('sijil.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM Users")
        count = c.fetchone()[0]
        conn.close()
        return count == 0

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    # ==================== لوحة التحكم الرئيسية (Dashboard) ====================
    def show_dashboard(self):
        self.clear_window()
        
        # --- الشريط العلوي (الهيدر) ---
        header_frame = ctk.CTkFrame(self, fg_color="#1e293b", height=70, corner_radius=0)
        header_frame.pack(fill="x", side="top")
        
        ctk.CTkLabel(header_frame, text="⚖️ نظام إدارة القضايا - سِجِل", font=("Arial", 20, "bold"), text_color="white").pack(side="right", padx=20)
        
        user_info_text = f"المستخدم: {self.current_user['username']} ({'آدمن' if self.current_user['role']=='admin' else 'موظف'})"
        ctk.CTkLabel(header_frame, text=user_info_text, font=("Arial", 14), text_color="#94a3b8").pack(side="left", padx=20)
        
        ctk.CTkButton(header_frame, text="تسجيل خروج", command=self.auth.show_login_screen, fg_color="#ef4444", hover_color="#dc2626", width=100, height=32).pack(side="left", padx=10)

        # زر لوحة الآدمن (يظهر فقط للآدمن)
        if self.current_user["role"] == "admin":
            from views import admin_views
            ctk.CTkButton(header_frame, text="🛡️ لوحة إدارة الموظفين", command=lambda: admin_views.open_employee_monitor_modal(self), fg_color="#2563eb", hover_color="#1d4ed8", height=32).pack(side="left", padx=10)
        ctk.CTkButton(
            header_frame, 
             text="💾 النسخ الاحتياطي",  
             fg_color="#0284c7", 
             command=lambda: self.open_backup_settings_modal(),
             hover_color="#0369a1", 
             font=("Arial", 13, "bold"),
             height=35
             ).pack(side="left", padx=5)
        # --- المحتوى الرئيسي ---
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. لوحة الإحصائيات (Dashboard Summary Cards)
        stats = database.get_dashboard_stats()
        stats_frame = ctk.CTkFrame(main_content, fg_color="transparent")
        stats_frame.pack(fill="x", pady=10)

        def create_stat_card(parent, title, value, color):
            card = ctk.CTkFrame(parent, fg_color=color, width=220, height=80, corner_radius=10)
            card.pack_propagate(False)
            card.pack(side="right", padx=10, expand=True)
            ctk.CTkLabel(card, text=title, font=("Arial", 13), text_color="white").pack(pady=(10, 0))
            ctk.CTkLabel(card, text=str(value), font=("Arial", 20, "bold"), text_color="white").pack(pady=(0, 10))

        create_stat_card(stats_frame, "إجمالي القضايا", stats["total"], "#334155")
        create_stat_card(stats_frame, "القضايا الجارية", stats["active"], "#0284c7")
        create_stat_card(stats_frame, "إجمالي المستخدمين", stats["users"], "#059669")

      
        controls_frame = ctk.CTkFrame(main_content, fg_color="transparent")
        controls_frame.pack(fill="x", pady=10)

        
        ctk.CTkButton(
            controls_frame, 
            text="➕ إضافة قضية جديدة", 
            command=self.open_add_case_modal, 
            fg_color="#16a34a", 
            hover_color="#15803d", 
            font=("Arial", 14, "bold"), 
            height=40
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            controls_frame, 
            text="📁 أرشيف القضايا", 
            command=self.open_archive_modal,
            fg_color="#d97706", 
            hover_color="#b45309", 
            font=("Arial", 14, "bold"), 
            height=40
        ).pack(side="right", padx=5)
        
        
        search_entry = ctk.CTkEntry(controls_frame, placeholder_text="بحث برقم القضية، اسم الموكل، أو رقم الهوية...", 
                                    width=350, height=40, font=("Arial", 13))
        search_entry.pack(side="left", padx=5)

        def perform_search(event=None):
            keyword = search_entry.get().strip()
            cases = database.search_cases(keyword) if keyword else database.get_all_cases()
            self.update_cases_table_view(cases)

        ctk.CTkButton(controls_frame, text="بحث", command=perform_search, fg_color="#3b82f6", width=80, height=40).pack(side="left")

        # 3. جدول عرض القضايا
        self.cases_scroll_frame = ctk.CTkScrollableFrame(main_content, width=1100, height=420)
        self.cases_scroll_frame.pack(fill="both", expand=True, pady=10)
        
        self.load_cases_list()

    def load_cases_list(self):
        cases = database.get_all_cases()
        self.update_cases_table_view(cases)

    def update_cases_table_view(self, cases):
        for widget in self.cases_scroll_frame.winfo_children():
            widget.destroy()

        if not cases:
            ctk.CTkLabel(self.cases_scroll_frame, text="لا توجد قضايا مسجلة مطابقة للبحث", font=("Arial", 15), text_color="gray").pack(pady=20)
            return

        for case in cases:
            case_num, client_name, client_id, def_name, def_id, status, notes, creator, created_at = case
            
            card = ctk.CTkFrame(self.cases_scroll_frame, fg_color="#1e293b", corner_radius=8)
            card.pack(fill="x", pady=6, padx=5)
            
            info_text = f"رقم القضية: {case_num}   |   الموكل: {client_name} (هوية: {client_id})   |   الخصم: {def_name}   |   الحالة: {status}   |   بواسطة: {creator}"
            ctk.CTkLabel(card, text=info_text, font=("Arial", 13, "bold"), text_color="white").pack(side="right", padx=15, pady=12)
            
          
            ctk.CTkButton(
                card, 
                text="التفاصيل و تصدير التقارير " , 
                command=lambda c=case: self.open_case_details(c), 
                fg_color="#3b82f6", 
                width=120, 
                height=32
                ).pack(side="left", padx=15, pady=10)
    def refresh_dashboard(self):
       
        self.show_dashboard()
    def open_case_details(self, case_number):

        if isinstance(case_number, (list, tuple)):
            case_num_str = case_number[0]
        else:
            case_num_str = case_number

  
        conn = sqlite3.connect('sijil.db')
        c = conn.cursor()
        c.execute("""
            SELECT Cases.case_number, Cases.client_name, Cases.client_id, 
                   Cases.defendant_name, Cases.defendant_id, Cases.status, 
                   Cases.notes, Users.username, Cases.created_at 
            FROM Cases 
            JOIN Users ON Cases.created_by = Users.id
            WHERE Cases.case_number = ?
        """, (case_num_str,))
        case = c.fetchone()
        conn.close()
        
        if not case:
            messagebox.showerror("لم يتم العثور على بيانات القضية!")
            return
            
        case_num, client, client_id, defendant, defendant_id, status, notes, creator, created_at = case
            
        case_num, client, client_id, defendant, defendant_id, status, notes, creator, created_at = case

        # 2. إنشاء النافذة المنبثقة
        modal = ctk.CTkToplevel(self)
        modal.title(f"{case_num} :تفاصيل القضية")
        modal.geometry("500x690")
        modal.grab_set()
        
        ctk.CTkLabel(modal, text=f"تفاصيل القضية رقم :{case_num}", font=("Arial", 18, "bold"), text_color="#38bdf8").pack(pady=12)
        

        info_frame = ctk.CTkFrame(modal, fg_color="#1e293b", corner_radius=8)
        info_frame.pack(fill="x", padx=20, pady=5)
        
        c_id_str = str(client_id).strip()
        d_id_str = str(defendant_id).strip()
        
        masked_client_id = f"******{c_id_str[-4:]}" if len(c_id_str) >= 4 else c_id_str
        masked_defendant_id = f"******{d_id_str[-4:]}" if len(d_id_str) >= 4 else d_id_str

        details_text = (
            f"اسم الموكل: {client}\n"
            f"رقم هوية الموكل: {masked_client_id}\n"
            f"اسم المدعى عليه: {defendant}\n"
            f"رقم هوية المدعى عليه: {masked_defendant_id}\n"
            f"تم الإنشاء بواسطة: {creator}\n"
            f"تاريخ الإنشاء: {created_at}"
        )
        ctk.CTkLabel(info_frame, text=details_text, font=("Arial", 13), justify="right", text_color="white").pack(padx=15, pady=12, anchor="e")
        
        # 4. تحديث حالة القضية
        ctk.CTkLabel(modal, text=":تحديث الحالة", font=("Arial", 13, "bold")).pack(anchor="e", padx=25, pady=(8, 0))
        status_combo = ctk.CTkComboBox(modal, values=["جارية", "منتهية", "معلقة"], width=440, height=35)
        status_combo.pack(pady=4)
        status_combo.set(status)
        
      
        ctk.CTkLabel(modal, text=":الملاحظات والتفاصيل", font=("Arial", 13, "bold")).pack(anchor="e", padx=25, pady=(8, 0))
        notes_entry = ctk.CTkTextbox(modal, width=440, height=95, font=("Arial", 12))
        notes_entry.pack(pady=4)
        
        placeholder_text = "تفاصيل وملاحظات القضية..."
        if notes and notes.strip():
            notes_entry.insert("0.0", notes)
        else:
            notes_entry.insert("0.0", placeholder_text)
            notes_entry.configure(text_color="gray")
            

        def on_focus_in(event):
            if notes_entry.get("0.0", "end").strip() == placeholder_text:
                notes_entry.delete("0.0", "end")
                notes_entry.configure(text_color="white")

        notes_entry.bind("<FocusIn>", on_focus_in)
        
        status_msg = ctk.CTkLabel(modal, text="", font=("Arial", 11, "bold"))
        status_msg.pack(pady=2)

        
        def save_changes():
            current_notes = notes_entry.get("0.0", "end").strip()
            if current_notes == placeholder_text:
                current_notes = ""
            res = database.update_case_details(case_num, status_combo.get(), current_notes)
            if "بنجاح" in res:
                status_msg.configure(text=res, text_color="#16a34a")
                self.load_cases_list()
            else:
                status_msg.configure(text=res, text_color="#ef4444")

        # 6. زر حفظ التعديلات
        ctk.CTkButton(modal, text="حفظ التعديلات", command=save_changes, fg_color="#2563eb", width=440, height=38, font=("Arial", 13, "bold")).pack(pady=6)

        # 7. أزرار التصدير (PDF / Excel)
        export_frame = ctk.CTkFrame(modal, fg_color="transparent")
        export_frame.pack(fill="x", padx=20, pady=4)

        ctk.CTkButton(export_frame, text="📊 تصدير إلى Excel", command=lambda: messagebox.showinfo("تصدير Excel", reports.export_case_to_excel(case_num)), fg_color="#16a34a", width=210, height=35).pack(side="right", padx=5)
        ctk.CTkButton(export_frame, text="📄 تصدير إلى PDF", command=lambda: messagebox.showinfo("تصدير PDF", reports.export_case_to_pdf(case_num)), fg_color="#dc2626", width=210, height=35).pack(side="left", padx=5)

        # 8. زر حذف القضية (للآدمن فقط)
        if self.current_user.get("role") == "admin":
            def confirm_archive():
                if messagebox.askyesno(f"هل أنت متأكد من أرشفة القضية رقم ({case_num})?"):
                    res = database.archive_case(case_num)
                    messagebox.showinfo("النتيجة", res)
                    if modal.winfo_exists():
                        modal.destroy()
                    self.refresh_dashboard()

            ctk.CTkButton(
                modal, 
                text="📁 أرشفة القضية", 
                command=confirm_archive, 
                fg_color="#d97706", 
                hover_color="#b45309", 
                width=440, 
                height=38, 
                font=("Arial", 13, "bold")
            ).pack(pady=6)
    def open_add_case_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("إضافة قضية جديدة - سِجِل")
        modal.geometry("450x650")
        modal.grab_set()
        
        ctk.CTkLabel(modal, text="تسجيل قضية جديدة", font=("Arial", 20, "bold")).pack(pady=15)
        
     
        c_num = ctk.CTkEntry(modal, width=380, height=40, font=("Arial", 14))
        c_num.pack(pady=8)
        auto_num = database.generate_next_case_number()
        c_num.insert(0, auto_num) 
        
        c_name = ctk.CTkEntry(modal, placeholder_text="اسم الموكل", width=380, height=40, font=("Arial", 14))
        c_name.pack(pady=8)
        c_id = ctk.CTkEntry(modal, placeholder_text="رقم هوية الموكل", width=380, height=40, font=("Arial", 14))
        c_id.pack(pady=8)
        d_name = ctk.CTkEntry(modal, placeholder_text="اسم المدعى عليه (الخصم)", width=380, height=40, font=("Arial", 14))
        d_name.pack(pady=8)
        d_id = ctk.CTkEntry(modal, placeholder_text="رقم هوية المدعى عليه", width=380, height=40, font=("Arial", 14))
        d_id.pack(pady=8)
        
        status_combo = ctk.CTkComboBox(modal, values=["جارية", "منتهية", "معلقة"], width=380, height=40)
        status_combo.pack(pady=8)
        status_combo.set("جارية")
        
        notes_entry = ctk.CTkTextbox(modal, width=380, height=100)
        notes_entry.pack(pady=8)
        
        notes_entry.tag_config("right", justify="right")
        
        placeholder_text = "تفاصيل وملاحظات القضية..."
        notes_entry.insert("0.0", placeholder_text, "right")
        notes_entry.configure(text_color="gray")

       
        def on_focus_in(event):
            if notes_entry.get("0.0", "end-1c").strip() == placeholder_text:
                notes_entry.delete("0.0", "end")
                notes_entry.configure(text_color=("black", "white"))

        def on_focus_out(event):
            if not notes_entry.get("0.0", "end-1c").strip():
                notes_entry.insert("0.0", placeholder_text, "right")
                notes_entry.configure(text_color="gray")

        notes_entry.bind("<FocusIn>", on_focus_in)
        notes_entry.bind("<FocusOut>", on_focus_out)

        def save_case():
            case_num = c_num.get().strip()
            client_name = c_name.get().strip()
            client_id = c_id.get().strip()
            def_name = d_name.get().strip()
            def_id = d_id.get().strip()
            status = status_combo.get()
            
         
            notes = notes_entry.get("0.0", "end-1c").strip()
            
            if not client_name or not client_id or not def_name or not def_id:
                messagebox.showerror("خطأ", "الرجاء تعبئة جميع الحقول الإجبارية للأطراف والهويات!")
                return
                
    
            if notes == placeholder_text or not notes:
                notes = ""

            user_id = self.current_user.get("id")

            res = database.add_case(case_num, client_name, client_id, def_name, def_id, status, notes, user_id)
            
            if "بنجاح" in res:
                messagebox.showinfo("نجاح", res)
                if modal.winfo_exists():
                    modal.destroy()
                self.refresh_dashboard() 
            else:
                messagebox.showerror("خطأ", res)

        
        ctk.CTkButton(
            modal, 
            text="حفظ القضية", 
            command=save_case, 
            fg_color="#16a34a", 
            hover_color="#15803d", 
            width=380, 
            height=40, 
            font=("Arial", 14, "bold")
        ).pack(pady=15)
    def handle_export(self, file_type):
        if not self.selected_case_num:
            messagebox.showwarning("الرجاء تحديد قضية أولاً من القائمة لطباعتها!")
            return
            
        if file_type == "excel":
            res = reports.export_case_to_excel(self.selected_case_num)
        elif file_type == "pdf":
            res = reports.export_case_to_pdf(self.selected_case_num)
            
        messagebox.showinfo("تصدير التقرير", res)

    def open_archive_modal(self):
        archive_modal = ctk.CTkToplevel(self)
        archive_modal.title("أرشيف القضايا - سِجِل")
        archive_modal.geometry("700x500")
        archive_modal.grab_set()
        
        ctk.CTkLabel(archive_modal, text="📁 سجل القضايا المؤرشفة", font=("Arial", 18, "bold"), text_color="#d97706").pack(pady=15)
        
        scroll_frame = ctk.CTkScrollableFrame(archive_modal, width=650, height=380)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
   
        import sqlite3
        conn = sqlite3.connect('sijil.db')
        c = conn.cursor()
        c.execute("""
            SELECT case_number, client_name, defendant_name, status, created_at 
            FROM Cases 
            WHERE status = 'مؤرشف'
        """)
        archived_cases = c.fetchall()
        conn.close()
        
        if not archived_cases:
            ctk.CTkLabel(scroll_frame, text="لا توجد قضايا مؤرشفة حالياً", font=("Arial", 14), text_color="gray").pack(pady=30)
            return
            
        for case in archived_cases:
            c_num, client, defendant, status, date = case
            card = ctk.CTkFrame(scroll_frame, fg_color="#1e293b", corner_radius=6)
            card.pack(fill="x", pady=5, padx=5)
            
            info = f"رقم القضية: {c_num}  |  الموكل: {client}  |  الخصم: {defendant}  |  التاريخ: {date}"
            ctk.CTkLabel(card, text=info, font=("Arial", 12, "bold"), text_color="white").pack(side="right", padx=15, pady=10)

    def open_backup_settings_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("إعدادات النسخ الاحتياطي - سِجِل")
        modal.geometry("480x380")
        modal.grab_set()

        ctk.CTkLabel(modal, text="💾 إدارة النسخ الاحتياطي والنسخ التلقائي", font=("Arial", 18, "bold")).pack(pady=15)

        path_var = ctk.StringVar(value="لم يتم اختيار مجلد النسخ الاحتياطي بعد")

        def select_folder():
            folder =filedialog.askdirectory(title="اختر مجلد النسخ الاحتياطي")
            if folder:
                path_var.set(folder)

        ctk.CTkButton(modal, text="📁 اختيار مجلد الحفظ", command=select_folder, fg_color="#3b82f6", height=38).pack(pady=5)
        ctk.CTkLabel(modal, textvariable=path_var, font=("Arial", 11), text_color="#94a3b8", wraplength=420).pack(pady=5)

        def run_immediate_backup():
            chosen_path = path_var.get()
            if chosen_path.startswith("لم يتم"):
                chosen_path = None
            res = database.backup_database(chosen_path)
            messagebox.showinfo("النسخ الاحتياطي", res)

        ctk.CTkButton(modal, text="⚡ أخذ نسخة احتياطية فورية الآن", command=run_immediate_backup, fg_color="#16a34a", hover_color="#15803d", height=42, font=("Arial", 14, "bold")).pack(pady=15)

        ctk.CTkLabel(modal, text="توقيت النسخ التلقائي اليومي:", font=("Arial", 13, "bold")).pack(pady=(10, 2))
        time_combo = ctk.CTkComboBox(modal, values=["الساعة 12:00 منتصف الليل", "الساعة 06:00 مساءً", "الساعة 08:00 صباحاً"], width=300, height=36)
        time_combo.pack(pady=5)

        def save_schedule():
            messagebox.showinfo( f"تم ضبط جدولة النسخ الاحتياطي على: {time_combo.get()}")
            modal.destroy()

        ctk.CTkButton(modal, text="حفظ إعدادات التوقيت", command=save_schedule, fg_color="#2563eb", width=300, height=38).pack(pady=15)

if __name__ == "__main__":
    app = SijilApp()
    app.mainloop()
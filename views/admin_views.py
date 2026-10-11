import customtkinter as ctk
from backend import sijil_db as database
from tkinter import messagebox

def open_employee_monitor_modal(parent_window):
    modal = ctk.CTkToplevel(parent_window)
    modal.title("مراقبة وإدارة الموظفين - للآدمن")
    modal.geometry("560x620")
    modal.grab_set()
    
    ctk.CTkLabel(modal, text="قائمة الموظفين وإدارة الصلاحيات", font=("Arial", 20, "bold")).pack(pady=15)
    
    scroll = ctk.CTkScrollableFrame(modal, width=510, height=240)
    scroll.pack(pady=5)
    
    def load_employees_list():
        for widget in scroll.winfo_children():
            widget.destroy()
            
        try:
            stats = database.get_employees_stats()
            if not stats:
                ctk.CTkLabel(scroll, text="لا يوجد موظفون مسجلون حالياً", font=("Arial", 13), text_color="gray").pack(pady=10)
            else:
                for emp in stats:
                    emp_id, username, role, count = emp
                    emp_card = ctk.CTkFrame(scroll, fg_color="#334155", height=60)
                    emp_card.pack(fill="x", pady=5, padx=5)
                    
                    role_txt = "آدمن" if role == "admin" else "موظف"
                    info = f"{username} ({role_txt}) | القضايا: {count}"
                    ctk.CTkLabel(emp_card, text=info, font=("Arial", 12, "bold"), text_color="white").pack(side="right", padx=10, pady=15)
                    
                    # زر تغيير كلمة المرور للموظف بواسطة الآدمن
                    def open_change_pass_modal(u_id, u_name):
                        pw_modal = ctk.CTkToplevel(modal)
                        pw_modal.title(f"تغيير كلمة المرور: {u_name}")
                        pw_modal.geometry("350x250")
                        pw_modal.grab_set()
                        
                        ctk.CTkLabel(pw_modal, text=f"تغيير كلمة مرور {u_name}", font=("Arial", 15, "bold")).pack(pady=15)
                        new_pass_entry = ctk.CTkEntry(pw_modal, placeholder_text="كلمة المرور الجديدة", show="*", width=280, height=40)
                        new_pass_entry.pack(pady=10)
                        
                        status_lbl = ctk.CTkLabel(pw_modal, text="", font=("Arial", 12))
                        status_lbl.pack(pady=5)
                        
                        def save_new_password():
                            np = new_pass_entry.get().strip()
                            if not np:
                                status_lbl.configure(text="الرجاء إدخال كلمة المرور!", text_color="#ef4444")
                                return
                            res = database.admin_update_user_password(u_id, np)
                            if "بنجاح" in res:
                                messagebox.showinfo("نجاح", res)
                                pw_modal.destroy()
                            else:
                                status_lbl.configure(text=res, text_color="#ef4444")
                                
                        ctk.CTkButton(pw_modal, text="حفظ التغيير", command=save_new_password, fg_color="#16a34a", width=280, height=40).pack(pady=10)

                    # --- زر حذف المستخدم (للآدمن فقط، ويستثني حساب admin الأساسي) ---
                    if username != "admin":
                        def delete_employee_action(uid=emp_id, uname=username):
                            if messagebox.askyesno(f"هل أنت متأكد من حذف المستخدم ({uname})؟"):
                                res = database.delete_user(uid)
                                messagebox.showinfo("النتيجة", res)
                                load_employees_list() 

                        ctk.CTkButton(
                            emp_card, 
                            text="حذف", 
                            command=delete_employee_action, 
                            fg_color="#dc2626", 
                            hover_color="#b91c1c", 
                            width=60, 
                            height=30, 
                            font=("Arial", 11, "bold")
                        ).pack(side="left", padx=5, pady=15)

                    ctk.CTkButton(
                        emp_card, 
                        text="تغيير كلمة المرور", 
                        command=lambda uid=emp_id, un=username: open_change_pass_modal(uid, un), 
                        fg_color="#d97706", 
                        hover_color="#b45309", 
                        width=110, 
                        height=30, 
                        font=("Arial", 11)
                    ).pack(side="left", padx=5, pady=15)
        except Exception as e:
            ctk.CTkLabel(scroll, text=f"خطأ: {e}", font=("Arial", 12), text_color="#ef4444").pack(pady=10)

            

    load_employees_list()

   
    ctk.CTkLabel(modal, text="إضافة موظف/محامي جديد للنظام", font=("Arial", 16, "bold")).pack(pady=(15, 5))
    emp_user = ctk.CTkEntry(modal, placeholder_text="اسم المستخدم للموظف", width=360, height=40, font=("Arial", 13))
    emp_user.pack(pady=6)
    
    emp_pass = ctk.CTkEntry(modal, placeholder_text="كلمة المرور الأولية", show="*", width=360, height=40, font=("Arial", 13))
    emp_pass.pack(pady=6)
    
    status_label = ctk.CTkLabel(modal, text="", font=("Arial", 13, "bold"))
    status_label.pack(pady=4)
    
    def add_employee():
        u = emp_user.get().strip()
        p = emp_pass.get().strip()
        if not u or not p:
            status_label.configure(text="الرجاء إدخال اسم المستخدم وكلمة المرور!", text_color="#ef4444")
            return
            
        r = database.register_user(u, p, role="user")
        response_msg = str(r) if r else ""
        
        if "بنجاح" in response_msg:
            status_label.configure(text=response_msg, text_color="#16a34a")
            emp_user.delete(0, 'end')
            emp_pass.delete(0, 'end')
            load_employees_list()
        else:
            status_label.configure(text=response_msg, text_color="#ef4444")

    ctk.CTkButton(modal, text="إنشاء حساب موظف", command=add_employee, fg_color="#2563eb", hover_color="#1d4ed8", font=("Arial", 14, "bold"), width=360, height=42).pack(pady=10)
    
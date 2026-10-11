import sqlite3
import os
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

import sqlite3
import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

def export_case_to_excel(case_number):

    try:
        conn = sqlite3.connect('sijil.db')
        c = conn.cursor()
        c.execute("""
            SELECT Cases.case_number, Cases.client_name, Cases.client_id, 
                   Cases.defendant_name, Cases.defendant_id, Cases.status, 
                   Cases.notes, Users.username, Cases.created_at 
            FROM Cases 
            JOIN Users ON Cases.created_by = Users.id
            WHERE Cases.case_number = ?
        """, (case_number,))
        case = c.fetchone()
        conn.close()
        
        if not case:
            return "خطأ: لم يتم العثور على بيانات القضية!"
            
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"قضية_{case_number}"
        ws.views.sheetView[0].rightToLeft = True 

      
        headers = ["رقم القضية", "اسم الموكل", "هوية الموكل", "المدعى عليه", "هوية المدعى عليه", "حالة القضية", "منشئ الملف", "تاريخ الإنشاء"]
        data_row = [case[0], case[1], case[2], case[3], case[4], case[5], case[7], case[8]]

   
        ws.append(headers)
        ws.append(data_row)

   
        ws.append([])
        ws.append(["الملاحظات والوصف التفصيلي:"])
        ws.append([case[6] if case[6] else "لا توجد ملاحظات"])

    
  
        tab = Table(displayName="CaseDetailsTable", ref="A1:H2")
        
  
        style = TableStyleInfo(
            name="TableStyleMedium9", 
            showFirstColumn=False,
            showLastColumn=False, 
            showRowStripes=True, 
            showColumnStripes=True
        )
        tab.tableStyleInfo = style
        ws.add_table(tab)

    
        align_right = Alignment(horizontal="center", vertical="center")
        
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                cell.alignment = align_right
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
           
            ws.column_dimensions[col_letter].width = max(max_len + 5, 18)

        filename = f"Case_{case_number}_Report.xlsx"
        wb.save(filename)
        return f"تم تصدير جدول Excel بنجاح ورسمياً باسم:\n{filename}"
        
    except Exception as e:
        return f"حدث خطأ أثناء تصدير Excel: {e}"

def export_case_to_pdf(case_number):
    try:
        conn = sqlite3.connect('sijil.db')
        c = conn.cursor()
        c.execute("""
            SELECT Cases.case_number, Cases.client_name, Cases.client_id, 
                   Cases.defendant_name, Cases.defendant_id, Cases.status, 
                   Cases.notes, Users.username, Cases.created_at 
            FROM Cases 
            JOIN Users ON Cases.created_by = Users.id
            WHERE Cases.case_number = ?
        """, (case_number,))
        case = c.fetchone()
        conn.close()
        
        if not case:
            return "خطأ: لم يتم العثور على بيانات القضية!"

        filename = f"Case_{case_number}_Report.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []

        font_path = "C:\\Windows\\Fonts\\arial.ttf"
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
            font_name = 'ArabicFont'
        else:
            font_name = 'Helvetica'  

        styles = getSampleStyleSheet()
        
        arabic_style = ParagraphStyle(
            'ArabicStyle',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=14,
            leading=20,
            alignment=2  # محاذاة لليمين
        )

        title_style = ParagraphStyle(
            'ArabicTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            leading=24,
            alignment=2
        )

        # التعديل هنا لضبط ترتيب الكلمات والحروف بدقة للـ PDF
        def fix_arabic(text):
            if not text:
                return ""
            reshaped_text = arabic_reshaper.reshape(str(text))
            bidi_text = get_display(reshaped_text)
            # عكس ترتيب الكلمات إذا ظهرت معكوسة في تقرير الـ PDF
            words = bidi_text.split(' ')
            return ' '.join(words[::-1])

        story.append(Paragraph(fix_arabic(f"تقرير إدارة القضايا - قضية رقم: {case[0]}"), title_style))
        story.append(Spacer(1, 15))

        content_lines = [
            f"اسم الموكل: {case[1]}",
            f"رقم هوية الموكل: {case[2]}",
            f"اسم المدعى عليه: {case[3]}",
            f"رقم هوية المدعى عليه: {case[4]}",
            f"حالة القضية: {case[5]}",
            f"تم الإنشاء بواسطة: {case[7]}",
            f"تاريخ الإنشاء: {case[8]}",
            "----------------------------------------",
            "الملاحظات والتفاصيل:",
            f"{case[6] if case[6] else 'لا توجد ملاحظات.'}"
        ]

        for line in content_lines:
            story.append(Paragraph(fix_arabic(line), arabic_style))
            story.append(Spacer(1, 5))

        doc.build(story)
        return f"تم تصدير ملف PDF بنجاح باسم:\n{filename}"
    except Exception as e:
        return f"حدث خطأ أثناء تصدير PDF: {e}"

def fix_arabic(text):
            if not text:
                return ""
            reshaped_text = arabic_reshaper.reshape(str(text))
            bidi_text = get_display(reshaped_text)
            # إحاطة النص بوسم الاتجاه العربي المباشر لفرض النظام من اليمين لليسار
            return f'<xml lang="ar"><rtl>{bidi_text}</rtl></xml>'
import customtkinter as ctk
import webbrowser
import sys
import requests
from datetime import datetime
from tkinter import messagebox

PASTEBIN_URL = "https://pastebin.com/raw/9QZpqyUH"
VALIDITY_DAYS = 7
WARNING_DAYS = 3  # عدد الأيام قبل انتهاء الصلاحية لاظهار التحذير

def get_online_date() -> datetime.date:
    """
    الحصول على تاريخ اليوم من الإنترنت باستخدام HTTP Header من Google
    """
    try:
        response = requests.head("https://www.google.com", timeout=5)
        date_str = response.headers.get("Date")
        if not date_str:
            raise ValueError("Date header not found")
        # صيغة التاريخ: "Tue, 16 Dec 2025 08:00:00 GMT"
        online_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z").date()
        return online_date
    except Exception as e:
        print("Failed to get online date:", e)
        return None
def show_update_popup(days_left: int, website_url: str):
    # إنشاء root مؤقت
    root = ctk.CTk()
    root.withdraw()
    
    popup = ctk.CTkToplevel(root)
    popup.title("Update Available")
    popup.geometry("400x150")
    
    if days_left <= 0:
        msg = "This version has expired. Please update the application."
    else:
        msg = f"Your version will expire in {days_left} day(s). Please update soon."
    
    label = ctk.CTkLabel(popup, text=msg, wraplength=350)
    label.pack(pady=20)
    
    def close_all():
        popup.destroy()
        root.destroy()
        if days_left <= 0:
            sys.exit(0)
    
    # زر فتح الموقع
    def open_site():
        if website_url:
            webbrowser.open(website_url)
        close_all()
    
    btn = ctk.CTkButton(popup, text="Open Download Page", command=open_site)
    btn.pack(pady=10)
    
    # التعامل مع زر الإغلاق (X)
    popup.protocol("WM_DELETE_WINDOW", close_all)
    
    popup.grab_set()
    popup.wait_window()


def check_usage_limit():
    """
    التحقق من صلاحية النسخة بالمقارنة مع Pastebin وتاريخ الإنترنت
    """
    online_date = get_online_date()
    if not online_date:
        # في حالة فشل الحصول على التاريخ من الإنترنت، يمنع التشغيل
        messagebox.showerror("Error", "Cannot verify date from internet. Exiting.")
        sys.exit(0)
    
    try:
        response = requests.get(PASTEBIN_URL, timeout=5)
        response.raise_for_status()
        lines = response.text.strip().splitlines()
        if len(lines) < 1:
            raise ValueError("Invalid Pastebin format")
        
        start_date_str = lines[0].strip()
        website_url = lines[1].strip() if len(lines) > 1 else None

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        days_left = VALIDITY_DAYS - (online_date - start_date).days

        if days_left <= 0:
            # انتهاء الصلاحية
            show_update_popup(days_left, website_url)
        elif days_left <= WARNING_DAYS:
            # تحذير قبل انتهاء الصلاحية
            show_update_popup(days_left, website_url)
        else:
            print(f"{days_left} day(s) remaining before expiration.")
    
    except Exception as e:
        print("Failed to check usage limit:", e)
        sys.exit(0)

# مثال على الاستخدام عند بداية التطبيق:
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")  # أو "light"
    ctk.set_default_color_theme("blue")
    
    check_usage_limit()
    # هنا يمكنك بدء تطبيقك الرئيسي بعد التحقق

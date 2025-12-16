import customtkinter as ctk
import webbrowser
import sys
import requests
from datetime import datetime
from tkinter import messagebox
import arabic_reshaper
from bidi.algorithm import get_display

PASTEBIN_URL = "https://pastebin.com/raw/9QZpqyUH"
VALIDITY_DAYS = 7
WARNING_DAYS = 3  # عدد الأيام قبل انتهاء الصلاحية لاظهار التحذير

def reshape_arabic(text: str) -> str:
    """
    إعادة تشكيل النص العربي ليظهر بشكل صحيح في Tk / CTk
    """
    if not text:
        return text
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)


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
def show_update_popup(days_left: int, website_url: str, custom_msg: str = None):
    root = ctk.CTk()
    root.withdraw()
    
    popup = ctk.CTkToplevel(root)
    popup.title("Update Available")
    popup.geometry("400x150")
    
    if custom_msg and len(custom_msg) > 1:
        msg = custom_msg  # استخدم الرسالة من السطر الثالث
    elif days_left <= 0:
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
    
    def open_site():
        if website_url:
            webbrowser.open(website_url)
        close_all()
    
    btn = ctk.CTkButton(popup, text="Open Download Page", command=open_site)
    btn.pack(pady=10)
    
    popup.protocol("WM_DELETE_WINDOW", close_all)
    popup.grab_set()
    popup.wait_window()


def check_usage_limit():
    """
    التحقق من صلاحية النسخة + قراءة إعدادات Pastebin
    """
    online_date = get_online_date()
    if not online_date:
        messagebox.showerror(
            "خطأ",
            "تعذر التحقق من التاريخ من الإنترنت.\nسيتم إغلاق التطبيق."
        )
        sys.exit(0)

    try:
        response = requests.get(PASTEBIN_URL, timeout=5)
        response.raise_for_status()

        config_data = parse_pastebin_config(response.text)

        # ===== Core =====
        start_date_str = config_data.get("start_date")
        website_url = config_data.get("website")

        if not start_date_str:
            raise ValueError("start_date is missing in Pastebin")

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        days_left = VALIDITY_DAYS - (online_date - start_date).days

        # ===== Custom Message =====
        msg_enabled = config_data.get("message_enabled", "false").lower() == "true"
        custom_msg = config_data.get("message", "")
        button_text = config_data.get("button_text", "تمام! 😄")
        msg_type = config_data.get("message_type", "info")
        auto_close = int(config_data.get("auto_close_seconds", 0))

        # ===== عرض الرسالة المخصصة (بدون شروط صلاحية) =====
        if msg_enabled and len(custom_msg.strip()) > 1:
            show_custom_message(
                custom_msg=custom_msg,
                button_text=button_text,
                message_type=msg_type,
                auto_close_seconds=auto_close
            )

        # ===== التحقق من الصلاحية =====
        if days_left <= 0:
            show_update_popup(days_left, website_url)
        elif days_left <= WARNING_DAYS:
            show_update_popup(days_left, website_url)
        else:
            print(f"✅ {days_left} يوم متبقي قبل انتهاء الصلاحية.")

    except Exception as e:
        print("❌ Failed to check usage limit:", e)
        messagebox.showerror(
            "خطأ",
            "حدث خطأ أثناء التحقق من صلاحية التطبيق.\nسيتم إغلاقه."
        )
        sys.exit(0)



def parse_pastebin_config(text: str) -> dict:
    config = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()
    return config

def show_custom_message(
    custom_msg: str,
    button_text: str = "تمام! 😄",
    message_type: str = "info",
    auto_close_seconds: int = 0
):
    root = ctk.CTk()
    root.withdraw()

    popup = ctk.CTkToplevel(root)
    popup.geometry("540x260")

    titles = {
        "info": "ℹ️ رسالة",
        "warning": "⚠️ تنبيه",
        "error": "❌ هام"
    }

    popup.title(titles.get(message_type, "رسالة"))

    # 👇 دعم العربي في النص
    fixed_message = custom_msg
    fixed_button = reshape_arabic(button_text)

    label = ctk.CTkLabel(
        popup,
        text=fixed_message,
        wraplength=500,
        font=("Arial", 21, "bold"),
        justify="center"
    )
    label.pack(pady=40)

    btn = ctk.CTkButton(
        popup,
        text=reshape_arabic_button(button_text),
        height=42,
        font=("Arial", 18),
        command=lambda: (popup.destroy(), root.destroy())
    )
    btn.pack(pady=15)

    if auto_close_seconds > 0:
        popup.after(auto_close_seconds * 1000, lambda: (popup.destroy(), root.destroy()))

    popup.protocol("WM_DELETE_WINDOW", lambda: (popup.destroy(), root.destroy()))
    popup.grab_set()
    popup.wait_window()
def reshape_arabic_button(text: str) -> str:
    if not text:
        return text
    return arabic_reshaper.reshape(text)  # بدون get_display
    
# مثال على الاستخدام عند بداية التطبيق:
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")  # أو "light"
    ctk.set_default_color_theme("blue")
    
    check_usage_limit()
    # هنا يمكنك بدء تطبيقك الرئيسي بعد التحقق

'''import random
import tkinter as tk
from tkinter import ttk
import statistics
import requests
import json
import os

# ---------------- نمونه داده ----------------
ip_ranges = {
    "Iran": ["5.160", "46.209", "91.98"],
    "Germany": ["80.150", "84.158", "93.184"],
    "India": ["49.32", "103.224", "117.200"],
    "Other": ["45.18", "192.168", "10.0"]
}

def generate_ipv4(country="Other"):
    base = random.choice(ip_ranges.get(country, ip_ranges["Other"]))
    return f"{base}.{random.randint(0,255)}.{random.randint(0,255)}"

def generate_ipv6(country="Other"):
    return f"0f01::{country}:{random.randint(0,999):03}:{random.randint(0,65535):04x}"

def test_fluctuation(country="Other", n=10):
    ipv4_list = [generate_ipv4(country) for _ in range(n)]
    ipv6_list = [generate_ipv6(country) for _ in range(n)]
    ipv4_lengths = [len(x) for x in ipv4_list]
    ipv6_lengths = [len(x) for x in ipv6_list]
    stats = {
        "ipv4_unique": len(set(ipv4_list)),
        "ipv6_unique": len(set(ipv6_list)),
        "ipv4_mean_length": round(statistics.mean(ipv4_lengths), 2),
        "ipv6_mean_length": round(statistics.mean(ipv6_lengths), 2),
        "ipv4_stdev": round(statistics.stdev(ipv4_lengths) if len(ipv4_lengths)>1 else 0, 2),
        "ipv6_stdev": round(statistics.stdev(ipv6_lengths) if len(ipv6_lengths)>1 else 0, 2)
    }
    return ipv4_list, ipv6_list, stats

# ---------------- اتصال مستقیم به Azure ----------------
def call_azure_chat(endpoint_or_base, deployment_name, api_key, user_prompt, temperature=0.2, max_tokens=600):
    if "deployments" in endpoint_or_base and "chat/completions" in endpoint_or_base:
        url = endpoint_or_base
    else:
        api_version = "2023-10-01-preview"
        url = endpoint_or_base.rstrip("/") + f"/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {"role":"system","content":"You are a helpful assistant."},
            {"role":"user","content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "n": 1
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()

# ---------------- رابط گرافیکی ----------------
root = tk.Tk()
root.title("AI IP Generator (Azure Direct)")
root.geometry("1000x760")

# دکمه‌های تولید
frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=8)
for country in ip_ranges.keys():
    tk.Button(frame_buttons, text=f"Generate {country}", command=lambda c=country: show_results(c)).pack(side=tk.LEFT, padx=6)

# فریم تنظیمات Azure
api_frame = tk.Frame(root)
api_frame.pack(fill=tk.X, padx=10, pady=6)

tk.Label(api_frame, text="API Endpoint").pack(side=tk.LEFT, padx=(0,4))
api_endpoint_var = tk.StringVar(value=os.environ.get("AZURE_OPENAI_ENDPOINT",""))
tk.Entry(api_frame, textvariable=api_endpoint_var, width=50).pack(side=tk.LEFT, padx=(0,10))

tk.Label(api_frame, text="API Key").pack(side=tk.LEFT, padx=(0,4))
api_key_var = tk.StringVar(value=os.environ.get("AZURE_OPENAI_KEY",""))
tk.Entry(api_frame, textvariable=api_key_var, width=30, show="*").pack(side=tk.LEFT, padx=(0,10))

model_frame = tk.Frame(root)
model_frame.pack(fill=tk.X, padx=10, pady=(0,6))
tk.Label(model_frame, text="Deployment name").pack(side=tk.LEFT, padx=(0,4))
model_var = tk.StringVar(value=os.environ.get("AZURE_OPENAI_DEPLOYMENT","gpt4-deploy"))
tk.Entry(model_frame, textvariable=model_var, width=25).pack(side=tk.LEFT, padx=(0,10))

# کادر پرامپت کاربر
prompt_frame = tk.Frame(root)
prompt_frame.pack(fill=tk.X, padx=10, pady=(0,6))
tk.Label(prompt_frame, text="Your prompt (دستور خود را بنویسید)").pack(anchor="w")
prompt_text_var = tk.StringVar()
tk.Entry(prompt_frame, textvariable=prompt_text_var, width=120).pack(fill=tk.X, padx=(0,10))

# دکمه تحلیل
action_frame = tk.Frame(root)
action_frame.pack(fill=tk.X, padx=10, pady=(0,6))
tk.Button(action_frame, text="Send prompt to Azure", command=lambda: analyze_with_azure()).pack(side=tk.LEFT, padx=6)

# جدول آمار
stats_frame = tk.Frame(root)
stats_frame.pack(fill=tk.X, padx=10, pady=(5,0))
stats_table = ttk.Treeview(stats_frame, columns=("stat","value"), show="headings", height=6)
stats_table.heading("stat", text="Statistic")
stats_table.heading("value", text="Value")
stats_table.column("stat", width=300, anchor="w")
stats_table.column("value", width=200, anchor="center")
stats_table.pack(fill=tk.X)

# پنجره خروجی
output = tk.Text(root, width=120, height=28)
output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# ذخیره آخرین اجرا
last_run = {}
def show_results(country):
    global last_run
    ipv4_list, ipv6_list, stats = test_fluctuation(country, n=10)
    last_run = {
        "country": country,
        "ipv4_list": ipv4_list,
        "ipv6_list": ipv6_list,
        "stats": stats
    }
    for item in stats_table.get_children():
        stats_table.delete(item)
    for k,v in stats.items():
        stats_table.insert("", tk.END, values=(k, v))
    output.delete("1.0", tk.END)
    output.insert(tk.END, f"=== {country} IPv4 Addresses ===\n")
    for ip in ipv4_list:
        output.insert(tk.END, ip + "\n")
    output.insert(tk.END, f"\n=== {country} IPv6 Addresses ===\n")
    for ip in ipv6_list:
        output.insert(tk.END, ip + "\n")

def analyze_with_azure():
    if not last_run:
        output.insert(tk.END, "\nابتدا یک کشور را Generate کنید.\n")
        return

    endpoint = api_endpoint_var.get().strip() or os.environ.get("AZURE_OPENAI_ENDPOINT","")
    api_key = api_key_var.get().strip() or os.environ.get("AZURE_OPENAI_KEY","")
    deployment = model_var.get().strip() or os.environ.get("AZURE_OPENAI_DEPLOYMENT","")
    prompt_text = prompt_text_var.get().strip()

    if not endpoint or not api_key or not deployment:
        output.insert(tk.END, "\nاطلاعات Azure کامل نیست.\n")
        return

    # پرامپت کاربر مستقیم به Azure فرستاده می‌شود
    user_prompt = prompt_text if prompt_text else f"Analyze IP data: {json.dumps(last_run, ensure_ascii=False)}"

    output.insert(tk.END, "\n=== Sending prompt to Azure ===\n")
    try:
        resp = call_azure_chat(endpoint_or_base=endpoint, deployment_name=deployment, api_key=api_key,
                               user_prompt=user_prompt, temperature=0.2, max_tokens=400)
        choices = resp.get("choices", [])
        if choices:
            text = choices[0].get("message", {}).get("content", "")
        else:
            text = resp.get("text") or resp.get("result") or json.dumps(resp, indent=2, ensure_ascii=False)
        output.insert(tk.END, "\n--- Model response ---\n")
        output.insert(tk.END, text + "\n")
    except Exception as e:
        output.insert(tk.END, f"\nخطا در تماس با Azure OpenAI: {e}\n")

root.mainloop()'''








''''

import random
import tkinter as tk
from tkinter import ttk
import statistics
import requests
import json
import os

# ---------------- داده نمونه ----------------
ip_ranges = {
    "Iran": ["5.160", "46.209", "91.98"],
    "Germany": ["80.150", "84.158", "93.184"],
    "India": ["49.32", "103.224", "117.200"],
    "Other": ["45.18", "192.168", "10.0"]
}

def generate_ipv4(country="Other"):
    base = random.choice(ip_ranges.get(country, ip_ranges["Other"]))
    return f"{base}.{random.randint(0,255)}.{random.randint(0,255)}"

def generate_ipv6(country="Other"):
    return f"0f01::{country}:{random.randint(0,999):03}:{random.randint(0,65535):04x}"

def test_fluctuation(country="Other", n=10):
    ipv4_list = [generate_ipv4(country) for _ in range(n)]
    ipv6_list = [generate_ipv6(country) for _ in range(n)]
    ipv4_lengths = [len(x) for x in ipv4_list]
    ipv6_lengths = [len(x) for x in ipv6_list]
    stats = {
        "ipv4_unique": len(set(ipv4_list)),
        "ipv6_unique": len(set(ipv6_list)),
        "ipv4_mean_length": round(statistics.mean(ipv4_lengths), 2),
        "ipv6_mean_length": round(statistics.mean(ipv6_lengths), 2),
        "ipv4_stdev": round(statistics.stdev(ipv4_lengths) if len(ipv4_lengths)>1 else 0, 2),
        "ipv6_stdev": round(statistics.stdev(ipv6_lengths) if len(ipv6_lengths)>1 else 0, 2)
    }
    return ipv4_list, ipv6_list, stats

# ---------------- Azure Chat ----------------
def call_azure_chat(endpoint_or_base, deployment_name, api_key, user_prompt, temperature=0.2, max_tokens=400):
    if "deployments" in endpoint_or_base and "chat/completions" in endpoint_or_base:
        url = endpoint_or_base
    else:
        api_version = "2023-10-01-preview"
        url = endpoint_or_base.rstrip("/") + f"/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"

    headers = {"api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "messages": [
            {"role":"system","content":"You are a helpful assistant."},
            {"role":"user","content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()

# ---------------- GUI ----------------
root = tk.Tk()
root.title("AI IP Generator (Azure Direct)")
root.geometry("1000x800")

# تنظیمات Azure
api_frame = tk.Frame(root)
api_frame.pack(fill=tk.X, padx=10, pady=6)

tk.Label(api_frame, text="API Endpoint").pack(side=tk.LEFT, padx=(0,4))
api_endpoint_var = tk.StringVar(value=os.environ.get("AZURE_OPENAI_ENDPOINT",""))
tk.Entry(api_frame, textvariable=api_endpoint_var, width=50).pack(side=tk.LEFT, padx=(0,10))

tk.Label(api_frame, text="API Key").pack(side=tk.LEFT, padx=(0,4))
api_key_var = tk.StringVar(value=os.environ.get("AZURE_OPENAI_KEY",""))
tk.Entry(api_frame, textvariable=api_key_var, width=30, show="*").pack(side=tk.LEFT, padx=(0,10))

model_frame = tk.Frame(root)
model_frame.pack(fill=tk.X, padx=10, pady=(0,6))
tk.Label(model_frame, text="Deployment name").pack(side=tk.LEFT, padx=(0,4))
model_var = tk.StringVar(value=os.environ.get("AZURE_OPENAI_DEPLOYMENT","gpt4-deploy"))
tk.Entry(model_frame, textvariable=model_var, width=25).pack(side=tk.LEFT, padx=(0,10))

# پرامپت کاربر
prompt_frame = tk.Frame(root)
prompt_frame.pack(fill=tk.X, padx=10, pady=(0,6))
tk.Label(prompt_frame, text="Your prompt (دستور خود را بنویسید)").pack(anchor="w")
prompt_text_var = tk.StringVar()
tk.Entry(prompt_frame, textvariable=prompt_text_var, width=120).pack(fill=tk.X, padx=(0,10))

# خروجی
output = tk.Text(root, width=120, height=20)
output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# جدول آمار
stats_frame = tk.Frame(root)
stats_frame.pack(fill=tk.X, padx=10, pady=(5,0))
stats_table = ttk.Treeview(stats_frame, columns=("stat","value"), show="headings", height=6)
stats_table.heading("stat", text="Statistic")
stats_table.heading("value", text="Value")
stats_table.column("stat", width=300, anchor="w")
stats_table.column("value", width=200, anchor="center")
stats_table.pack(fill=tk.X)

# ذخیره آخرین اجرا
last_run = {}

def show_results(country):
    global last_run
    ipv4_list, ipv6_list, stats = test_fluctuation(country, n=10)
    last_run = {"country": country, "ipv4_list": ipv4_list, "ipv6_list": ipv6_list, "stats": stats}
    for item in stats_table.get_children():
        stats_table.delete(item)
    for k,v in stats.items():
        stats_table.insert("", tk.END, values=(k, v))
    output.delete("1.0", tk.END)
    output.insert(tk.END, f"=== {country} IPv4 Addresses ===\n")
    for ip in ipv4_list:
        output.insert(tk.END, ip + "\n")
    output.insert(tk.END, f"\n=== {country} IPv6 Addresses ===\n")
    for ip in ipv6_list:
        output.insert(tk.END, ip + "\n")

def send_prompt_to_azure():
    endpoint = api_endpoint_var.get().strip() or os.environ.get("AZURE_OPENAI_ENDPOINT","")
    api_key = api_key_var.get().strip() or os.environ.get("AZURE_OPENAI_KEY","")
    deployment = model_var.get().strip() or os.environ.get("AZURE_OPENAI_DEPLOYMENT","")
    prompt_text = prompt_text_var.get().strip()

    if not endpoint or not api_key or not deployment:
        output.insert(tk.END, "\nاطلاعات Azure کامل نیست.\n")
        return
    if not prompt_text:
        output.insert(tk.END, "\nلطفاً یک پرامپت وارد کنید.\n")
        return

    output.insert(tk.END, "\n=== Sending ONLY user prompt to Azure ===\n")
    try:
        resp = call_azure_chat(endpoint_or_base=endpoint,
                               deployment_name=deployment,
                               api_key=api_key,
                               user_prompt=prompt_text,
                               temperature=0.2,
                               max_tokens=400)
        choices = resp.get("choices", [])
        if choices:
            text = choices[0].get("message", {}).get("content", "")
        else:
            text = resp.get("text") or resp.get("result") or json.dumps(resp, indent=2, ensure_ascii=False)
        output.insert(tk.END, "\n--- Model response ---\n")
        output.insert(tk.END, text + "\n")
    except Exception as e:
        output.insert(tk.END, f"\nخطا در تماس با Azure OpenAI: {e}\n")

# دکمه‌ها
action_frame = tk.Frame(root)
action_frame.pack(fill=tk.X, padx=10, pady=(0,6))
tk.Button(action_frame, text="Generate Iran", command=lambda: show_results("Iran")).pack(side=tk.LEFT, padx=6)
tk.Button(action_frame, text="Generate Germany", command=lambda: show_results("Germany")).pack(side=tk.LEFT, padx=6)
tk.Button(action_frame, text="Generate India", command=lambda: show_results("India")).pack(side=tk.LEFT, padx=6)
tk.Button(action_frame, text="Generate Other", command=lambda: show_results("Other")).pack(side=tk.LEFT, padx=6)
tk.Button(action_frame, text="Send prompt only to Azure", command=send_prompt_to_azure).pack(side=tk.LEFT, padx=6)

root.mainloop()'''















"""
import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
from gpt4all import GPT4All

# ---------------- تنظیمات ----------------
MODEL_PATH = "models/mistral.gguf"
API_URL = "http://127.0.0.1:8000/chat"

KEYWORDS = [
    "کلیه","سنگ کلیه","دیالیز","کراتینین",
    "اوره","ادرار","پیوند","نارسایی","GFR"
]

SYSTEM_PROMPT = """
"""تو پزشک متخصص کلیه هستی.
فقط در مورد کلیه، آزمایشات کلیوی و درمان پاسخ بده."""
"""

model = GPT4All(MODEL_PATH)

# ---------------- توابع ----------------
def is_kidney_related(text):
    return any(k in text for k in KEYWORDS)

def analyze_lab(creatinine, gfr, urea):
    result = "🔍 تحلیل آزمایش کلیه:\n"

    if creatinine > 1.3:
        result += "⚠️ کراتینین بالا است.\n"
    else:
        result += "✅ کراتینین نرمال است.\n"

    if gfr < 60:
        result += "⚠️ GFR پایین، کاهش عملکرد کلیه.\n"
    else:
        result += "✅ GFR مناسب است.\n"

    if urea > 45:
        result += "⚠️ اوره بالا است.\n"
    else:
        result += "✅ اوره نرمال است.\n"

    result += "\n📌 تفسیر نهایی باید توسط پزشک انجام شود."
    return result

def ask_offline(q):
    prompt = SYSTEM_PROMPT + f"\nسوال: {q}\nپاسخ:"
    return model.generate(prompt, max_tokens=300, temp=0.4)

def ask_online(q):
    r = requests.post(API_URL, json={"text": q}, timeout=30)
    return r.json()["answer"]

def send_question():
    q = entry.get()
    chat.insert(tk.END, f"🧑 شما: {q}\n")

    if not is_kidney_related(q):
        answer = "❌ فقط سوالات مربوط به کلیه پاسخ داده می‌شود."
    else:
        try:
            if mode.get() == "online":
                answer = ask_online(q)
            else:
                answer = ask_offline(q)
        except Exception as e:
            answer = f"⚠️ خطا: {e}"

    chat.insert(tk.END, f"🤖 پاسخ: {answer}\n\n")
    entry.delete(0, tk.END)

def run_analysis():
    try:
        c = float(creatinine_entry.get())
        g = float(gfr_entry.get())
        u = float(urea_entry.get())
        result = analyze_lab(c, g, u)
        chat.insert(tk.END, result + "\n\n")
    except:
        messagebox.showerror("خطا", "اعداد معتبر وارد کنید")

# ---------------- GUI ----------------
root = tk.Tk()
root.title("🩺 هوش مصنوعی تخصصی کلیه (آنلاین / آفلاین)")

mode = tk.StringVar(value="offline")
tk.Radiobutton(root, text="آفلاین", variable=mode, value="offline").pack()
tk.Radiobutton(root, text="آنلاین", variable=mode, value="online").pack()

chat = scrolledtext.ScrolledText(root, width=75, height=22)
chat.pack(padx=10, pady=10)

entry = tk.Entry(root, width=65)
entry.pack(padx=10)
tk.Button(root, text="ارسال سوال", command=send_question).pack(pady=5)

# ---- تحلیل آزمایش ----
frame = tk.LabelFrame(root, text="🧪 تحلیل آزمایش کلیه")
frame.pack(padx=10, pady=10)

tk.Label(frame, text="کراتینین").grid(row=0, column=0)
tk.Label(frame, text="GFR").grid(row=0, column=2)
tk.Label(frame, text="اوره").grid(row=0, column=4)

creatinine_entry = tk.Entry(frame, width=8)
gfr_entry = tk.Entry(frame, width=8)
urea_entry = tk.Entry(frame, width=8)

creatinine_entry.grid(row=0, column=1)
gfr_entry.grid(row=0, column=3)
urea_entry.grid(row=0, column=5)

tk.Button(frame, text="تحلیل", command=run_analysis).grid(row=0, column=6, padx=5)

root.mainloop()

"""














"""import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk 
import cv2

cap = cv2.VideoCapture("movie.mp4")

root = tk.Tk()
root.title("عکس وسط و دکمه‌ها اطراف")
root.geometry("900x600")


left = tk.Frame(root, width=150, bg="lightgray")
left.pack(side="left", fill="y")

right = tk.Frame(root, width=150, bg="lightgray")
right.pack(side="right", fill="y")

center = tk.Frame(root, bg="white")
center.pack(side="left", fill="both", expand=True)

label = tk.Label(center)
label.pack(expand=True)

current_img = None
current_Video = None
def select_image():
    global current_img
    file_path = filedialog.askopenfilename(filetypes=[("Image files","Video files", "*.jpg *.png *.jpeg *.mp4")])
    if file_path:
        current_img = cv2.imread(file_path)
        show_image(current_img)

def show_image(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img)
    img_pil = img_pil.resize((500, 400))
    img_tk = ImageTk.PhotoImage(img_pil)
    label.config(image=img_tk)
    label.image = img_tk


def apply_original():
    if current_img is not None:
        show_image(current_img)

def apply_bw():
    if current_img is not None:
        gray = cv2.cvtColor(current_img, cv2.COLOR_BGR2GRAY)
        show_image(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))

def apply_edges():
    if current_img is not None:
        edges = cv2.Canny(current_img, 100, 200)
        show_image(cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR))

def apply_gradient():
    if current_img is not None:
        grad_x = cv2.Sobel(current_img, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(current_img, cv2.CV_64F, 0, 1, ksize=3)
        grad = cv2.convertScaleAbs(cv2.addWeighted(grad_x, 0.5, grad_y, 0.5, 0))
        show_image(grad)
def apply_erosion():
    if current_img is not None:
        erosion_y = cv2.Sobel(current_img , cv2.CV_64F , 0,1, ksize=4)
        erosion_x = cv2.Sobel(current_img , cv2.CV_64F , 1,0, ksize=5)
        erosion = cv2.convertScaleAbs(cv2.addWeighted(erosion_x, 0.5, erosion_y, 0.6, 0))
        show_image(erosion)


btn_select = tk.Button(left, text="انتخاب عکس", command=select_image)
btn_select.pack(pady=10, fill="x")

btn_bw = tk.Button(left, text="سیاه و سفید", command=apply_bw)
btn_bw.pack(pady=10, fill="x")

btn_edges = tk.Button(left, text="لبه‌ها", command=apply_edges)
btn_edges.pack(pady=10, fill="x")


original = tk.Button(right, text="ارجینال", command=apply_original)
original.pack(pady=10, fill="x")

grad = tk.Button(right, text="گرادیان", command=apply_gradient)
grad.pack(pady=10, fill="x")

grad = tk.Button(right, text="erosion", command=apply_erosion())
grad.pack(pady=10, fill="x")
cap.release()
root.mainloop()"""









"""
import mysql.connector
from mysql.connector import Error

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "YOUR_PASSWORD"

sql_script = """
"""

CREATE DATABASE IF NOT EXISTS vpn_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE vpn_platform;

CREATE TABLE users (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(150) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('user','admin') DEFAULT 'user',
  is_active BOOLEAN DEFAULT TRUE,
  is_locked BOOLEAN DEFAULT FALSE,
  locked_until DATETIME NULL,
  abuse_status ENUM('clean','suspected','blocked') DEFAULT 'clean',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE plans (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  price DECIMAL(10,2),
  duration_days INT
) ENGINE=InnoDB;

CREATE TABLE subscriptions (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNSIGNED,
  plan_id INT UNSIGNED,
  start_date DATETIME,
  end_date DATETIME,
  status ENUM('active','expired','cancelled') DEFAULT 'active',
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE server_locations (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  country_name VARCHAR(100),
  country_code CHAR(2),
  city VARCHAR(100)
) ENGINE=InnoDB;

CREATE TABLE servers (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  location_id INT UNSIGNED,
  hostname VARCHAR(150),
  provider VARCHAR(100),
  is_active BOOLEAN DEFAULT TRUE,
  health_status ENUM('online','offline','dead') DEFAULT 'online',
  load_status ENUM('normal','busy','full') DEFAULT 'normal',
  max_connections INT DEFAULT 500,
  last_heartbeat DATETIME,
  FOREIGN KEY (location_id) REFERENCES server_locations(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE ip_addresses (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  server_id INT UNSIGNED,
  ip_address VARCHAR(45),
  version ENUM('IPv4','IPv6'),
  status ENUM('free','assigned','blocked') DEFAULT 'free',
  FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE connections (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNSIGNED,
  server_id INT UNSIGNED,
  ip_id INT UNSIGNED,
  connection_status ENUM('active','dropped','dead') DEFAULT 'active',
  connected_at DATETIME,
  disconnected_at DATETIME,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
  FOREIGN KEY (ip_id) REFERENCES ip_addresses(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE usage_logs (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  connection_id INT UNSIGNED,
  upload_mb DECIMAL(12,2),
  download_mb DECIMAL(12,2),
  log_time DATETIME,
  FOREIGN KEY (connection_id) REFERENCES connections(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE usage_logs_archive LIKE usage_logs;

CREATE TABLE login_logs (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNSIGNED NULL,
  ip_address VARCHAR(45),
  status ENUM('success','failed'),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE failed_attempts (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(150),
  ip_address VARCHAR(45),
  attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE server_load_stats (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  server_id INT UNSIGNED,
  active_connections INT DEFAULT 0,
  recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE server_latency_logs (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  server_id INT UNSIGNED,
  latency_ms INT,
  checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE server_scores (
  server_id INT UNSIGNED PRIMARY KEY,
  latency_ms INT,
  reliability_score FLOAT,
  load_score FLOAT,
  overall_score FLOAT,
  updated_at DATETIME,
  FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE abuse_flags (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNSIGNED,
  reason VARCHAR(255),
  severity ENUM('low','medium','high'),
  flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE wallets (
  user_id INT UNSIGNED PRIMARY KEY,
  balance DECIMAL(12,2) DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE wallet_transactions (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNSIGNED,
  amount DECIMAL(12,2),
  type ENUM('deposit','withdraw','subscription_payment'),
  description VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

"""











import mysql.connector
from mysql.connector import Error
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "YOUR_PASSWORD"
DB_NAME = "vpn_platform"

# ================= DATABASE =================
def get_data():
    conn = None
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM servers")
        total_servers = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT 
                SUM(health_status='online'),
                SUM(health_status='offline'),
                SUM(health_status='dead')
            FROM servers
        """)
        online, offline, dead = cursor.fetchone()
        online = online or 0
        offline = offline or 0
        dead = dead or 0

        cursor.execute("SELECT COUNT(*) FROM connections WHERE connection_status='active'")
        active_connections = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(upload_mb), SUM(download_mb) FROM usage_logs")
        upload, download = cursor.fetchone()
        upload = upload or 0
        download = download or 0

        cursor.execute("SELECT SUM(balance) FROM wallets")
        total_balance = cursor.fetchone()[0] or 0

        return {
            "total_users": total_users,
            "total_servers": total_servers,
            "online": online,
            "offline": offline,
            "dead": dead,
            "active_connections": active_connections,
            "upload": upload,
            "download": download,
            "total_balance": total_balance
        }

    except Error as e:
        print("DB ERROR:", e)
        return None

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ================= GUI =================
class Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("VPN Platform Dashboard")
        self.root.geometry("800x600")

        self.frame_top = tk.Frame(root)
        self.frame_top.pack(pady=10)

        self.labels = []
        for _ in range(9):
            lbl = tk.Label(self.frame_top, font=("Arial", 12))
            lbl.pack(anchor='w')
            self.labels.append(lbl)

        self.frame_bottom = tk.Frame(root)
        self.frame_bottom.pack(fill='both', expand=True)

        self.fig, self.ax = plt.subplots(figsize=(6,4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_bottom)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        self.update_dashboard()

    def update_dashboard(self):
        data = get_data()
        if not data:
            self.root.after(10000, self.update_dashboard)
            return

        stats = [
            f"Total Users: {data['total_users']}",
            f"Total Servers: {data['total_servers']}",
            f"Online Servers: {data['online']}",
            f"Offline Servers: {data['offline']}",
            f"Dead Servers: {data['dead']}",
            f"Active Connections: {data['active_connections']}",
            f"Upload MB: {data['upload']:.2f}",
            f"Download MB: {data['download']:.2f}",
            f"Total Wallet Balance: ${data['total_balance']:.2f}"
        ]

        for lbl, text in zip(self.labels, stats):
            lbl.config(text=text)

        self.ax.clear()
        self.ax.bar(['Online','Offline','Dead'],
                    [data['online'], data['offline'], data['dead']],
                    color=['green','orange','red'])
        self.ax.set_title("Server Status")
        self.canvas.draw()

        # رفرش هر 10 ثانیه
        self.root.after(10000, self.update_dashboard)

# ================= MAIN =================
if __name__ == "__main__":
    root = tk.Tk()
    app = Dashboard(root)
    root.mainloop()

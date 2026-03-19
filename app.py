from flask import Flask, render_template, request, redirect, session
import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from urllib.parse import quote
import requests
from dotenv import load_dotenv

# ---------------- ENVIRONMENT ----------------
load_dotenv()  # Loads .env file
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SESSION_SECRET = os.getenv("SESSION_SECRET", "supersecretkey")  # fallback
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.secret_key = SESSION_SECRET

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("site.db")

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS media(
            id INTEGER PRIMARY KEY,
            filename TEXT,
            type TEXT,
            category TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route('/')
def index():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT filename FROM media WHERE category='service'")
    services = [x[0] for x in c.fetchall()]
    c.execute("SELECT filename FROM media WHERE category='project'")
    projects = [x[0] for x in c.fetchall()]
    conn.close()
    return render_template("index.html", services=services, projects=projects)

# ---------------- CONTACT ----------------
@app.route('/contact', methods=['POST'])
def contact():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    message = request.form['message']
    text = f"Name: {name}, Email: {email}, Phone: {phone}, Message: {message}"

    # EMAIL
    if EMAIL_SENDER and EMAIL_PASSWORD:
        msg = MIMEText(text)
        msg['Subject'] = "Client Message"
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_SENDER
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print("Email failed:", e)

    # WHATSAPP
    encoded = quote(text)
    return redirect(f"https://wa.me/254757250466?text={encoded}")

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        user = c.fetchone()
        conn.close()
        if user:
            session['user'] = u
            return redirect('/dashboard')
    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO users(username,password) VALUES(?,?)", (u, p))
        conn.commit()
        conn.close()
        return redirect('/login')
    return render_template("register.html")

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM media")
    files = c.fetchall()
    conn.close()
    return render_template("dashboard.html", files=files)

# ---------------- UPLOAD ----------------
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    category = request.form['category']
    if file:
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO media(filename,type,category) VALUES(?,?,?)", (file.filename, "image", category))
        conn.commit()
        conn.close()
    return redirect('/dashboard')

# ---------------- DELETE ----------------
@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT filename FROM media WHERE id=?", (id,))
    file = c.fetchone()
    if file:
        try:
            os.remove(os.path.join(UPLOAD_FOLDER, file[0]))
        except Exception as e:
            print("Delete failed:", e)
        c.execute("DELETE FROM media WHERE id=?", (id,))
        conn.commit()
    conn.close()
    return redirect('/dashboard')

# ---------------- M-PESA (DARaja) ----------------
@app.route('/pay')
def pay():
    MPESA_TOKEN = os.getenv("MPESA_TOKEN")
    MPESA_PASS = os.getenv("MPESA_PASS")
    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {MPESA_TOKEN}"}
    data = {
        "BusinessShortCode": "174379",
        "Password": MPESA_PASS,
        "Timestamp": "20260101010101",
        "TransactionType": "CustomerPayBillOnline",
        "Amount": "1",
        "PartyA": "254757250466",
        "PartyB": "174379",
        "PhoneNumber": "254757250466",
        "CallBackURL": "https://yourdomain.com/callback",
        "AccountReference": "Jakentronics",
        "TransactionDesc": "Payment"
    }
    try:
        requests.post(url, json=data, headers=headers)
    except Exception as e:
        print("M-PESA request failed:", e)
    return "Payment Request Sent"

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
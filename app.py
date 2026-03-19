from flask import Flask, render_template, request, redirect, session
import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from urllib.parse import quote
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    return sqlite3.connect("site.db")

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS media(
        id INTEGER PRIMARY KEY,
        filename TEXT,
        type TEXT,
        category TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

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

@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT filename FROM media WHERE id=?", (id,))
    file = c.fetchone()

    if file:
        try:
            os.remove(os.path.join(UPLOAD_FOLDER, file[0]))
        except:
            pass

    c.execute("DELETE FROM media WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/dashboard')

if __name__ == "__main__":
    app.run()
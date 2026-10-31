import os, sqlite3
from flask import Flask, g, request, redirect, render_template_string, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'campus_secret_123'
DATABASE = 'campus.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png','jpg','jpeg','gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# SECRET ADMIN URL - Sirf tujhe pata hai
ADMIN_SECRET_URL = '/admin-secret-kha-786'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS items
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      type TEXT, name TEXT, description TEXT,
                      location TEXT, contact TEXT, image TEXT, delete_code TEXT)''')
        try: db.execute("ALTER TABLE items ADD COLUMN image TEXT")
        except: pass
        try: db.execute("ALTER TABLE items ADD COLUMN delete_code TEXT")

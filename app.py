import os, sqlite3
from flask import Flask, g, request, redirect, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)
DATABASE = 'campus.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png','jpg','jpeg','gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
                      location TEXT, contact TEXT, image TEXT)''')
        try:
            db.execute("ALTER TABLE items ADD COLUMN image TEXT")
        except:
            pass
        db.commit()

init_db()

def render_page(content):
    base = """
    <!DOCTYPE html><html><head><title>CampusConnect</title>
    <style>
    body{font-family:Arial;margin:0;background:#f4f6f8}
    nav{background:#1e3a8a;color:white;padding:15px}
    nav a{color:white;margin-left:15px;text-decoration:none}
    .container{max-width:800px;margin:20px auto;background:white;padding:20px;border-radius:10px}
    input,textarea,select{width:100%;padding:10px;margin:8px 0;box-sizing:border-box}
    button{background:#1e3a8a;color:white;padding:10px 15px;border:none;border-radius:5px;cursor:pointer}
    .item{border-left:4px solid #1e3a8a;padding:10px;margin:15px 0;background:#f9f9f9;border-radius:5px;overflow:hidden}
    .item img{max-width:100%;max-height:200px;margin-top:10px;border-radius:5px;display:block}
    .delete-btn{background:#dc2626;color:white;padding:6px 12px;text-decoration:none;border-radius:5px;float:right;font-size:13px}
    </style></head><body>
    <nav><b>CampusConnect</b><a href="/">Home</a><a href="/items">Found Items</a><a href="/report">Report Item</a></nav>
    <div class="container">__CONTENT__</div></body></html>
    """
    return render_template_string(base.replace("__CONTENT__", content))

@app.route('/')
def home():
    return render_page("<h2>Welcome to CampusConnect - Lost & Found</h2><p><a href='/report'>Report Lost/Found Item</a></p>")

@app.route('/items')
def items():
    db = get_db()
    cur = db.execute("SELECT * FROM items ORDER BY id DESC")
    rows = cur.fetchall()
    html = "<h2>Found Items</h2><hr>"
    for item in rows:
        img_html = f"<img src='/{item['image']}'>" if item['image'] else ""
        html += f"<div class='item'><a class='delete-btn' href='/delete/{item['id']}' onclick=\"return confirm('Delete?')\">Delete</a><b>{item['type']} - {item['name']}</b><br>{item['description']}<br><small>{item['location']} | {item['contact']}</small>{img_html}</div>"
    return render_page(html)

@app.route('/report', methods=['GET','POST'])
def report():
    if request.method == 'POST':
        file_path = None
        if 'photo' in request.files:
            f = request.files['photo']
            if f and f.filename and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                f.save(save_path)
                file_path = save_path
        db = get_db()
        db.execute("INSERT INTO items (type,name,description,location,contact,image) VALUES (?,?,?,?,?,?)",
                   (request.form['type'], request.form['name'], request.form['description'], request.form['location'], request.form['contact'], file_path))
        db.commit()
        return redirect('/items')
    form = """<h2>Report Item</h2><form method="post" enctype="multipart/form-data">
    <select name="type"><option>Lost</option><option>Found</option></select>
    <input name="name" placeholder="Item name" required>
    <textarea name="description" placeholder="Description" required></textarea>
    <input name="location" placeholder="Location">
    <input name="contact" placeholder="Contact">
    <label><b>Item Photo (optional):</b></label>
    <input type="file" name="photo" accept="image/*">
    <button>Submit</button></form>"""
    return render_page(form)

@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    db = get_db()
    cur = db.execute("SELECT image FROM items WHERE id=?", (item_id,))
    row = cur.fetchone()
    if row and row['image'] and os.path.exists(row['image']):
        try: os.remove(row['image'])
        except: pass
    db.execute("DELETE FROM items WHERE id=?", (item_id,))
    db.commit()
    return redirect('/items')

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    app.run()

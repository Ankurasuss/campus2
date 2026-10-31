from flask import Flask, request, redirect, g
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'campus.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT, name TEXT, description TEXT, 
            location TEXT, contact TEXT)''')
        db.commit()

BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>CampusConnect</title>
<style>
body { font-family: Arial; margin: 0; background: #f4f6f9; }
nav { background: #1e3a8a; color: white; padding: 15px; display: flex; justify-content: space-between; }
nav a { color: white; margin-left: 15px; text-decoration: none; font-weight: bold; }
.container { max-width: 800px; margin: 20px auto; background: white; padding: 20px; border-radius: 10px; }
input, textarea, select { width: 100%; padding: 10px; margin: 8px 0; border-radius: 5px; border: 1px solid #ccc; }
button { background: #1e3a8a; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
.item { border: 1px solid #ddd; padding: 10px; margin: 10px 0; border-radius: 5px; }
.lost { border-left: 5px solid red; }
.found { border-left: 5px solid green; }
</style>
</head>
<body>
<nav><div><b>CampusConnect - Lost & Found</b></div><div><a href="/">Home</a><a href="/report">Report</a><a href="/items">All Items</a></div></nav>
<div class="container">
{content}
</div>
</body>
</html>
"""

@app.route("/")
def home():
    content = """
    <h2>Welcome to CampusConnect</h2>
    <p>Smart Lost & Found Management System - B.Sc CS 5th Sem Project.</p>
    <p><b>Tech Stack:</b> Python + Flask + SQLite + HTML/CSS</p>
    <a href='/report'><button>Report Lost / Found Item</button></a>
    <a href='/items'><button style='background:green'>View All Items</button></a>
    """
    return BASE_HTML.replace("{content}", content)

@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        db = get_db()
        db.execute("INSERT INTO items (type, name, description, location, contact) VALUES (?,?,?,?,?)",
                   (request.form['type'], request.form['name'], request.form['description'], request.form['location'], request.form['contact']))
        db.commit()
        return redirect("/items")
    content = """
    <h2>Report Lost / Found Item</h2>
    <form method="post">
        <label>Type</label><select name="type"><option value="Lost">Lost</option><option value="Found">Found</option></select>
        <label>Item Name</label><input name="name" required placeholder="e.g. ID Card, Bottle">
        <label>Description</label><textarea name="description" required></textarea>
        <label>Location</label><input name="location" required placeholder="e.g. Library, Canteen">
        <label>Contact</label><input name="contact" required placeholder="Mobile / Email">
        <button type="submit">Save to Database</button>
    </form>
    """
    return BASE_HTML.replace("{content}", content)

@app.route("/items")
def items():
    q = request.args.get("q", "")
    db = get_db()
    if q:
        cur = db.execute("SELECT * FROM items WHERE name LIKE ? OR description LIKE ? ORDER BY id DESC", (f'%{q}%', f'%{q}%'))
    else:
        cur = db.execute("SELECT * FROM items ORDER BY id DESC")
    rows = cur.fetchall()
    
    search_box = f"""<form method="get"><input name="q" value="{q}" placeholder="Search items..."><button>Search</button></form><hr>"""
    items_html = search_box
    for r in rows:
        match_html = ""
        if r['type'] == 'Lost':
            cur2 = db.execute("SELECT * FROM items WHERE type='Found' AND name LIKE ?", (f"%{r['name']}%",))
            if cur2.fetchall():
                match_html = "<b style='color:green'>Smart Match Found: Similar Found item exists!</b>"
        items_html += f"""
        <div class="item {'lost' if r['type']=='Lost' else 'found'}">
            <b>{r['type']} - {r['name']}</b><br>
            {r['description']}<br>
            <small>Location: {r['location']} | Contact: {r['contact']}</small><br>{match_html}
        </div>
        """
    if not rows:
        items_html += "<p>No items yet.</p>"
    return BASE_HTML.replace("{content}", items_html)

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == "__main__":
    if not os.path.exists(DATABASE):
        init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
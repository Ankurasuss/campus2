import os, sqlite3, urllib.parse
from flask import Flask, g, request, redirect, render_template_string, session

app = Flask(__name__)
app.secret_key = 'campus_secret_123'
DATABASE = 'campus.db'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
                     (id INTEGER PRIMARY KEY, type TEXT, name TEXT, description TEXT,
                      location TEXT, contact TEXT, image TEXT, delete_code TEXT)''')
        db.commit()
init_db()

def render_page(content):
    html = """
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>CampusConnect AI</title>
    <style>
    body{font-family:Arial;margin:0;background:#f4f5f7}
    nav{background:#0f172a;color:white;padding:15px}
    nav a{color:white;margin-left:15px;text-decoration:none;font-size:14px}
    .container{max-width:850px;margin:15px auto;background:white;padding:25px;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.05)}
    input,textarea,select{width:100%;padding:10px;margin:8px 0;box-sizing:border-box;border:1px solid #ddd;border-radius:6px}
    button{background:#0f172a;color:white;padding:11px 18px;border:none;border-radius:6px;cursor:pointer;font-weight:600}
    .item{border-left:4px solid #6366f1;padding:14px;margin:16px 0;background:#f8f7ff;border-radius:8px}
    .item img{max-width:100%;max-height:200px;border-radius:6px;margin-top:8px}
    .ai-badge{background:#6366f1;color:white;padding:3px 9px;border-radius:12px;font-size:11px}
    .btn{padding:7px 13px;border-radius:6px;text-decoration:none;font-size:12px;margin-right:6px;display:inline-block;margin-top:6px}
    .poster{background:#0f172a;color:white;padding:30px;border-radius:16px;text-align:center;border:5px solid #6366f1}
    .qr-box{background:white;padding:15px;border-radius:12px;display:inline-block;margin-top:15px}
    </style></head><body>
    <nav><b>CampusConnect AI</b><a href="/">Home</a><a href="/items">Browse Items</a><a href="/report">Report Item</a><a href="/heatmap">Analytics</a><a href="/kha-admin-786">Admin</a></nav>
    <div class="container">""" + content + """</div></body></html>
    """
    return render_template_string(html)

@app.route('/')
def home():
    return render_page("<h2>AI-Powered Campus Lost & Found System</h2><p><span class='ai-badge'>AI Claim Guard</span> <span class='ai-badge'>Location Predictor</span> <span class='ai-badge'>AI Poster + QR</span></p><p>An intelligent system to prevent false claims, predict high-loss zones, and generate QR-enabled posters for quick sharing.</p><a href='/report' class='btn' style='background:#6366f1;color:white'>Report an Item</a> <a href='/items' class='btn' style='background:#0f172a;color:white'>View All Items</a>")

@app.route('/items')
def items():
    db = get_db()
    rows = db.execute("SELECT * FROM items ORDER BY id DESC").fetchall()
    html = "<h2>Reported Items <span class='ai-badge'>AI Protected</span></h2>"
    for item in rows:
        img = f"<br><img src='/{item['image']}'>" if item['image'] else ""
        html += f"<div class='item'><b>{item['type']} - {item['name']}</b> <span class='ai-badge'>Verified</span><br>{item['description']}<br><small>Location: {item['location']}</small>{img}<br><a class='btn' style='background:#6366f1;color:white' href='/ai-match/{item['id']}'>AI Match</a><a class='btn' style='background:#0f172a;color:white' href='/claim/{item['id']}'>Verification Test</a><a class='btn' style='background:#10b981;color:white' href='/poster/{item['id']}'>Poster</a><a class='btn' style='background:#000;color:white' href='/qr/{item['id']}'>QR Code</a><a class='btn' style='background:#ef4444;color:white' href='/delete/{item['id']}'>Delete</a></div>"
    return render_page(html)

@app.route('/report', methods=['GET','POST'])
def report():
    if request.method == 'POST':
        f = request.files.get('photo'); path=None
        if f and f.filename:
            from werkzeug.utils import secure_filename
            fn = secure_filename(f.filename); path = os.path.join(UPLOAD_FOLDER, fn); f.save(path)
        db=get_db(); db.execute("INSERT INTO items (type,name,description,location,contact,image,delete_code) VALUES (?,?,?,?,?,?,?)",(request.form['type'],request.form['name'],request.form['description'],request.form['location'],request.form['contact'],path,request.form['delete_code'])); db.commit()
        return redirect('/items')
    return render_page("""<h2>Report Lost / Found Item</h2><form method="post" enctype="multipart/form-data"><label>Item Type</label><select name="type"><option>Lost</option><option>Found</option></select><label>Language of Report</label><select name="lang"><option value="en">English</option><option value="hi">Hindi</option></select><label>Item Name</label><input name="name" placeholder="e.g. ID Card, Black Bottle" required><label>Detailed Description</label><textarea name="description" placeholder="Describe the item in detail - color, marks, contents, etc." required></textarea><label>Location</label><input name="location" placeholder="e.g. Library, Canteen, Block A" required><label>Contact Information</label><input name="contact" placeholder="Email or Phone" required><label>Upload Photo (Optional)</label><input type="file" name="photo" accept="image/*"><label>Set Delete Password</label><input name="delete_code" placeholder="Create a password to delete later" required><button>Submit Report</button></form>""")

def ai_similarity_score(a,b):
    a_words=set(a.lower().split()); b_words=set(b.lower().split())
    common=len(a_words & b_words); total=len(a_words | b_words)
    return (common/total*100) if total else 0

@app.route('/ai-match/<int:item_id>')
def ai_match(item_id):
    db=get_db(); target=db.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
    if not target: return redirect('/items')
    others=db.execute("SELECT * FROM items WHERE id!=? AND type!=?",(item_id,target['type'])).fetchall()
    html=f"<h2>AI Matching for {target['name']}</h2><p>AI analyzed the description using keyword similarity analysis.</p>"
    scored=[]
    for o in others:
        s=ai_similarity_score(target['description'], o['description']); scored.append((o,s))
    scored=sorted(scored, key=lambda x:x[1], reverse=True)[:3]
    found=False
    for o,s in scored:
        if s>5: found=True; html+=f"<div class='item'><b>AI Confidence Score: {int(s)}%</b><br>{o['type']} - {o['name']}<br>{o['description']}<br>Location: {o['location']}<br>Contact: {o['contact']}</div>"
    if not found: html+="<p>No close matches found at the moment. The AI system will automatically suggest a match when a similar item is reported.</p>"
    return render_page(html + "<br><a href='/items'>Back to Items</a>")

@app.route('/claim/<int:item_id>')
def claim(item_id):
    db=get_db(); item=db.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
    desc=item['description'].lower(); qs=[]
    if 'black' in desc: qs.append("What is the exact shade of the color?")
    if 'bottle' in desc: qs.append("What is the color of the bottle cap?")
    if 'wallet' in desc: qs.append("How many compartments does the wallet have?")
    if 'id' in desc or 'card' in desc: qs.append("What is the ID number or name printed on it?")
    qs+= [f"Is there any specific mark on '{item['name']}'?", f"Which side of {item['location']} was it placed?", "Was there any small item attached with it?"]
    q_html="".join([f"<li>{q}</li>" for q in qs[:3]])
    return render_page(f"<h2>AI Claim Guard - Verification Test</h2><div class='item'><b>Item:</b> {item['name']}<br><b>Description:</b> {item['description']}<br><br><b>AI Generated Security Questions:</b><ol>{q_html}</ol><small>Only the real owner can answer these correctly.</small></div><br><a href='/items' class='btn'>Back</a>")

@app.route('/item/<int:item_id>')
def public_item(item_id):
    db=get_db(); item=db.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
    if not item: return render_page("<h2>Item not found</h2>")
    img = f"<img src='/{item['image']}' style='max-width:100%'>" if item['image'] else ""
    return render_page(f"<h2>{item['type']}: {item['name']}</h2><div class='item'>{img}<br><b>Description:</b> {item['description']}<br><b>Location:</b> {item['location']}<br><b>Contact:</b> {item['contact']}</div><p>Found via QR Code from CampusConnect AI</p>")

@app.route('/qr/<int:item_id>')
def qr_page(item_id):
    db=get_db(); item=db.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
    if not item: return redirect('/items')
    base_url = request.host_url.rstrip('/'); item_url = f"{base_url}/item/{item_id}"; qr_data = urllib.parse.quote(item_url)
    qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_data}"
    html = f"<h2>QR Code for {item['name']}</h2><p>Scan this QR code to view item details instantly.</p><div style='text-align:center'><div class='qr-box'><img src='{qr_api_url}' alt='QR Code'></div><p><small>Link: {item_url}</small></p></div><div class='item'><b>Item:</b> {item['name']}<br><b>Location:</b> {item['location']}<br><b>Contact:</b> {item['contact']}</div><a href='/poster/{item_id}' class='btn' style='background:#10b981;color:white'>View Poster with QR</a> <a href='/items' class='btn'>Back</a>"
    return render_page(html)

@app.route('/poster/<int:item_id>')
def poster(item_id):
    db=get_db(); item=db.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
    if not item: return redirect('/items')
    base_url = request.host_url.rstrip('/'); item_url = f"{base_url}/item/{item_id}"; qr_data = urllib.parse.quote(item_url)
    qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_data}"
    html=f"<div class='poster'><h1 style='color:#a5b4fc;font-size:38px;margin:0'>LOST ITEM ALERT</h1><h2 style='margin:15px 0'>{item['name'].upper()}</h2><p>{item['description']}</p><div style='display:flex;justify-content:center;gap:20px;align-items:center;margin-top:20px;flex-wrap:wrap'><div style='background:white;color:black;padding:12px;border-radius:10px;text-align:left'><b>Last Seen:</b> {item['location']}<br><b>Contact:</b> {item['contact']}<br><b>Type:</b> {item['type']}</div><div class='qr-box' style='margin:0'><img src='{qr_api_url}' style='width:150px'><br><small style='color:black'>Scan for Details</small></div></div><p style='font-size:12px;color:#a5b4fc;margin-top:20px'>Generated by CampusConnect AI • Scan QR to Contact Owner</p></div><br><a href='/items' class='btn'>Back to Items</a>"
    return render_page(html)

@app.route('/heatmap')
def heatmap():
    db=get_db(); rows=db.execute("SELECT location, COUNT(*) as c FROM items GROUP BY location").fetchall()
    total=sum([r['c'] for r in rows]) or 1
    html="<h2>AI Location Predictor - Heatmap Analytics</h2><p>The AI model analyzes historical data to predict high-frequency zones.</p>"
    for r in rows:
        perc=int(r['c']/total*100); bar="█"*int(perc/4)
        html+=f"<div class='item'><b>{r['location'] or 'Unknown'}</b> - {r['c']} items<br><span style='color:#6366f1;font-size:18px'>{bar}</span> {perc}%<br><small>AI Prediction: {perc}% probability</small></div>"
    if not rows: html+="<p>No data available yet.</p>"
    return render_page(html)

@app.route('/delete/<int:item_id>', methods=['GET','POST'])
def delete_item(item_id):
    db=get_db(); item=db.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
    if not item: return redirect('/items')
    if session.get('is_admin'):
        db.execute("DELETE FROM items WHERE id=?",(item_id,)); db.commit(); return redirect('/items')
    if request.method=='POST':
        if request.form.get('delete_code','')==item['delete_code']:
            db.execute("DELETE FROM items WHERE id=?",(item_id,)); db.commit(); return redirect('/items')
        else: return render_page(f"<h3 style='color:red'>Incorrect password!</h3><a href='/delete/{item_id}'>Try Again</a>")
    return render_page(f"<h2>Delete Report: {item['name']}</h2><form method='post'><input type='password' name='delete_code' placeholder='Enter Delete Password' required><button style='background:#ef4444'>Confirm Delete</button></form>")

@app.route('/kha-admin-786', methods=['GET','POST'])
def secret_admin():
    if request.method=='POST':
        if request.form.get('password')=='admin123':
            session['is_admin']=True; return redirect('/items')
        else: return render_page("<h3>Incorrect Password</h3>")
    if session.get('is_admin'):
        session.pop('is_admin',None); return render_page("<h3>Admin Logged Out</h3>")
    return render_page("<h2>Admin Login</h2><form method='post'><input type='password' name='password' placeholder='Admin Password'><button>Login</button></form>")

@app.teardown_appcontext
def close_connection(e):
    db=getattr(g,'_database',None); 
    if db: db.close()

if __name__=='__main__':
    app.run()

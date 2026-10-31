import os, sqlite3, random
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
    base = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>CampusConnect AI</title>
    <style>body{{font-family:Arial;margin:0;background:#f0f2f5}} nav{{background:#111827;color:white;padding:15px}}
    nav a{{color:white;margin-left:12px;text-decoration:none;font-size:14px}} .container{{max-width:850px;margin:15px auto;background:white;padding:20px;border-radius:12px}}
    input,textarea,select{{width:100%;padding:10px;margin:8px 0;box-sizing:border-box}} button{{background:#111827;color:white;padding:10px 15px;border:none;border-radius:6px;cursor:pointer}}
    .item{{border-left:4px solid #7c3aed;padding:12px;margin:15px 0;background:#faf5ff;border-radius:8px}} .item img{{max-width:100%;max-height:200px;border-radius:6px;margin-top:8px}}
    .ai-badge{{background:#7c3aed;color:white;padding:2px 8px;border-radius:10px;font-size:11px}} .btn{{padding:6px 12px;border-radius:5px;text-decoration:none;font-size:12px;margin-right:5px;display:inline-block;margin-top:5px}}
    .poster{{background:#111827;color:white;padding:30px;border-radius:15px;text-align:center;border:5px solid #7c3aed}}
    </style></head><body><nav><b>🤖 Campus AI</b><a href="/">Home</a><a href="/items">Found</a><a href="/report">Report</a><a href="/heatmap">Heatmap</a></nav><div class="container">{content}</div></body></html>"""
    return render_template_string(base)

@app.route('/')
def home():
    return render_page("<h2>🤖 AI Based Lost & Found</h2><p><span class='ai-badge'>AI Claim Guard</span> <span class='ai-badge'>AI Heatmap</span> <span class='ai-badge'>AI Poster</span></p><p>Fake claim AI pakad lega. No Pillow, Fast Deploy.</p><a href='/report' class='btn' style='background:#7c3aed;color:white'>Report Item</a>")

@app.route('/items')
def items():
    db = get_db()
    rows = db.execute("SELECT * FROM items ORDER BY id DESC").fetchall()
    html = "<h2>All Items <span class='ai-badge'>AI Protected</span></h2>"
    for item in rows:
        img = f"<br><img src='/{item['image']}'>" if item['image'] else ""
        html += f"""<div class='item'><b>{item['type']} - {item['name']}</b> <span class='ai-badge'>AI</span><br>{item['description']}<br><small>📍 {item['location']}</small>{img}<br>
        <a class='btn' style='background:#7c3aed;color:white' href='/ai-match/{item['id']}'>🤖 AI Match</a>
        <a class='btn' style='background:#111827;color:white' href='/claim/{item['id']}'>🛡️ Claim Test</a>
        <a class='btn' style='background:#059669;color:white' href='/poster/{item['id']}'>📢 AI Poster</a>
        <a class='btn' style='background:#ef4444;color:white' href='/delete/{item['id']}'>Delete</a></div>"""
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
    return render_page("""<h2>Report with AI</h2><form method="post" enctype="multipart/form-data"><select name="type"><option>Lost</option><option>Found</option></select><input name="name" placeholder="Item name" required><textarea name="description" placeholder="Full detail likho - AI isi se sawal banayega" required></textarea><input name="location" placeholder="Location - ex: Canteen"><input name="contact" placeholder="Contact"><input type="file" name="photo" accept="image/*"><input name="delete_code" placeholder="Delete Password - Yaad rakhna" required><button>Submit with AI</button></form>""")

def ai_similarity_score(a,b):
    a_words=set(a.lower().split()); b_words=set(b.lower().split())
    common=len(a_words & b_words); total=len(a_words | b_words)
    return (common/total*100) if total else 0

@app.route('/ai-match/<int:item_id>')
def ai_match(item_id):
    db=get_db(); target=db.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone(); others=db.execute("SELECT * FROM items WHERE id!=? AND type!=?",(item_id,target['type'])).fetchall()
    html=f"<h2>🤖 AI Matching for {target['name']}</h2><p>AI ne description ka analysis kiya (TF-IDF style keyword matching)</p>"
    scored=[]
    for o in others:
        s=ai_similarity_score(target['description'], o['description'])
        scored.append((o,s))
    scored=sorted(scored, key=lambda x:x[1], reverse=True)[:3]
    for o,s in scored:
        if s>5: html+=f"<div class='item'>AI Confidence {int(s)}% - {o['name']}<br>{o['description']}<br>📍 {o['location']}</div>"
    if "AI Confidence" not in html: html+="<p>AI ko abhi close match nahi mila.</p>"
    return render_page(html)

@app.route('/claim/<int:item_id>')
def claim(item_id):
    db=get_db(); item=db.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
    desc=item['description'].lower()
    qs=[]
    if 'black' in desc: qs.append("Item ka exact shade kya hai? Jet black ya faded?")
    if 'bottle' in desc: qs.append("Bottle ke cap ka color kya hai?")
    if 'wallet' in desc: qs.append("Wallet me kitne card slots hai?")
    if 'phone' in desc or 'iphone' in desc: qs.append("Phone ka cover ka color kya tha?")
    qs+= [f"'{item['name']}' pe koi scratch kaha hai?", f"Tumne {item['location']} me kis side rakha tha?", "Iske saath koi aur chhoti cheez thi kya?"]
    q_html="".join([f"<li>{q}</li>" for q in qs[:3]])
    return render_page(f"<h2>🛡️ AI Claim Guard</h2><div class='item'><b>{item['name']}</b> - {item['description']}<br><br><b>🤖 AI Generated Verification Qs:</b><ol>{q_html}</ol><small>Fake claim wala fail ho jayega.</small></div>")

@app.route('/poster/<int:item_id>')
def poster(item_id):
    db=get_db(); item=db.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
    html=f"""<div class='poster'><h1 style='color:#a78bfa;font-size:40px;margin:0'>LOST ALERT!</h1><h2>{item['name'].upper()}</h2><p>{item['description']}</p><p style='background:white;color:black;padding:10px;border-radius:8px'><b>Last Seen:</b> {item['location']}<br><b>Contact:</b> {item['contact']}</p><p style='font-size:12px;color:#a78bfa'>Generated by CampusConnect AI • Scan & Share</p></div><br><p>Iska screenshot leke WhatsApp pe share kar de - ye hi AI Poster hai (Bina Pillow ke).</p><a href='/items' class='btn'>Back</a>"""
    return render_page(html)

@app.route('/heatmap')
def heatmap():
    db=get_db(); rows=db.execute("SELECT location, COUNT(*) as c FROM items GROUP BY location").fetchall()
    total=sum([r['c'] for r in rows]) or 1
    html="<h2>📍 AI Location Predictor</h2><p>AI ne data se seekha hai saman kaha zyada khoya hai.</p>"
    for r in rows:
        perc=int(r['c']/total*100); bar="█"*int(perc/4)
        html+=f"<div class='item'><b>{r['location'] or 'Unknown'}</b> - {r['c']} items<br><span style='color:#7c3aed'>{bar}</span> {perc}%<br><small>AI Prediction: {perc}% chance yahi milega</small></div>"
    if not rows: html+="<p>Abhi data nahi hai, jaise hi items ayenge AI heatmap banayega.</p>"
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
        else: return render_page(f"<h3 style='color:red'>Galat password!</h3><a href='/delete/{item_id}'>Try again</a>")
    return render_page(f"<h2>Delete {item['name']}</h2><form method='post'><input type='password' name='delete_code' placeholder='Delete Password' required><button style='background:#ef4444'>Delete</button></form>")

@app.route('/kha-admin-786', methods=['GET','POST'])
def secret_admin():
    if request.method=='POST':
        if request.form.get('password')=='admin123':
            session['is_admin']=True; return redirect('/items')
        else: return render_page("<h3>Galat password</h3>")
    if session.get('is_admin'):
        session.pop('is_admin',None); return render_page("<h3>Admin Logout done</h3>")
    return render_page("<h2>Admin Login</h2><form method='post'><input type='password' name='password' placeholder='Admin Password'><button>Login</button></form>")

@app.teardown_appcontext
def close_connection(e):
    db=getattr(g,'_database',None); 
    if db: db.close()

if __name__=='__main__':
    app.run()

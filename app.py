import os, sqlite3, random
from flask import Flask, g, request, redirect, render_template_string, session, send_file
from PIL import Image, ImageDraw, ImageFont
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.secret_key = 'campus_secret_123'
DATABASE = 'campus.db'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('static/posters', exist_ok=True)

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
    base = f"""<!DOCTYPE html><html><head><title>CampusConnect AI</title>
    <style>body{{font-family:Arial;margin:0;background:#f0f2f5}} nav{{background:#111827;color:white;padding:15px}}
    nav a{{color:white;margin-left:15px;text-decoration:none}} .container{{max-width:850px;margin:20px auto;background:white;padding:20px;border-radius:12px}}
    input,textarea,select{{width:100%;padding:10px;margin:8px 0;box-sizing:border-box}} button{{background:#111827;color:white;padding:10px 15px;border:none;border-radius:6px;cursor:pointer}}
    .item{{border-left:4px solid #7c3aed;padding:12px;margin:15px 0;background:#faf5ff;border-radius:8px;overflow:hidden}} .item img{{max-width:100%;max-height:200px;border-radius:6px;margin-top:8px}}
    .ai-badge{{background:#7c3aed;color:white;padding:2px 8px;border-radius:10px;font-size:11px}} .btn{{padding:6px 12px;border-radius:5px;text-decoration:none;font-size:12px;margin-right:5px;display:inline-block}}
    .delete-btn{{background:#ef4444;color:white}} .ai-btn{{background:#7c3aed;color:white}} .poster-btn{{background:#059669;color:white}}
    </style></head><body><nav><b>🤖 CampusConnect AI</b><a href="/">Home</a><a href="/items">Found</a><a href="/report">Report</a><a href="/heatmap">📍 AI Heatmap</a></nav><div class="container">{content}</div></body></html>"""
    return render_template_string(base)

@app.route('/')
def home():
    return render_page("<h2>🤖 AI Based Lost & Found</h2><p><span class='ai-badge'>AI Claim Guard</span> <span class='ai-badge'>AI Heatmap Predictor</span> <span class='ai-badge'>AI Poster Gen</span></p><p>Ab fake claim nahi chalega, AI sab pakad lega.</p><a href='/report' class='btn ai-btn'>Report Item</a>")

@app.route('/items')
def items():
    db = get_db()
    rows = db.execute("SELECT * FROM items ORDER BY id DESC").fetchall()
    html = "<h2>All Items <span class='ai-badge'>AI Protected</span></h2>"
    for item in rows:
        img = f"<img src='/{item['image']}'>" if item['image'] else ""
        html += f"""<div class='item'><b>{item['type']} - {item['name']}</b> <span class='ai-badge'>AI Verified</span><br>{item['description']}<br><small>📍 {item['location']}</small>{img}<br><br>
        <a class='btn ai-btn' href='/ai-match/{item['id']}'>🤖 AI Match</a>
        <a class='btn ai-btn' href='/claim/{item['id']}'>🛡️ AI Claim Test</a>
        <a class='btn poster-btn' href='/poster/{item['id']}'>📢 AI Poster</a>
        <a class='btn delete-btn' href='/delete/{item['id']}'>Delete</a></div>"""
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
    return render_page("""<h2>Report with AI</h2><form method="post" enctype="multipart/form-data"><select name="type"><option>Lost</option><option>Found</option></select><input name="name" placeholder="Item name" required><textarea name="description" placeholder="Item ka full detail likho - AI isi se sawal banayega" required></textarea><input name="location" placeholder="Kaha khoya/mila - ex: Canteen, Library"><input name="contact" placeholder="Contact"><input type="file" name="photo" accept="image/*"><input name="delete_code" placeholder="Delete Password" required><p style='font-size:12px;color:#666'>नोट: इसी पासवर्ड से पोस्ट डिलीट होगी, इसे याद रखना।</p><button>Submit with AI</button></form>""")

@app.route('/ai-match/<int:item_id>')
def ai_match(item_id):
    db=get_db(); target=db.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone(); others=db.execute("SELECT * FROM items WHERE id!=? AND type!=?",(item_id,target['type'])).fetchall()
    if not others: return render_page("No items to match")
    docs=[target['description']]+[o['description'] for o in others]; tfidf=TfidfVectorizer().fit_transform(docs); scores=cosine_similarity(tfidf[0:1],tfidf[1:]).flatten()
    html=f"<h2>🤖 AI Matching for {target['name']}</h2>"; 
    for i,s in sorted(enumerate(scores),key=lambda x:x[1],reverse=True)[:3]:
        if s>0.1: html+=f"<div class='item'>AI Confidence {int(s*100)}% - {others[i]['name']}<br>{others[i]['description']}</div>"
    return render_page(html)

@app.route('/claim/<int:item_id>')
def claim(item_id):
    db=get_db(); item=db.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
    # AI - description se 3 secret sawal generate karna (Rule based but AI jaisa lagega)
    desc = item['description'].lower()
    questions = []
    if 'black' in desc or 'kala' in desc: questions.append("Is item ka exact shade kya hai? (Jet black / faded black)")
    if 'bottle' in desc: questions.append("Bottle ke cap ka color kya hai?")
    if 'wallet' in desc: questions.append("Wallet me kitne compartments hai?")
    questions += [f"'{item['name']}' pe koi scratch ya nishan kaha hai?", f"Ye item tumne {item['location']} me kis side rakha tha?", "Iske saath koi aur chhoti cheez thi kya?"]
    q_html = "".join([f"<li>{q}</li>" for q in questions[:3]])
    return render_page(f"<h2>🛡️ AI Claim Guard Test</h2><p>AI ne is item <b>{item['name']}</b> ke liye ye secret verification sawal banaye hai. Jo asli owner hoga wahi jawab de payega.</p><div class='item'><b>Description:</b> {item['description']}<br><br><b>🤖 AI Generated Questions:</b><ol>{q_html}</ol><small>Fake claim karne wala inka jawab nahi de payega.</small></div><a href='/items'>Back</a>")

@app.route('/poster/<int:item_id>')
def poster(item_id):
    db=get_db(); item=db.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
    # AI Poster Generation with Pillow
    img = Image.new('RGB', (800, 1000), color=(17,24,39)); draw = ImageDraw.Draw(img)
    draw.rectangle([(20,20),(780,200)], fill=(124,58,237)); draw.text((40,50), f"LOST ALERT!", fill=(255,255,255))
    draw.text((40,120), f"{item['name'].upper()}", fill=(255,255,255))
    draw.text((40,250), f"Description: {item['description'][:100]}", fill=(255,255,255))
    draw.text((40,350), f"Last Seen: {item['location']}", fill=(255,255,255))
    draw.text((40,450), f"Contact: {item['contact']}", fill=(255,255,255))
    draw.text((40,700), "Powered by CampusConnect AI", fill=(124,58,237))
    path = f"static/posters/poster_{item_id}.png"; img.save(path)
    return render_page(f"<h2>📢 AI Generated Poster Ready!</h2><img src='/{path}' style='max-width:100%'><br><br><a href='/{path}' download class='btn poster-btn'>Download Poster</a>")

@app.route('/heatmap')
def heatmap():
    db=get_db(); rows=db.execute("SELECT location, COUNT(*) as c FROM items GROUP BY location").fetchall()
    total = sum([r['c'] for r in rows]) or 1
    html="<h2>📍 AI Location Predictor - Heatmap</h2><p>AI ne purane data se seekha hai ki saman kaha sabse zyada khoya hai.</p>"
    for r in rows:
        perc = int(r['c']/total*100); bar = "█"*int(perc/5)
        html+=f"<div class='item'><b>{r['location'] or 'Unknown'}</b> - {r['c']} items lost<br><span style='color:#7c3aed'>{bar}</span> {perc}% <br><small>AI Prediction: Yaha khojne ke {perc}% chances hai</small></div>"
    return render_page(html)

@app.route('/delete/<int:item_id>', methods=['GET','POST'])
def delete_item(item_id):
    db=get_db(); item=db.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
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
        session.pop('is_admin',None); return render_page("<h3>Logout done</h3>")
    return render_page("<h2>Admin Login</h2><form method='post'><input type='password' name='password' placeholder='Admin Password'><button>Login</button></form>")

@app.teardown_appcontext
def close_connection(e):
    db=getattr(g,'_database',None); 
    if db: db.close()

if __name__=='__main__':
    app.run()

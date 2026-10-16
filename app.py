import os, sqlite3, csv, io
from flask import Flask, render_template_string, request, redirect, session, Response
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

os.makedirs('static/uploads', exist_ok=True)
app = Flask(__name__)
app.secret_key = 'clean-final-no-email-show'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

def get_db():
    conn = sqlite3.connect('savings.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT, is_admin INTEGER DEFAULT 0, sq TEXT, sa TEXT, group_name TEXT DEFAULT "MAIN")')
    conn.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, user_id INTEGER, week TEXT, amount INTEGER DEFAULT 200, status TEXT DEFAULT "pending", proof TEXT, created_at TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY, name TEXT, owner_email TEXT, fee_paid INTEGER DEFAULT 0, created_at TEXT)')
    if not conn.execute("SELECT * FROM users WHERE email='hm3516674@gmail.com'").fetchone():
        conn.execute("INSERT INTO users (name,email,password,is_admin,sq,sa) VALUES (?,?,?,?,?,?)",
        ('HARUNA MUSA','hm3516674@gmail.com',generate_password_hash('admin123'),'1','Best friend?','musa'))
    if not conn.execute("SELECT * FROM users WHERE email='admin'").fetchone():
        conn.execute("INSERT INTO users (name,email,password,is_admin,sq,sa) VALUES (?,?,?,?,?,?)",
        ('ADMIN','admin',generate_password_hash('admin123'),'1','Best friend?','musa'))
    conn.commit()
    conn.close()
init_db()

def get_friday():
    t=datetime.now(); d=4-t.weekday()
    if d<=0: d+=7
    return t+timedelta(days=d)

LOGIN = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Login</title><style>
*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui}body{background:linear-gradient(135deg,#eef2ff,#f0f9ff);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{width:100%;max-width:390px;background:white;border-radius:28px;overflow:hidden;box-shadow:0 15px 40px rgba(37,99,235,.15)}
.top{background:linear-gradient(135deg,#1d4ed8,#2563eb 45%,#06b6d4);padding:32px 26px;color:white;text-align:center}.top h1{font-size:24px;font-weight:800}.content{padding:22px}.f{position:relative;margin-bottom:13px}input{width:100%;padding:15px 14px 15px 46px;border:2px solid #e2e8f0;border-radius:14px;font-size:14px;font-weight:600}.ic{position:absolute;left:14px;top:50%;transform:translateY(-50%)}.btn{width:100%;padding:15px;border:0;border-radius:14px;font-weight:800;color:white}.g{background:linear-gradient(135deg,#16a34a,#22c55e)}.b{background:linear-gradient(135deg,#2563eb,#3b82f6);margin-top:12px}.err{background:#fef2f2;color:#dc2626;padding:10px;border-radius:10px;text-align:center;margin-bottom:12px;font-size:13px;font-weight:700}
</style></head><body><div class="card"><div class="top"><h1>TOGETHER WE RISE</h1><p>Sign in to continue</p></div><div class="content">{% if error %}<div class="err">{{error}}</div>{% endif %}<form method="POST"><div class="f"><div class="ic">✉️</div><input name="email" placeholder="Email" required></div><div class="f"><div class="ic">🔒</div><input name="password" type="password" placeholder="Password" required></div><div style="text-align:right;margin:6px 0 18px"><a href="/forgot" style="color:#2563eb;text-decoration:none;font-weight:800;font-size:12px">Forgot password?</a></div><button class="btn g">Sign In</button></form><a href="/register"><button class="btn b">Create account</button></a></div></div></body></html>"""

DASH = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dashboard</title><style>
*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui}body{background:#f6f8ff}.header{position:sticky;top:0;background:rgba(255,255,255,.9);backdrop-filter:blur(20px);border-bottom:1px solid #eef2ff;padding:14px 16px;display:flex;justify-content:space-between;align-items:center}
.wrap{max-width:480px;margin:0 auto;padding:14px}.hero{background:linear-gradient(135deg,#1e40af,#2563eb 45%,#06b6d4);color:white;border-radius:26px;padding:22px;box-shadow:0 18px 40px rgba(37,99,235,.3)}.stats{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}
.stat{background:white;border-radius:18px;padding:16px;box-shadow:0 6px 20px rgba(0,0,0,.05);border:1px solid #f1f5f9}.card{background:white;border-radius:20px;padding:18px;margin-top:14px;box-shadow:0 8px 26px rgba(0,0,0,.05);border:1px solid #f1f5f9}
.member{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid #f8fafc}.avatar{width:46px;height:46px;border-radius:14px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;display:grid;place-items:center;font-weight:900;position:relative}.avatar.paid::after{content:'✓';position:absolute;bottom:-4px;right:-4px;background:#22c55e;color:white;width:18px;height:18px;border-radius:50%;display:grid;place-items:center;font-size:11px;border:2px solid white}
.badge-paid{background:#dcfce7;color:#15803d;padding:4px 8px;border-radius:20px;font-size:10px;font-weight:800}.badge-pending{background:#fef3c7;color:#92400e;padding:4px 8px;border-radius:20px;font-size:10px;font-weight:800}.badge-none{background:#f1f5f9;color:#64748b;padding:4px 8px;border-radius:20px;font-size:10px;font-weight:800}
.btn{width:100%;padding:14px;border:0;border-radius:14px;font-weight:800;color:white;cursor:pointer}.input{width:100%;padding:13px;border:2px solid #e2e8f0;border-radius:12px;margin-bottom:10px;font-weight:600}.upload{border:2px dashed #cbd5e1;border-radius:14px;padding:18px;text-align:center;background:#f8fafc;cursor:pointer}.tx{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid #f8fafc}.tx img{width:48px;height:48px;border-radius:10px;object-fit:cover;border:1px solid #e2e8f0}
.success{background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:1px solid #bbf7d0;color:#15803d;padding:12px;border-radius:12px;margin-bottom:12px;font-weight:700;text-align:center}
.you-box{background:linear-gradient(135deg,#1e40af,#3b82f6);color:white;border-radius:18px;padding:16px;margin-top:14px;text-align:center}
.action-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}
.action-btn{padding:14px;border-radius:14px;border:0;font-weight:800;font-size:12px;cursor:pointer;color:white;text-decoration:none;text-align:center;display:block}
.wa-group{background:linear-gradient(135deg,#25D366,#128C7E);color:white;border-radius:18px;padding:16px;margin-top:14px;text-align:center}
</style></head><body>
<div class="header"><b>🚀 TOGETHER WE RISE</b><div><a href="/admin" style="background:#2563eb;color:white;padding:6px 12px;border-radius:20px;font-size:11px;font-weight:800;text-decoration:none">👑 ADMIN</a><a href="/logout" style="background:#f1f5f9;padding:6px 12px;border-radius:20px;font-size:11px;text-decoration:none;color:#333;margin-left:6px">Logout</a></div></div>
<div class="wrap">
{% if msg %}<div class="success">{{msg}}</div>{% endif %}

<div class="hero"><div style="font-size:11px;letter-spacing:1px;font-weight:800;opacity:.85">PALMPAY • 8084576491 • HARUNA MUSA</div><div style="font-size:22px;font-weight:900;margin:10px 0 4px">TOGETHER WE RISE</div><div style="font-size:12px;opacity:.9">70 Years Savings • Verified Account</div></div>

<div class="wa-group">
<div style="font-size:14px;font-weight:800">📱 OUR WHATSAPP GROUP</div>
<div style="font-size:12px;margin:6px 0">Join group for updates & reminders</div>
<a href="https://chat.whatsapp.com/FJ9Ok6Dds5A6EXngUM7Nam?s=cl&p=i&ilr=4&iam=0" target="_blank" style="display:block;background:white;color:#128C7E;padding:10px;border-radius:10px;font-weight:900;text-decoration:none;margin-top:8px">👉 Click to Join WhatsApp Group</a>
</div>

<div class="stats">
<div class="stat"><div style="font-size:11px;font-weight:800;color:#64748b">TOTAL SAVED</div><div style="font-size:26px;font-weight:900;margin-top:4px">₦{{total}}</div><div style="font-size:11px;color:#64748b;margin-top:4px">{{friday_count}} Fridays paid</div></div>
<div class="stat"><div style="font-size:11px;font-weight:800;color:#64748b">NEXT FRIDAY</div><div style="font-size:15px;font-weight:900;margin-top:4px">{{friday}}</div><div style="font-size:11px;color:#2563eb;font-weight:800;margin-top:4px">{{users|length}} members</div></div>
</div>

<div class="you-box">
<div style="font-size:12px;letter-spacing:1px;opacity:.9">YOU: {{my_name}}</div>
<div style="font-size:28px;font-weight:900;margin:8px 0">{{my_fridays}} Fridays Paid</div>
<div style="font-size:14px;font-weight:700">Total: ₦{{my_total}} • {{my_count}} transactions</div>
</div>

<div class="action-grid">
<a href="/export/excel" class="action-btn" style="background:linear-gradient(135deg,#16a34a,#22c55e)">📊 Excel Report</a>
<a href="/export/pdf" class="action-btn" style="background:linear-gradient(135deg,#dc2626,#ef4444)">📄 PDF Print</a>
<a href="https://wa.me/?text={{wa_text}}" target="_blank" class="action-btn" style="background:linear-gradient(135deg,#25D366,#128C7E)">💬 WhatsApp Reminder</a>
<a href="https://chat.whatsapp.com/FJ9Ok6Dds5A6EXngUM7Nam?s=cl&p=i&ilr=4&iam=0" target="_blank" class="action-btn" style="background:linear-gradient(135deg,#075E54,#25D366)">📱 Join Group</a>
</div>

{% if is_admin and pendings %}
<div class="card" style="background:linear-gradient(135deg,#fff7ed,#ffedd5);border:1px solid #fed7aa">
<h3>⚠️ {{pendings|length}} Proofs Need Approval</h3>
{% for p in pendings %}
<div style="background:white;border-radius:12px;padding:12px;margin-top:10px">
<div style="font-weight:800;font-size:13px">👤 {{p['name']}} • ₦{{p['amount']}} = {{p['amount']//200}} Fridays</div>
<div style="font-size:11px;color:#92400e">{{p['created_at']}}</div>
{% if p['proof'] %}<img src="/{{p['proof']}}" style="width:100%;max-height:200px;object-fit:contain;border-radius:10px;margin-top:8px;border:1px solid #eee">{% endif %}
<div style="display:flex;gap:8px;margin-top:10px">
<form method="POST" action="/approve" style="flex:1"><input type="hidden" name="id" value="{{p['id']}}"><button class="btn" style="background:#16a34a;padding:10px;font-size:11px">✅ Approve ₦{{p['amount']}} ({{p['amount']//200}}x)</button></form>
<form method="POST" action="/reject" style="flex:1"><input type="hidden" name="id" value="{{p['id']}}"><button class="btn" style="background:#ef4444;padding:10px;font-size:11px">❌ Reject</button></form>
</div>
</div>
{% endfor %}
</div>
{% endif %}

<div class="card"><h3>👥 Members</h3>
{% for u in users %}
<div class="member">
<div class="avatar {% if paid_status.get(u['id'])=='approved' %}paid{% endif %}">{{u['name'][0]}}</div>
<div style="flex:1"><div style="font-weight:800;font-size:13.5px">{{u['name']}} {% if u['is_admin'] %}👑{% endif %}</div><div style="font-size:11.5px;color:#64748b">₦{{user_totals.get(u['id'],0)}} • {{user_fridays.get(u['id'],0)}} Fridays</div></div>
<div>{% if paid_status.get(u['id'])=='approved' %}<span class="badge-paid">✅ PAID</span>{% elif paid_status.get(u['id'])=='pending' %}<span class="badge-pending">⏳ PENDING</span>{% else %}<span class="badge-none">NOT PAID</span>{% endif %}</div>
</div>
{% endfor %}
</div>

<div class="card">
<h3>💸 Pay Multiple Fridays</h3>
{% if is_admin %}
<form method="POST" action="/pay" enctype="multipart/form-data">
<select name="user_id" class="input" required>{% for u in users %}<option value="{{u['id']}}">{{u['name']}}</option>{% endfor %}</select>
{% else %}
<p style="font-size:12px;margin-bottom:8px;font-weight:700">Paying as: <b style="color:#2563eb">{{my_name}}</b></p>
<form method="POST" action="/pay" enctype="multipart/form-data">
<input type="hidden" name="user_id" value="{{my_id}}">
{% endif %}
<select name="amount" class="input" required>
<option value="200">1 Friday = ₦200</option>
<option value="400">2 Fridays = ₦400</option>
<option value="600">3 Fridays = ₦600</option>
<option value="800">4 Fridays = ₦800</option>
<option value="1000" selected>5 Fridays = ₦1000</option>
<option value="2000">10 Fridays = ₦2000</option>
<option value="4000">20 Fridays = ₦4000</option>
<option value="10000">50 Fridays = ₦10000</option>
</select>
<div class="upload" onclick="document.getElementById('proof').click()"><div style="font-size:28px">📸</div><div style="font-weight:800;font-size:13px" id="uploadText">Upload PalmPay Proof</div><input type="file" name="proof" id="proof" accept="image/*" required style="display:none" onchange="document.getElementById('uploadText').innerHTML='✅ '+this.files[0].name"></div>
<button class="btn" style="background:linear-gradient(135deg,#16a34a,#22c55e);margin-top:12px">📤 Submit Proof</button>
</form>
</div>

{% if recent %}
<div class="card"><h3>📜 History - 70 Years</h3>
{% for r in recent %}
<div class="tx">
{% if r['proof'] %}<img src="/{{r['proof']}}">{% else %}<div style="width:48px;height:48px;background:#f1f5f9;border-radius:10px;display:grid;place-items:center">📄</div>{% endif %}
<div style="flex:1"><div style="font-weight:800;font-size:13px">{{r['name']}} • ₦{{r['amount']}} ({{r['amount']//200}} Fridays)</div><div style="font-size:11px;color:#64748b">{{r['created_at']}} • {{r['status']|upper}}</div></div>
<div>{% if r['status']=='approved' %}✅{% else %}⏳{% endif %}</div>
</div>
{% endfor %}
</div>
{% endif %}
</div>
</body></html>
"""

@app.route('/')
def home():
    if 'uid' not in session: return redirect('/login')
    msg = request.args.get('msg')
    conn=get_db()
    users=conn.execute("SELECT * FROM users").fetchall()
    me=conn.execute("SELECT * FROM users WHERE id=?", (session['uid'],)).fetchone()
    pays=conn.execute("SELECT user_id, SUM(amount) as total, COUNT(*) as cnt FROM payments WHERE status='approved' GROUP BY user_id").fetchall()
    user_totals={r['user_id']:r['total'] for r in pays}
    user_fridays={r['user_id']:r['total']//200 for r in pays}
    total=sum(user_totals.values()) if user_totals else 0
    friday_count=total//200
    latest=conn.execute("SELECT user_id, status FROM payments WHERE id IN (SELECT MAX(id) FROM payments GROUP BY user_id)").fetchall()
    paid_status={r['user_id']:r['status'] for r in latest}
    pendings=[]
    if me['is_admin']:
        pendings=conn.execute("SELECT payments.*, users.name FROM payments JOIN users ON users.id=payments.user_id WHERE payments.status='pending' ORDER BY payments.id DESC").fetchall()
    recent=conn.execute("SELECT payments.*, users.name FROM payments JOIN users ON users.id=payments.user_id ORDER BY payments.id DESC LIMIT 15").fetchall()
    my_row=conn.execute("SELECT COUNT(*) as cnt, COALESCE(SUM(amount),0) as total FROM payments WHERE user_id=? AND status='approved'", (session['uid'],)).fetchone()
    my_count=my_row['cnt']; my_total=my_row['total']; my_fridays=my_total//200
    conn.close()
    f=get_friday()
    wa_text = f"🚨 TOGETHER WE RISE Payment Reminder! 🚨%0A%0APalmPay: 8084576491 HARUNA MUSA%0ATotal: ₦{total} ({friday_count} Fridays)%0A%0APay your ₦200 before {f.strftime('%A')}!%0AUpload proof on website.%0A%0AWhatsApp Group: https://chat.whatsapp.com/FJ9Ok6Dds5A6EXngUM7Nam"
    return render_template_string(DASH, users=users, total=total, friday_count=friday_count, user_totals=user_totals, user_fridays=user_fridays, paid_status=paid_status, pendings=pendings, recent=recent, friday=f.strftime('%A %d %B'), my_name=me['name'], my_id=me['id'], my_count=my_count, my_total=my_total, my_fridays=my_fridays, is_admin=me['is_admin'], msg=msg, wa_text=wa_text)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        e=request.form['email']; p=request.form['password']
        conn=get_db(); u=conn.execute("SELECT * FROM users WHERE email=? OR name=?", (e,e)).fetchone(); conn.close()
        if u and check_password_hash(u['password'], p):
            session['uid']=u['id']; return redirect('/')
        return render_template_string(LOGIN, error="Wrong email or password")
    return render_template_string(LOGIN, error=None)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        conn=get_db()
        try:
            conn.execute("INSERT INTO users (name,email,password,sq,sa,group_name) VALUES (?,?,?,?,?,?)",(request.form['name'],request.form['email'],generate_password_hash(request.form['password']),request.form['sq'],request.form['sa'].lower(),request.form.get('group_name','MAIN')))
            conn.commit(); conn.close(); return redirect('/login')
        except:
            conn.close(); return render_template_string(LOGIN, error="Email taken")
    return render_template_string("""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>*{box-sizing:border-box;font-family:system-ui}body{background:#eef2ff;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px}.card{background:white;max-width:400px;width:100%;border-radius:20px;padding:24px}input,select{width:100%;padding:13px;border:2px solid #e2e8f0;border-radius:10px;margin-bottom:10px}button{width:100%;padding:13px;background:#2563eb;color:white;border:0;border-radius:10px;font-weight:800}</style></head><body><div class="card"><h2 style="text-align:center">Create Account</h2><form method="POST"><input name="name" placeholder="Full Name" required><input name="email" placeholder="Email" required><input name="group_name" placeholder="Group Name" value="MAIN" required><input name="password" type="password" placeholder="Password" required><select name="sq" required><option value="">Security Question</option><option>Best friend?</option><option>Village?</option><option>Phone?</option></select><input name="sa" placeholder="Answer" required><button>Create</button></form><a href="/login" style="display:block;text-align:center;margin-top:12px">Back</a></div></body></html>""")

@app.route('/forgot', methods=['GET','POST'])
def forgot():
    if request.method=='GET':
        return render_template_string("""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>*{box-sizing:border-box;font-family:system-ui}body{background:#eef2ff;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px}.card{background:white;max-width:390px;width:100%;border-radius:20px;padding:24px}input{width:100%;padding:13px;border:2px solid #e2e8f0;border-radius:10px;margin-bottom:10px}button{width:100%;padding:13px;background:#16a34a;color:white;border:0;border-radius:10px;font-weight:800}</style></head><body><div class="card"><h2 style="text-align:center">Recover Password</h2><p style="font-size:12px;color:#64748b;text-align:center;margin-bottom:12px">Enter your email</p><form method="POST"><input name="email" placeholder="Email" required><button>Find Account</button></form><a href="/login" style="display:block;text-align:center;margin-top:12px">Back</a></div></body></html>""")
    e=request.form.get('email'); ans=request.form.get('answer'); new=request.form.get('newpass')
    conn=get_db(); u=conn.execute("SELECT * FROM users WHERE email=? OR name=?", (e,e)).fetchone()
    if not u: conn.close(); return "Account not found"
    if not ans:
        q=u['sq']; conn.close()
        return render_template_string(f"<div style='font-family:system-ui;max-width:390px;margin:50px auto;background:white;padding:24px;border-radius:20px'><h3>Recover Account</h3><p><b>Security Question: {q}</b></p><form method='POST'><input type='hidden' name='email' value='{e}'><input name='answer' placeholder='Your Answer' required style='width:100%;padding:13px;border:2px solid #e2e8f0;border-radius:10px;margin-bottom:10px'><input name='newpass' type='password' placeholder='New Password' required style='width:100%;padding:13px;border:2px solid #e2e8f0;border-radius:10px;margin-bottom:10px'><button style='width:100%;padding:13px;background:#16a34a;color:white;border:0;border-radius:10px;font-weight:800'>Reset Password</button></form></div>")
    if u['sa'].lower()==ans.lower():
        conn.execute("UPDATE users SET password=? WHERE id=?", (generate_password_hash(new), u['id'])); conn.commit(); conn.close()
        return redirect('/login')
    else:
        conn.close(); return "Wrong answer"

@app.route('/pay', methods=['POST'])
def pay():
    if 'uid' not in session: return redirect('/login')
    conn=get_db(); me=conn.execute("SELECT * FROM users WHERE id=?", (session['uid'],)).fetchone()
    requested_id = int(request.form['user_id'])
    if not me['is_admin'] and requested_id!= me['id']: requested_id = me['id']
    amount = int(request.form.get('amount', 200))
    file=request.files.get('proof'); proof_path=''
    if file and file.filename:
        filename=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secure_filename(file.filename)}"
        path=os.path.join(app.config['UPLOAD_FOLDER'], filename); file.save(path); proof_path=path
    conn.execute("INSERT INTO payments (user_id, week, amount, status, proof, created_at) VALUES (?,?,?,?,?,?)",(requested_id, datetime.now().strftime('%Y-%m-%d'), amount, 'pending', proof_path, datetime.now().strftime('%d %b %H:%M')))
    conn.commit(); conn.close()
    return redirect(f'/?msg=✅ Submitted ₦{amount} for {amount//200} Fridays!')

@app.route('/approve', methods=['POST'])
def approve():
    conn=get_db(); me=conn.execute("SELECT * FROM users WHERE id=?", (session.get('uid',0),)).fetchone()
    if not me or not me['is_admin']: conn.close(); return "Only admin"
    conn.execute("UPDATE payments SET status='approved' WHERE id=?", (request.form['id'],)); conn.commit(); conn.close()
    return redirect('/?msg=✅ Approved! Money added!')

@app.route('/reject', methods=['POST'])
def reject():
    conn=get_db(); conn.execute("UPDATE payments SET status='rejected' WHERE id=?", (request.form['id'],)); conn.commit(); conn.close()
    return redirect('/?msg=❌ Rejected')

@app.route('/export/excel')
def export_excel():
    conn=get_db()
    rows=conn.execute("SELECT users.name, users.email, payments.amount, payments.status, payments.created_at FROM payments JOIN users ON users.id=payments.user_id ORDER BY payments.id DESC").fetchall()
    conn.close()
    output=io.StringIO(); writer=csv.writer(output)
    writer.writerow(['Name','Email','Amount','Fridays','Status','Date'])
    for r in rows:
        writer.writerow([r['name'], r['email'], r['amount'], r['amount']//200, r['status'], r['created_at']])
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=weekly_report.csv'})

@app.route('/export/pdf')
def export_pdf():
    conn=get_db()
    rows=conn.execute("SELECT users.name, payments.amount, payments.status, payments.created_at FROM payments JOIN users ON users.id=payments.user_id WHERE payments.status='approved' ORDER BY payments.id DESC").fetchall()
    total=conn.execute("SELECT SUM(amount) FROM payments WHERE status='approved'").fetchone()[0] or 0
    conn.close()
    html=f"<html><head><style>body{{font-family:system-ui;padding:20px}}table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #ddd;padding:8px;font-size:12px}}th{{background:#2563eb;color:white}}.header{{background:#1e40af;color:white;padding:20px;border-radius:12px;text-align:center;margin-bottom:20px}}@media print{{.no-print{{display:none}}}}</style></head><body><div class='header'><h1>TOGETHER WE RISE - Weekly Report</h1><p>8084576491 HARUNA MUSA | Total: ₦{total} | {datetime.now().strftime('%d %B %Y')}</p><p>WhatsApp: https://chat.whatsapp.com/FJ9Ok6Dds5A6EXngUM7Nam</p></div><table><tr><th>#</th><th>Name</th><th>Amount</th><th>Fridays</th><th>Status</th><th>Date</th></tr>"
    for i,r in enumerate(rows,1):
        html+=f"<tr><td>{i}</td><td>{r['name']}</td><td>₦{r['amount']}</td><td>{r['amount']//200}</td><td>{r['status']}</td><td>{r['created_at']}</td></tr>"
    html+=f"</table><p><b>Total: ₦{total} = {total//200} Fridays</b></p><button class='no-print' onclick='window.print()' style='padding:12px 24px;background:#2563eb;color:white;border:0;border-radius:8px;font-weight:800'>🖨️ Print</button> <a href='/' class='no-print'>Back</a></body></html>"
    return html

@app.route('/admin')
def admin():
    conn=get_db(); me=conn.execute("SELECT * FROM users WHERE id=?", (session.get('uid',0),)).fetchone()
    if not me or not me['is_admin']: conn.close(); return "Only admin!"
    users=conn.execute("SELECT * FROM users").fetchall()
    pays=conn.execute("SELECT user_id, SUM(amount) as t FROM payments WHERE status='approved' GROUP BY user_id").fetchall()
    totals={r['user_id']:r['t'] for r in pays}
    conn.close()
    html=f"<div style='font-family:system-ui;padding:16px'><h2>👑 Admin Panel</h2><a href='/'>← Back</a> | <a href='/export/excel'>Excel</a> | <a href='/export/pdf'>PDF</a><br><br><table border=1 cellpadding=8 style='width:100%;border-collapse:collapse'><tr><th>Name</th><th>Email</th><th>Total</th><th>Fridays</th><th>Delete</th></tr>"
    for u in users:
        html+=f"<tr><td>{u['name']}</td><td>{u['email']}</td><td>₦{totals.get(u['id'],0)}</td><td>{totals.get(u['id'],0)//200}</td><td><form method='POST' action='/admin/delete'><input type='hidden' name='id' value='{u['id']}'><button style='background:#ef4444;color:white;border:0;padding:6px 10px;border-radius:6px'>Delete</button></form></td></tr>"
    html+="</table></div>"
    return html

@app.route('/admin/delete', methods=['POST'])
def adel():
    conn=get_db(); conn.execute("DELETE FROM users WHERE id=?",(int(request.form['id']),)); conn.execute("DELETE FROM payments WHERE user_id=?",(int(request.form['id']),)); conn.commit(); conn.close(); return redirect('/admin')

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

if __name__=='__main__':
    print("=== CLEAN FINAL - NO EMAIL SHOW ===")
    print("Admin: hm3516674@gmail.com / admin123 still works, but NOT shown!")
    print("Login shows only Email + Password")
    print("Recover shows only Email")
    print("http://127.0.0.1:5001")
    app.run(host='0.0.0.0', debug=True, port=5001)
#!/usr/bin/env python3
"""Halaxy Clinic local web app. Uses only Python's standard library and SQLite."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
import sqlite3, json, hashlib, secrets, os, mimetypes, threading
from datetime import date, datetime

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "clinic_data"
DB_PATH = DATA_DIR / "halaxy.db"
HOST, PORT = "127.0.0.1", 8000
SESSIONS = {}
LOCK = threading.Lock()

def db():
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def pw_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 180000).hex()
    return salt + "$" + digest

def verify_pw(password, stored):
    try:
        salt, digest = stored.split("$", 1)
        return secrets.compare_digest(pw_hash(password, salt).split("$",1)[1], digest)
    except Exception:
        return False

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
          email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
          role TEXT NOT NULL CHECK(role IN ('doctor','patient')), phone TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS appointments(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          patient_id INTEGER NOT NULL REFERENCES users(id),
          doctor_id INTEGER NOT NULL REFERENCES users(id),
          date TEXT NOT NULL, time TEXT NOT NULL, reason TEXT DEFAULT '',
          status TEXT NOT NULL DEFAULT 'Pending'
        );
        CREATE TABLE IF NOT EXISTS payments(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          patient_id INTEGER NOT NULL REFERENCES users(id),
          amount REAL NOT NULL, method TEXT NOT NULL, date TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'Paid'
        );
        CREATE TABLE IF NOT EXISTS settings(
          id INTEGER PRIMARY KEY CHECK(id=1), name TEXT NOT NULL,
          email TEXT NOT NULL, phone TEXT NOT NULL, address TEXT NOT NULL
        );
        """)
        if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            c.execute("INSERT INTO users(name,email,password_hash,role,phone) VALUES(?,?,?,?,?)",
                      ("Dr Sarah Smith","doctor@halaxy.com",pw_hash("password"),"doctor","0123456789"))
            c.execute("INSERT INTO users(name,email,password_hash,role,phone) VALUES(?,?,?,?,?)",
                      ("John Patient","patient@halaxy.com",pw_hash("password"),"patient","0712345678"))
            doc = c.execute("SELECT id FROM users WHERE email='doctor@halaxy.com'").fetchone()[0]
            pat = c.execute("SELECT id FROM users WHERE email='patient@halaxy.com'").fetchone()[0]
            from datetime import timedelta
            c.execute("INSERT INTO appointments(patient_id,doctor_id,date,time,reason,status) VALUES(?,?,?,?,?,?)",
                      (pat,doc,(date.today()+timedelta(days=2)).isoformat(),"10:00","General checkup","Pending"))
            c.execute("INSERT INTO appointments(patient_id,doctor_id,date,time,reason,status) VALUES(?,?,?,?,?,?)",
                      (pat,doc,(date.today()+timedelta(days=5)).isoformat(),"14:00","Follow-up consultation","Approved"))
            c.execute("INSERT INTO payments(patient_id,amount,method,date,status) VALUES(?,?,?,?,?)",
                      (pat,500,"Cash",date.today().isoformat(),"Paid"))
            c.execute("INSERT INTO payments(patient_id,amount,method,date,status) VALUES(?,?,?,?,?)",
                      (pat,350,"Card",(date.today()).isoformat(),"Paid"))
        if not c.execute("SELECT 1 FROM settings WHERE id=1").fetchone():
            c.execute("INSERT INTO settings VALUES(1,?,?,?,?)",
                      ("Halaxy Clinic","info@halaxyclinic.com","+27 12 345 6789","123 Health Street, Wellness City"))

def asdict(row):
    return dict(row) if row else None

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def send_json(self, obj, status=200, headers=None):
        raw=json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(raw)))
        self.send_header("Cache-Control","no-store")
        if headers:
            for k,v in headers.items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(raw)

    def body(self):
        n=int(self.headers.get("Content-Length","0") or 0)
        if n>1_000_000: raise ValueError("Request too large")
        return json.loads(self.rfile.read(n) or b"{}")

    def current_user(self):
        token=self.headers.get("Cookie","")
        token=next((x.split("=",1)[1] for x in token.split("; ") if x.startswith("halaxy_session=")),None)
        uid=SESSIONS.get(token)
        if not uid: return None
        with db() as c: return asdict(c.execute("SELECT id,name,email,role,phone FROM users WHERE id=?",(uid,)).fetchone())

    def require_user(self):
        u=self.current_user()
        if not u: self.send_json({"error":"Please log in."},401); return None
        return u

    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/api/me":
            return self.send_json({"user":self.current_user()})
        if path=="/api/data":
            u=self.require_user()
            if not u: return
            with db() as c:
                if u["role"]=="doctor":
                    apps=c.execute("""SELECT a.*,p.name patient_name,d.name doctor_name FROM appointments a
                        JOIN users p ON p.id=a.patient_id JOIN users d ON d.id=a.doctor_id
                        WHERE a.doctor_id=? ORDER BY a.date,a.time""",(u["id"],)).fetchall()
                    pats=c.execute("""SELECT DISTINCT p.id,p.name,p.email,p.phone FROM users p
                        JOIN appointments a ON a.patient_id=p.id WHERE a.doctor_id=? ORDER BY p.name""",(u["id"],)).fetchall()
                    pays=c.execute("""SELECT x.*,p.name patient_name FROM payments x JOIN users p ON p.id=x.patient_id ORDER BY x.date DESC""").fetchall()
                else:
                    apps=c.execute("""SELECT a.*,p.name patient_name,d.name doctor_name FROM appointments a
                        JOIN users p ON p.id=a.patient_id JOIN users d ON d.id=a.doctor_id
                        WHERE a.patient_id=? ORDER BY a.date,a.time""",(u["id"],)).fetchall()
                    pats=[]
                    pays=c.execute("""SELECT x.*,p.name patient_name FROM payments x JOIN users p ON p.id=x.patient_id
                        WHERE x.patient_id=? ORDER BY x.date DESC""",(u["id"],)).fetchall()
                doctors=c.execute("SELECT id,name FROM users WHERE role='doctor' ORDER BY name").fetchall()
                settings=asdict(c.execute("SELECT name,email,phone,address FROM settings WHERE id=1").fetchone())
            return self.send_json({"appointments":[asdict(x) for x in apps],"patients":[asdict(x) for x in pats],
                                   "payments":[asdict(x) for x in pays],"doctors":[asdict(x) for x in doctors],"settings":settings})
        if path=="/api/export":
            u=self.require_user()
            if not u: return
            with db() as c:
                data={t:[asdict(r) for r in c.execute("SELECT * FROM "+t)] for t in ("users","appointments","payments","settings")}
                for person in data["users"]: person.pop("password_hash", None)
            return self.send_json(data,headers={"Content-Disposition":'attachment; filename="halaxy-backup.json"'})
        if path=="/" or path=="/index.html":
            file=ROOT/"index.html"
        else:
            file=ROOT/path.lstrip("/")
        if not file.exists() or not file.is_file() or ROOT not in file.resolve().parents and file.resolve()!=ROOT/"index.html":
            self.send_error(404); return
        raw=file.read_bytes(); typ=mimetypes.guess_type(str(file))[0] or "application/octet-stream"
        self.send_response(200); self.send_header("Content-Type",typ+"; charset=utf-8" if typ.startswith("text/") else typ)
        self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)

    def do_POST(self):
        path=urlparse(self.path).path
        try: data=self.body()
        except Exception as e: return self.send_json({"error":str(e)},400)
        if path=="/api/register":
            name=str(data.get("name","")).strip(); email=str(data.get("email","")).strip().lower()
            password=str(data.get("password","")); role=data.get("role","patient"); phone=str(data.get("phone",""))
            if not name or "@" not in email or len(password)<6 or role not in ("patient","doctor"):
                return self.send_json({"error":"Enter a name, valid email, password of at least 6 characters and account type."},400)
            try:
                with db() as c:
                    cur=c.execute("INSERT INTO users(name,email,password_hash,role,phone) VALUES(?,?,?,?,?)",
                                  (name,email,pw_hash(password),role,phone))
                    uid=cur.lastrowid
            except sqlite3.IntegrityError: return self.send_json({"error":"An account with that email already exists."},409)
            return self.login_user(uid)
        if path=="/api/login":
            email=str(data.get("email","")).strip().lower(); password=str(data.get("password",""))
            with db() as c: row=c.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
            if not row or not verify_pw(password,row["password_hash"]): return self.send_json({"error":"Invalid email or password."},401)
            return self.login_user(row["id"])
        u=self.require_user()
        if not u: return
        if path=="/api/appointments":
            if u["role"]!="patient": return self.send_json({"error":"Only patients can create bookings."},403)
            doctor_id=data.get("doctor_id"); day=str(data.get("date","")); tm=str(data.get("time",""))
            try: datetime.strptime(day,"%Y-%m-%d"); datetime.strptime(tm,"%H:%M")
            except ValueError: return self.send_json({"error":"Choose a valid date and time."},400)
            if day<date.today().isoformat(): return self.send_json({"error":"Please choose a future date."},400)
            with db() as c:
                if not c.execute("SELECT 1 FROM users WHERE id=? AND role='doctor'",(doctor_id,)).fetchone():
                    return self.send_json({"error":"Please select a valid doctor."},400)
                c.execute("INSERT INTO appointments(patient_id,doctor_id,date,time,reason,status) VALUES(?,?,?,?,?,'Pending')",
                          (u["id"],doctor_id,day,tm,str(data.get("reason",""))))
            return self.send_json({"ok":True})
        return self.send_json({"error":"Not found"},404)

    def login_user(self, uid):
        token=secrets.token_urlsafe(32); SESSIONS[token]=uid
        with db() as c: u=asdict(c.execute("SELECT id,name,email,role,phone FROM users WHERE id=?",(uid,)).fetchone())
        return self.send_json({"user":u},headers={"Set-Cookie":f"halaxy_session={token}; HttpOnly; SameSite=Lax; Path=/"})

    def do_PATCH(self):
        path=urlparse(self.path).path
        u=self.require_user()
        if not u: return
        try: data=self.body()
        except Exception as e: return self.send_json({"error":str(e)},400)
        if path.startswith("/api/appointments/"):
            try: aid=int(path.rsplit("/",1)[1])
            except: return self.send_json({"error":"Invalid appointment."},400)
            status=data.get("status")
            if status not in ("Approved","Completed","Cancelled"): return self.send_json({"error":"Invalid status."},400)
            with db() as c:
                ap=c.execute("SELECT * FROM appointments WHERE id=?",(aid,)).fetchone()
                if not ap: return self.send_json({"error":"Appointment not found."},404)
                if (u["role"]=="doctor" and ap["doctor_id"]!=u["id"]) or (u["role"]=="patient" and (ap["patient_id"]!=u["id"] or status!="Cancelled")):
                    return self.send_json({"error":"You cannot change this appointment."},403)
                c.execute("UPDATE appointments SET status=? WHERE id=?",(status,aid))
            return self.send_json({"ok":True})
        return self.send_json({"error":"Not found"},404)

    def do_PUT(self):
        path=urlparse(self.path).path
        u=self.require_user()
        if not u: return
        try: data=self.body()
        except Exception as e: return self.send_json({"error":str(e)},400)
        if path=="/api/settings":
            if u["role"]!="doctor": return self.send_json({"error":"Only doctors can update clinic details."},403)
            vals=[str(data.get(k,"")).strip() for k in ("name","email","phone","address")]
            if not vals[0] or "@" not in vals[1]: return self.send_json({"error":"Enter a clinic name and valid email."},400)
            with db() as c: c.execute("UPDATE settings SET name=?,email=?,phone=?,address=? WHERE id=1",vals)
            return self.send_json({"ok":True})
        return self.send_json({"error":"Not found"},404)

    def do_DELETE(self):
        path=urlparse(self.path).path
        if path=="/api/logout":
            token=self.headers.get("Cookie","")
            token=next((x.split("=",1)[1] for x in token.split("; ") if x.startswith("halaxy_session=")),None)
            if token: SESSIONS.pop(token,None)
            return self.send_json({"ok":True},headers={"Set-Cookie":"halaxy_session=; Max-Age=0; HttpOnly; SameSite=Lax; Path=/"})
        return self.send_json({"error":"Not found"},404)

if __name__=="__main__":
    init_db()
    print("\\nHalaxy Clinic is running at http://127.0.0.1:8000")
    print("Database file:", DB_PATH)
    print("Press Ctrl+C to stop the server.\\n")
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()

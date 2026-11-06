import os
import csv
import io
import json
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, request, redirect, url_for, session, flash,
    render_template_string, make_response, abort
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "exam_portal.db")
DURATION_MINUTES = int(os.getenv("EXAM_DURATION_MINUTES", "30"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-this-password")
SECRET_KEY = os.getenv("SECRET_KEY", "replace-this-with-a-long-random-secret")

app = Flask(__name__)
app.secret_key = SECRET_KEY

QUESTIONS = [
    {"q": "What is computational thinking?",
     "o": ["Writing stories", "Logical problem-solving approach", "Drawing pictures", "Playing games"], "a": 1},
    {"q": "Which are the four characteristics of computational thinking?",
     "o": ["Input, Output, Storage, Processing", "Reading, Writing, Listening, Speaking",
           "Decomposition, Pattern Recognition, Abstraction, Algorithm Design",
           "Hardware, Software, Network, Internet"], "a": 2},
    {"q": "Which flowchart symbol represents a decision?",
     "o": ["Oval", "Rectangle", "Diamond", "Parallelogram"], "a": 2},
    {"q": "Which of the following is a Python data type?",
     "o": ["int", "float", "str", "All of the above"], "a": 3},
    {"q": "What is the purpose of input()?",
     "o": ["Display output", "Receive user data", "Delete data", "Stop the program"], "a": 1},
    {"q": "Which is a logical operator in Python?",
     "o": ["+", "==", "and", ">"], "a": 2},
    {"q": "What is a Boolean expression?",
     "o": ["Returns a number", "Returns True or False", "Returns a string", "Returns a list"], "a": 1},
    {"q": "Which statements are used for decision-making?",
     "o": ["for and while", "break and continue", "if, if-else, if-elif-else", "print and input"], "a": 2},
    {"q": "Which is used as a ternary operator in Python?",
     "o": ["+", "if-else expression", "//", "%"], "a": 1},
    {"q": "Which loop is generally used when iterations are known?",
     "o": ["while loop", "for loop", "if statement", "break statement"], "a": 1},
    {"q": "What is an infinite loop?",
     "o": ["A loop that runs once", "A loop that never executes",
           "A loop that runs continuously", "A loop that runs twice"], "a": 2},
    {"q": "Which statement terminates a loop immediately?",
     "o": ["continue", "break", "pass", "print"], "a": 1},
    {"q": "What is operator precedence?",
     "o": ["Order of evaluating operators", "Stopping a program",
           "Accepting input", "Creating a list"], "a": 0},
    {"q": "What is string concatenation?",
     "o": ["Deleting strings", "Comparing strings", "Joining strings", "Reversing strings"], "a": 2},
    {"q": "What is the use of len()?",
     "o": ["Find length", "Convert string", "Delete list", "Sort list"], "a": 0},
    {"q": "Which method converts a string into uppercase?",
     "o": ["lower()", "upper()", "len()", "split()"], "a": 1},
    {"q": "Which brackets are used to create a list?",
     "o": ["()", "{}", "[]", "<>"], "a": 2},
    {"q": "Which statement about Python lists is correct?",
     "o": ["Lists are immutable", "Lists are ordered and mutable",
           "Lists do not allow duplicates", "Lists store only integers"], "a": 1},
    {"q": "Which method adds an element at the end of a list?",
     "o": ["extend()", "insert()", "append()", "remove()"], "a": 2},
    {"q": "Which method inserts an element at a specific position?",
     "o": ["append()", "extend()", "insert()", "pop()"], "a": 2},
]

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT NOT NULL UNIQUE,
                student_name TEXT NOT NULL,
                started_at TEXT NOT NULL,
                deadline TEXT NOT NULL,
                answers TEXT NOT NULL DEFAULT '{}',
                submitted_at TEXT,
                score INTEGER,
                total INTEGER NOT NULL
            )
        """)

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper

def current_attempt():
    attempt_id = session.get("attempt_id")
    if not attempt_id:
        return None
    with db() as con:
        return con.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()

def parse_dt(value):
    return datetime.fromisoformat(value)

def finish_attempt(attempt):
    answers = json.loads(attempt["answers"] or "{}")
    score = sum(1 for i, q in enumerate(QUESTIONS)
                if str(answers.get(str(i), "")) == str(q["a"]))
    with db() as con:
        con.execute("""
            UPDATE attempts SET submitted_at=?, score=? WHERE id=? AND submitted_at IS NULL
        """, (datetime.now().isoformat(timespec="seconds"), score, attempt["id"]))

BASE = """
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} | Ashoka Online Exam</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3f6fb;color:#172033;font-family:Arial,sans-serif}
header{background:#17365d;color:white;padding:18px 5%;display:flex;justify-content:space-between;align-items:center;gap:12px}
header small{display:block;opacity:.85;margin-top:4px}.wrap{max-width:980px;margin:28px auto;padding:0 16px}
.card{background:white;border-radius:14px;padding:24px;box-shadow:0 5px 22px #152b4612;margin-bottom:18px}
h1,h2,h3{margin-top:0}.muted{color:#64748b}.btn{display:inline-block;border:0;border-radius:8px;background:#1769aa;color:white;padding:11px 17px;text-decoration:none;cursor:pointer;font-size:15px}
.btn.secondary{background:#64748b}.btn.danger{background:#b42318}.field{width:100%;padding:12px;border:1px solid #cbd5e1;border-radius:8px;margin:7px 0 16px;font-size:16px}
label{font-weight:600}.option{display:block;padding:13px;border:1px solid #dbe3ee;border-radius:9px;margin:10px 0;cursor:pointer;font-weight:400}
.option input{margin-right:10px}.row{display:flex;gap:12px;flex-wrap:wrap;align-items:center;justify-content:space-between}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.stat{background:#eef4fb;padding:16px;border-radius:10px}.stat b{display:block;font-size:25px;margin-top:5px}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:11px;border-bottom:1px solid #e5eaf1}th{background:#f8fafc}
.timer{font-weight:bold;color:#b42318;font-size:20px}.flash{background:#fff4e5;padding:12px;border-radius:8px;margin-bottom:12px}
@media(max-width:600px){.card{padding:18px}header{align-items:flex-start;flex-direction:column}}
</style></head><body>
<header><div><strong>ASHOKA ONLINE EXAM PORTAL</strong><small>Programming for Problem Solving using Python</small></div>
<div>{{ header_right|safe }}</div></header><main class="wrap">
{% with messages = get_flashed_messages() %}{% for m in messages %}<div class="flash">{{m}}</div>{% endfor %}{% endwith %}
{{ body|safe }}</main></body></html>
"""

def page(title, body, header_right=""):
    return render_template_string(BASE, title=title, body=body, header_right=header_right)

@app.route("/")
def home():
    body = """
    <section class="card">
      <h1>Online Examination</h1>
      <p class="muted">Students can log in with their name and roll number. Faculty can access the result dashboard.</p>
      <div class="row">
        <a class="btn" href="/student">Student Login</a>
        <a class="btn secondary" href="/admin/login">Faculty Login</a>
      </div>
    </section>
    <section class="card"><h3>Examination details</h3>
      <p>20 multiple-choice questions · 20 marks · """ + str(DURATION_MINUTES) + """ minutes</p>
      <p class="muted">Submit your answers before the timer ends. Only one attempt is permitted per roll number.</p>
    </section>"""
    return page("Home", body)

@app.route("/student", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll = request.form.get("roll", "").strip().upper()
        if not name or not roll:
            flash("Enter both student name and roll number.")
            return redirect(url_for("student_login"))
        with db() as con:
            existing = con.execute("SELECT * FROM attempts WHERE roll_no=?", (roll,)).fetchone()
            if existing:
                if existing["submitted_at"]:
                    flash("An examination attempt is already submitted for this roll number.")
                    return redirect(url_for("student_login"))
                session["attempt_id"] = existing["id"]
                return redirect(url_for("exam"))
            now = datetime.now()
            cur = con.execute("""
                INSERT INTO attempts (roll_no,student_name,started_at,deadline,answers,total)
                VALUES (?,?,?,?,?,?)
            """, (roll, name, now.isoformat(timespec="seconds"),
                  (now + timedelta(minutes=DURATION_MINUTES)).isoformat(timespec="seconds"),
                  "{}", len(QUESTIONS)))
            session["attempt_id"] = cur.lastrowid
        return redirect(url_for("exam"))
    body = """
    <section class="card"><h2>Student Login</h2>
    <form method="post">
      <label>Student Name</label><input class="field" name="name" required maxlength="100">
      <label>Roll Number</label><input class="field" name="roll" required maxlength="30">
      <button class="btn" type="submit">Start Examination</button>
    </form></section>"""
    return page("Student Login", body)

@app.route("/exam")
def exam():
    attempt = current_attempt()
    if not attempt:
        return redirect(url_for("student_login"))
    if attempt["submitted_at"]:
        return redirect(url_for("result"))
    deadline = parse_dt(attempt["deadline"])
    remaining = max(0, int((deadline - datetime.now()).total_seconds()))
    if remaining <= 0:
        finish_attempt(attempt)
        return redirect(url_for("result"))
    answers = json.loads(attempt["answers"] or "{}")
    safe_questions = [{"q": q["q"], "o": q["o"]} for q in QUESTIONS]
    body = """
    <section class="card">
      <div class="row"><div><h2>Python Online Examination</h2>
      <p class="muted">{{name}} · {{roll}}</p></div>
      <div class="timer">Time left: <span id="timer"></span></div></div>
      <p class="muted">Select one answer for each question. Your answers are saved as you move between questions.</p>
      <div class="row"><span id="progress">Question 1 of {{total}}</span><span id="saved" class="muted">Ready</span></div>
      <div style="height:8px;background:#e5eaf1;border-radius:10px;margin:10px 0 22px"><div id="bar" style="height:8px;background:#1769aa;width:5%;border-radius:10px"></div></div>
      <div id="question"></div>
      <div class="row" style="margin-top:20px">
        <button class="btn secondary" id="prev" type="button">Previous</button>
        <button class="btn" id="next" type="button">Next</button>
        <button class="btn danger" id="submit" type="button">Submit Exam</button>
      </div>
    </section>
    <section class="card"><h3>Question navigation</h3><div id="nav" class="row"></div></section>
    <script>
    const questions = {{questions|tojson}};
    let answers = {{answers|tojson}};
    let current = 0;
    let remaining = {{remaining}};
    const questionBox=document.getElementById('question');
    const nav=document.getElementById('nav');
    function render(){
      const q=questions[current];
      document.getElementById('progress').textContent=`Question ${current+1} of ${questions.length}`;
      document.getElementById('bar').style.width=((current+1)/questions.length*100)+'%';
      questionBox.innerHTML='<h3>'+(current+1)+'. '+q.q+'</h3>'+q.o.map((o,i)=>
        `<label class="option"><input type="radio" name="answer" value="${i}" ${String(answers[current])===String(i)?'checked':''}> ${String.fromCharCode(65+i)}. ${o}</label>`
      ).join('');
      questionBox.querySelectorAll('input').forEach(el=>el.addEventListener('change',()=>{
        answers[current]=Number(el.value); saveAnswer(current, Number(el.value));
      }));
      document.getElementById('prev').disabled=current===0;
      document.getElementById('next').textContent=current===questions.length-1?'Last Question':'Next';
      nav.innerHTML=questions.map((_,i)=>`<button type="button" class="btn ${answers[i]===undefined?'secondary':''}" style="padding:8px 12px;margin:3px" data-i="${i}">${i+1}</button>`).join('');
      nav.querySelectorAll('button').forEach(b=>b.onclick=()=>{current=Number(b.dataset.i);render()});
    }
    async function saveAnswer(index,value){
      document.getElementById('saved').textContent='Saving...';
      const r=await fetch('/save-answer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:index,answer:value})});
      document.getElementById('saved').textContent=r.ok?'All changes saved':'Save failed - check connection';
    }
    document.getElementById('prev').onclick=()=>{if(current>0){current--;render()}};
    document.getElementById('next').onclick=()=>{if(current<questions.length-1){current++;render()}};
    async function submitExam(auto=false){
      if(!auto && !confirm('Are you sure you want to submit the examination?')) return;
      document.getElementById('submit').disabled=true;
      await fetch('/submit',{method:'POST'});
      window.location='/result';
    }
    document.getElementById('submit').onclick=()=>submitExam(false);
    function tick(){
      const m=Math.floor(remaining/60),s=remaining%60;
      document.getElementById('timer').textContent=String(m).padStart(2,'0')+':'+String(s).padStart(2,'0');
      if(remaining<=0){submitExam(true);return}
      remaining--;setTimeout(tick,1000);
    }
    render();tick();
    </script>"""
    rendered = render_template_string(body, name=attempt["student_name"], roll=attempt["roll_no"],
        total=len(QUESTIONS), questions=safe_questions, answers=answers, remaining=remaining)
    return page("Examination", rendered, '<a style="color:white" href="/logout">Exit</a>')

@app.route("/save-answer", methods=["POST"])
def save_answer():
    attempt = current_attempt()
    if not attempt or attempt["submitted_at"]:
        abort(403)
    if datetime.now() >= parse_dt(attempt["deadline"]):
        finish_attempt(attempt)
        abort(403)
    data = request.get_json(silent=True) or {}
    try:
        index, answer = int(data["index"]), int(data["answer"])
    except (KeyError, TypeError, ValueError):
        abort(400)
    if not 0 <= index < len(QUESTIONS) or not 0 <= answer < len(QUESTIONS[index]["o"]):
        abort(400)
    answers = json.loads(attempt["answers"] or "{}")
    answers[str(index)] = answer
    with db() as con:
        con.execute("UPDATE attempts SET answers=? WHERE id=?", (json.dumps(answers), attempt["id"]))
    return {"saved": True}

@app.route("/submit", methods=["POST"])
def submit():
    attempt = current_attempt()
    if not attempt:
        abort(403)
    if not attempt["submitted_at"]:
        finish_attempt(attempt)
    return {"submitted": True}

@app.route("/result")
def result():
    attempt = current_attempt()
    if not attempt:
        return redirect(url_for("student_login"))
    if not attempt["submitted_at"]:
        return redirect(url_for("exam"))
    score = attempt["score"] or 0
    pct = score / len(QUESTIONS) * 100
    body = f"""
    <section class="card"><h2>Examination Submitted</h2>
    <p>Student: <b>{attempt['student_name']}</b></p>
    <p>Roll Number: <b>{attempt['roll_no']}</b></p>
    <div class="grid">
      <div class="stat">Marks Scored<b>{score}/{len(QUESTIONS)}</b></div>
      <div class="stat">Percentage<b>{pct:.1f}%</b></div>
      <div class="stat">Result<b>{'PASS' if pct >= 40 else 'FAIL'}</b></div>
    </div><p class="muted">Your response has been recorded. Contact faculty for any clarification.</p>
    <a class="btn" href="/">Home</a></section>"""
    return page("Result", body)

@app.route("/logout")
def logout():
    session.pop("attempt_id", None)
    return redirect(url_for("home"))

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("dashboard"))
        flash("Incorrect faculty password.")
    body = """
    <section class="card"><h2>Faculty Login</h2>
    <form method="post"><label>Admin Password</label>
    <input class="field" type="password" name="password" required>
    <button class="btn" type="submit">Login</button></form></section>"""
    return page("Faculty Login", body)

@app.route("/admin")
@admin_required
def dashboard():
    with db() as con:
        rows = con.execute("SELECT * FROM attempts ORDER BY started_at DESC").fetchall()
    submitted = [r for r in rows if r["submitted_at"]]
    avg = (sum(r["score"] or 0 for r in submitted) / len(submitted)) if submitted else 0
    passed = sum(1 for r in submitted if (r["score"] or 0) >= len(QUESTIONS)*0.4)
    table_rows = []
    for r in rows:
        status = "Submitted" if r["submitted_at"] else "In progress"
        marks = f"{r['score']}/{r['total']}" if r["submitted_at"] else "—"
        percentage = f"{(r['score'] or 0)/r['total']*100:.1f}%" if r["submitted_at"] else "—"
        table_rows.append(
            f"<tr><td>{r['student_name']}</td><td>{r['roll_no']}</td>"
            f"<td>{status}</td><td>{marks}</td><td>{percentage}</td></tr>"
        )
    table = "".join(table_rows)
    body = f"""
    <section class="card"><div class="row"><h2>Faculty Dashboard</h2>
    <a class="btn" href="/admin/export">Download CSV</a></div>
    <div class="grid">
      <div class="stat">Registered attempts<b>{len(rows)}</b></div>
      <div class="stat">Submitted<b>{len(submitted)}</b></div>
      <div class="stat">Class average<b>{avg:.1f}/{len(QUESTIONS)}</b></div>
      <div class="stat">Pass percentage<b>{(passed/len(submitted)*100 if submitted else 0):.1f}%</b></div>
    </div></section>
    <section class="card"><h3>Student Results</h3>
    <div style="overflow-x:auto"><table><thead><tr><th>Name</th><th>Roll Number</th><th>Status</th><th>Marks</th><th>Percentage</th></tr></thead>
    <tbody>{table or '<tr><td colspan="5">No student attempts yet.</td></tr>'}</tbody></table></div></section>
    <p><a class="btn secondary" href="/admin/logout">Faculty Logout</a></p>"""
    return page("Faculty Dashboard", body)

@app.route("/admin/export")
@admin_required
def export_csv():
    with db() as con:
        rows = con.execute("SELECT student_name,roll_no,started_at,submitted_at,score,total FROM attempts ORDER BY started_at").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student Name", "Roll Number", "Started At", "Submitted At", "Score", "Total", "Percentage", "Status"])
    for r in rows:
        score = r["score"]
        writer.writerow([r["student_name"], r["roll_no"], r["started_at"], r["submitted_at"],
                         score if score is not None else "", r["total"],
                         round(score/r["total"]*100, 2) if score is not None else "",
                         "Submitted" if r["submitted_at"] else "In progress"])
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=python_exam_results.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)

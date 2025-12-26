from flask import Flask, request, render_template, redirect, url_for, session, make_response
import sqlite3
from groq import Groq

# Рождественская история

app = Flask(__name__)
app.secret_key = "super_secret_key"  

client = Groq(api_key="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")
DB_PATH = "chat.db"
DB_PATH2 = "data.db"
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn2 = sqlite3.connect(DB_PATH2)
    cur = conn.cursor()
    cur2 = conn2.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,password TEXT,email TEXT,type TEXT,
            age INTEGER,weight INTEGER,height INTEGER,target TEXT,program TEXT,food TEXT)
    """)
    cur2.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,description TEXT)
    """)
    conn.commit()
    conn.close()

init_db()
def show_programs():
    conn2 = sqlite3.connect(DB_PATH2)
    cur2 = conn2.cursor()
    programs = cur2.execute("SELECT * FROM exercises").fetchall()
    conn2.close()
    return programs
def save_user(name, password, email, place, age, weight, height, target,program,food):
    global conn, cur
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (name, password, email, type, age, weight, height, target,program,food)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, password, email, place, age, weight, height, target,program,food))
    conn.commit()
    conn.close()
def set_program(name, description):
    conn2 = sqlite3.connect(DB_PATH2)
    cur2 = conn2.cursor()
    cur2.execute(
        "INSERT INTO exercises (name, description) VALUES (?, ?)",
        (name, description)
    )
    conn2.commit()
    conn2.close()

@app.route("/", methods=["GET", "POST"])
def index():
    # Получаем куки
    u, e = request.cookies.get("username"), request.cookies.get("email")

    # Автологин по cookies
    if u and e:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            user = cur.execute(
                "SELECT * FROM users WHERE name=? AND email=?",
                (u, e)
            ).fetchone()

        if user:
            session["name"] = user[1]
            session["program"] = user[9]
            session["food"] = user[10]
            return redirect(url_for("home"))

    # Если POST — берем данные из формы
    if request.method == "POST":
        username = request.form.get("user-name")
        email = request.form.get("user-email")
        password = request.form.get("user-password")

        session["name"] = username
        session["email"] = email
        session["password"] = password

        print("SESSION EMAIL:", session["email"], 
              "SESSION NAME:", session["name"], 
              "SESSION PASSWORD:", session["password"])
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        exists = cur.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not exists:
            save_user(username, password, email, "", 0, 0, 0, "", "", "")
            print(f"NEW USER SAVED: {username}, {password}, {email}")
        conn.close()
        # Сохраняем куки
        resp = make_response(redirect(url_for("categories")))
        resp.set_cookie("username", username, max_age=604800)  # 7 дней
        resp.set_cookie("email", email, max_age=604800)
        return resp
        # Сохраняем пользователя в БД только если его там ещё нет
        

    # GET — показываем форму
    return render_template("auth.html")

@app.route("/categories", methods=["GET", "POST"])
def categories():
    if request.method == "POST":
        session["type"] = request.form.get("place")
        session["age"] = request.form.get("age")
        session["weight"] = request.form.get("weight")
        session["height"] = request.form.get("height")
        session["target"] = request.form.get("goal")
        return redirect(url_for("chat"))

    return render_template("categories.html")


@app.route("/chat")
def chat():
    if "name" not in session:
        return redirect(url_for("index"))

    prompt = f"""
    Створи персональну программу тренувань на 7 днів.

    Ім'я: {session['name']}
    Вік: {session['age']}
    Вага: {session['weight']} кг
    Рост: {session['height']} см
    Де тренується: {session['type']}
    Ціль: {session['target']}

    Вимоги:
    - найбільша ефективність
    - різноманітність вправ
    - вправи, підходи, повтори
    - рекомендації по відпочинку
    - враховуй ціль
    І на українській мові.Пиши чітко і ЩОБ НЕ БУЛО ПОМИЛОК У НАПИСАННІ А ТАКОЖ МАКСИМАЛЬНА ЕФЕКТИВНІСТЬ
    """
    prompt2 = f"""
        Створи режим харчування з варіантами вибору на кожен прийом їжі.
        Вага: {session['weight']} кг
        Рост: {session['height']} см
        Ціль: {session['target']}
        Вимоги:
        - збалансованість
        - різноманітність страв
        - враховуй ціль
        І на українській мові.Пиши чітко і ЩОБ НЕ БУЛО ПОМИЛОК У НАПИСАННІ А ТАКОЖ МАКСИМАЛЬНА ЕФЕКТИВНІСТЬ
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Ти — профессиональный фітнес-тренер ИИ."},
            {"role": "user", "content": prompt},
        ]
    )
    response2 = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Ти — професійний дієтолог ИИ."},
            {"role": "user", "content": prompt2},
        ]
    )

    program = response.choices[0].message.content
    food = response2.choices[0].message.content

    session["program"] = program
    session["food"] = food

    # Сохраняем только программу и питание в базу без создания нового пользователя
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET program = ?, food = ? WHERE name = ?",
        (program, food, session["name"])
    )
    result = cur.execute(
        "SELECT * FROM users WHERE name = ?",
        (session["name"],)
    ).fetchone()
    print("UPDATED USER:", result)
    conn.commit()
    conn.close()
    
    print(f"Program and food saved for {session['name']},{session['password']},{session['email']}")
    return render_template("chat.html", program=program)

@app.route("/save_program", methods=["POST"])
def save_program():
    if "name" not in session:
        return {"status": "error"}, 403

    data = request.get_json()
    program = data.get("program")

    session["program"] = program

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET program = ? WHERE name = ?",
        (program, session["name"])
    )
    conn.commit()
    conn.close()

    return {"status": "ok"}

@app.route("/program",methods=["GET", "POST"])
def program():
    return render_template("my_program.html", program=session.get("program"))
@app.route("/home")
def home():
    return render_template("home_page.html", program=session.get("program"), food=session.get("food"))
@app.route("/profile", methods=["GET", "POST"])
def profile():
    return render_template("profile.html", name=session["name"])
@app.route("/food", methods=["GET", "POST"])
def food():
    return render_template("my_food.html", eat=session.get("food"))
@app.route("/exersices", methods=["GET","POST"])
def sport():
    print(show_programs())
    content = show_programs()
    return f"""
<meta name=viewport content="width=device-width,initial-scale=1">
<style>
body{{margin:0;padding:20px;background:#000;color:#fff;font-family:system-ui}}

.card{{background:#111;padding:16px;border-radius:14px;margin-bottom:16px}}
h2{{margin:0 0 8px;font-size:18px}}
p{{margin:0 0 12px;color:#ccc}}
button{{background:#5c6cff;border:0;color:#fff;padding:10px 14px;border-radius:10px;cursor:pointer}}
</style>
<button onclick='window.location.href="/tasks"' style='background-color:gold; color:red;'>Техніка до вправ</button>
<button onclick='window.location.href="/home"' style='background-color:red; position:absolute; right:0; color:white;'>На головну</button>

<div class="exercise" onclick="window.location.href='/create'" id="add_program" style="position:fixed;right:24px;bottom:24px;width:40px;height:40px;border-radius:50%;background:#2ecc71;color:#fff;display:flex;align-items:center;justify-content:center;font-size:36px;font-weight:600;box-shadow:0 10px 25px rgba(0,0,0,.35);cursor:pointer;">+</div>

{''.join(f"<div class=card><h2>{i[1] or 'Без назви'}</h2><p>{i[2]}</p><button onclick=\"saveProgram('{i[2].replace(chr(39), chr(92)+chr(39))}', this)\">Зробити моєю програмою</button></div>" for i in content)}
<script>
function saveProgram(program, button) {{
    fetch('/save_program', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{program: program}})
    }}).then(r => r.json()).then(data => {{
        if(data.status === 'ok') {{
            button.textContent = 'Збережено!';
            button.disabled = true;
            setTimeout(() => window.location.href = '/home', 1000);
        }}
    }});
}}
</script>
"""
@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    return render_template("index.html")
@app.route("/delete_account", methods=["POST"])
def delete_account():
    if "name" not in session:
        return redirect(url_for("index"))

    name = session["name"]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM users WHERE name = ?",
        (name,)
    )
    conn.commit()
    conn.close()

    session.clear()

    resp = make_response(redirect(url_for("index")))
    resp.set_cookie("username", "", expires=0)
    resp.set_cookie("email", "", expires=0)

    return resp
@app.route("/enter", methods=["GET", "POST"])
def enter():
    if request.method == "POST":
        session["password"] = request.form.get("user-password")
        session["email"] = request.form.get("user-email")

        email = session["email"]
        password = session["password"]
        print("EMAIL:", email)
        print("PASSWORD:", password)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        result = cur.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()

        print(result)

        conn.close()
        print(result)

        if result:
            session["name"] = result[1]
            session["password"] = result[2]
            session["email"] = result[3]
            session["program"] = result[9]
            print(session["program"])
            program = session["program"]
            return redirect(url_for("home"))
        else:
            return render_template("enter.html", error="Неправильний email або пароль")

    return render_template("enter.html")
@app.route("/save", methods=["POST"])
def save():
    program = request.form.get("subtitle")
    print("PROGRAM:", program)

    session["program"] = program

    return redirect(url_for("home"))
@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        set_program(name, description)
        print(f"NEW PROGRAM SAVED: {name}, {description}")
        return redirect(url_for("sport"))
    return render_template("create.html")

if __name__ == "__main__":
   app.run(debug=True, port=5000)

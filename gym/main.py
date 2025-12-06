from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3
from groq import Groq

# Рождественская история

app = Flask(__name__)
app.secret_key = "super_secret_key"  

client = Groq(api_key="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")
DB_PATH = "chat.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            password TEXT,
            email TEXT,
            type TEXT,
            age INTEGER,
            weight INTEGER,
            height INTEGER,
            target TEXT,
            program TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


def save_user(name, password, email, place, age, weight, height, target,program):
    global conn, cur
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (name, password, email, type, age, weight, height, target,program)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, password, email, place, age, weight, height, target,program))
    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        session["name"] = request.form.get("user-name")
        session["password"] = request.form.get("user-password")
        session["email"] = request.form.get("user-email")

        return redirect(url_for('categories'))

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
    І на українській мові.Пиши чітко і без помилок
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
        І на українській мові.Пиши чітко і без помилок
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
            {"role": "system", "content": "Ти — профессиональный дієтолог ИИ."},
            {"role": "user", "content": prompt2},
        ]
    )
    session["program"] = response.choices[0].message.content
    session["food"] = response2.choices[0].message.content

    session["food"] = food
    save_user(session["name"],session["password"],session["email"],session["type"],session["age"],session["weight"],session["height"],session["target"],program)
    return render_template("chat.html", program=program)

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
    return render_template("index.html")

@app.route("/enter", methods=["GET", "POST"])
def enter():
    if request.method == "POST":
        session["password"] = request.form.get("user-password")
        session["email"] = request.form.get("user-email")

        email = session["email"]
        password = session["password"]

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        result = cur.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()

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


if __name__ == "__main__":
   app.run(debug=True, port=5000)

from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3
from groq import Groq

app = Flask(__name__)
app.secret_key = "super_secret_key"   # для session

client = Groq(api_key="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")
DB_PATH = "chat.db"


# --------- БАЗА ДАННЫХ ---------
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
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (name, password, email, type, age, weight, height, target,program)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, password, email, place, age, weight, height, target,program))
    conn.commit()
    conn.close()


# --------- Роуты ---------
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

        # сохраняем в БД
        
        return redirect(url_for("chat"))

    return render_template("categories.html")


@app.route("/chat")
def chat():
    # если пользователь зашел напрямую — отправляем на начало
    if "name" not in session:
        return redirect(url_for("index"))

    prompt = f"""
    Составь персональную программу тренировок на 7 дней.

    Имя: {session['name']}
    Возраст: {session['age']}
    Вес: {session['weight']} кг
    Рост: {session['height']} см
    Где тренируется: {session['type']}
    Цель: {session['target']}

    Требования:
    - расписание на 7 дней
    - упражнения, подходы, повторы
    - рекомендации по отдыху
    - советы по питанию
    - учитывай цель
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Ты — профессиональный фитнес-тренер ИИ."},
            {"role": "user", "content": prompt}
        ]
    )

    # Берём текст из ответа
    program = response.choices[0].message.content
    save_user(
        session["name"],
        session["password"],
        session["email"],
        session["type"],
        session["age"],
        session["weight"],
        session["height"],
        session["target"],
        program
    )


    return render_template("chat.html", program=program)
@app.route("/program",methods=["GET", "POST"])
def program():
    global program
    print(program)
    return render_template("my_program.html", program=program)
@app.route("/home")
def home():
    return render_template("home_page.html")
if __name__ == "__main__":
    app.run(debug=True, port=5000)

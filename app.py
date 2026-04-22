from flask import render_template as rt,Flask

app = Flask(__name__)

@app.route("/")
def home():
    return rt('home.html')

@app.route("/login")
def login():
    return rt('login.html')

@app.route("/register")
def register():
    return rt('register.html')

@app.route("/gegevens")
def metingen():
    return rt('home.html')

app.run()
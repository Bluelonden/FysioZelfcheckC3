from flask import Flask, render_template as rt

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

app.run()
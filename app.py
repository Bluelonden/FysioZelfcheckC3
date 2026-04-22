
from flask import render_template as rt, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from main import app
from forms import LoginForm, RegisterForm
from models import db, User

@app.route("/")
def home():
    return rt('home.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'GET' and current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if form.validate_on_submit():
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                flash('Welkom terug! Je bent nu ingelogd.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Ongeldige gebruikersnaam of wachtwoord.', 'danger')
                return redirect(url_for('login'))

    return rt('login.html', form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if request.method == 'GET':
        return rt("register.html", form=form)

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if form.validate_on_submit():
            check_user = User.query.filter_by(username=username).first()
            check_email = User.query.filter_by(email=email).first()

            if check_user:
                flash("Deze gebruikersnaam is al bezet!", "danger")
                return redirect(url_for("register"))

            if check_email:
                flash("Dit e-mailadres is al in gebruik!", "danger")
                return redirect(url_for("register"))

            new_user = User(username=username, email=email, role=role)
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            flash("Account succesvol aangemaakt!", "success")
            return redirect(url_for('login'))

    return rt("register.html", form=form)


@app.route("/dashboard")
@login_required
def dashboard():
    return rt("dashboard.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/gegevens")
def metingen():
    return rt("home.html")
from flask import Flask, render_template as rt, session, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from forms import LoginForm, RegisterForm 
from models import db, migrate, login_manager, User
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import os

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'vervang-dit-door-een-echte-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'website.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)

login_manager.login_view = "login" # type: ignore
login_manager.login_message_category = "info"

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return rt('home.html')

@app.route("/login", methods=['GET', 'POST']) 
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is not None and user.check_password(form.password.data):
            login_user(user)
            flash('Welkom terug! Je bent nu ingelogd.', 'success')
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('home')
            
            return redirect(next_page)
        else:
            flash('Ongeldige gebruikersnaam of wachtwoord.', 'danger')
            
    return rt("login.html", form=form)

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        check_user = User.query.filter_by(username=form.username.data).first()
        check_email = User.query.filter_by(email=form.email.data).first()

        if check_user:
            flash("Deze gebruikersnaam is al bezet!", "danger")
            return rt("register.html", form=form)
        
        if check_email:
            flash("Dit e-mailadres is al in gebruik!", "danger")
            return rt("register.html", form=form)

        new_user = User(
            email=form.email.data, # type: ignore
            username=form.username.data, # type: ignore
            password_hash=generate_password_hash(form.password.data) # type: ignore
        )
        
        db.session.add(new_user)
        db.session.commit()
        flash("Account succesvol aangemaakt! Je kunt nu inloggen.", "success")
        return redirect(url_for('login'))
        
    return rt("register.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Je bent nu uitgelogd.', 'info')
    return redirect(url_for('home'))

@app.route("/dashboard")
@login_required
def dashboard():
    return rt("dashboard.html", name=current_user.username)

if __name__ == '__main__':
    app.run(debug=True)
    

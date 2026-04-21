from flask import Flask, render_template as rt, session, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from forms import LoginForm, RegisterForm
from models import db, migrate, login_manager, User, exists
from dotenv import load_dotenv
import requests
import os

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
# app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') # WERKT NIET ZONDER .ENV 
app.config['SECRET_KEY'] = 'mijngeheimesleutel' # TEST KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'website.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TMDB_API_KEY'] = os.getenv('TMDB_API_KEY')

db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
login_manager.login_view = "login"

with app.app_context():
    if not exists():
        db.create_all()

@app.route("/")
def home():
   return rt('home.html')

@app.route("/login", methods=['GET', 'POST']) 
def login():
    # check of iemand al is ingelogd
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    form = LoginForm()
    
    # check of het formulier is verzonden en valide is
    if form.validate_on_submit():
        # hier wordt 'user' gedefinieerd
        user = User.query.filter_by(username=form.username.data).first()
        
        # nu kunnen we 'user' pas controleren
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
    # if request.method == 'GET':
    #     return rt('register.html')

    # elif request.method == 'POST':
    #     username = request.form['username']
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

        # maak een nieuwe gebruiker aan
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        # gebruik de set_password methode om het wachtwoord te hashen voor opslag
        new_user.set_password(form.password.data)
        
        db.session.add(new_user)
        db.session.commit()
        flash("Account succesvol aangemaakt!", "success")
        return redirect(url_for('login'))
        
    return rt("register.html", form=form)

@app.route("/dashboard")
@login_required
def dashboard():
    return rt("dashboard.html", name=current_user.username) # pas deze html redirect aan als het moet 

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template as rt, session, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from forms import LoginForm, RegisterForm
from models import db, migrate, login_manager, User, exists
from dotenv import load_dotenv
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
    form = LoginForm()

    # check of iemand al is ingelogd
    if request.method == 'GET':
        if current_user.is_authenticated:
            return rt('dashboard.html', form=form)
    
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # check of het formulier is verzonden en valide is
        if form.validate_on_submit():
            # hier wordt 'user' gedefinieerd
            user = User.query.filter_by(username=username).first()

            # check user password
            if user is not None and user.check_password(password):
                login_user(user)
                flash('Welkom terug! Je bent nu ingelogd.', 'success')
                return redirect(url_for('dashboard', form=form))
            # zoniet, terug naar login pagina
            else:
                flash('Ongeldige gebruikersnaam of wachtwoord.', 'danger')
                return redirect(url_for('login', form=form))

                """next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('dashboard', form=form) """
                
        
    return rt('login.html', form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if request.method == 'GET':
        return rt("register.html", form=form)

    elif request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if form.validate_on_submit():
            check_user = User.query.filter_by(username=username).first()
            check_email = User.query.filter_by(email=email).first()

            if check_user:
                flash("Deze gebruikersnaam is al bezet!", "danger")
                return redirect(url_for("register", form=form))
            
            if check_email:
                flash("Dit e-mailadres is al in gebruik!", "danger")
                return redirect(url_for("register", form=form))
            
            # check of username al bestaat en zoniet maak een nieuwe gebruiker aan
            if not check_user and not check_email:
                new_user = User(
                    username=username, # was form.username.data
                    email=email,
                    role=role
                    )
            
                # gebruik de set_password methode om het wachtwoord te hashen voor opslag
                new_user.set_password(password)
                
                db.session.add(new_user)
                db.session.commit()
                flash("Account succesvol aangemaakt!", "success")
            
            return redirect(url_for('login', form=form))
        

@app.route("/dashboard")
@login_required
def dashboard():
    return rt("dashboard.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
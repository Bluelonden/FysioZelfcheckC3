
from flask import render_template as rt, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from main import app
from forms import LoginForm, RegisterForm, WaardesForm
from models import db, User, Waardes
from config import DREMPELWAARDES

@app.route("/")
def home():
    return rt('home.html')

## GET = rt('route.html')
## POST = redirect(url_for('route'))

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'GET':
        if current_user.is_authenticated:
            return rt('dashboard.html')
        else:
            return rt('login.html', form=form)

    if request.method == 'POST':
        username = form.username.data
        password = form.password.data

        if form.validate_on_submit():
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                flash('Welkom terug! Je bent nu ingelogd.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Ongeldige gebruikersnaam of wachtwoord.', 'danger')
                return redirect(url_for('login'))


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if request.method == 'POST':
        username = form.username.data
        email = form.email.data
        password = form.password.data
        role = form.role.data
        waardes = None

        if form.validate_on_submit():
            check_user = User.query.filter_by(username=username).first()
            check_email = User.query.filter_by(email=email).first()

            if check_user:
                flash("Deze gebruikersnaam is al bezet!", "danger")
                return redirect(url_for("register"))

            if check_email:
                flash("Dit e-mailadres is al in gebruik!", "danger")
                return redirect(url_for("register"))

            new_user = User(username=username, email=email, role=role, waardes=waardes)
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            flash("Account succesvol aangemaakt!", "success")
            return redirect(url_for('login'))
    
    return rt('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    return rt('dashboard.html')

@app.route('/results')
@login_required
def results():
    user = current_user
    niveau = user.waardes.niveau
    score = user.waardes.score
    drempels = DREMPELWAARDES[niveau]

    return rt('results.html', niveau=niveau,
              score=score, drempels=drempels)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/vragenlijst", methods=['GET', 'POST'])
@login_required
def vragenlijst():
    form = WaardesForm()
    
    if request.method == 'GET':

        if current_user.waardes:
            flash('Formulier is al eerder ingevuld!', 'danger')
            return redirect(url_for('results'))
        else:
            return rt('vragenlijst.html', form=form)

    if request.method == 'POST' and form.validate_on_submit():
        try:    
            leeftijd = form.leeftijd.data
            diagnose = form.diagnose.data
            rookt = form.rookt.data
            dag = form.dag.data
            nacht = form.nacht.data
            saba = form.saba.data
            beperking = form.beperking.data
            hospital = form.hospital.data
            prednison = form.prednison.data
            exacerbaties = form.exacerbaties.data

            data = Waardes(leeftijd=leeftijd, diagnose=diagnose, rookt=rookt,
                            dag=dag, nacht=nacht, saba=saba, beperking=beperking,
                            hospital=hospital, prednison=prednison,
                            exacerbaties=exacerbaties, user=current_user)
            
            data.score_niveau()
            
            db.session.add(data)
            db.session.commit()

            flash("Data succesvol opgeslagen!", "success")
            return redirect(url_for('results'))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Er is een fout opgetreden: {str(e)}", "danger")
    
    return rt("vragenlijst.html", form=form)

if __name__ == "__main__":
    app.run()
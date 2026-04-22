from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import DataRequired, EqualTo, Email, ValidationError 

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    # dit ding kijkt of er al een gebruiker is met dezelfde gebruikersnaam en geeft dus een foutcode terug ipv een irritante jinja error
    def validate_username(self, username):
        from models import User # Import HIER binnenin zetten
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Deze gebruikersnaam is al bezet. Kies een andere.')

    def validate_email(self, email):
        from models import User # ik zat vast in een loop, bleek dat dit de oplossing was volgens een forum (de import in de functie zetten)
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Dit e-mailadres is al in gebruik.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])    
    password = PasswordField("Wachtwoord", render_kw={"Placeholder":"Wachtwoord"})
    submit = SubmitField("Inloggen", render_kw={"class":"btn btn-primary"})
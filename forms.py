from flask_wtf import FlaskForm as FF
from wtforms import (StringField as StrF, PasswordField as PassF, SubmitField,
                     EmailField as MailF, SelectField, IntegerField,RadioField,BooleanField)
from wtforms.validators import DataRequired, Length, NumberRange


class LoginForm(FF):
    username = StrF('Username',
                    validators=[DataRequired()])
    password = PassF('Wachtwoord',
                     validators=[DataRequired()])
    submit = SubmitField('Login')


class RegisterForm(FF):
    username = StrF('Username',
                    validators=[DataRequired()])
    email = MailF('Email',
                  validators=[DataRequired()])
    password = PassF('Wachtwoord',
                     validators=[DataRequired(),
                                 Length(min=8)])
    role = SelectField('Role',
                choices=[('patient', 'Patient'), ('arts', 'Arts')],
                validators=[DataRequired()])
    submit = SubmitField('Registreren')

class Drempelwaardes(FF):
    leeftijd = IntegerField("Wat is uw leeftijd?", validators=[DataRequired(), NumberRange(min=0, max=120)])
    diagnose = SelectField("Wat is uw Diagnose?", choices=[("astma","Astma"),("copd","COPD"),("beide","Beide"),("onbekend","Onbekend")])
    rookt = RadioField("Rookt u?", choices=[("ja","Ja"), ("nee","Nee")], default="nee")

    symptoom_dag = BooleanField("Ik heb vaker dan 2x per week dagelijkse klachten")
    symptoom_nacht = BooleanField("Ik word regelmatig s'nachts wakker met ademhalingsproblemen")
    symptoom_saba = BooleanField("Ik gebruik mijn SABA(nood-inhaler) meer dan 2x per week")
    symptoom_beperking = BooleanField("Ik beperk mijn dagelijkse activeit vanwege mijn ademhaling")

    hospitalisatie = BooleanField("Bent u de afgelopen 12 maanden gehospitaliseerd?")
    prednison_gebruik = BooleanField("Heeft u in de afgelopen 12 maanden prednison gebruikt?")
    exacerbaties = RadioField("Aantal exacerbaties afgelopen 12 maanden", choices=[("0","0"),("1","1"),("2+","≥2")], default="0")
    submit = SubmitField("Opslaan en berekenen")
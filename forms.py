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
    rookt = BooleanField("Rookt u?")

    symptoom_dag = BooleanField("Heeft u vaker dan 2x per week dagelijkse klachten?")
    symptoom_nacht = BooleanField("Wordt u regelmatig s'nachts wakker met ademhalingsproblemen")
    symptoom_saba = BooleanField("Gebruikt u uw SABA (nood-inhaler) meer dan 2x per week")
    symptoom_beperking = BooleanField("Bent u beperkt in uw dagelijkse activiteiten door uw ademhaling?")

    exacerbaties = RadioField("Aantal exacerbaties afgelopen 12 maanden", choices=[("0","0"),("1","1"),("2+","≥2")], default="0")
    hospitalisatie = BooleanField("Bent u de afgelopen maanden gehospitaliseerd?")
    prednison_gebruik = BooleanField("Heeft u in de afgelopen 12 maanden prednison gebruikt?")
    submit = SubmitField("Opslaan en berekenen")
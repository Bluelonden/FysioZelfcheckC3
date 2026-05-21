from flask_wtf import FlaskForm as FF
from wtforms import (StringField as StrF, PasswordField as PassF, SubmitField as SubF,
                     EmailField as MailF, SelectField as SelF, IntegerField as IntF,
                     RadioField as RadF, BooleanField as BoolF)
from wtforms.validators import DataRequired, Length, NumberRange


class LoginForm(FF):
    username = StrF('Username',
                    validators=[DataRequired()])
    password = PassF('Wachtwoord',
                     validators=[DataRequired()])
    submit = SubF('Login')


class RegisterForm(FF):
    username = StrF('Username',
                    validators=[DataRequired()])
    email = MailF('Email',
                  validators=[DataRequired()])
    password = PassF('Wachtwoord',
                     validators=[DataRequired(),
                                 Length(min=8)])
    role = SelF('Role',
                choices=[('patient', 'Patient'), ('arts', 'Arts')],
                validators=[DataRequired()])
    submit = SubF('Registreren')

class WaardesForm(FF):
    leeftijd = IntF("Wat is uw leeftijd?",
                    validators=[DataRequired(), 
                                NumberRange(min=0, max=120)])
    diagnose = SelF("Wat is uw Diagnose?",
                    choices=[("astma","Astma"),("copd","COPD"),
                             ("beide","Beide"),("onbekend","Onbekend")])
    rookt = BoolF("Rookt u?")
    dag = BoolF("Ik heb vaker dan 2x per week dagelijkse klachten")
    nacht = BoolF("Ik word regelmatig s'nachts wakker met ademhalingsproblemen")
    saba = BoolF("Ik gebruik mijn SABA(nood-inhaler) meer dan 2x per week")
    beperking = BoolF("Ik beperk mijn dagelijkse activeit vanwege mijn ademhaling")
    hospital = BoolF("Ik ben in de afgelopen 12 maanden vanwegen mijn ziekte/symptomen in het ziekenhuis opgenomen geweest")
    prednison = BoolF("Ik heb in de afgelopen 12 maanden prednison gebruikt")
    exacerbaties = RadF("Aantal exacerbaties afgelopen 12 maanden", 
                        choices=[(0, "0"), (1, "1"), (2, "≥2")], 
                        coerce=int,  # Zorgt voor automatische conversie naar int
                        default=0)   # Int in plaats van string
    submit = SubF("Opslaan en berekenen")
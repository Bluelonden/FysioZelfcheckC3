from flask_wtf import FlaskForm as FF
from wtforms import (StringField as StrF, PasswordField as PassF, SubmitField as SubF,
                     EmailField as MailF, SelectField as SelF, IntegerField as IntF,
                     RadioField as RadF, BooleanField as BoolF)
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField as QSF
from models import db, User


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
    
    def validate_email(self, field):
        """controleert of email al in gebruik is"""
        # zoek op ingevuld email in db en geef error als gevonden
        if db.session.execute(db.select(User).filter_by(email=field.data)).scalar_one_or_none():
            raise ValidationError('Dit e-mailadres is al in gebruik')
    
    def validate_username(self, field):
        """controleert of email al in gebruik is"""
        # zoek op ingevuld email in db en geef error als gevonden
        if db.session.execute(db.select(User).filter_by(username=field.data)).scalar_one_or_none():
            raise ValidationError('Deze username is al in gebruik')

class WaardesForm(FF):
    leeftijd = IntF("Wat is uw leeftijd?",
                    validators=[DataRequired(), 
                                NumberRange(min=0, max=120)])
    diagnose = SelF("Wat is uw Diagnose?",
                    choices=[("astma","Astma"),("copd","COPD")]
                    )
    level = SelF("Wat is de ernst van uw diagnose?",
                 choices=[('intermittent', "Astma - intermittent"),
                          ("mild", "Astma - mild"), ("matig","Astma - matig"),
                          ("ernstig", "Astma - ernstig"), ("g1","GOLD 1"),
                          ("g2", "GOLD 2"), ("g3", "GOLD 3"), ("g4", "GOLD 4")])
    rookt = BoolF("Rookt u?")
    dag = BoolF("Ik heb vaker dan 2x per week dagelijkse klachten")
    nacht = BoolF("Ik word regelmatig s'nachts wakker met ademhalingsproblemen")
    saba = BoolF("Ik gebruik mijn SABA(nood-inhaler) meer dan 2x per week")
    beperking = BoolF("Ik beperk mijn dagelijkse activeit vanwege mijn ademhaling")
    hospital = BoolF("Ik ben in de afgelopen 12 maanden vanwegen mijn ziekte/symptomen in het ziekenhuis opgenomen geweest")
    prednison = BoolF("Ik heb in de afgelopen 12 maanden prednison gebruikt")
    exacerbaties = RadF("Aantal exacerbaties afgelopen 12 maanden", 
                        choices=[(0, "0"), (1, "1"), (2, "≥2")],
                        coerce=int,
                        default=0)
    submit = SubF("Opslaan en berekenen")


class HandmatigForm(FF):
    allergens = SelF('Allergenen',
                      validators=[DataRequired()],
                      choices=[('niet', 'Niet'),
                               ('matig', 'Matig'), ('veel', 'Veel')
                            ]
                    )
    irritants = SelF('Irriterende stoffen',
            validators=[DataRequired()],
            choices=[('niet', 'Niet'),
                     ('matig', 'Matig'), ('veel', 'Veel')
                    ]
                )
    infection = SelF('Luchtweginfecties',
            validators=[DataRequired()],
            choices=[('niet', 'Niet'),
                     ('matig', 'Matig'), ('veel', 'Veel')])
    
    exercise = SelF('Sporten',
            validators=[DataRequired()],
            choices=[('niet', 'Niet'),
                     ('matig', 'Matig'), ('veel', 'Veel')])
    
    weather = SelF('Weer',
            validators=[DataRequired()],
            choices=[('niet', 'Niet'),
                     ('matig', 'Matig'), ('veel', 'Veel')])

    pollution = SelF('Luchtvervuiling',
            validators=[DataRequired()],
            choices=[('niet', 'Niet'),
                     ('matig', 'Matig'), ('veel', 'Veel')])
    
    submit = SubF('Opslaan')

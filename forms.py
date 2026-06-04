from flask_wtf import FlaskForm as FF
from wtforms import (StringField as StrF, PasswordField as PassF, SubmitField as SubF,
                     EmailField as MailF, SelectField as SelF, IntegerField as IntF,
                     RadioField as RadF, BooleanField as BoolF)
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from models import db, User

class LoginForm(FF):
    username = StrF('Gebruikersnaam', validators=[DataRequired()])
    password = PassF('Wachtwoord', validators=[DataRequired()])
    submit = SubF('Login')

class RegisterForm(FF):
    username = StrF('Gebruikersnaam', validators=[DataRequired()])
    email = MailF('Email', validators=[DataRequired()])
    password = PassF('Wachtwoord', 
                     validators=[DataRequired(), Length(min=8)])
    role = SelF('Rol', 
                choices=[('patient', 'Patiënt'), ('arts', 'Arts')], 
                validators=[DataRequired()])
    submit = SubF('Registreren')
    
    def validate_email(self, field):
        """Controleert of email al in gebruik is"""
        user = db.session.execute(db.select(User).filter_by(email=field.data)).scalar_one_or_none()
        if user:
            raise ValidationError('Dit e-mailadres is al in gebruik.')
    
    def validate_username(self, field):
        """Controleert of gebruikersnaam al in gebruik is"""
        user = db.session.execute(db.select(User).filter_by(username=field.data)).scalar_one_or_none()
        if user:
            raise ValidationError('Deze gebruikersnaam is al in gebruik.')

class WaardesForm(FF):
    leeftijd = IntF("Wat is uw leeftijd?",
                    validators=[DataRequired(), 
                                NumberRange(min=0, max=120)])
    
    diagnose = SelF("Wat is uw Diagnose?",
                    choices=[("astma","Astma"), ("copd","COPD"), 
                             ("beide","Beide"), ("onbekend","Onbekend")],
                    validators=[DataRequired()])
    
    # Dit is het veld dat de Jinja2-fout veroorzaakte
    level = SelF("Wat is de ernst van uw diagnose?",
                 choices=[('intermittent', "Astma - intermittent"),
                          ("mild", "Astma - mild"), 
                          ("matig","Astma - matig"),
                          ("ernstig", "Astma - ernstig"), 
                          ("g1","GOLD 1"),
                          ("g2", "GOLD 2"), 
                          ("g3", "GOLD 3"), 
                          ("g4", "GOLD 4")],
                 validators=[DataRequired()])

    rookt = BoolF("Rookt u?")
    dag = BoolF("Ik heb vaker dan 2x per week dagelijkse klachten")
    nacht = BoolF("Ik word regelmatig 's nachts wakker met ademhalingsproblemen")
    saba = BoolF("Ik gebruik mijn SABA (nood-inhaler) meer dan 2x per week")
    beperking = BoolF("Ik beperk mijn dagelijkse activiteit vanwege mijn ademhaling")
    hospital = BoolF("Ik ben in de afgelopen 12 maanden opgenomen in het ziekenhuis")
    prednison = BoolF("Ik heb in de afgelopen 12 maanden prednison gebruikt")
    
    exacerbaties = RadF("Aantal exacerbaties afgelopen 12 maanden", 
                        choices=[(0, "0"), (1, "1"), (2, "≥2")],
                        coerce=int,
                        default=0)
    
    submit = SubF("Opslaan en berekenen")

class HandmatigForm(FF):
    # De veldnamen hier (allergens, irritants etc.) komen nu exact overeen met je model
    allergens = SelF('Allergenen: huisstofmijt, pollen, schimmel, huidschilfers',
                     choices=[('niet', 'Niet'), ('weinig', 'Weinig'),
                              ('matig', 'Matig'), ('veel', 'Veel')],
                     validators=[DataRequired()])
    
    irritants = SelF('Irriterende stoffen: rook, sterke geuren, dampen',
                     choices=[('niet', 'Niet'), ('weinig', 'Weinig'),
                              ('matig', 'Matig'), ('veel', 'Veel')],
                     validators=[DataRequired()])
    
    infection = SelF('Luchtweginfecties: griep, verkoudheid',
                     choices=[('niet', 'Niet'), ('weinig', 'Weinig'),
                              ('matig', 'Matig'), ('veel', 'Veel')],
                     validators=[DataRequired()])
    
    exercise = SelF('Sporten',
                    choices=[('niet', 'Niet'), ('weinig', 'Weinig'),
                             ('matig', 'Matig'), ('veel', 'Veel')],
                    validators=[DataRequired()])
    
    weather = SelF('Weer: kou, hitte, luchtvochtigheid, wind',
                   choices=[('niet', 'Niet'), ('weinig', 'Weinig'),
                            ('matig', 'Matig'), ('veel', 'Veel')],
                   validators=[DataRequired()])

    pollution = SelF('Luchtvervuiling: smog, uitlaatgassen, (fijn)stof',
                     choices=[('niet', 'Niet'), ('weinig', 'Weinig'),
                              ('matig', 'Matig'), ('veel', 'Veel')],
                     validators=[DataRequired()])
    
    submit = SubF('Opslaan')
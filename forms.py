from flask_wtf import FlaskForm as FF
from wtforms import (StringField as StrF, PasswordField as PassF, SubmitField as SubF,
                     EmailField as MailF, SelectField as SelF, IntegerField as IntF,
                     RadioField as RadF, BooleanField as BoolF, HiddenField as HF)
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from models import db, User


class LoginForm(FF):
    username = StrF('Gebruikersnaam', validators=[DataRequired()])
    password = PassF('Wachtwoord', validators=[DataRequired()])
    submit = SubF('Login')


class RegisterForm(FF):
    username = StrF('Username',
                    validators=[DataRequired()])
    email = MailF('Email',
                  validators=[DataRequired()])
    password = PassF('Wachtwoord',
                     validators=[DataRequired(),
                                 Length(min=8)])
    confirm_password = PassF('Bevestig Wachtwoord',
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
                    validators=[DataRequired(), NumberRange(min=0, max=120)])
    
    # Gebruik hier de lowercase keys: 'astma' of 'copd'
    diagnose = SelF("Wat is uw Diagnose?", 
                    choices=[("astma", "Astma"), ("copd", "COPD")],
                    validators=[DataRequired()])
    
    # Gebruik hier de exacte keys: 'intermittent', 'mild', 'matig', 'ernstig', 'g1', 'g2', 'g3', 'g4'
    level = SelF("Wat is de ernst van uw diagnose?",
                 choices=[
                     ('intermittent', "Astma - intermittent"),
                     ('mild', "Astma - mild"), 
                     ('matig', "Astma - matig"),
                     ('ernstig', "Astma - ernstig"), 
                     ('g1', "GOLD 1"),
                     ('g2', "GOLD 2"), 
                     ('g3', "GOLD 3"), 
                     ('g4', "GOLD 4")
                 ],
                 validators=[DataRequired()])
    
    rookt = BoolF("Rookt u?")
    dag = BoolF("Ik heb vaker dan 2x per week dagelijkse klachten")
    nacht = BoolF("Ik word regelmatig 's nachts wakker met ademhalingsproblemen")
    saba = BoolF("Ik gebruik mijn SABA (nood-inhaler) meer dan 2x per week")
    beperking = BoolF("Ik beperk mijn dagelijkse activiteit vanwege mijn ademhaling")
    hospital = BoolF("Ik ben in de afgelopen 12 maanden vanwege mijn ziekte/symptomen in het ziekenhuis opgenomen geweest")
    prednison = BoolF("Ik heb in de afgelopen 12 maanden prednison gebruikt")
    
    # Belangrijk: hier gebruik je integers als keys
    exacerbaties = RadF("Aantal exacerbaties afgelopen 12 maanden", 
                        choices=[(0, "0"), (1, "1"), (2, "2 of meer")],
                        coerce=int,
                        default=0)
    
    submit = SubF("Opslaan en berekenen")


class HandmatigForm(FF):
    
    allergens = HF()
    irritants = HF()
    weather   = HF()
    pollution = HF()
    
    submit = SubF('Opslaan')

class TimeRangeForm(FF):
    minutes = IntF(
        "Data (minuten)",
        default=1,
        validators=[NumberRange(min=1, max=1440)]
    )
    submit = SubF("Update grafiek")

#Geupdate voor het esp wachtwoord
class EspIDForm(FF):
    esp_id = IntF(
        "ESP-ID",
        validators=[DataRequired()],
        render_kw={"placeholder": "ESP_ID"}
    )

    esp_password = PassF(
        "ESP Wachtwoord",
        validators=[DataRequired()],
        render_kw={"placeholder": "ESP wachtwoord"}
    )

    submit = SubF("Opslaan")


class UnpairForm(FF):
    submit = SubF("Ontkoppel")

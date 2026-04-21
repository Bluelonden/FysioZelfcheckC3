from flask_wtf import FlaskForm as FF
from wtforms import (StringField as StrF, PasswordField as PassF, SubmitField as SubF,
                     EmailField as MailF, SelectField as SelF)
from wtforms.validators import DataRequired, Length


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
                choices=[('user', 'Patient'), ('admin', 'Huisarts')],
                validators=[DataRequired()])
    submit = SubF('Registreren')
#All imports needed
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

#registration form with validators 
#we use render_kw to add additional data into the html input fields
class RegistrationForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired(), Length(min=3, max=50)],render_kw={"class": "form-control","id": "register_username","placeholder": "Please enter your username"})
    email = StringField('Email', validators=[DataRequired(), Email()],render_kw={"class": "form-control","id": "register_email","aria-describedby": "registerEmailHelp","placeholder": "Please enter your email"})
    password = PasswordField('Password', validators=[DataRequired(), Length(min=5)],render_kw={"class": "form-control","id": "register_password","placeholder": "Please enter a password"})
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')],render_kw={"class": "form-control","id": "register_confirm_password","placeholder": "Confirm the password"})
    submit = SubmitField('Register',render_kw={"class": "btn btn-primary w-100"})

#login form with validators 
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()],render_kw={"class": "form-control","id": "login_email","aria-describedby": "loginEmailHelp","placeholder": "Please enter your email"})
    password = PasswordField('Password', validators=[DataRequired()],render_kw={"class": "form-control","id": "login_password","placeholder": "Please enter the password"})
    submit = SubmitField('Login',render_kw={"class": "btn btn-primary w-100"})
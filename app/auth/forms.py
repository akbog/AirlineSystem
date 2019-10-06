from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField, SelectField
from wtforms.validators import Required, Email, Length, Regexp, EqualTo
from wtforms import ValidationError
from wtforms_components import DateRange
from datetime import datetime, date
from ..models import Customer

class RegistrationForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    name = StringField('Name', validators = [Required(), Length(1, 64), Regexp('^[A-Za-z]*$', 0, 'Name must have only letters')])
    passport_num = StringField('Passport Number', validators = [Required(), Length(1, 64)])
    passport_expir = DateField('Expiration Date', validators = [Required()])
    passport_country = SelectField('Country', choices = []) #Later need to set the Country
    date_of_birth = DateField('Date of Birth', validators = [Required(), DateRange(date(1900,1,1), datetime.today())])
    password = PasswordField('Password', validators = [Required(), Length(8,64), EqualTo('password2', message = 'Passwords must match.')])
    password2 = PasswordField('Confirm password', validators = [Required()])
    submit = SubmitField('Register')


    #When a form defines a method with the prefix validate_ followed by the name of a field,
    #the method is invoked in addition to any regularly defined validators
    def validate_email(self, field):
        if Customer.query.filter_by(email = field.data).first():
            raise ValidationError('Email already registered.')


class LoginForm(Form):
    email = StringField('Email', validators = [Required(), Length(1, 64), Email()])
    password = PasswordField('Password', validators = [Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

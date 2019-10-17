from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField#,DateField
from wtforms.validators import Required, Email, Length, Regexp, EqualTo, NumberRange
from wtforms import ValidationError
from wtforms.fields.html5 import DateField
from wtforms_components import DateRange
from datetime import datetime, date
from ..models import Customer, User, Airport
from .. import db

class CustomerRegistrationForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    first_name = StringField('First Name', validators = [Required(), Length(1, 64), Regexp('^[A-Za-z\s]*$', 0, 'Name must have only letters')])
    last_name = StringField('Last Name', validators = [Required(), Length(1, 64), Regexp('^[A-Za-z\s]*$', 0, 'Name must have only letters')])
    middle_name = StringField('Middle Name', validators = [Regexp('^[A-Za-z\s]*$', 0, 'Name must have only letters')])
    date_of_birth = DateField('Date of Birth', validators = [Required(), DateRange(date(1900,1,1), date.today())])
    passport_num = StringField('Passport Number', validators = [Required(), Length(1, 64)])
    passport_expir = DateField('Expiration Date', validators = [Required()])
    passport_country = SelectField('Country', validators = [Required()]) #choices = [('country','United States'),('country','Italy'),('country','Zimbabwe')]) #Later need to set the Country
    password = PasswordField('Password', validators = [Required(), Length(8,64), EqualTo('password2', message = 'Passwords must match.')])
    password2 = PasswordField('Confirm password', validators = [Required()])
    submit = SubmitField('Register')
    #When a form defines a method with the prefix validate_ followed by the name of a field,
    #the method is invoked in addition to any regularly defined validators
    def validate_email(self, field):
        if Customer.query.filter_by(email = field.data).first():
            raise ValidationError('Email already registered.')


class CustomerLoginForm(FlaskForm):
    email = StringField('Email', validators = [Required(), Length(1, 64), Email()])
    password = PasswordField('Password', validators = [Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class AgentLoginForm(FlaskForm):
    booking_agent_id = StringField('Agent ID', validators = [Required(), Length(1,64)])
    email = StringField('Email', validators = [Required(), Length(1, 64), Email()])
    password = PasswordField('Password', validators = [Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class PartnerLoginForm(FlaskForm):
    username = StringField('Username', validators = [Required(), Length(1,64)])
    password = PasswordField('Password', validators = [Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class ExploreForm(FlaskForm):
    departure_airport = SelectField('Depart from:')
    arrival_airport = SelectField('Arrive at:')
    departure_date = DateField('Depart Date', validators = [Required(), DateRange(date.today())])
    arrival_date = DateField('Arrival Date', validators = [Required(), DateRange(date.today())])
    group_size = IntegerField('Group Size', validators = [Required(), NumberRange(0,10)])
    submit = SubmitField('Explore')

    def validate_arrival_date(self, field):
        if field.data <= self.departure_date.data:
            raise ValidationError('Please input a valid date range')

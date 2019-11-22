from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField #,DateField
from wtforms.validators import Required, Email, Length, Regexp, EqualTo, NumberRange
from wtforms import ValidationError
from wtforms.fields.html5 import DateField
from wtforms_components import DateRange
from datetime import datetime, date
from ..models import Customer, User, Airport
from dateutil.relativedelta import relativedelta
from .. import db

class BookingAgentCheckoutForm(FlaskForm):
    email = StringField('Customer Email', validators = [Required(),Email()])
    submit = SubmitField('Confirm Purchase')

    def validate_email(self, field):
        if not Customer.query.filter_by(email = field.data).first():
            raise ValidationError('Email does not belong to an existing customer')

class CustomerCheckoutForm(FlaskForm):
    submit = SubmitField('Confirm Purchase')

class TrackingSearchForm(FlaskForm):
    airport = SelectField('Airport:', validators = [Required()])
    date = DateField('Departure Date', validators = [Required(), DateRange(date.today())])
    submit = SubmitField('See Flights')

class SearchByFlightNum(FlaskForm):
    flight_num = StringField('Flight #')
    airline = SelectField('Select an Airline')
    submit = SubmitField('Check Flight')

class SearchMyFlights(FlaskForm):
    start_date = DateField('Begin:')
    end_date = DateField('End:')
    city = SelectField('City', default = (None, 'Optional'))
    submit = SubmitField('Search Flights')

    def validate_end_date(self, field):
        if field.data:
            if field.data < self.start_date.data:
                raise ValidationError('Please input a valid date range')

    def validate_start_date(self, field):
        if field.data:
            if field.data > self.end_date.data:
                raise ValidationError('Please input a valid date range')

class SearchCustomerFlights(FlaskForm):
    start_date = DateField('Begin:')
    end_date = DateField('End:')
    city = SelectField('City', default = (None, 'Optional'))
    customer = SelectField('Customer', default = (None, 'All'))
    submit = SubmitField('Search Flights')

    def validate_end_date(self, field):
        if field.data:
            if field.data < self.start_date.data:
                raise ValidationError('Please input a valid date range')

    def validate_start_date(self, field):
        if field.data:
            if field.data > self.end_date.data:
                raise ValidationError('Please input a valid date range')

class PersonalFinances(FlaskForm):
    start_date = DateField('Start Date:')
    end_date = DateField('End Date:')
    submit = SubmitField('Explore Finances')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.start_date.data:
            self.start_date.data = date.today() - relativedelta(years = 1)
        if not self.end_date.data:
            self.end_date.data = date.today()

    def validate_end_date(self, field):
        if field.data:
            if field.data < self.start_date.data:
                raise ValidationError('Please input a valid date range')

    def validate_start_date(self, field):
        if field.data:
            if field.data > self.end_date.data:
                raise ValidationError('Please input a valid date range')

class CommissionForm(FlaskForm):
    start_date = DateField('Start Date:')
    end_date = DateField('End Date:')
    submit = SubmitField('Explore My Commission')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.start_date.data:
            self.start_date.data = date.today() - relativedelta(days = 30)
        if not self.end_date.data:
            self.end_date.data = date.today()

    def validate_end_date(self, field):
        if field.data:
            if field.data < self.start_date.data:
                raise ValidationError('Please input a valid date range')

    def validate_start_date(self, field):
        if field.data:
            if field.data > self.end_date.data:
                raise ValidationError('Please input a valid date range')

class TopCustomerForm(FlaskForm):
    start_date = DateField('Start Date:', validators =[Required()])
    end_date = DateField('End Date:', validators =[Required()])
    top = IntegerField('Top N Customers:', validators =[Required()])
    submit = SubmitField('See Top Customers')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.top.data:
            self.top.data = 5

    def validate_end_date(self, field):
        if field.data:
            if field.data < self.start_date.data:
                raise ValidationError('Please input a valid date range')

    def validate_start_date(self, field):
        if field.data:
            if field.data > self.end_date.data:
                raise ValidationError('Please input a valid date range')

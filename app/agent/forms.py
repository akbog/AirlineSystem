from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField, DecimalField
from wtforms.validators import Required, Email, Length, Regexp, EqualTo, NumberRange
from wtforms import ValidationError
from wtforms.fields.html5 import DateField, DateTimeField, TimeField
from wtforms_components import DateRange
from datetime import datetime, date
from ..models import Customer, User, Airport, Flight
from dateutil.relativedelta import relativedelta
from .. import db

class SearchAirlineFlights(FlaskForm):
    start_date = DateField('Begin:')
    end_date = DateField('End:')
    origin_city = SelectField('Origin City', default = (None, 'Optional'))
    destination_city = SelectField('Destination City', default = (None, 'Optional'))
    submit = SubmitField('Search Flights')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.start_date.data:
            self.start_date.data = date.today()
        if not self.end_date.data:
            self.end_date.data = date.today() + relativedelta(days = 30)

    def validate_end_date(self, field):
        if field.data:
            if field.data < self.start_date.data:
                raise ValidationError('Please input a valid date range')

    def validate_start_date(self, field):
        if field.data:
            if field.data > self.end_date.data:
                raise ValidationError('Please input a valid date range')

class AddFlights(FlaskForm):
    origin_airport = SelectField('Origin Airport:', validators = [Required()])
    destination_airport = SelectField('Destination Airport:', validators = [Required()])
    airplane_id = SelectField('Airplane ID:', validators = [Required()])
    departure_date = DateField('Departure Date:', validators = [Required()])
    departure_time = TimeField('Departure Time: 12hr', validators = [Required()], format = "%H:%M")
    arrival_date = DateField('Arrival Date:', validators = [Required()])
    arrival_time = TimeField('Arrival Time: 12hr', validators = [Required()], format = "%H:%M")
    status = SelectField('Status:', validators = [Required()])
    price = DecimalField('Price', validators = [Required()])
    submit = SubmitField('Add Flight')

    def validate_price(self, field):
        if (field.data).as_tuple().exponent < -2:
            raise ValidationError('Please input a valid Price')

    def validate_departure_date(self, field):
        if field.data:
            if field.data > self.arrival_date.data:
                raise ValidationError('Please input a valid date range')

    def validate_departure_time(self, field):
        if field.data:
            if self.departure_date.data == self.arrival_date.data:
                if field.data > self.arrival_time.data:
                    raise ValidationError('Arrival Time must be after Departure Time')

    def validate_origin_airport(self, field):
        if field.data:
            if field.data == self.destination_airport.data:
                raise ValidationError('Airports must differ!')

    def validate_arrival_date(self, field):
        if field.data:
            if field.data < self.departure_date.data:
                raise ValidationError('Please input a valid date range')

    def validate_airplane_id(self, field):
        if field.data:
            taken = Flight.query.filter((Flight.airplane_id == field.data) & (Flight.departure_date >= self.departure_time.data) & (Flight.arrival_date < self.arrival_time.data)).all()
            if taken:
                raise ValidationError('The aircraft you requested is scheduled for the desired date range')

class UpdateStatus(FlaskForm):
    status = SelectField('Status:', validators = [Required()])
    submit = SubmitField('Update')

class AddAirplane(FlaskForm):
    model = SelectField('Select Aircraft:', validators = [Required()])
    submit = SubmitField('Add Airplane')

class AddAirport(FlaskForm):
    name = StringField('Airport Name', validators = [Required()])
    code = StringField('Airport Code', validators = [Required(), Length(min = 3), Length(max = 3)])
    city = StringField('City', validators = [Required()])
    country = StringField('Country', validators = [Required()])
    longitude = DecimalField('Longitude', validators = [Required()])
    latitude = DecimalField('Latitude', validators = [Required()])
    submit = SubmitField('Add Airport')

    def validate_code(self, field):
        if field.data:
            codes = list(zip(*Airport.query.with_entities(Airport.code).all()))[0]
            print(codes)
            if field.data in codes:
                raise ValidationError('This Airport Code Already Exists!')

    def validate_name(self, field):
        if field.data:
            names = list(zip(*Airport.query.with_entities(Airport.name).all()))[0]
            print(names)
            if field.data in names:
                raise ValidationError('An Airport with this Name Already Exists!')

class CustomerSearchForm(FlaskForm):
    start_date = DateField('Start Date', validators = [Required()])
    end_date = DateField('End Date', validators = [Required()])
    customers = SelectField('Select a Customer')
    submit = SubmitField('Search')

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

class StatsForm(FlaskForm):
    start_date = DateField('Start Date', validators = [Required()])
    end_date = DateField('End Date', validators = [Required()])
    submit = SubmitField('View Stats')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.start_date.data:
            self.start_date.data = date.today() - relativedelta(months = 6)
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


class TopDestForm(FlaskForm):
    start_date = DateField('Start Date', validators = [Required()])
    end_date = DateField('End Date', validators = [Required()])
    top_n = IntegerField('Number to Rank', validators = [Required()])
    submit = SubmitField('View Stats')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.start_date.data:
            self.start_date.data = date.today() - relativedelta(months = 6)
        if not self.end_date.data:
            self.end_date.data = date.today()
        if not self.top_n.data:
            self.top_n.data = 3

    def validate_end_date(self, field):
        if field.data:
            if field.data < self.start_date.data:
                raise ValidationError('Please input a valid date range')

    def validate_start_date(self, field):
        if field.data:
            if field.data > self.end_date.data:
                raise ValidationError('Please input a valid date range')

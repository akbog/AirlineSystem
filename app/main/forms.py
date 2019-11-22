from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField #,DateField
from wtforms.validators import Required, Email, Length, Regexp, EqualTo, NumberRange
from wtforms import ValidationError
from wtforms.fields.html5 import DateField
from wtforms_components import DateRange
from datetime import datetime, date
from ..models import Customer, User, Airport
from .. import db

class ExploreForm(FlaskForm):
    departure_airport = SelectField('Departure Airport:', validators = [Required()])
    arrival_airport = SelectField('Arrival Airport:', validators = [Required()])
    departure_date = DateField('Departure Date', validators = [Required(), DateRange(date.today())])
    return_date = DateField('Return Date (Optional)', validators = [DateRange(date.today())])
    submit = SubmitField('Explore')

    def validate_return_date(self, field):
        if field.data <= self.departure_date.data:
            raise ValidationError('Please input a valid date range')

    def validate_arrival_airport(self, field):
        if field.data == self.departure_airport.data:
            raise ValidationError('Airports must be different.')

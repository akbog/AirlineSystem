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
    departure_airport = SelectField('Depart from:', validators = [Required()])
    arrival_airport = SelectField('Arrive at:', validators = [Required()])
    departure_date = DateField('Depart Date', validators = [Required(), DateRange(date.today())])
    return_date = DateField('Return Date (Optional)', validators = [DateRange(date.today())])
    group_size = IntegerField('Group Size', validators = [Required(), NumberRange(0,10)])
    submit = SubmitField('Explore')

    def validate_return_date(self, field):
        if field.data <= self.departure_date.data:
            raise ValidationError('Please input a valid date range')

    def validate_arrival_airport(self, field):
        print(field.data)
        print(self.departure_airport.data)
        if field.data == self.departure_airport.data:
            raise ValidationError('Airports must be different.')

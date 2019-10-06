from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager

@login_manager.user_loader
def load_customer(customer_id):
    return Customer.query.get(customer_id)

class Airline(db.Model):
    name = db.Column(db.String(64), primary_key = True)
    airplanes = db.relationship('Airplane', backref='airline', lazy = True)
    flights = db.relationship('Flight', backref = 'airline', lazy = True)
    tickets = db.relationship('Ticket', backref = 'airline', lazy = True)
    employees = db.relationship('Airline_staff', backref = 'employee_of', lazy = True)

class Airplane(db.Model):
    id_num = db.Column(db.String(64), primary_key = True)
    seat_capacity = db.Column(db.Integer, nullable = False)
    airline_name = db.Column(db.String(64), db.ForeignKey('Airline.name'), primary_key = True)
    flights = db.relationship('Flight', backref = 'airplane', lazy = True)

class Airport(db.Model):
    name = db.Column(db.String(64), primary_key = True)
    city = db.Column(db.String(64), unique = False)
    flight_arrival = db.relationship('Flight',foreign_keys = 'flight.arrival', backref = 'arrival_port', lazy = True)
    flight_departure = db.relationship('Flight', foreign_keys = 'flight.departure', backref = 'departure_port', lazy = True)

class Flight(db.Model):
    flight_num = db.Column(db.String(64), primary_key = True)
    price = db.Column(db.Float(), nullable = False)
    airline_name = db.Column(db.String(64), db.ForeignKey('Airline.name'), primary_key = True)
    airplane_id = db.Column(db.String(64), db.ForeignKey('Airplane.id_num'), nullable = False)
    arrival = db.Column(db.String(64), db.ForeignKey('Airport.name'), nullable = False)
    departure = db.Column(db.String(64), db.ForeignKey('Airport.name'), nullable = False)
    arrival_time = db.Column(db.DateTime, nullable = False)
    departure_time = db.Column(db.DateTime, nullable = False)
    tickets = db.relationship('Ticket', backref = 'flight', lazy = True)

class Customer(UserMixin, db.Model):
    email = db.Column(db.String(64), primary_key = True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(64), nullable = False)
    passport_num = db.Column(db.String(64), nullable = False)
    passport_expir = db.Column(db.Date, nullable = False)
    passport_country = db.Column(db.String(64), nullable = False)
    date_of_birth = db.Column(db.Date, nullable = False)
    addresses = db.relationship('Address', backref = 'customer', lazy = True)
    phone_numbers = db.relationship('Phone_number', backref = 'customer', lazy = True)
    tickets = db.relationship('Ticket', backref = 'customer', lazy = True)
    confirmed = db.Column(db.Boolean, default=False)
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm':self.email})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.email:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def __repr__(self):
        return '<Customer %r>' % self.email

class Address(db.Model):
    email = db.Column(db.String(64), db.ForeignKey('Customer.email'), primary_key = True)
    building_num = db.Column(db.String(64), nullable = False, primary_key = True)
    street = db.Column(db.String(64), nullable = False, primary_key = True)
    city = db.Column(db.String(64), nullable = False, primary_key = True)
    state = db.Column(db.String(64), nullable = False, primary_key = True)
    zip_code = db.Column(db.Integer, nullable = False, primary_key = True)

    def __repr__(self):
        return '<Address %r>' % self.building_num

class Phone_number(db.Model):
    email = db.Column(db.String(64), db.ForeignKey('Customer.email'), primary_key = True)
    number = db.Column(db.String(64), primary_key = True)

class Booking_agent(db.Model):
    booking_agent_id = db.Column(db.String(64),primary_key = True)
    email = db.Column(db.String(64), nullable = False, unique = True)
    password = db.Column(db.String(64), nullable = False)
    tickets_sold = db.relationship('Ticket', backref = 'booking_agent', lazy = True)

class Airline_staff(db.Model):
    username = db.Column(db.String(64), primary_key = True)
    password = db.Column(db.String(64), nullable = False)
    first_name = db.Column(db.String(64), nullable = False)
    last_name = db.Column(db.String(64), nullable = False)
    date_of_birth = db.Column(db.DateTime, nullable = False)
    airline = db.Column(db.String(64), db.ForeignKey('Airline.name'), nullable = False)

class Ticket(db.Model):
    ticket_id = db.Column(db.String(64), primary_key = True)
    customer_email = db.Column(db.String(64), db.ForeignKey('Customer.email'), nullable = False)
    airline_name = db.Column(db.String(64), db.ForeignKey('Airline.name'), nullable = False)
    flight_num = db.Column(db.String(64), db.ForeignKey('Flight.flight_num'), nullable = False)
    booking_agent_ID = db.Column(db.String(64), db.ForeignKey('Booking_agent.booking_agent_id'), nullable = True)

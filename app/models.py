from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(UserMixin, db.Model):
    user_id = db.Column(db.Integer, primary_key = True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    last_seen = db.Column(db.DateTime(), default = datetime.utcnow)
    member_since = db.Column(db.DateTime(), default = datetime.utcnow)
    customers = db.relationship('Customer', backref = 'user', lazy = True)
    agents = db.relationship('Booking_agent', backref = 'user', lazy = True)
    staff = db.relationship('Airline_staff', backref = 'user', lazy = True)

    def get_id(self):
        return self.user_id

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.user_id == current_app.config['FLASKY_ADMIN']:
                self.role_id = Role.query.filter_by(permissions=0xff).first()
            if self.role_id is None:
                self.role = Role.query.filter_by(default = True).first()

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
        return s.dumps({'confirm':self.user_id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.user_id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def __repr__(self):
        return '<User %r>' % self.user_id

    def can(self, permissions):
        return self.role is not None and \
                (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

class Customer(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable = False)
    email = db.Column(db.String(64), primary_key = True)
    first_name = db.Column(db.String(64), nullable = False)
    last_name = db.Column(db.String(64), nullable = False)
    middle_name = db.Column(db.String(64), nullable = True)
    passport_num = db.Column(db.String(64), nullable = False)
    passport_expir = db.Column(db.Date, nullable = False)
    passport_country = db.Column(db.String(64), nullable = False)
    date_of_birth = db.Column(db.Date, nullable = False)
    addresses = db.relationship('Address', backref = 'customer', lazy = True)
    phone_numbers = db.relationship('Phone_number', backref = 'customer', lazy = True)
    tickets = db.relationship('Ticket', backref = 'customer', lazy = True)

    def get_id(self):
        return self.user_id

class Booking_agent(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable = False)
    booking_agent_id = db.Column(db.String(64),primary_key = True)
    email = db.Column(db.String(64), nullable = False, unique = True)
    password = db.Column(db.String(64), nullable = False)
    tickets_sold = db.relationship('Ticket', backref = 'booking_agent', lazy = True)

class Airline_staff(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable = False)
    username = db.Column(db.String(64), primary_key = True)
    first_name = db.Column(db.String(64), nullable = False)
    last_name = db.Column(db.String(64), nullable = False)
    date_of_birth = db.Column(db.DateTime, nullable = False)
    airline = db.Column(db.String(64), db.ForeignKey('airline.name'), nullable = False)


class Role(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64), unique = True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref = 'role', lazy = 'dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'Customer' : (Permission.BOOK_FLIGHTS, True),
            'Booking_agent' : (Permission.BOOK_FLIGHTS |
                                Permission.BOOK_FLIGHTS_FOR_OTHERS,
                                False),
            'Airline_staff' : (Permission.BOOK_FLIGHTS |
                                Permission.BOOK_FLIGHTS_FOR_OTHERS |
                                Permission.UPDATE_FLIGHTS,
                                False),
            'Administrator' : (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name = r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

class Permission:
    BOOK_FLIGHTS = 0x01
    BOOK_FLIGHTS_FOR_OTHERS = 0x02
    UPDATE_FLIGHTS = 0x03


class Airline(db.Model):
    name = db.Column(db.String(64), primary_key = True)
    airplanes = db.relationship('Airplane', backref='airline', lazy = True)
    flights = db.relationship('Flight', backref = 'airline', lazy = True)
    tickets = db.relationship('Ticket', backref = 'airline', lazy = True)
    employees = db.relationship('Airline_staff', backref = 'employee_of', lazy = True)

class Airplane(db.Model):
    id_num = db.Column(db.String(64), primary_key = True)
    seat_capacity = db.Column(db.Integer, nullable = False)
    airline_name = db.Column(db.String(64), db.ForeignKey('airline.name'), primary_key = True)
    flights = db.relationship('Flight', backref = 'airplane', lazy = True)

class Airport(db.Model):
    name = db.Column(db.String(64), primary_key = True)
    city = db.Column(db.String(64), unique = False)
    flight_arrival = db.relationship('Flight',foreign_keys = 'Flight.arrival', backref = 'arrival_port', lazy = True)
    flight_departure = db.relationship('Flight',foreign_keys = 'Flight.departure', backref = 'departure_port', lazy = True)

class Flight(db.Model):
    flight_num = db.Column(db.String(64), primary_key = True)
    price = db.Column(db.Float(), nullable = False)
    airline_name = db.Column(db.String(64), db.ForeignKey('airline.name'), primary_key = True)
    airplane_id = db.Column(db.String(64), db.ForeignKey('airplane.id_num'), nullable = False)
    arrival = db.Column(db.String(64), db.ForeignKey('airport.name'), nullable = False)
    departure = db.Column(db.String(64), db.ForeignKey('airport.name'), nullable = False)
    arrival_time = db.Column(db.DateTime, nullable = False)
    departure_time = db.Column(db.DateTime, nullable = False)
    tickets = db.relationship('Ticket', backref = 'flight', lazy = True)

class Address(db.Model):
    email = db.Column(db.String(64), db.ForeignKey('customer.email'), primary_key = True)
    building_num = db.Column(db.String(64), nullable = False, primary_key = True)
    street = db.Column(db.String(64), nullable = False, primary_key = True)
    city = db.Column(db.String(64), nullable = False, primary_key = True)
    state = db.Column(db.String(64), nullable = False, primary_key = True)
    zip_code = db.Column(db.Integer, nullable = False, primary_key = True)

    def __repr__(self):
        return '<Address %r>' % self.building_num

class Phone_number(db.Model):
    email = db.Column(db.String(64), db.ForeignKey('customer.email'), primary_key = True)
    number = db.Column(db.String(64), primary_key = True)

class Ticket(db.Model):
    ticket_id = db.Column(db.String(64), primary_key = True)
    customer_email = db.Column(db.String(64), db.ForeignKey('customer.email'), nullable = False)
    airline_name = db.Column(db.String(64), db.ForeignKey('airline.name'), nullable = False)
    flight_num = db.Column(db.String(64), db.ForeignKey('flight.flight_num'), nullable = False)
    booking_agent_ID = db.Column(db.String(64), db.ForeignKey('booking_agent.booking_agent_id'), nullable = True)

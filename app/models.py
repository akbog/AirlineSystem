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
    last_seen = db.Column(db.DateTime(), default = datetime.utcnow)
    member_since = db.Column(db.DateTime(), default = datetime.utcnow)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    customers = db.relationship('Customer', backref = 'user', lazy = True)
    agents = db.relationship('Booking_agent', backref = 'user', lazy = True)
    staff = db.relationship('Airline_staff', backref = 'user', lazy = True)

    def get_id(self):
        return self.user_id

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.user_id == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

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

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def can(self, permissions):
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymouse_user = AnonymousUser

class Permission:
    BOOK_FLIGHTS_AS_CUST = 0x01
    BOOK_FLIGHTS_AS_AGENT = 0x02
    MANAGE_AIRLINES = 0x04
    ADMINISTER = 0x80

class Role(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64), unique = True)
    default = db.Column(db.Boolean, default = False, index = True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref = 'role', lazy = 'dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'Customer':(Permission.BOOK_FLIGHTS_AS_CUST, True),
            'BOOKING_AGENT' : (Permission.BOOK_FLIGHTS_AS_AGENT, False),
            'Airline_Staff' : (Permission.MANAGE_AIRLINES, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

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
    tickets_sold = db.relationship('Ticket', backref = 'booking_agent', lazy = True)

class Airline_staff(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable = False)
    username = db.Column(db.String(64), primary_key = True)
    first_name = db.Column(db.String(64), nullable = False)
    last_name = db.Column(db.String(64), nullable = False)
    date_of_birth = db.Column(db.DateTime, nullable = False)
    airline = db.Column(db.String(64), db.ForeignKey('airline.name'), nullable = False)

class Airline(db.Model):
    name = db.Column(db.String(64), primary_key = True)
    airplanes = db.relationship('Airline_stock', backref='airline', lazy = True)
    employees = db.relationship('Airline_staff', backref = 'employee_of', lazy = True)

class Airplane(db.Model):
    id_num = db.Column(db.String(3), primary_key = True)
    aircraft_name = db.Column(db.String(128), nullable = False, unique = True)
    seat_capacity = db.Column(db.Integer, nullable = False)
    airline_name = db.relationship('Airline_stock', backref = 'airplane')

class Airline_stock(db.Model):
    airline_name = db.Column(db.String(64), db.ForeignKey('airline.name'), primary_key = True, unique = False)
    model = db.Column(db.String(3), db.ForeignKey('airplane.id_num'), primary_key = True, unique = False)
    unique_id = db.Column(db.String(64), primary_key = True, unique = False)

class Airport(db.Model):
    name = db.Column(db.String(64), primary_key = True)
    code = db.Column(db.String(3), unique = True)
    city = db.Column(db.String(64), unique = False)
    country = db.Column(db.String(64), unique = False)
    latitude = db.Column(db.Float())
    longitude = db.Column(db.Float())
    flight_arrival = db.relationship('Flight',foreign_keys = 'Flight.arrival', backref = 'arrival_port', lazy = True)
    flight_departure = db.relationship('Flight',foreign_keys = 'Flight.departure', backref = 'departure_port', lazy = True)

class Flight(db.Model):
    flight_num = db.Column(db.String(64), primary_key = True, unique = False)
    price = db.Column(db.Float(), nullable = False)
    airline_name = db.Column(db.String(64), primary_key = True, unique = False)
    airplane_model = db.Column(db.String(3), unique = False, nullable = False)
    airplane_id = db.Column(db.String(64), unique = False, nullable = False)
    arrival = db.Column(db.String(64), db.ForeignKey('airport.name'), nullable = False)
    departure = db.Column(db.String(64), db.ForeignKey('airport.name'), nullable = False)
    arrival_date = db.Column(db.DateTime, nullable = False)
    departure_date = db.Column(db.DateTime, nullable = False)
    status = db.Column(db.String(64), db.ForeignKey('status.status'))
    tickets = db.relationship('Ticket', foreign_keys = 'Ticket.flight_num', backref = 'flight', lazy = True)
    tickets = db.relationship('Ticket', foreign_keys = 'Ticket.airline_name', backref = 'flight', lazy = True)
    __table_args__ = (
        db.ForeignKeyConstraint(['airline_name','airplane_model','airplane_id'],['airline_stock.airline_name','airline_stock.model','airline_stock.unique_id'], name = 'fk_flight_name_model_id'),
    )

class Status(db.Model):
    status = db.Column(db.String(64), primary_key = True)

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
    ticket_id = db.Column(db.Integer, primary_key = True)
    customer_email = db.Column(db.String(64), db.ForeignKey('customer.email'), nullable = False)
    airline_name = db.Column(db.String(64), primary_key = True, nullable = False)
    flight_num = db.Column(db.String(64), primary_key = True, nullable = False)
    date_purchased = db.Column(db.DateTime, nullable = True)
    booking_agent_ID = db.Column(db.String(64), db.ForeignKey('booking_agent.booking_agent_id'), nullable = True)
    __table_args__ = (
        db.ForeignKeyConstraint(['flight_num','airline_name'],['flight.flight_num','flight.airline_name'], name = 'fk_ticket_name_num'),
    )

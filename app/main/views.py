from datetime import datetime
from datetime import date
from flask import render_template, session, redirect, url_for
from . import main
from .. import db
from ..booking import booking
from ..auth.forms import CustomerLoginForm

from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from ..models import Customer, User, Booking_agent, Airline_staff, Airport, Flight, Permission, Ticket, Airplane
from .forms import ExploreForm

from dateutil.relativedelta import relativedelta

@main.route('/', methods = ['GET','POST'])
def index():
    if request.form:
        form = ExploreForm(request.form)
        type = "requested"
        print("found form")
    else:
        form = ExploreForm()
        type = "old"
        print("no Form")
    airports = [(i,i) for (i,) in db.session.query(Airport.name).all()]
    form.departure_airport.choices = airports
    form.arrival_airport.choices = airports
    if form.validate_on_submit():
        print(type)
        start_date = form.departure_date.data
        ret_date = form.return_date.data
        dep_air = form.departure_airport.data
        arr_air = form.arrival_airport.data
        available_departure_flight = Flight.query.join(Ticket,(Ticket.flight_num == Flight.flight_num) & (Ticket.airline_name == Flight.airline_name), isouter = True) \
                    .join(Airplane, Flight.airplane_model == Airplane.id_num) \
                    .filter((Flight.departure == dep_air) & (Flight.arrival == arr_air) & (Flight.departure_date < start_date + relativedelta(days = 1)) & (Flight.departure_date >= date.today())) \
                    .group_by(Flight.flight_num, Flight.airline_name, Airplane.seat_capacity, Flight.departure_date, Flight.arrival_date, Flight.price) \
                    .having((db.func.max(Ticket.ticket_id) < Airplane.seat_capacity - 1) | (db.func.max(Ticket.ticket_id) == None)) \
                    .order_by(Flight.departure_date.desc()).all()
        session['ret_date'] = ret_date
        session['form'] = {'departure_date' : form.departure_date.data, 'return_date' : form.return_date.data, 'departure_airport' : form.departure_airport.data, 'arrival_airport' : form.arrival_airport.data}
        return render_template('booking/bookdeparture.html', dep_flights = available_departure_flight, permissions = Permission, form = form)
    return render_template('index.html', explore_form = form, permissions = Permission)

@main.route('/bookdeparture', methods = ['GET', 'POST'])
def bookdeparture():
    form = ExploreForm(request.form)
    print('request')
    airports = [(i,i) for (i,) in db.session.query(Airport.name).all()]
    form.departure_airport.choices = airports
    form.arrival_airport.choices = airports
    print(form.validate_on_submit())
    print(request.method)
    if request.method == "POST" and form.validate():
        print(type)
        start_date = form.departure_date.data
        ret_date = form.return_date.data
        dep_air = form.departure_airport.data
        arr_air = form.arrival_airport.data
        available_departure_flight = Flight.query.join(Ticket,(Ticket.flight_num == Flight.flight_num) & (Ticket.airline_name == Flight.airline_name), isouter = True) \
                    .join(Airplane, Flight.airplane_model == Airplane.id_num) \
                    .filter((Flight.departure == dep_air) & (Flight.arrival == arr_air) & (Flight.departure_date < start_date + relativedelta(days = 1)) & (Flight.departure_date >= date.today())) \
                    .group_by(Flight.flight_num, Flight.airline_name, Airplane.seat_capacity, Flight.departure_date, Flight.arrival_date, Flight.price) \
                    .having((db.func.max(Ticket.ticket_id) < Airplane.seat_capacity - 1) | (db.func.max(Ticket.ticket_id) == None)) \
                    .order_by(Flight.departure_date.desc()).all()
        session['ret_date'] = ret_date
        session['form'] = {'departure_date' : form.departure_date.data, 'return_date' : form.return_date.data, 'departure_airport' : form.departure_airport.data, 'arrival_airport' : form.arrival_airport.data}
        return render_template('booking/bookdeparture.html', dep_flights = available_departure_flight, permissions = Permission, form = form)
    else:
        flash(form.errors)
    return render_template('booking/bookdeparture.html', permissions = Permission, form = form)


# select flight.flight_num, airline_name, max(ticket_id)
# from flight natural join ticket join airplane on (flight.airplane_model = airplane.id_num)
# where arrival = "Pudong International Airport"
# and departure = "John F. Kennedy Airport"
# and flight.arrival_date > "2020-01-01 00:00:00"
# and flight.departure_date < "2020-01-01 00:00:00"
# group by flight.flight_num, flight.airline_name, airplane.seat_capacity
# having max(ticket_id) < airplane.seat_capacity
# order by departure_date desc;
#
# select flight.flight_num, airline_name, max(ticket_id)
# from flight natural join ticket join airplane on (flight.airplane_model = airplane.id_num)
# where arrival = "Pudong International Airport"
# and departure = "John F. Kennedy Airport"
# and flight.departure_date < "2020-01-01 00:00:00"
# group by flight.flight_num, flight.airline_name, airplane.seat_capacity
# having max(ticket_id) < airplane.seat_capacity
# order by departure_date desc
#
#
# """select flight.flight_num, departure_date, arrival_date, price, airline_name, max(ticket_id)
# from flight natural join ticket join airplane on (flight.airplane_model = airplane.id_num)
# where arrival = "Pudong International Airport"
# and departure = "John F. Kennedy Airport"
# and flight.departure_date < "2020-01-01 00:00:00"
# group by flight.flight_num, flight.airline_name, airplane.seat_capacity, departure_date, arrival_date, price
# having max(ticket_id) < airplane.seat_capacity - 1
# order by departure_date desc"""

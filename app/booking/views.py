from flask import render_template, redirect, request, url_for, flash, session
from . import booking
from flask_login import login_user, login_required, logout_user, current_user
from ..models import Permission, Customer, User, Booking_agent, Airline_staff, Airport, Flight, Ticket, Airline, Airplane
from .forms import BookingAgentCheckoutForm, CustomerCheckoutForm, TrackingSearchForm, SearchByFlightNum, SearchMyFlights, PersonalFinances, SearchCustomerFlights, CommissionForm, TopCustomerForm
from ..main.forms import ExploreForm
# from .forms import
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from ..decorators import permission_required
from collections import defaultdict
from .. import db
import re

@booking.route('/bookflight/<depart_id>', methods = ['GET','POST'])
def bookflight(depart_id):
    form = ExploreForm()
    form.departure_date.data = datetime.strptime(session['form']['departure_date'], '%a, %d %b %Y %H:%M:%S %Z')
    form.return_date.data = datetime.strptime(session['form']['return_date'], '%a, %d %b %Y %H:%M:%S %Z')
    form.departure_airport.data = session['form']['departure_airport']
    form.arrival_airport.data = session['form']['arrival_airport']
    airports = [(i,i) for (i,) in db.session.query(Airport.name).all()]
    form.departure_airport.choices = airports
    form.arrival_airport.choices = airports
    if request.method == "POST" and form.validate():
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
        return render_template('booking/bookdeparture.html', dep_flights = available_departure_flight, permissions = Permission, form = form)
    air_name = request.args.get('airline')
    departure_flight = Flight.query.filter_by(flight_num = depart_id).filter_by(airline_name = air_name).first()
    dep_date = datetime.strptime(session.get('ret_date'), "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=None)
    session['depart_flight_num'] = depart_id
    session['depart_flight_airline'] = air_name
    return_flights = Flight.query.join(Ticket,(Ticket.flight_num == Flight.flight_num) & (Ticket.airline_name == Flight.airline_name), isouter = True) \
                .join(Airplane, Flight.airplane_model == Airplane.id_num) \
                .filter((Flight.departure == departure_flight.arrival) & (Flight.arrival == departure_flight.departure) & (Flight.departure_date > dep_date - relativedelta(days = 1)) & (Flight.departure_date >= date.today())) \
                .group_by(Flight.flight_num, Flight.airline_name, Airplane.seat_capacity, Flight.departure_date, Flight.arrival_date, Flight.price) \
                .having((db.func.max(Ticket.ticket_id) < Airplane.seat_capacity - 1) | (db.func.max(Ticket.ticket_id) == None)) \
                .order_by(Flight.departure_date.asc()).all()
    # return_flights = Flight.query.filter_by(departure = departure_flight.arrival).filter_by(arrival = departure_flight.departure).filter(Flight.departure_date > dep_date - relativedelta(days=1)).order_by(Flight.departure_date.asc()).all()
    return render_template('booking/bookreturn.html', ret_flights = return_flights, permissions = Permission, form = form)

@booking.route('/checkout/<return_id>', methods = ['GET','POST'])
@login_required
def checkout(return_id):
    return_air_name = request.args.get('airline')
    departure_flight = Flight.query.filter_by(flight_num = session.get('depart_flight_num')).filter_by(airline_name = session.get('depart_flight_airline')).first()
    session['return_flight_num'] = return_id
    session['return_flight_airline'] = return_air_name
    depart_id = session.get('depart_flight_num')
    depart_air_name = session.get('depart_flight_airline')
    return_flight = Flight.query.filter_by(flight_num = return_id).filter_by(airline_name = return_air_name).first()
    booking_form = BookingAgentCheckoutForm()
    customer_form = CustomerCheckoutForm()
    total_price = "{0:.2f}".format(departure_flight.price + return_flight.price)
    if current_user.can(Permission.BOOK_FLIGHTS_AS_CUST):
        if customer_form.validate_on_submit():
            user_email = (Customer.query.filter_by(user_id = current_user.user_id).first()).email
            dep_ticket_id = Ticket.query.with_entities(Ticket.flight_num, Ticket.airline_name, db.func.max(Ticket.ticket_id)).filter((Ticket.flight_num == depart_id) & (Ticket.airline_name == depart_air_name)).group_by(Ticket.flight_num, Ticket.airline_name).first()
            ret_ticket_id = Ticket.query.with_entities(Ticket.flight_num, Ticket.airline_name, db.func.max(Ticket.ticket_id)).filter((Ticket.flight_num == return_id) & (Ticket.airline_name == return_air_name)).group_by(Ticket.flight_num, Ticket.airline_name).first()
            print(ret_ticket_id)
            if not dep_ticket_id:
                d_tick = 0
            else:
                d_tick = dep_ticket_id[2]
            if not ret_ticket_id:
                r_tick = 0
            else:
                r_tick = ret_ticket_id[2]
            dep_seats = Airplane.query.filter(Airplane.id_num == departure_flight.airplane_model).first()
            ret_seats = Airplane.query.filter(Airplane.id_num == return_flight.airplane_model).first()
            print(dep_ticket_id, ret_ticket_id, dep_seats.seat_capacity, ret_seats.seat_capacity)
            if d_tick < dep_seats.seat_capacity and r_tick < ret_seats.seat_capacity:
                dep_ticket = Ticket(ticket_id = d_tick + 1,
                                customer_email = user_email,
                                airline_name = session.get('depart_flight_airline'),
                                flight_num = session.get('depart_flight_num'),
                                booking_agent_ID = None,
                                date_purchased = datetime.now())

                ret_ticket = Ticket(ticket_id = r_tick + 1,
                                customer_email = user_email,
                                airline_name = session.get('return_flight_airline'),
                                flight_num = session.get('return_flight_num'),
                                booking_agent_ID = None,
                                date_purchased = datetime.now())
                db.session.add(dep_ticket)
                db.session.add(ret_ticket)
                db.session.commit()
                flash('Thanks for using Tripmetic for your Flight Services!')
                return redirect(url_for("main.index"))
            else:
                flash("We're sorry, but the flights you have requested are currently sold out!")
                return redirect(url_for("main.index"))
    elif current_user.can(Permission.BOOK_FLIGHTS_AS_AGENT):
        if booking_form.validate_on_submit():
            booking_id = (Booking_agent.query.filter_by(user_id = current_user.user_id).first()).booking_agent_id
            dep_ticket_id = Ticket.query.with_entities(Ticket.flight_num, Ticket.airline_name, db.func.max(Ticket.ticket_id)).filter((Ticket.flight_num == depart_id) & (Ticket.airline_name == depart_air_name)).group_by(Ticket.flight_num, Ticket.airline_name).first()
            ret_ticket_id = Ticket.query.with_entities(Ticket.flight_num, Ticket.airline_name, db.func.max(Ticket.ticket_id)).filter((Ticket.flight_num == return_id) & (Ticket.airline_name == return_air_name)).group_by(Ticket.flight_num, Ticket.airline_name).first()
            if not dep_ticket_id:
                d_tick = 0
            else:
                d_tick = dep_ticket_id[2]
            if not ret_ticket_id:
                r_tick = 0
            else:
                r_tick = ret_ticket_id[2]
            dep_seats = Airplane.query.filter(Airplane.id_num == departure_flight.airplane_model).first()
            ret_seats = Airplane.query.filter(Airplane.id_num == return_flight.airplane_model).first()
            if d_tick < dep_seats.seat_capacity and r_tick < ret_seats.seat_capacity:
                dep_ticket = Ticket(ticket_id = d_tick + 1,
                                customer_email = booking_form.email.data,
                                airline_name = session.get('depart_flight_airline'),
                                flight_num = session.get('depart_flight_num'),
                                booking_agent_ID = booking_id,
                                date_purchased = datetime.now())

                ret_ticket = Ticket(ticket_id = r_tick + 1,
                                customer_email = booking_form.email.data,
                                airline_name = session.get('return_flight_airline'),
                                flight_num = session.get('return_flight_num'),
                                booking_agent_ID = booking_id,
                                date_purchased = datetime.now())
                db.session.add(dep_ticket)
                db.session.add(ret_ticket)
                db.session.commit()
                flash('Thanks for using Tripmetic for your Flight Services!')
                return redirect(url_for("main.index"))
            else:
                flash("We're sorry, but the flights you have requested are currently sold out!")
                return redirect(url_for("main.index"))
    return render_template('booking/checkout.html', book_form = booking_form, cust_form = customer_form, dep_flight = departure_flight, ret_flight = return_flight, tot_price = total_price, permissions = Permission)

@booking.route('/trackflights', methods = ['GET','POST'])
def trackflights():
    searchForm = TrackingSearchForm()
    searchFlightNum = SearchByFlightNum()
    airports = Airport.query.with_entities(Airport.name).order_by(Airport.name.asc())
    searchForm.airport.choices = [(i.name,i.name) for i in airports]
    searchFlightNum.airline.choices = [(i.name, i.name) for i in Airline.query.order_by(Airline.name.asc()).all()]
    if searchForm.validate_on_submit():
        departure = searchForm.airport.data
        arrival = searchForm.airport.data
        departures = Flight.query.filter((Flight.departure == departure) & (Flight.departure_date > searchForm.date.data) & (Flight.departure_date < searchForm.date.data + relativedelta(days=1))).all()
        arrivals = Flight.query.filter((Flight.arrival == arrival) & (Flight.arrival_date > searchForm.date.data) & (Flight.arrival_date < searchForm.date.data + relativedelta(days=1))).all()
        return render_template('booking/trackflights.html', searchFlightNum = searchFlightNum, searchForm = searchForm, dep_flights = departures, arr_flights = arrivals, permissions = Permission)
    if searchFlightNum.validate_on_submit():
        number = searchFlightNum.flight_num.data
        airline = searchFlightNum.airline.data
        departures = Flight.query.filter((Flight.flight_num == number) & (Flight.airline_name == airline)).all()
        arrivals = departures
        return render_template('booking/trackflights.html', searchFlightNum = searchFlightNum, searchForm = searchForm, dep_flights = departures, arr_flights = arrivals, permissions = Permission)
    return render_template('booking/trackflights.html', searchFlightNum = searchFlightNum, searchForm = searchForm, arr_flights = [], dep_flights = [], permissions = Permission)

@booking.route('/myflights', methods = ['GET','POST'])
@login_required
@permission_required(Permission.BOOK_FLIGHTS_AS_CUST)
def myflights():
    user_email = (Customer.query.filter_by(user_id = current_user.user_id).first()).email
    upcoming = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter(Ticket.customer_email == user_email).filter(Flight.departure_date > datetime.now()).order_by(Flight.departure_date.asc()).all()
    historical = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter(Ticket.customer_email == user_email).filter(Flight.departure_date < datetime.now()).order_by(Flight.departure_date.desc()).all()
    quantity = Ticket.query.with_entities(Ticket.flight_num, Ticket.airline_name, db.func.count(Ticket.ticket_id)).filter(Ticket.customer_email == user_email).group_by(Ticket.flight_num, Ticket.airline_name).all()
    quantities = defaultdict(list)
    for i, j, k in quantity:
        quantities[i].append(j)
        quantities[i].append(k)
    form = SearchMyFlights()
    cities = Airport.query.with_entities(Airport.city).order_by(Airport.city.asc())
    form.city.choices = [('None', 'Optional')] + [(i.city, i.city) for i in cities]
    if form.validate_on_submit():
        if form.city.data != 'None':
            city_airports = Airport.query.filter_by(city = form.city.data).all()
            upcoming = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter(Ticket.customer_email == user_email).filter(Flight.arrival.in_([i.name for i in city_airports]) | Flight.departure.in_([i.name for i in city_airports])).filter(Flight.departure_date > datetime.now()).order_by(Flight.departure_date.asc()).all()
            historical = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter(Ticket.customer_email == user_email).filter(Flight.arrival.in_([i.name for i in city_airports]) | Flight.departure.in_([i.name for i in city_airports])).filter(Flight.departure_date < datetime.now()).order_by(Flight.departure_date.desc()).all()
            return render_template('booking/myflights.html', permissions = Permission, upcoming = upcoming, historical = historical, form = form, quantities = quantities)
        else:
            if form.start_date.data > datetime.now().date():
                upcoming = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter(Ticket.customer_email == user_email).filter(Flight.departure_date > form.start_date.data).filter(Flight.departure_date < form.end_date.data).order_by(Flight.departure_date.asc()).all()
            else:
                upcoming = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter(Ticket.customer_email == user_email).filter(Flight.departure_date > datetime.now()).filter(Flight.departure_date < form.end_date.data).order_by(Flight.departure_date.asc()).all()
            historical = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter(Ticket.customer_email == user_email).filter(Flight.departure_date > form.start_date.data).filter(Flight.departure_date < datetime.now()).order_by(Flight.departure_date.asc()).all()
            return render_template('booking/myflights.html', permissions = Permission, upcoming = upcoming, historical = historical, form = form, quantities = quantities)
    return render_template('booking/myflights.html', permissions = Permission, upcoming = upcoming, historical = historical, form = form, quantities = quantities)

@booking.route('/customerflights', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.BOOK_FLIGHTS_AS_AGENT)
def customerflights():
    booking_id = (Booking_agent.query.filter_by(user_id = current_user.user_id).first()).booking_agent_id
    upcoming = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter(Ticket.booking_agent_ID == booking_id).filter(Flight.departure_date > datetime.now()).order_by(Flight.departure_date.asc()).all()
    historical = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter(Ticket.booking_agent_ID == booking_id).filter(Flight.departure_date < datetime.now()).order_by(Flight.departure_date.desc()).all()
    quantity = Ticket.query.with_entities(Ticket.flight_num, Ticket.airline_name, db.func.count(Ticket.ticket_id)).filter(Ticket.booking_agent_ID == booking_id).group_by(Ticket.flight_num, Ticket.airline_name).all()
    quantities = defaultdict(list)
    for i, j, k in quantity:
        quantities[i].append(j)
        quantities[i].append(k)
    form = SearchCustomerFlights()
    cities = Airport.query.with_entities(Airport.city).order_by(Airport.city.asc())
    form.city.choices = [('None', 'Optional')] + [(i.city, i.city) for i in cities]
    customers = Customer.query.join(Ticket, (Customer.email == Ticket.customer_email)).filter(Ticket.booking_agent_ID == booking_id).with_entities(Customer.email).distinct().order_by(Customer.email.asc())
    form.customer.choices = [('None', 'All')] + [(i.email, i.email) for i in customers]
    if form.validate_on_submit():
        if form.city.data != 'None':
            if form.customer.data == 'None':
                city_airports = Airport.query.filter_by(city = form.city.data).all()
                upcoming = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter((Ticket.booking_agent_ID == booking_id) & ((Flight.arrival.in_([i.name for i in city_airports])) | (Flight.departure.in_([i.name for i in city_airports]))) & (Flight.departure_date > datetime.now())).order_by(Flight.departure_date.asc()).all()
                historical = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter((Ticket.booking_agent_ID == booking_id) & ((Flight.arrival.in_([i.name for i in city_airports])) | (Flight.departure.in_([i.name for i in city_airports]))) & (Flight.departure_date < datetime.now())).order_by(Flight.departure_date.desc()).all()
                return render_template('booking/myflights.html', permissions = Permission, upcoming = upcoming, historical = historical, form = form, quantities = quantities)
            else:
                customer = form.customer.data
                city_airports = Airport.query.filter_by(city = form.city.data).all()
                upcoming = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter((Ticket.booking_agent_ID == booking_id) & (Ticket.customer_email == customer) & ((Flight.arrival.in_([i.name for i in city_airports])) | (Flight.departure.in_([i.name for i in city_airports]))) & (Flight.departure_date > datetime.now())).order_by(Flight.departure_date.asc()).all()
                historical = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter((Ticket.booking_agent_ID == booking_id) & (Ticket.customer_email == customer) & ((Flight.arrival.in_([i.name for i in city_airports])) | (Flight.departure.in_([i.name for i in city_airports]))) & (Flight.departure_date < datetime.now())).order_by(Flight.departure_date.desc()).all()
                return render_template('booking/myflights.html', permissions = Permission, upcoming = upcoming, historical = historical, form = form, quantities = quantities)
        else:
            if form.customer.data != 'None':
                upcoming = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter((Ticket.booking_agent_ID == booking_id) & (Ticket.customer_email == customer) & (Flight.departure_date > datetime.now())).order_by(Flight.departure_date.asc()).all()
                historical = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter((Ticket.booking_agent_ID == booking_id)  & (Ticket.customer_email == customer) & (Flight.departure_date < datetime.now())).order_by(Flight.departure_date.desc()).all()
                return render_template('booking/myflights.html', permissions = Permission, upcoming = upcoming, historical = historical, form = form, quantities = quantities)
            else:
                upcoming = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter((Ticket.booking_agent_ID == booking_id) & (Flight.departure_date > datetime.now())).order_by(Flight.departure_date.asc()).all()
                historical = Flight.query.join(Ticket, (Flight.flight_num == Ticket.flight_num) & (Flight.airline_name == Ticket.airline_name)).filter((Ticket.booking_agent_ID == booking_id) & (Flight.departure_date < datetime.now())).order_by(Flight.departure_date.desc()).all()
                return render_template('booking/myflights.html', permissions = Permission, upcoming = upcoming, historical = historical, form = form, quantities = quantities)
    return render_template('booking/myflights.html', permissions = Permission, upcoming = upcoming, historical = historical, form = form, quantities = quantities)

@booking.route('/finances', methods = ['GET','POST'])
@login_required
@permission_required(Permission.BOOK_FLIGHTS_AS_CUST)
def finances():
    default_start = date.today() + relativedelta(days = 1)
    visualization_end = date.today() - relativedelta(months = 6)
    default_end= date.today() - relativedelta(years = 1)
    form = PersonalFinances()
    cust_email = (Customer.query.filter(Customer.user_id == current_user.user_id).first()).email
    spend = Ticket.query.filter((Ticket.customer_email == cust_email) & (Ticket.date_purchased < default_start) & (Ticket.date_purchased > default_end)).join(Flight, (Ticket.flight_num == Flight.flight_num) & (Ticket.airline_name == Flight.airline_name)).with_entities(Ticket.flight_num, Ticket.airline_name, Ticket.date_purchased, Flight.price).all()
    total_spend = "${0:.2f}".format(sum([val[3] for val in spend]))
    months = {}
    month_start = visualization_end
    while month_start <= default_start:
        key = datetime.strptime((month_start).strftime("%Y-%m-01"), "%Y-%m-%d")
        print(key)
        months[key] = 0
        month_start += relativedelta(months=1)
    for i,j,k,l in spend:
        key = datetime.strptime(k.strftime("%Y-%m-01"), "%Y-%m-%d")
        if key in months:
            months[key] += l
        else:
            months[key] = l
    print(months)
    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data + relativedelta(days = 1)
        spend = Ticket.query.filter((Ticket.customer_email == cust_email) & (Ticket.date_purchased < end_date) & (Ticket.date_purchased > start_date)).join(Flight, (Ticket.flight_num == Flight.flight_num) & (Ticket.airline_name == Flight.airline_name)).with_entities(Ticket.flight_num, Ticket.airline_name, Ticket.date_purchased, Flight.price).all()
        total_spend = "${0:.2f}".format(sum([val[3] for val in spend]))
        #get (month range) as dictionary
        months = {}
        month_start = start_date
        while month_start <= end_date:
            key = datetime.strptime((month_start).strftime("%Y-%m-01"), "%Y-%m-%d")
            print(key)
            months[key] = 0
            month_start += relativedelta(months=1)
        for i,j,k,l in spend:
            key = datetime.strptime(k.strftime("%Y-%m-01"), "%Y-%m-%d")
            if key in months:
                months[key] += l
            else:
                months[key] = l
        print(months)
        return render_template('booking/finances.html', permissions = Permission, form = form, months = months, total_spend = total_spend)
    return render_template('booking/finances.html', permissions = Permission, form = form, months = months, total_spend = total_spend)

@booking.route('/commission', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.BOOK_FLIGHTS_AS_AGENT)
def commission():
    default_start = date.today() + relativedelta(days = 1)
    default_end= date.today() - relativedelta(days = 30)
    form = CommissionForm()
    booking_id = (Booking_agent.query.filter_by(user_id = current_user.user_id).first()).booking_agent_id
    total_price = Ticket.query.filter((Ticket.date_purchased > default_end) & (Ticket.date_purchased < default_start) & (Ticket.booking_agent_ID == booking_id)).join(Flight, (Ticket.flight_num == Flight.flight_num) & (Ticket.airline_name == Flight.airline_name)).with_entities(db.func.count(Flight.price),db.func.sum(Flight.price)).first()
    if total_price:
        total_commission = "${0:.2f}".format(total_price[1] * 0.15)
        avg_commission = "${0:.2f}".format((total_price[1] * 0.15) / total_price[0])
        total_tickets_sold = total_price[0]
    else:
        total_commission = avg_commission = "$0.00"
        total_tickets_sold = 0
    if form.validate_on_submit():
        default_start = form.start_date.data
        default_end = form.end_date.data + relativedelta(days = 1)
        total_price = Ticket.query.filter((Ticket.date_purchased < default_end) & (Ticket.date_purchased > default_start) & (Ticket.booking_agent_ID == booking_id)).join(Flight, (Ticket.flight_num == Flight.flight_num) & (Ticket.airline_name == Flight.airline_name)).with_entities(db.func.count(Flight.price),db.func.sum(Flight.price)).first()
        if total_price[1]:
            total_commission = "${0:.2f}".format(total_price[1] * 0.15)
            avg_commission = "${0:.2f}".format((total_price[1] * 0.15) / total_price[0])
            total_tickets_sold = total_price[0]
        else:
            total_commission = avg_commission = "$0.00"
            total_tickets_sold = 0
        return render_template('booking/commission.html', permissions = Permission, form = form, total_commission = total_commission, avg_commission = avg_commission, total_tickets_sold = total_tickets_sold)
    return render_template('booking/commission.html', permissions = Permission, form = form, total_commission = total_commission, avg_commission = avg_commission, total_tickets_sold = total_tickets_sold)

@booking.route('/topcustomers', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.BOOK_FLIGHTS_AS_AGENT)
def topcustomers():
    booking_id = (Booking_agent.query.filter_by(user_id = current_user.user_id).first()).booking_agent_id
    purchased_start = date.today() - relativedelta(months = 6)
    commission_start = date.today() - relativedelta(years = 1)
    default_end = date.today() + relativedelta(days = 1)
    top_purchased = Ticket.query.filter((Ticket.booking_agent_ID == booking_id) & (Ticket.date_purchased > purchased_start) & (Ticket.date_purchased < default_end)).join(Customer, (Ticket.customer_email == Customer.email)).with_entities(Ticket.customer_email, Customer.first_name, Customer.last_name, db.func.count(Ticket.customer_email)).group_by(Ticket.customer_email, Customer.first_name, Customer.last_name).order_by(db.func.count(Ticket.customer_email).desc()).limit(5).all()
    top_commission = Ticket.query.filter((Ticket.booking_agent_ID == booking_id) & (Ticket.date_purchased > purchased_start) & (Ticket.date_purchased < default_end)).join(Flight, (Ticket.flight_num == Flight.flight_num) & (Ticket.airline_name == Flight.airline_name)) \
    .join(Customer, (Ticket.customer_email == Customer.email)).with_entities(Ticket.customer_email, Customer.first_name, Customer.last_name, db.func.sum(Flight.price)).group_by(Ticket.customer_email, Customer.first_name, Customer.last_name).order_by(db.func.sum(Flight.price).desc()).limit(5).all()
    form = TopCustomerForm()
    if form.validate_on_submit():
        purchased_start = form.start_date.data
        commission_start = form.start_date.data
        default_end = form.end_date.data
        top = form.top.data
        top_purchased = Ticket.query.filter((Ticket.booking_agent_ID == booking_id) & (Ticket.date_purchased > purchased_start) & (Ticket.date_purchased < default_end)).join(Customer, (Ticket.customer_email == Customer.email)).with_entities(Ticket.customer_email, Customer.first_name, Customer.last_name, db.func.count(Ticket.customer_email)).group_by(Ticket.customer_email, Customer.first_name, Customer.last_name).order_by(db.func.count(Ticket.customer_email).desc()).limit(top).all()
        top_commission = Ticket.query.filter((Ticket.booking_agent_ID == booking_id) & (Ticket.date_purchased > purchased_start) & (Ticket.date_purchased < default_end)).join(Flight, (Ticket.flight_num == Flight.flight_num) & (Ticket.airline_name == Flight.airline_name)) \
        .join(Customer, (Ticket.customer_email == Customer.email)).with_entities(Ticket.customer_email, Customer.first_name, Customer.last_name, db.func.sum(Flight.price)).group_by(Ticket.customer_email, Customer.first_name, Customer.last_name).order_by(db.func.sum(Flight.price).desc()).limit(top).all()
        return render_template('booking/topcustomers.html', permissions = Permission, top_purchased = top_purchased, top_commission = top_commission, form = form)
    return render_template('booking/topcustomers.html', permissions = Permission, top_purchased = top_purchased, top_commission = top_commission, form = form)

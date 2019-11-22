from flask import render_template, redirect, request, url_for, flash, session
from . import agent
from flask_login import login_user, login_required, logout_user, current_user
from ..models import Permission, Customer, User, Booking_agent, Airline_staff, Airport, Flight, Ticket, Airline, Airplane, Airline_stock, Status
from .forms import SearchAirlineFlights, AddFlights, UpdateStatus, AddAirplane, AddAirport, CustomerSearchForm, StatsForm, TopDestForm
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from ..decorators import permission_required
from collections import defaultdict
from .. import db
import re

@agent.route('/airlineflights', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_AIRLINES)
def airlineflights():
    #on-click functionality: Show all customers of a particular flight
    line = (Airline_staff.query.filter(Airline_staff.user_id == current_user.user_id).first()).airline
    print(line)
    default_start = date.today()
    default_end = date.today() + relativedelta(days = 31)
    upcoming = Flight.query.filter((Flight.departure_date > default_start) & (Flight.departure_date < default_end) & (Flight.airline_name == line)).order_by(Flight.departure_date.asc()).all()
    form = SearchAirlineFlights()
    cities = Airport.query.with_entities(Airport.city).order_by(Airport.city.asc())
    form.origin_city.choices = [('None', 'Optional')] + [(i.city, i.city) for i in cities]
    form.destination_city.choices = [('None', 'Optional')] + [(i.city, i.city) for i in cities]
    if form.validate_on_submit():
        if form.origin_city.data != "None" and form.destination_city.data != "None":
            origin_airports = Airport.query.filter_by(city = form.origin_city.data).all()
            destination_airports = Airport.query.filter_by(city = form.destination_city.data).all()
            default_start = form.start_date.data
            default_end = form.end_date.data
            upcoming = Flight.query.filter((Flight.airline_name == line) & ((Flight.arrival.in_([i.name for i in destination_airports])) & (Flight.departure.in_([i.name for i in origin_airports]))) & (Flight.departure_date > default_start) & (Flight.departure_date < default_end)).order_by(Flight.departure_date.asc()).all()
            return render_template('agent/airlineflights.html', permissions = Permission, form = form, upcoming = upcoming, line = line)
        elif form.origin_city.data != "None":
            origin_airports = Airport.query.filter_by(city = form.origin_city.data).all()
            default_start = form.start_date.data
            default_end = form.end_date.data
            upcoming = Flight.query.filter((Flight.airline_name == line) & (Flight.departure.in_([i.name for i in origin_airports])) & (Flight.departure_date > default_start) & (Flight.departure_date < default_end)).order_by(Flight.departure_date.asc()).all()
            return render_template('agent/airlineflights.html', permissions = Permission, form = form, upcoming = upcoming, line = line)
        elif form.destination_city.data != "None":
            destination_airports = Airport.query.filter_by(city = form.destination_city.data).all()
            default_start = form.start_date.data
            default_end = form.end_date.data
            upcoming = Flight.query.filter((Flight.airline_name == line) & (Flight.arrival.in_([i.name for i in destination_airports])) & (Flight.departure_date > default_start) & (Flight.departure_date < default_end)).order_by(Flight.departure_date.asc()).all()
            return render_template('agent/airlineflights.html', permissions = Permission, form = form, upcoming = upcoming, line = line)
        else:
            default_start = form.start_date.data
            default_end = form.end_date.data
            upcoming = Flight.query.filter((Flight.departure_date > default_start) & (Flight.departure_date < default_end) & (Flight.airline_name == line)).order_by(Flight.departure_date.asc()).all()
            return render_template('agent/airlineflights.html', permissions = Permission, form = form, upcoming = upcoming, line = line)
    return render_template('agent/airlineflights.html', permissions = Permission, form = form, upcoming = upcoming, line = line)

@agent.route('/flightpassengers/<flight_num>', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_AIRLINES)
def flightpassengers(flight_num):
    line = (Airline_staff.query.filter(Airline_staff.user_id == current_user.user_id).first()).airline
    passengers = Ticket.query.join(Customer, (Customer.email == Ticket.customer_email)).filter((Ticket.flight_num == flight_num) & (Ticket.airline_name == line)).all()
    if request.method == "POST" and request.form['name'] == "return":
        return url_for('agent.airlineflights')
    return render_template('agent/flightpassengers.html', permissions = Permission, passengers = passengers, flight_number = flight_num, line = line)

@agent.route('/addflights', methods = ['GET','POST'])
@login_required
@permission_required(Permission.MANAGE_AIRLINES)
def addflights():
    line = (Airline_staff.query.filter(Airline_staff.user_id == current_user.user_id).first()).airline
    default_start = date.today()
    default_end = date.today() + relativedelta(days = 31)
    upcoming = Flight.query.filter((Flight.departure_date > default_start) & (Flight.departure_date < default_end) & (Flight.airline_name == line)).order_by(Flight.departure_date.asc()).all()
    form = AddFlights()
    airports = [(i,i) for (i,) in db.session.query(Airport.name).all()]
    airplane_ids = Airline_stock.query.filter((Airline_stock.airline_name == line)).with_entities(Airline_stock.unique_id).distinct().all()
    status_opt = Status.query.all()
    form.origin_airport.choices = airports
    form.destination_airport.choices = airports
    form.airplane_id.choices = [(i,i) for (i,) in airplane_ids]
    form.status.choices = [(i.status, i.status) for i in status_opt]
    if form.validate_on_submit():
        airplane_id = form.airplane_id.data
        airplane_model = Airline_stock.query.filter(Airline_stock.unique_id == airplane_id).with_entities(Airline_stock.model).first()[0]
        flight_count = Flight.query.filter((Flight.airline_name == line) & (Flight.airplane_id == airplane_id)).with_entities(db.func.count(Flight.flight_num)).first()[0]
        departure_date = datetime.combine(form.departure_date.data,form.departure_time.data)
        arrival_date = datetime.combine(form.arrival_date.data,form.arrival_time.data)
        flight_num = flight_count + 1
        new_flight = Flight(flight_num = '{}{:06d}'.format(airplane_id,flight_num),
                            price = form.price.data,
                            airline_name = line,
                            arrival = form.origin_airport.data,
                            departure = form.destination_airport.data,
                            arrival_date = arrival_date,
                            departure_date = departure_date,
                            airplane_id = airplane_id,
                            airplane_model = airplane_model,
                            status = form.status.data
                            )
        db.session.add(new_flight)
        db.session.commit()
        flash('The Flight has been added.')
        return redirect(url_for('main.index'))
    return render_template('agent/addflights.html', permissions = Permission, upcoming = upcoming, form = form)

@agent.route('/updatestatus/<flight_id>', methods = ['GET','POST'])
@login_required
@permission_required(Permission.MANAGE_AIRLINES)
def updatestatus(flight_id):
    line = (Airline_staff.query.filter(Airline_staff.user_id == current_user.user_id).first()).airline
    flight = Flight.query.filter((Flight.flight_num == flight_id) & (Flight.airline_name == line)).first()
    form = UpdateStatus()
    status_opt = Status.query.all()
    form.status.choices = [(i.status, i.status) for i in status_opt]
    if form.validate_on_submit():
        flight.status = form.status.data
        db.session.commit()
        flash('The Flight Status has been updated.')
        return redirect(url_for('main.index'))
    return render_template('agent/updatestatus.html', permissions = Permission, flight = flight, form = form)

@agent.route('/addplanes', methods = ['GET','POST'])
@login_required
@permission_required(Permission.MANAGE_AIRLINES)
def addplanes():
    line = (Airline_staff.query.filter(Airline_staff.user_id == current_user.user_id).first()).airline
    planes = Airline_stock.query.join(Airplane, (Airline_stock.model == Airplane.id_num)).filter(Airline_stock.airline_name == line).all()
    print(planes)
    form = AddAirplane()
    #can use airplane models instead of id because of unique constraint
    form.model.choices = [(None, 'Select Flight')] + [(i.id_num, i.aircraft_name) for i in Airplane.query.order_by(Airplane.aircraft_name.asc()).all()]
    if form.validate_on_submit():
        if form.model.data:
            id_number = form.model.data
            plane = Airline_stock.query.filter((Airline_stock.airline_name == line) & (Airline_stock.model == id_number)).with_entities(Airline_stock.model, db.func.count(Airline_stock.unique_id)).first()
            if plane[0]:
                new_plane = Airline_stock(model = plane[0],
                                        unique_id = '{}_{:04d}'.format(plane[0],plane[1] + 1),
                                        airline_name = line)
            else:
                new_plane = Airline_stock(model = id_number,
                                            unique_id = '{}_{:04d}'.format(id_number,1),
                                            airline_name = line)
            db.session.add(new_plane)
            db.session.commit()
            # planes = Airline_stock.query.join(Airplane, (Airline_stock.model == Airplane.id_num)).filter(Airline_stock.airline_name == line).all()
            flash('The Airplane has been added to the Stock.')
            return redirect(url_for('main.index'))
    return render_template('agent/addplanes.html', permissions = Permission, form = form, planes = planes, line = line)

@agent.route('/addairport', methods = ['GET','POST'])
@login_required
@permission_required(Permission.MANAGE_AIRLINES)
def addairport():
    line = (Airline_staff.query.filter(Airline_staff.user_id == current_user.user_id).first()).airline
    form = AddAirport()
    if request.method == "POST" and form.validate_on_submit():
        new_port = Airport(name = form.name.data,
                            city = form.city.data,
                            code = form.code.data,
                            country = form.country.data,
                            latitude = form.latitude.data,
                            longitude = form.longitude.data)
        db.session.add(new_port)
        db.session.commit()
        flash('You have successfully added an Airport')
        return redirect(url_for('main.index'))
    return render_template('agent/addairport.html', permissions = Permission, form = form)

@agent.route('/bookingagents', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_AIRLINES)
def bookingagents():
    line = (Airline_staff.query.filter(Airline_staff.user_id == current_user.user_id).first()).airline
    #Month
    month_start = date.today() - relativedelta(months = 1)
    month_end = date.today() + relativedelta(days = 1)
    top_tickets_month = Booking_agent.query.join(Ticket, (Ticket.booking_agent_ID == Booking_agent.booking_agent_id)) \
                                            .filter((Ticket.date_purchased > month_start) & (Ticket.date_purchased < month_end) & (Ticket.airline_name == line)) \
                                            .with_entities(Booking_agent.email, Booking_agent.booking_agent_id, db.func.count(Ticket.ticket_id)) \
                                            .group_by(Booking_agent.email, Booking_agent.booking_agent_id) \
                                            .order_by(db.func.count(Ticket.ticket_id).desc()).all()[:5]
    top_commission_month = Booking_agent.query.join(Ticket, (Ticket.booking_agent_ID == Booking_agent.booking_agent_id)) \
                                            .join(Flight, (Ticket.flight_num == Flight.flight_num) & (Ticket.airline_name == Flight.airline_name)) \
                                            .filter((Ticket.date_purchased > month_start) & (Ticket.date_purchased < month_end) & (Ticket.airline_name == line)) \
                                            .with_entities(Booking_agent.email, Booking_agent.booking_agent_id, db.func.sum(Flight.price) *.15) \
                                            .group_by(Booking_agent.email, Booking_agent.booking_agent_id).order_by(db.func.sum(Flight.price).desc()).all()[:5]
    #year
    year_start = date.today() - relativedelta(years = 1)
    year_end = date.today() + relativedelta(days = 1)
    top_tickets_year = Booking_agent.query.join(Ticket, (Ticket.booking_agent_ID == Booking_agent.booking_agent_id)) \
                                            .with_entities(Booking_agent.email, Booking_agent.booking_agent_id, db.func.count(Ticket.ticket_id)) \
                                            .filter((Ticket.date_purchased > year_start) & (Ticket.date_purchased < year_end) & (Ticket.airline_name == line)) \
                                            .group_by(Booking_agent.email, Booking_agent.booking_agent_id) \
                                            .order_by(db.func.count(Ticket.ticket_id).desc()).all()[:5]
    top_commission_year = Booking_agent.query.join(Ticket, (Ticket.booking_agent_ID == Booking_agent.booking_agent_id)) \
                                            .join(Flight, (Ticket.flight_num == Flight.flight_num) & (Ticket.airline_name == Flight.airline_name)) \
                                            .filter((Ticket.date_purchased > year_start) & (Ticket.date_purchased < year_end) & (Ticket.airline_name == line)) \
                                            .with_entities(Booking_agent.email, Booking_agent.booking_agent_id, db.func.sum(Flight.price) * .15) \
                                            .group_by(Booking_agent.email, Booking_agent.booking_agent_id).order_by(db.func.sum(Flight.price).desc()).all()[:5]
    return render_template("agent/bookingagents.html", permissions = Permission, top_tickets_month=top_tickets_month, top_tickets_year=top_tickets_year, top_commission_month = top_commission_month, top_commission_year=top_commission_year)

@agent.route('/customers', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_AIRLINES)
def customers():
#      Airline Staff will also be able to see the most frequent customer within
#       the last year. In addition, Airline Staff will be able to see a list of all flights a particular Customer has
#       taken only on that particular airline.
    line = (Airline_staff.query.filter(Airline_staff.user_id == current_user.user_id).first()).airline
    default_start = date.today() - relativedelta(years = 1)
    default_end = date.today() + relativedelta(days = 1)
    form = CustomerSearchForm()
    all_customers = Customer.query.join(Ticket, (Customer.email == Ticket.customer_email)).filter(Ticket.airline_name == line).all()
    form.customers.choices = [("None", 'Optional')] + [(i.email, i.email + ", " + i.first_name + " " + i.last_name) for i in all_customers]
    customers = Customer.query.join(Ticket, (Customer.email == Ticket.customer_email)) \
                                .filter((Ticket.airline_name == line) & (Ticket.date_purchased > default_start) & (Ticket.date_purchased < default_end)) \
                                .with_entities(Customer.email, Customer.first_name, Customer.last_name, Customer.passport_country, db.func.count(Customer.email)).group_by(Customer.email, Customer.first_name, Customer.last_name,) \
                                .order_by(db.func.count(Customer.email).desc()).all()
    if form.validate_on_submit():
        if form.customers.data != "None":
            chosen = form.customers.data
            default_start = form.start_date.data
            default_end = form.end_date.data + relativedelta(days = 1)
            customers = Customer.query.join(Ticket, (Customer.email == Ticket.customer_email)) \
                                        .with_entities(Customer.email, Customer.first_name, Customer.last_name, Customer.passport_country, db.func.count(Customer.email)) \
                                        .filter((Ticket.airline_name == line) & (Ticket.date_purchased > default_start) & (Ticket.date_purchased < default_end) & (Customer.email == chosen)) \
                                        .group_by(Customer.email, Customer.first_name, Customer.last_name) \
                                        .order_by(db.func.count(Customer.email).desc()).all()
        else:
            default_start = form.start_date.data
            default_end = form.end_date.data + relativedelta(days = 1)
            customers = Customer.query.join(Ticket, (Customer.email == Ticket.customer_email)) \
                                        .filter((Ticket.airline_name == line) & (Ticket.date_purchased > default_start) & (Ticket.date_purchased < default_end)) \
                                        .with_entities(Customer.email, Customer.first_name, Customer.last_name, Customer.passport_country, db.func.count(Customer.email)).group_by(Customer.email, Customer.first_name, Customer.last_name) \
                                        .order_by(db.func.count(Customer.email).desc()).all()
        return render_template('agent/customerinfo.html', permissions = Permission, customers = customers, form = form)
    return render_template('agent/customerinfo.html', permissions = Permission, customers = customers, form = form)

@agent.route('/customerflightinfo/<cust_id>', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_AIRLINES)
def customerflightinfo(cust_id):
    line = (Airline_staff.query.filter(Airline_staff.user_id == current_user.user_id).first()).airline
    flights = Ticket.query.join(Flight, (Flight.airline_name == Ticket.airline_name) & (Flight.flight_num == Ticket.flight_num)) \
                            .filter((Ticket.customer_email == cust_id) & (Ticket.airline_name == line)).order_by(Flight.departure_date.desc()).all()
    customer = Customer.query.filter(Customer.email == cust_id).all()[0]
    print(customer)
    return render_template('agent/customerflightinfo.html', permissions = Permission, flights = flights, customer = customer)

@agent.route('/stats', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_AIRLINES)
def stats():
    line = (Airline_staff.query.filter(Airline_staff.user_id == current_user.user_id).first()).airline
    default_start = date.today() - relativedelta(months = 6)
    default_end = date.today() + relativedelta(days = 1)
    tickets_sold = Ticket.query.filter((Ticket.airline_name == line) & (Ticket.date_purchased > default_start) & (Ticket.date_purchased < default_end)).with_entities(Ticket.date_purchased, Ticket.ticket_id).all()
    form = StatsForm()
    months = {}
    month_start = default_start
    while month_start <= default_end:
        key = datetime.strptime((month_start).strftime("%Y-%m-01"), "%Y-%m-%d")
        print(key)
        months[key] = 0
        month_start += relativedelta(months=1)
    total_tickets = 0
    for i, j in tickets_sold:
        key = datetime.strptime(i.strftime("%Y-%m-01"), "%Y-%m-%d")
        if key in months:
            months[key] += 1
        else:
            months[key] = 1
        total_tickets += 1
    direct_revenue = Ticket.query.join(Flight, (Ticket.airline_name == Flight.airline_name) & (Ticket.flight_num == Flight.flight_num)) \
                                .filter((Ticket.airline_name == line) & (Ticket.date_purchased > default_start) & (Ticket.date_purchased < default_end) & (Ticket.booking_agent_ID == None)) \
                                .with_entities(db.func.sum(Flight.price)).first()[0];
    agent_revenue = Ticket.query.join(Flight, (Ticket.airline_name == Flight.airline_name) & (Ticket.flight_num == Flight.flight_num)) \
                                .filter((Ticket.airline_name == line) & (Ticket.date_purchased > default_start) & (Ticket.date_purchased < default_end) & (Ticket.booking_agent_ID != None)) \
                                .with_entities(db.func.sum(Flight.price)).first()[0];
    print(direct_revenue, agent_revenue)
    if form.validate_on_submit():
        default_start = form.start_date.data
        default_end = form.end_date.data + relativedelta(days = 1)
        tickets_sold = Ticket.query.filter((Ticket.airline_name == line) & (Ticket.date_purchased > default_start) & (Ticket.date_purchased < default_end)).with_entities(Ticket.date_purchased, Ticket.ticket_id).all()
        months = {}
        month_start = default_start
        while month_start <= default_end:
            key = datetime.strptime((month_start).strftime("%Y-%m-01"), "%Y-%m-%d")
            print(key)
            months[key] = 0
            month_start += relativedelta(months=1)
        total_tickets = 0
        for i, j in tickets_sold:
            key = datetime.strptime(i.strftime("%Y-%m-01"), "%Y-%m-%d")
            if key in months:
                months[key] += 1
            else:
                months[key] = 1
            total_tickets += 1
        direct_revenue = Ticket.query.join(Flight, (Ticket.airline_name == Flight.airline_name) & (Ticket.flight_num == Flight.flight_num)) \
                                    .filter((Ticket.airline_name == line) & (Ticket.date_purchased > default_start) & (Ticket.date_purchased < default_end) & (Ticket.booking_agent_ID == None)) \
                                    .with_entities(db.func.sum(Flight.price)).first()[0];
        agent_revenue = Ticket.query.join(Flight, (Ticket.airline_name == Flight.airline_name) & (Ticket.flight_num == Flight.flight_num)) \
                                    .filter((Ticket.airline_name == line) & (Ticket.date_purchased > default_start) & (Ticket.date_purchased < default_end) & (Ticket.booking_agent_ID != None)) \
                                    .with_entities(db.func.sum(Flight.price)).first()[0];
        if not direct_revenue:
            direct_revenue = 0
        if not agent_revenue:
            agent_revenue = 0
        return render_template('agent/stats.html', permissions = Permission, form = form, months = months, total_tickets = total_tickets, direct_revenue = direct_revenue, agent_revenue = agent_revenue)
    return render_template('agent/stats.html', permissions = Permission, form = form, months = months, total_tickets = total_tickets, direct_revenue = direct_revenue, agent_revenue = agent_revenue)

@agent.route('/topdest', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_AIRLINES)
def topdest():
    #. View Top destinations: Find the top 3 most popular destinations for last 3 months and last year.
    line = (Airline_staff.query.filter(Airline_staff.user_id == current_user.user_id).first()).airline
    default_start = date.today() - relativedelta(months = 6)
    default_end = date.today() + relativedelta(days = 1)
    form = TopDestForm()
    n = 3
    top_n = Flight.query.join(Ticket, (Flight.airline_name == Ticket.airline_name) & (Flight.flight_num == Ticket.flight_num)) \
                        .join(Airport, (Airport.name == Flight.arrival)) \
                        .filter((Flight.airline_name == line) & (Ticket.date_purchased > default_start) & (Ticket.date_purchased < default_end)) \
                        .with_entities(Airport.city, db.func.count(Ticket.ticket_id)).group_by(Airport.city).order_by(db.func.count(Ticket.ticket_id).desc()) \
                        .all()[0:n]
    if form.validate_on_submit:
        n = form.top_n.data
        default_start = form.start_date.data
        default_end = form.end_date.data
        top_n = Flight.query.join(Ticket, (Flight.airline_name == Ticket.airline_name) & (Flight.flight_num == Ticket.flight_num)) \
                            .join(Airport, (Airport.name == Flight.arrival)) \
                            .filter((Flight.airline_name == line) & (Ticket.date_purchased > default_start) & (Ticket.date_purchased < default_end)) \
                            .with_entities(Airport.city, db.func.count(Ticket.ticket_id)).group_by(Airport.city).order_by(db.func.count(Ticket.ticket_id).desc()) \
                            .all()[0:n]
        return render_template('agent/topdest.html', permissions = Permission, form = form, top_n = top_n, line = line)
    return render_template('agent/topdest.html', permissions = Permission, form = form, top_n = top_n, line = line)

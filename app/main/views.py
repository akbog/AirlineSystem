from datetime import datetime
from flask import render_template, session, redirect, url_for
from . import main
from .. import db
from ..auth.forms import CustomerLoginForm

from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from ..models import Customer, User, Booking_agent, Airline_staff, Airport, Flight
from .forms import ExploreForm

@main.route('/', methods = ['GET','POST'])
def index():
    form = ExploreForm()
    loginform = CustomerLoginForm()
    airports = [(i,i) for (i,) in db.session.query(Airport.name).all()]
    form.departure_airport.choices = airports
    form.arrival_airport.choices = airports
    if loginform.validate_on_submit():
        cust = Customer.query.filter_by(email=loginform.email.data).first()
        user = User.query.filter_by(user_id = cust.user_id).first()
        if cust is not None and user.verify_password(loginform.password.data):
            login_user(user, loginform.remember_me.data)
            #if login form was presented to the user to prevent
            #unauthorized access to a protected URL, Flask-Login
            #Saves the original URL in the next query string
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid email or password.')
    if form.validate_on_submit():
        #Code for querrying the tables to bring results of flights
        #flights = Flight.query.filter(arrival_time <= form.return_date.data, departure_time >= form.departure_date.data).filter_by(departure = form.departure_airport.data, arrival = form.arrival_airport.data)
        pass
    return render_template('index.html', explore_form = form, login_form = loginform)

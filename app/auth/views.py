from flask import render_template, redirect, request, url_for, flash
from . import auth
from flask_login import login_user, login_required, logout_user, current_user
from ..models import Customer, User, Booking_agent, Airline_staff, Airport
from .forms import CustomerLoginForm, CustomerRegistrationForm, AgentLoginForm, PartnerLoginForm
from ..email import send_email
from .. import db
import re

@auth.route('/customerlogin', methods = ['GET','POST'])
def customerlogin():
    form = CustomerLoginForm()
    if form.validate_on_submit():
        cust = Customer.query.filter_by(email=form.email.data).first()
        user = User.query.filter_by(user_id = cust.user_id).first()
        if cust is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            #if login form was presented to the user to prevent
            #unauthorized access to a protected URL, Flask-Login
            #Saves the original URL in the next query string
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid email or password.')
        #if the username or password is incorrect, form is
        #rendered again
    return render_template('auth/customerlogin.html', form = form)

@auth.route('/agentlogin', methods = ['GET', 'POST'])
def agentlogin():
    form = AgentLoginForm()
    if form.validate_on_submit():
        agent = Booking_agent.query.filter_by(booking_agent_id = form.booking_agend_id.data, email = form.email.data).first()
        user = User.query.filter_by(user_id = agent.user_id).first()
        if agent is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid Login Credentials.')
    return render_template('auth/agentlogin.html', form = form)

@auth.route('/partnerlogin', methods = ['GET', 'POST'])
def partnerlogin():
    form = PartnerLoginForm()
    if form.validate_on_submit():
        partner = Airline_staff.query.filter_by(username = form.username.data).first()
        user = User.query.filter_by(user_id = partner.user_id).first()
        if partner is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid Login Credentials.')
    return render_template('auth/partnerlogin.html', form = form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@auth.route('/register', methods = ['GET', 'POST'])
def register_customer():
    form = CustomerRegistrationForm()
    airports = db.session.query(Airport.name).all()
    print(airports)
    form.passport_country.choices = [('country',i) for (i,) in airports]
    if form.validate_on_submit():
        user = User(password = form.password.data)
        db.session.add(user)
        db.session.commit()
        cust = Customer(email = form.email.data,
                        first_name = form.first_name.data,
                        last_name = form.last_name.data,
                        middle_name = form.middle_name.data,
                        passport_num = form.passport_num.data,
                        passport_expir = form.passport_expir.data,
                        passport_country = form.passport_country.data,
                        date_of_birth = form.date_of_birth.data,
                        user = user)
        db.session.add(cust)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(cust.email, 'Confirm Your Account',
                    'auth/email/confirm', user=cust, token=token)
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('auth.customerlogin'))
    return render_template('auth/register.html', form = form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))

@auth.before_app_request
def before_request():
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint \
            and request.endpoint[:5] != 'auth.' \
            and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))


#The current_user variables used in the conditional is
#defined by Flask-Login and is automatically available
#to view functions and templates

from flask import Flask, session
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
# from flask_session import Session
from config import config

bootstrap = Bootstrap()
moment = Moment()
db = SQLAlchemy()
mail = Mail()
# sess = Session()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.customerlogin'

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    moment.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    # sess.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix = '/auth')

    from .booking import booking as booking_blueprint
    app.register_blueprint(booking_blueprint, url_prefix = '/booking')

    from .agent import agent as agent_blueprint
    app.register_blueprint(agent_blueprint, url_prefix = '/agent')

    return app

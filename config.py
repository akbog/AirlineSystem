import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'password'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') #os.environ.get('MAIL_PASSWORD')
    SYSTEM_MAIL_SUBJECT_PREFIX = '[HEALTHHub]'
    SYSTEM_MAIL_SENDER = 'alexkbog@gmail.com'
    SYSTEM_ADMIN = os.environ.get('SYSTEM_ADMIN')


    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI')

config = {
    'development':DevelopmentConfig,

    'default':DevelopmentConfig
}

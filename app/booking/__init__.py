from flask import Blueprint

booking = Blueprint('booking',__name__)

from . import views
from ..models import Permission

@booking.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)

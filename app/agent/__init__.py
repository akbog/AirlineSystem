from flask import Blueprint

agent = Blueprint('agent',__name__)

from . import views
from ..models import Permission

@agent.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)

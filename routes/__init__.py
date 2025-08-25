from flask import Blueprint

auth_bp = Blueprint("auth", __name__, template_folder="../templates")
jobs_bp = Blueprint("jobs", __name__, template_folder="../templates")

from . import auth 
from . import jobs
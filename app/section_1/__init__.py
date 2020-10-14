from flask import Blueprint

section_1 = Blueprint('section_1', __name__)

from . import views

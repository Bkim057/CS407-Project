import re
from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from numpy import delete
from .models import User, Post
from . import db
from werkzeug.security import generate_password_hash

muscle_groups = Blueprint('muscle_groups', __name__)

@muscle_groups.route('/muscles_page')
def muscles_page():
    return render_template('muscle_groups.html')

@muscle_groups.route('/muscle_page/upper_body')
def upper_body_page():
    return render_template('upper_body.html')

@muscle_groups.route('/muscle_page/core')
def core_page():
    return render_template('core.html')

@muscle_groups.route('/muscle_page/lower_body')
def lower_body_page():
    return render_template('lower_body.html')
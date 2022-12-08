import re
from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash

# from . import generate_confirmation_token, confirm_token
from datetime import datetime
from .models import User
from flask_login import login_user, login_required, logout_user, current_user
from . import db
from .email_test import send_email
from .token import generate_confirmation_token, confirm_token

auth = Blueprint('auth', __name__)
confirmed = True
# Login page
@auth.route('/login')
def login():
    return render_template('login.html')
    

@auth.route('/login', methods=['POST'])
def login_post():
    global confirmed
    # Grab information User passed to login fields
    email = request.form.get('email')
    password = request.form.get('password')
    remember = False
    if request.form.get('remember'):
        remember = True

    # Ensure that all the fields are filled in
    user = User.query.filter_by(email=email).first()
    if not email or not password:
        flash('PLEASE FILL OUT ALL DAH FIELDS')
        return redirect(url_for('auth.login'))
    
    # If the user is not in the database or login info is incorrect
    if not user or not check_password_hash(user.password, password): 
        flash('Login credentials were incorrect or User does not exist.')
        return redirect(url_for('auth.login'))

    if not confirmed:
        # TODO: user must be set after verifying it is a valid user from database
        flash('Make sure to confirm your email')
        return redirect(url_for('auth.login'))
    login_user(user, remember=remember)

    # Good2go login and send user to profile
    return redirect(url_for('prof.profile'))

@auth.route('/guest_login')
def login_guest():
    global confirmed
    # Ensure that all the fields are filled in
    user = User.query.filter_by(id=-1).first()
    login_user(user, remember=False)
    # Good2go login and send user to profile
    return redirect(url_for('main.index'))

# Signup page
@auth.route('/signup')
def signup():
    return render_template('signup.html')

# Signup function
@auth.route('/signup', methods=['POST'])
def signup_post():
    global confirmed
    # Grab all the information User passed to Signup fields
    # TODO: Change with information actually to be used, doing so will
    #       require an update to signup.html as well as login.html
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first() 
    confirmed = False
    if not email or not name or not password:
        flash('PLEASE FILL OUT ALL DAH FIELDS')
        return redirect(url_for('auth.signup'))

    # TODO: Validate new user. Use above bool var, he_do_exist
   
    token = generate_confirmation_token(email)
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    html = render_template('activate.html', confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_email(email, subject, html)
    if user: # If the user do already be in the database, go back
        flash('YOU ALREADY EXIST GET OUTTA HERE BUDDY')
        confirmed = True
        return redirect(url_for('auth.signup'))

    # Create a new User with passed information
    # TODO: Create User with passed information into database
    new_dude = User(email=email, name=name, password=generate_password_hash(password, method='sha256'), chat_restriction=True, admin=False)

    # TODO: Add new guy to database
    
    db.session.add(new_dude)
    db.session.commit()
    # Send user back to login page
    return redirect(url_for('auth.login'))

# Logout function
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/confirm/<token>')
@login_required
def confirm_email(token):
    global confirmed
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
    user = User.query.filter_by(email=email).first_or_404()
    if confirmed is True:
        flash('Account already confirmed. Please login.', 'success')
    else:

        print("LINK CLICKED!", confirmed)
        # user.confirmed_on = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()
        email = request.form.get('email')
        user = User.query.filter_by(email=email)
        if user:
            confirmed = True
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('main.index'))
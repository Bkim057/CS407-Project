from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask_login import login_required, current_user
from . import db

calc = Blueprint('calc', __name__)


# Display all currently available topics
@calc.route('/calc_page')
def calc_page():
    return render_template('calc.html')

@calc.route('/calc_page', methods=['POST'])
def calc_post():
    # Grab all information for calculation
    gender = request.form.get('gender')
    age = request.form.get('age')
    weight = request.form.get('weight')
    height = request.form.get('height')
    activity = request.form.get('activity')

    # Clean some of the info for integer use
    try:
        age_num = int(age)
        weight_num = int(weight)
    except:
        flash('Make sure age, weight, and bodyfat are integer values')
        return render_template('calc.html')
    
    height_num = int(height)
    activity_num = float(activity)
    
    # Debug print all accepted values
    # print("Gender >>> " + gender)
    # print("Age >>> " + str(age_num))
    # print("Weight >>> " + str(weight_num))
    # print("Height >>> " + str(height_num))
    # print("Activity >>> " + str(activity_num))

    # Do actual calculation
    bmr = 0
    if (gender == "male"):
        bmr = 66 + (13.7 * (weight_num / 2.2)) + (5 * (height_num * 2.54)) - (6.8 * age_num)
    if (gender == "female"):
        bmr = 655 + (9.6 * (weight_num / 2.2)) + (1.8 * (height_num * 2.54)) - (4.7 * age_num)

    # print("BMR WAS >>> " + str(bmr))

    tdee = bmr * activity_num

    flash('Your TDEE is ' + str(int(tdee)) + ' calories a day')
    return render_template('calc.html')
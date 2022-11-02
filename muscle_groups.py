import re
from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask import session as cur_session
from flask_login import login_required, current_user
from numpy import delete
from .models import User, Post, Workout, Muscle
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

@muscle_groups.route('/muscle_page/workout_splits')
def workout_splits():
    return render_template('workout_splits.html')

@muscle_groups.route('/like_workout/<id>')
def like_workout(id):
    workout = Workout.query.filter_by(id=id).first()
    if current_user.is_disliking_exercise(workout): 
        undislike_workout(id) 
    #target_muscle = Muscle.query.filter_by(name=id).first()
    if current_user.is_liking_exercise(workout):
        return redirect(url_for('muscle_groups.muscles_page'))
    workout.likes += 1
    current_user.like_exercise(workout)
    db.session.commit()
    if 'url' in cur_session:
        return redirect(cur_session['url'])
    else:
        return redirect(url_for('muscle_groups.muscles_page'))
    

@muscle_groups.route('/unlike_workout/<id>')
def unlike_workout(id):
    workout = Workout.query.filter_by(id=id).first()
    if workout is None:
        return redirect(url_for('index', id=id))
    workout.likes -= 1
    current_user.remove_like(workout)
    db.session.commit()
    if 'url' in cur_session:
        return redirect(cur_session['url'])
    else:
        return redirect(url_for('muscle_groups.muscles_page'))

@muscle_groups.route('/dislike_workout/<id>')
def dislike_workout(id):
    workout = Workout.query.filter_by(id=id).first()
    if current_user.is_liking_exercise(workout): 
        unlike_workout(id) 
    #target_muscle = Muscle.query.filter_by(name=id).first()
    if current_user.is_disliking_exercise(workout):
        return redirect(url_for('muscle_groups.muscles_page'))
    workout.dislikes += 1
    current_user.dislike_exercise(workout)
    db.session.commit()
    if 'url' in cur_session:
        return redirect(cur_session['url'])
    else:
        return redirect(url_for('muscle_groups.muscles_page'))

@muscle_groups.route('/undislike_workout/<id>')
def undislike_workout(id):
    workout = Workout.query.filter_by(id=id).first()
    if workout is None:
        return redirect(url_for('index', id=id))
    workout.dislikes -= 1
    current_user.remove_dislike(workout)
    db.session.commit()
    if 'url' in cur_session:
        return redirect(cur_session['url'])
    else:
        return redirect(url_for('muscle_groups.muscles_page'))

@muscle_groups.route('/view_workout/<id>')
def view_workout(id):
    cur_session['url'] = request.url
    # query for the id
    print(id)
    target_muscle = Muscle.query.filter_by(name=id).first()
    workout_objs = Workout.query.all()

    workout_html = ""
    for workout in workout_objs:
        muscles_worked = [muscle_group.name for muscle_group in workout.muscle_groups]
        if (muscles_worked):
            muscles_worked.sort()
        if (target_muscle.name in muscles_worked):
            muscles_worked_list = ""
            for mn in muscles_worked:
                muscles_worked_list += mn + " ,"

            muscles_worked_list = muscles_worked_list[:-1]
            workout_html += f"<div class=\"column is-half is-offset-one-quarter\">\
                <div class=\"box\">\
                    <div class=\"content\">\
                        <h3 class=\"title is-3 has-text-black has-text-left\">{workout.exercise_name}</h3>\
                        <h4 class=\"has-text-left has-text-black\">targetted muscles: {muscles_worked_list}</h4>\
                        <p class=\"has-text-left\">{workout.description}</p>\
                        <button class=\"button is-block is-info is-medium is-fullwidth\" value=\"Post Created\" name=\"action\" button\
                            style=\"margin: 5px;\"><a href=\"{workout.URL}\">workout\
                                details</a></button>"
            if (current_user.is_liking_exercise(workout)):
                workout_html  += f"<form action=\"/unlike_workout/"+str(workout.id)+"\">\
                    <button>Remove Like</button>\
                        </form>"
            else:
                workout_html  += f"<form action=\"/like_workout/"+str(workout.id)+"\">\
                    <button>Like</button>\
                        </form>"

            if (current_user.is_disliking_exercise(workout)):
                workout_html  += f"<form action=\"/undislike_workout/"+str(workout.id)+"\">\
                    <button>Remove Dislike</button>\
                        </form>"
            else:
                workout_html  += f"<form action=\"/dislike_workout/"+str(workout.id)+"\">\
                    <button>Dislike</button>\
                        </form>"


            workout_html += f"</div>\
                <div class=\"level-left\">\
              <p>\
                Likes: " + str(workout.likes) + "</p>\
              </div>\
                <div class=\"level-left\">\
              <p>\
                Dislikes: " + str(workout.dislikes) + "</p>\
              </div>\
                </div>\
            </div>"



    return render_template('view_exercise.html', workout_html=workout_html)
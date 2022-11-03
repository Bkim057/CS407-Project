import re
from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask import session as cur_session
from flask_login import login_required, current_user
from numpy import delete
from .models import User, Post, Workout, Muscle, saved_workout, workout_muscle_groups
from . import db, share
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
    print(cur_session)
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

@muscle_groups.route('/save_workout/<id>')
def save_workout(id):
    workout = Workout.query.filter_by(id=id).first()
    if current_user.has_saved_workout(workout):
        flash('workout already saved!')
        return redirect(url_for('muscle_groups.muscles_page'))
    current_user.save_workout(workout)
    db.session.commit()
    if 'url' in cur_session:
        return redirect(cur_session['url'])
    else:
        return redirect(url_for('muscle_groups.muscles_page'))

@muscle_groups.route('/unsave_workout/<id>')
def unsave_workout(id):
    workout = Workout.query.filter_by(id=id).first()
    if workout is None:
        return redirect(url_for('index', id=id))
    current_user.unsave_workout(workout)
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
                        <button class=\"button is-block is-black is-medium is-fullwidth\" value=\"Post Created\" name=\"action\" button\
                            style=\"margin: 5px;\"><a href=\"{workout.URL}\">workout\
                                details</a></button><div class=\"field is-grouped\" style=\"padding-top: 10px;\">"
            workout_html += "<p class=\"control\">"
            if (current_user.id != -1): 
                if (not current_user.has_saved_workout(workout)):
                    workout_html += f"<form action=\"/save_workout/"+str(workout.id)+"\">\
                            <button class=\"button is-primary is-outlined is-small\">Save</button>\
                                </form>"
                else:
                    workout_html += f"<form action=\"/unsave_workout/"+str(workout.id)+"\">\
                            <button class=\"button is-primary is-small\">Unsave</button>\
                                </form>"
            workout_html += "</p>"
            workout_html += "<p class=\"control\">"
            if (current_user.is_liking_exercise(workout)):
                workout_html  += f"<form action=\"/unlike_workout/"+str(workout.id)+"\">\
                    <button class=\"button is-link is-small\">Remove Like</button>\
                        </form>"
            else:
                workout_html  += f"<form action=\"/like_workout/"+str(workout.id)+"\">\
                    <button class=\"button is-link is-small is-outlined\">Like</button>\
                        </form>"
            workout_html += "</p>"
            workout_html += "<p class=\"control\">"
            if (current_user.is_disliking_exercise(workout)):
                workout_html  += f"<form action=\"/undislike_workout/"+str(workout.id)+"\">\
                    <button class=\"button is-danger is-small\">Remove Dislike</button>\
                        </form>"
            else:
                workout_html  += f"<form action=\"/dislike_workout/"+str(workout.id)+"\">\
                    <button class=\"button is-danger is-outlined is-small\">Dislike</button>\
                        </form>"
            workout_html += "</p>"
            workout_html += f"</div></div>\
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

@muscle_groups.route('/saved_workout_list/<id>')
def saved_workout_list(id):
    cur_session['url'] = request.url
    saved_workouts_obj = db.session.query(saved_workout).all()
    saved_workout_html = ""
    for s_workout in saved_workouts_obj:
        muscle_name_list = ""
        if str(s_workout.user_id) == str(id):
            workout_info = Workout.query.filter_by(id=s_workout.workout_id).first()

            muscle_names = db.session.query(workout_muscle_groups).filter_by(workout_id=workout_info.id)
            for musc_obj in muscle_names:
                muscle_name_list += musc_obj.muscle + ", "

            if muscle_name_list:
                muscle_name_list = muscle_name_list[:-2]

            saved_workout_html += f"<html><div class=\"column is-half is-offset-one-quarter\">\
                <div class=\"box\">\
                    <div class=\"content\">\
                        <h3 class=\"title is-3 has-text-black has-text-left\">{workout_info.exercise_name}</h3>\
                        <h4 class=\"has-text-left has-text-black\">targetted muscles: {muscle_name_list}</h4>\
                        <p class=\"has-text-left\">{workout_info.description}</p>\
                        <button class=\"button is-block is-black is-medium is-fullwidth\" value=\"Post Created\" name=\"action\" button\
                            style=\"margin: 5px;\"><a href=\"{workout_info.URL}\">workout\
                                details</a></button><div class=\"field is-grouped\" style=\"padding-top: 10px;\">"
            if (current_user.is_authenticated and str(current_user.id) == str(id)):
                saved_workout_html += "<p class=\"control\">"
                if (current_user.id != -1): 
                    if (not current_user.has_saved_workout(workout_info)):
                        saved_workout_html += f"<form action=\"/save_workout/"+str(workout_info.id)+"\">\
                                <button class=\"button is-primary is-outlined is-small\">Save</button>\
                                    </form>"
                    else:
                        saved_workout_html += f"<form action=\"/unsave_workout/"+str(workout_info.id)+"\">\
                                <button class=\"button is-primary is-small\">Unsave</button>\
                                    </form>"
                saved_workout_html += "</p>"
                saved_workout_html += "<p class=\"control\">"
                if (current_user.is_liking_exercise(workout_info)):
                    saved_workout_html  += f"<form action=\"/unlike_workout/"+str(workout_info.id)+"\">\
                        <button class=\"button is-link is-small\">Remove Like</button>\
                            </form>"
                else:
                    saved_workout_html  += f"<form action=\"/like_workout/"+str(workout_info.id)+"\">\
                        <button class=\"button is-link is-small is-outlined\">Like</button>\
                            </form>"
                saved_workout_html += "</p>"
                saved_workout_html += "<p class=\"control\">"
                if (current_user.is_disliking_exercise(workout_info)):
                    saved_workout_html  += f"<form action=\"/undislike_workout/"+str(workout_info.id)+"\">\
                        <button class=\"button is-danger is-small\">Remove Dislike</button>\
                            </form>"
                else:
                    saved_workout_html  += f"<form action=\"/dislike_workout/"+str(workout_info.id)+"\">\
                        <button class=\"button is-danger is-outlined is-small\">Dislike</button>\
                            </form>"
                saved_workout_html += "</p></div>"
                saved_workout_html += f"<div class=\"level-left\">\
                <p>\
                    Likes: " + str(workout_info.likes) + "</p>\
                </div>\
                    <div class=\"level-left\">\
                <p>\
                    Dislikes: " + str(workout_info.dislikes) + "</p>\
                </div>"
            saved_workout_html += f"</div></div></div>"

    
    saved_workout_html += f"<head>\
        <meta charset=\"UTF-8\">\
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\
        <title>Flask-Share Demo</title>\
        {share.load()}\
    </head>\
    <body>\
            { share.create(title='Share with: ',sites='facebook,twitter,wechat',mobile_sites='facebook,twitter,wechat') }\
    </body></html>"
    return render_template('saved_workout_list.html', saved_workout_html=saved_workout_html)
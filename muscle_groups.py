import re
from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask import session as cur_session
from flask_login import login_required, current_user
from numpy import delete
from .models import User, Post, Workout, Muscle, Workout_Comment, saved_workout, workout_muscle_groups
from . import db, share
from werkzeug.security import generate_password_hash
from collections import defaultdict

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

@muscle_groups.route('/muscle_page/workout_splits/workout_planner')
def workout_planner():
    workout_list = Workout.query.all()
    all_workouts = "<option value=\"none\" selected>none</option>"
    for workout in workout_list:
        all_workouts += f'<option value=\"{workout.exercise_name}\">{workout.exercise_name}</option>'


    workout_html = ''
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
        workout_html += f'<h3 class=\"title\">{day}</h3>'
        workout_html += f'<div class=\"box\"><table>'
        for i in range(1,7):
            workout_html += f'<tr><td class=\"col1\"><label for=\"exercise\">Exercise#{i}</label></td>\
            <td><select name=\"{day+str(i)}\" class=\"form-control\" id=\"exercise\">{all_workouts}</select></td></tr>'
        workout_html += f'</table></div>'

    return render_template('workout_planner.html', workout_html=workout_html)

@muscle_groups.route('/muscle_page/workout_splits/workout_planned', methods=['POST'])
def workout_planned():
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    choices = request.form.items()
    split_dic = defaultdict(list)

    for choice in choices:
        if choice[0][:-1] in days and choice[1] != 'none':
            split_dic[choice[0][:-1]].append(choice[1])

    workout_plan_html = ''
    for day in days:
        workout_plan_html += f'<div class=\"column is-1.5\"><div class=\"box\">\
            <div class=\"content is-medium is-left has-text-left\"><h4>{day}</h4></div>\
            <div class=\"container has-text-left\">'
            
        if day not in split_dic:
            workout_plan_html += f'<p><strong>Rest</strong></p>'
        else:
            for exercise in split_dic[day]:
                workout_plan_html += f'<p>- {exercise}</p>'
        workout_plan_html += f'</div></div></div>'

    return render_template('workout_planned.html', workout_plan_html=workout_plan_html)

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

@muscle_groups.route("/create-workout-comment/<workout_id>", methods=['POST'])
@login_required
def create_workout_comment(workout_id):
  contents = request.form.get('text')

  if not contents:
    flash('Comment cannot be empty!', category='error')
  else:
    workout = Workout.query.filter_by(id=workout_id)
    if workout:
      comment = Workout_Comment(contents=contents, author=current_user.id, author_name=current_user.name,workout_id=workout_id)
      db.session.add(comment)
      db.session.commit()
    
  return redirect(cur_session['url'])

@muscle_groups.route("/delete-workout-comment/<comment_id>")
@login_required
def delete_workout_comment(comment_id):
  comment = Workout_Comment.query.filter_by(id=comment_id).first()

  if not comment:
    flash('Comment does not exist')
  else:
    db.session.delete(comment)
    db.session.commit()

  return redirect(cur_session['url'])
@muscle_groups.route('/upvote_workout/<id>')
def upvoted_workout(id):
    workout = Workout.query.filter_by(id=id).first()
    if current_user.downvoted_exercise(workout): 
        undownvote_workout(id) 
    if current_user.upvoted_exercise(workout):
        return redirect(url_for('muscle_groups.muscles_page'))
    workout.upvotes += 1
    current_user.upvote_exercise(workout)
    db.session.commit()
    print(cur_session)
    if 'url' in cur_session:
        return redirect(cur_session['url'])
    else:
        return redirect(url_for('muscle_groups.muscles_page'))
    

@muscle_groups.route('/unupvote_workout/<id>')
def unupvote_workout(id):
    workout = Workout.query.filter_by(id=id).first()
    if workout is None:
        return redirect(url_for('index', id=id))
    workout.upvotes -= 1
    current_user.remove_upvote(workout)
    db.session.commit()
    if 'url' in cur_session:
        return redirect(cur_session['url'])
    else:
        return redirect(url_for('muscle_groups.muscles_page'))

@muscle_groups.route('/downvote_workout/<id>')
def downvote_workout(id):
    workout = Workout.query.filter_by(id=id).first()
    if current_user.upvoted_exercise(workout): 
        unupvote_workout(id) 
    if current_user.downvoted_exercise(workout):
        return redirect(url_for('muscle_groups.muscles_page'))
    workout.downvotes += 1
    current_user.downvote_exercise(workout)
    db.session.commit()
    if 'url' in cur_session:
        return redirect(cur_session['url'])
    else:
        return redirect(url_for('muscle_groups.muscles_page'))

@muscle_groups.route('/undownvote_workout/<id>')
def undownvote_workout(id):
    workout = Workout.query.filter_by(id=id).first()
    if workout is None:
        return redirect(url_for('index', id=id))
    workout.downvotes -= 1
    current_user.remove_downvote(workout)
    db.session.commit()
    if 'url' in cur_session:
        return redirect(cur_session['url'])
    else:
        return redirect(url_for('muscle_groups.muscles_page'))

# Function to sort workouts
def myFunc(workout):
    vote_count = workout.downvotes - workout.upvotes; 
    return vote_count

@muscle_groups.route('/view_workout/<id>')
def view_workout(id):
    cur_session['url'] = request.url
    # query for the id
    print(id)
    target_muscle = Muscle.query.filter_by(name=id).first()
    workout_objs = Workout.query.all()
    workout_objs.sort(key=myFunc)

    workout_html = ""
    for workout in workout_objs:
        print("Processing..." + workout.exercise_name)
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
                        <h3 class=\"title is-3 has-text-black has-text-left\">{workout.exercise_name}</h3>"
            if (workout.video_link != None) and (workout.video_link != "") and ("https://www.youtube.com/embed/" in workout.video_link):
                workout_html += "<div class=\"Box-body\">\
                            <iframe width=\"360\" height=\"315\"\
                                src=\"" + workout.video_link + "\">\
                            </iframe>\
                        </div>"
            workout_html += f"<h4 class=\"has-text-left has-text-black\">targetted muscles: {muscles_worked_list}</h4>\
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
            workout_html += "<p class=\"control\">"
            if (current_user.upvoted_exercise(workout)):
                workout_html  += f"<form action=\"/unupvote_workout/"+str(workout.id)+"\">\
                    <button class=\"button is-info is-light is-small\">Remove Upvote</button>\
                        </form>"
            else:
                workout_html  += f"<form action=\"/upvote_workout/"+str(workout.id)+"\">\
                    <button class=\"button is-info is-light is-small is-outlined\">Upvote</button>\
                        </form>"
            workout_html += "</p>"
            workout_html += "<p class=\"control\">"
            if (current_user.downvoted_exercise(workout)):
                workout_html  += f"<form action=\"/undownvote_workout/"+str(workout.id)+"\">\
                    <button class=\"button is-warning is-light is-small\">Remove Downvote</button>\
                        </form>"
            else:
                workout_html  += f"<form action=\"/downvote_workout/"+str(workout.id)+"\">\
                    <button class=\"button is-warning is-light is-outlined is-small\">Downvote</button>\
                        </form>"
            workout_html += "</p>"
            vote_count = workout.upvotes - workout.downvotes;
            workout_html += f"</div></div>\
                <div class=\"level-left\">\
              <p>\
                Likes: " + str(workout.likes) + "</p>\
              </div>\
                <div class=\"level-left\">\
              <p>\
                Dislikes: " + str(workout.dislikes) + "</p>\
                </div>\
                <div class=\"level-left\">\
                <p>\
                Vote Count: " + str(vote_count) + "</p>\
                </div>"
            comment_bar = "<form class=\"input-group\" method='POST' action=\"/create-workout-comment/"+str(workout.id)+"\" >\
          <input type=\"text\" id=\"text\" name=\"text\" class =\"form-control\ placeholder=\"Comment something\" />\
          <button type=\"submit\" class=\"btn btn-primary\">Comment</button> </form> \
            <br>"
            if current_user.id != -1:
                workout_html += comment_bar
        for comment in workout.comments:
            comments = comment.contents
            if current_user.id == comment.author:
                poster = current_user.name
            else:
                author = User.query.filter_by(id=comment.author).first()
                poster = author.name
            third_section = "<p><strong>" + str(poster) + ": </strong>" + str(comments) + ""
            if current_user.id == comment.author or current_user.admin:
                fourth_section = "&nbsp; &nbsp; <a href=\"/delete-workout-comment/"+str(comment.id)+"\" style=\"color:red\">Delete</a></p>"
            else:
                fourth_section = ''
            workout_html += third_section
            workout_html += fourth_section
    
    workout_html += "</div>"
    workout_html += "</article>\
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
                        <h3 class=\"title is-3 has-text-black has-text-left\">{workout_info.exercise_name}</h3>"
            if (workout_info.video_link != None) and (workout_info.video_link != "") and ("https://www.youtube.com/embed/" in workout_info.video_link):
                saved_workout_html += "<div class=\"Box-body\">\
                            <iframe width=\"360\" height=\"315\"\
                                src=\"" + workout_info.video_link + "\">\
                            </iframe>\
                        </div>"
            saved_workout_html += f"<h4 class=\"has-text-left has-text-black\">targetted muscles: {muscle_name_list}</h4>\
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
            else:
                saved_workout_html += f"</div></div></div></div>"

    
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
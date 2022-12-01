import re
from flask import Blueprint, redirect, render_template, request, url_for, flash, jsonify
from flask import session as cur_session
from flask_login import login_required, current_user, UserMixin
from numpy import delete
import pusher
import sqlalchemy
from .models import User, Post, Topic, Commented, Message
from .posts import delete_comment, delete_post, post_to_html, pfp_to_html
from . import db
from werkzeug.security import generate_password_hash

prof = Blueprint('prof', __name__)

# Profile page
@prof.route('/profile')
@login_required
def profile():
    # TODO: post_to_html parameter is only for testing purposes, REMOVE 
    topic_list = []
    for topic_obj in current_user.followed_topics.all():
        topic_list.append(topic_obj.name)
    return render_template('profile.html', name = current_user.name, bio = current_user.bio, id = current_user.id, followed_topics = topic_list, post_to_html=post_to_html, pfp_to_html=pfp_to_html)

# Edit Profile Page
@prof.route('/edit_profile')
@login_required
def edit_profile():
    return render_template('edit_profile.html', name = current_user.name, bio = current_user.bio)

# Account delete and other functions, differentiated based on 'action's value
@prof.route('/profile', methods=['POST'])
@login_required
def profile_delete():
    # Deleting a user account and all of their associated data
    if request.form.get('action') == "Delete Account":
        usr_obj = User.query.filter_by(id=current_user.id).one()

        posts_for_user = Post.query.filter_by(user_id=usr_obj.id)
        for p in posts_for_user:
            print("type", type(p))
            #db.session.delete(p)
            delete_post(p.id)
        
        comments_for_user = Commented.query.filter_by(author=usr_obj.id)
        for c in comments_for_user:
            delete_comment(c.id)
        
        db.session.delete(usr_obj)
        db.session.commit()

        return redirect(url_for('auth.logout'))

    # TODO: Other buttons if they exist
    return redirect(url_for('prof.profile'))

# Access the Edit Profile page
@prof.route('/edit_profile', methods=['GET'])
@login_required
def show_edit_profile():
    return redirect(url_for('prof.edit_profile'))

# Functionality to update a user's profile
@prof.route('/edit_profile', methods=['POST'])
@login_required
def update_profile():
    if request.form.get('action') == "Edit Profile":
        print(request.form)
        print(request.files)

        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        bio = request.form.get('bio')
        file = request.files['pfp_file']
        delete_pfp = request.form.get('delete_pfp')
        isValidFile = False if not file else file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'))

        if not email:
            email = current_user.email
        else:
            email_exists = User.query.filter_by(email=email).first()

            if email_exists is not None:
                flash('That email is already in use!')
                return redirect(url_for('prof.profile')) 
        if not password:
            password = None
        else:
            password = generate_password_hash(request.form.get('password'), method='sha256')
        if not name:
            name = current_user.name
        if not bio:
            bio = current_user.bio

        user = current_user
        
        if (isValidFile):
            user.pfp_filename = file.filename
            user.pfp = file.read()
        if (delete_pfp):
            user.pfp_filename = None
            user.pfp = None

        user.email = email
        if password:
            user.password = password
        user.name = name
        user.bio = bio 
        db.session.merge(user)
        db.session.flush()
        db.session.commit()
    return redirect(url_for('prof.profile'))

# Function to turn a user into some html usable text
def user_to_html(user_id):
    user_to_view = User.query.get(user_id)

    # Grab and shorten bio if need be
    bio = user_to_view.bio
    if (isinstance(bio, type(None))):
        bio = "None"
    if (len(bio) > 20):
        bio = bio[0:20] + "..."
    # html conversion
    html_string =  "<div class=\"box\">\
                        <h3>Name: " + str(user_to_view.name) + "</h3>\
                        <h3>Bio: " + str(bio) + "</h3>\
                        <form action=\"/view_profile/" + str(user_id) + "\">\
                            <button>View this User</button>\
                        </form>\
                    </div>"
 
    return html_string

@prof.route('/handle_private/')
def make_private():
    if (current_user.private):
        current_user.private = False
        db.session.commit()
        return redirect(url_for('prof.profile'))
    current_user.private = True
    db.session.commit()
    return redirect(url_for('prof.profile'))

# Create a list of all the possible people a user could have been searching for
@prof.route('/search_user', methods=['GET'])
def search_user():
    # Grab what username was searched for, put list of possible users into possible_people
    username = request.args.get('search')
    possible_people = User.query.filter_by(name=username).all()
    everyone_get_in_here = ""

    # Using list of possible users, turn all users into html strings with their id's
    for i in range(len(possible_people)):
        id_cur = possible_people[i].id
        user = possible_people[i]
        print(id_cur)
        if (current_user.admin == False):
            if (not user.is_blocking(current_user) and not user.private):
                everyone_get_in_here += user_to_html(id_cur)
        else:
            everyone_get_in_here += user_to_html(id_cur)

    # String will be empty if no possible users were found, add the error
    if (len(everyone_get_in_here) == 0):
        everyone_get_in_here += "<div class=\"box\">\
                                    <h3>No Users of that username were found!</h3>\
                                 </div>"
    return render_template('search_users.html', users_string = everyone_get_in_here)
    

# View another user's profile
@prof.route('/view_profile/<id>')
def view_profile(id):
    user_to_view = User.query.get(id)
    return render_template('other_profile_view.html', user = user_to_view, name = user_to_view.name, bio = user_to_view.bio, id = id, followed_topics = list(user_to_view.followed_topics), pfp_to_html=pfp_to_html)

# Following another dude
@prof.route('/follow_user/<id>')
def follow_user(id):
    # id of user to be followed should be supplied by whatever is calling this
    #print(id)
    user = User.query.filter_by(id=id).first()
    if current_user.is_following(user):
        flash('Hey buddy I know you like this guy, but you\'re already following them')
        return redirect(url_for('prof.view_profile', id=id))
    if user == current_user:
        flash('Hey dude u cant follow yourself, like ur not that cool')
        return redirect(url_for('prof.view_profile', id=id))
    current_user.follow(user)
    flash('You are following {}!'.format(user.name))
    db.session.commit()
    return redirect(url_for('prof.view_profile', id=id))

# Unfollowing another dude
@prof.route('/unfollow_user/<id>')
def unfollow_user(id):
    # id of user to be unfollowed should be supplied by whatever is calling this
    #print(id)
    user = User.query.filter_by(id=id).first()
    if user is None:
        return redirect(url_for('index', id=id))
    if user == current_user:
        return redirect(url_for('user', id=id))
    current_user.unfollow(user)
    db.session.commit()
    return redirect(url_for('prof.view_profile', id=id))

@prof.route('/temp_admin_self/')
def admin_give():
    if (current_user.admin):
        current_user.admin = False
        db.session.commit()
        return redirect(url_for('prof.profile'))
    current_user.admin = True
    db.session.commit()
    return redirect(url_for('prof.profile'))

@prof.route('/temp_admin_other/<id>')
def admin_other_give(id):
    user = User.query.filter_by(id=id).first()
    if (user.admin):
        user.admin = False
        db.session.commit()
        return redirect(url_for('prof.view_profile', id=id))
    user.admin = True
    db.session.commit()
    return redirect(url_for('prof.view_profile', id=id))


@prof.route('/unrestrict_user/')
def unrestrict_user():
    current_user.chat_restriction = False
    db.session.commit()
    return redirect(url_for('prof.profile'))

@prof.route('/restrict_user/')
def restrict_user():
    current_user.chat_restriction = True
    db.session.commit()
    return redirect(url_for('prof.profile'))

@prof.route('/follow_topic/<id>')
def follow_topic(id):
    #topic = Topic.query.filter_by(id=id).first()
    if current_user.is_following_topic(id):
        flash('This topic is already followed!')
        return redirect(url_for('prof.view_topic', id=id))
    current_user.follow_topic(id)
    db.session.commit()
    if 'url' in cur_session:
        return redirect(cur_session['url'])
    else:
        return redirect(url_for('topics.view_topic', id=id, post_num=0))

@prof.route('/unfollow_topic/<id>')
def unfollow_topic(id):
    #topic = Topic.query.filter_by(id=id).first()
    if not current_user.is_following_topic(id):
        flash("You don't follow this muscle group!")
        return redirect(url_for('prof.view_topic', id=id))
    current_user.unfollow_topic(id)
    db.session.commit()
    if 'url' in cur_session:
            return redirect(cur_session['url'])
    else:
        return redirect(url_for('topics.view_topic', id=id, post_num=0))


# Chat server setup
pusher_client = pusher.Pusher(
app_id='1385712',
key='4eefb1b81ae21d331cbf',
secret='441266c2faec85226f05',
cluster='us2',
ssl=True
)

@prof.route('/chat_with/<id>')
def chat_with(id):

    user = User.query.filter_by(id=id).first()
    new_name = user.name

    # Can query only of the 2 id's that are chatting
    messages = Message.query.filter_by(username=current_user.name)
    messages2 = Message.query.filter_by(username=new_name)
    messages_total = messages.union(messages2)
    # messages_total = Message.query.all()
    #print(messages_total)
    #messages2 = Message.query.filter_by(username=new_name)

    return render_template('starting_template.html', messages=messages_total, curr_user=current_user, id=id)

@prof.route('/message', methods=['POST'])
def message():
    try:
        username = current_user.name
        message = request.form.get('message')
        db.create_all()
        new_message = Message(username=username, message=message)
        db.session.add(new_message)
        db.session.commit()

        pusher_client.trigger('chat-channel', 'new-message', {'username': username, 'message': message})
        return jsonify({'result' : 'success'})
    except:
        return jsonify({'result' : 'error'})

# Blocking an user
@prof.route('/block_user/<id>')
def block_user(id):
    user_to_block = User.query.filter_by(id=id).first()
    if current_user.is_blocking(user_to_block):
        flash('Hey buddy I know you dislike this guy, but you\'re already blocking them')
        return redirect(url_for('prof.view_profile', id=id))
    if user_to_block == current_user:
        flash('Hey dude u cant block yourself, seek counseling')
        return redirect(url_for('prof.view_profile', id=id))
    current_user.block(user_to_block)
    flash('You are blocking {}!'.format(user_to_block.name))
    db.session.commit()
    return redirect(url_for('prof.view_profile', id=id))

# Unblocking an user
@prof.route('/unblock_user/<id>')
def unblock_user(id):
    # id of user to be unfollowed should be supplied by whatever is calling this
    #print(id)
    user = User.query.filter_by(id=id).first()
    if user is None:
        return redirect(url_for('index', id=id))
    if user == current_user:
        return redirect(url_for('user', id=id))
    current_user.unblock(user)
    db.session.commit()
    return redirect(url_for('prof.view_profile', id=id))

# Added below for all following page
def followed_topic_to_html(name, id):
    html_string =  "<div class=\"box\">\
                            <h3>" + str(name) + "</h3>\
                            <form action=\"/unfollow_topic/" + str(id) + "\">\
                                <button>Unfollow!</button>\
                            </form>\
                        </div>"
    return html_string

def followed_user_to_html(name, id):
    html_string =  "<div class=\"box\">\
                            <h3>" + str(name) + "</h3>\
                            <form action=\"/unfollow_user/" + str(id) + "\">\
                                <button>Unfollow!</button>\
                            </form>\
                        </div>"
    return html_string

@prof.route('/all_following')
def all_following_page():
    # config topics
    topics = current_user.followed_topics.all()
    topics_html_string = ""
    if len(topics) == 0:
        topics_html_string += "<div class=\"box\">\
                                    <h3>You don't folllow any muscle groups!</h3>\
                                </div>"
    else:
        for topic in topics:
            name = topic.name
            id = topic.id
            topics_html_string += followed_topic_to_html(name, id)
    
    # config users
    users = current_user.followed.all()
    users_html_string = ""
    if len(users) == 0:
        users_html_string += "<div class=\"box\">\
                                    <h3>You don't folllow any users!</h3>\
                                </div>"
    else:
        for user in users:
            name = user.name
            id = user.id
            users_html_string += followed_user_to_html(name, id)
    
    # return
    return render_template('all_following.html', topics_string=topics_html_string, users_string=users_html_string)
            
# Added above for all following page
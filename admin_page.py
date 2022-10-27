from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask_login import login_required, current_user
from .models import User, Post, Topic, post_topic, liked_post, saved_post
from . import db
from .posts import post_to_approve_to_html

admin_page = Blueprint('admin_page', __name__)

# Goto the admin control page
@admin_page.route('/admin_page')
def admin_page_options():
    return render_template('admin_page.html')

# Approve a post and redirect to the list's next post
@admin_page.route('/approve_post/<post_id>/<post_num>', methods=['POST'])
def approve_post(post_id, post_num):
    # Set post to approved
    post = Post.query.filter_by(id=post_id).first()
    post.moderated = True
    db.session.commit()
    # go to next post now
    print("Post number is " + str(post_num))
    posts = Post.query.filter_by(moderated=False).all()
    post_list = []
    for post in posts:
        post_list.append(post.id)
    if len(post_list) == 0:
        flash("No unmoderated posts")
        return redirect(url_for('admin_page.admin_page_options'))
    post_num = int(post_num)
    list_len = len(post_list)
    if (list_len == 0):
        return render_template('admin_page.html')
    while (post_num >= list_len):
        post_num-=1
    post_html = post_to_approve_to_html(post_list[post_num], post_num)
    return render_template('moderate_post.html', id = id, post_num=post_num, post_html=post_html, list_len=list_len)

@admin_page.route('/unapprove_post/<id>/<post_num>', methods=['POST'])
def unapprove_post(id, post_num):
    obj = Post.query.filter_by(id=id).first()
    # update relational databases
    q1 = post_topic.delete().where(post_topic.c.post_id == obj.id)
    db.session.execute(q1)
    db.session.commit()
    q2 = liked_post.delete().where(liked_post.c.liked_id == obj.id)
    db.session.execute(q2)
    db.session.commit()
    q3 = saved_post.delete().where(saved_post.c.saved_id == obj.id)
    db.session.execute(q3)
    db.session.commit()
    # update Posts db
    db.session.delete(obj)
    db.session.commit()
    posts = Post.query.filter_by(moderated=False).all()
    post_list = []
    for post in posts:
        post_list.append(post.id)
    if len(post_list) == 0:
        flash("No unmoderated posts")
        return redirect(url_for('admin_page.admin_page_options'))
    post_num = int(post_num)
    list_len = len(post_list)
    if (list_len == 0):
        return render_template('admin_page.html')
    while (post_num >= list_len):
        post_num-=1
    post_html = post_to_approve_to_html(post_list[post_num], post_num)
    return render_template('moderate_post.html', id = id, post_num=post_num, post_html=post_html, list_len=list_len)

# Access the list of all unapproved posts
@admin_page.route('/moderate_posts_list/<post_num>')
def moderate_posts_list(post_num):
    posts = Post.query.filter_by(moderated=False).all()
    post_list = []
    for post in posts:
        post_list.append(post.id)
    if len(post_list) == 0:
        flash("No unmoderated posts")
        return redirect(url_for('admin_page.admin_page_options'))
    post_num = int(post_num)
    list_len = len(post_list)
    if (list_len == 0):
        return render_template('admin_page.html')
    while (post_num >= list_len):
        post_num-=1
    post_html = post_to_approve_to_html(post_list[post_num], post_num)
    return render_template('moderate_post.html', id = id, post_num=post_num, post_html=post_html, list_len=list_len)

# Give admin to a certain user
@admin_page.route('/give_admin', methods=['GET'])
def give_admin_to_user():
    user_to_change = request.args.get('uname')
    return user_to_change

# Take admin from a certain user
@admin_page.route('/take_admin', methods=['GET'])
def take_admin_from_user():
    user_to_change = request.args.get('uname')
    return user_to_change
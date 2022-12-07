from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask_login import login_required, current_user
from flask import session as cur_session
from .models import User, Post, Topic, Nutrition, added_nutrition_goals
from . import db
import random

nutrition_goals = Blueprint('nutrition_goals', __name__)
@nutrition_goals.route('/nutrition_goals')
def nutrition_goals_page():
    nutrition_goals_html = ""
    cur_session.pop('_flashes', None)

    tip_relation = db.session.query(added_nutrition_goals).filter_by(user_id=current_user.id)
    if not tip_relation:
        return render_template('nutrition_goals.html', nutrition_goals_html=nutrition_goals_html)

    for tip in tip_relation:
        curr_user_tip = Nutrition.query.filter_by(id=tip.nutr_id).first()
        if curr_user_tip.category == 1:
            nutrition_goals_html += f"<html><div class=\"column is-half is-offset-one-quarter\">\
                    <div class=\"box\">\
                        <div class=\"content\">\
                            <h3 class=\"title is-3 has-text-black has-text-left\">Fruits and Vegetables Goals</h3>"
        if curr_user_tip.category == 2:
            nutrition_goals_html += f"<html><div class=\"column is-half is-offset-one-quarter\">\
                    <div class=\"box\">\
                        <div class=\"content\">\
                            <h3 class=\"title is-3 has-text-black has-text-left\">Protein Goals</h3>"
        if curr_user_tip.category == 3:
            nutrition_goals_html += f"<html><div class=\"column is-half is-offset-one-quarter\">\
                    <div class=\"box\">\
                        <div class=\"content\">\
                            <h3 class=\"title is-3 has-text-black has-text-left\">Beverage Goals</h3>"
        if curr_user_tip.category == 4:
            nutrition_goals_html += f"<html><div class=\"column is-half is-offset-one-quarter\">\
                    <div class=\"box\">\
                        <div class=\"content\">\
                            <h3 class=\"title is-3 has-text-black has-text-left\">Meal Planning Goals</h3>"
        if curr_user_tip.category == 5:
            nutrition_goals_html += f"<html><div class=\"column is-half is-offset-one-quarter\">\
                    <div class=\"box\">\
                        <div class=\"content\">\
                            <h3 class=\"title is-3 has-text-black has-text-left\">Mindful Eating Goals</h3>"
        nutrition_goals_html += curr_user_tip.goal
        nutrition_goals_html += "</div></div></div></html>"
        print(nutrition_goals_html)
    return render_template('nutrition_goals.html', nutrition_goals_html=nutrition_goals_html)

@nutrition_goals.route('/add_goal/<category>')
def add_goal(category):
    nutrition_tips = Nutrition.query.filter_by(category=category).all()
    choice = random.choice(nutrition_tips)
    print(choice.goal)
    current_user.add_nutr_goal(choice)
    db.session.commit()
    return redirect(url_for('prof.profile'))

@nutrition_goals.route('/clear_goals')
def clear_goals():
    nutrition_tips = db.session.query(added_nutrition_goals).filter_by(user_id=current_user.id)
    for tip in nutrition_tips:
        q1 = added_nutrition_goals.delete().where(added_nutrition_goals.c.nutr_id == tip.nutr_id)
        db.session.execute(q1)
        db.session.commit()
    return redirect(url_for('nutrition_goals.nutrition_goals_page'))
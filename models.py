from pickle import FALSE
from flask_login import UserMixin
from sqlalchemy import LargeBinary

from . import db

# User model that stores information regarding the person logged in atm
# TODO: Connect to database, Make fields actually what we need, will require
#       edits to signup.html and auth.py for user field changes 

# Followers association table
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

# Topics association table, foreign key -> link btw two tables
user_topic = db.Table('user_topic',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('topic_id', db.Integer, db.ForeignKey('topic.id'))
)

# Topics association table, foreign key -> link btw two tables
post_topic = db.Table('post_topic',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
    db.Column('topic_id', db.Integer, db.ForeignKey('topic.id'))
)

# Blocked users association table
blocked_users = db.Table('blocked_users',
    db.Column('blocking_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('blocked_id', db.Integer, db.ForeignKey('user.id'))
)

# Likes in posts (reaction)
liked_post = db.Table('liked_post',
    db.Column('liking_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('liked_id', db.Integer, db.ForeignKey('post.id'))
)

# Likes in exercises
liked_exercise = db.Table('liked_exercise',
    db.Column('user_like', db.Integer, db.ForeignKey('user.id')),
    db.Column('exercise_liked', db.Integer, db.ForeignKey('workout.id'))
)

# Dislikes in exercises
disliked_exercise = db.Table('disliked_exercise',
    db.Column('user_dislike', db.Integer, db.ForeignKey('user.id')),
    db.Column('exercise_disliked', db.Integer, db.ForeignKey('workout.id'))
)

upvoted_exercise = db.Table('upvoted_exercise',
    db.Column('user_upvoted', db.Integer, db.ForeignKey('user.id')),
    db.Column('exercise_upvoted', db.Integer, db.ForeignKey('workout.id'))
)

downvoted_exercise = db.Table('downvoted_exercise',
    db.Column('user_downvoted', db.Integer, db.ForeignKey('user.id')),
    db.Column('exercise_downvoted', db.Integer, db.ForeignKey('workout.id'))
)

# User to post relational db to store saved_posts
saved_post = db.Table('saved_post',
    db.Column('saving_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('saved_id', db.Integer, db.ForeignKey('post.id'))
)

saved_workout = db.Table('saved_workout',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('workout_id', db.Integer, db.ForeignKey('workout.id'))
)

workout_muscle_groups = db.Table('workout_muscle_groups',
    db.Column('workout_id', db.Integer, db.ForeignKey('workout.id')),
    db.Column('muscle', db.String, db.ForeignKey('muscle.name')))

added_nutrition_goals = db.Table('nutrition_goals_relationship',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('nutr_id', db.Integer, db.ForeignKey('nutrition.id'))
)

class User(UserMixin, db.Model):

    # Some of these fields are required
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    bio = db.Column(db.String(1000))
    chat_restriction = db.Column(db.Boolean)
    pfp_filename = db.Column(db.String(50))
    pfp = db.Column(LargeBinary)
    admin = db.Column(db.Boolean)
    private = db.Column(db.Boolean)
    # End of warning
    followed_topics = db.relationship('Topic', secondary=user_topic, backref='followed_by', lazy='dynamic')
    comments = db.relationship('Commented',  backref='user', passive_deletes=True)
    workout_comments = db.relationship('Workout_Comment', backref='user', passive_deletes=True)
    saved_posts = db.relationship('Post', secondary=saved_post, backref='saved_by', lazy='dynamic', overlaps="saved_by,saved_posts")
    

    def is_following_topic(self, topic):
        query_user_topic = User.query.join(user_topic).join(Topic).filter((user_topic.c.user_id == self.id) & (user_topic.c.topic_id == topic)).count()
        if query_user_topic > 0:
            return True
        return False

    def follow_topic(self, id):
        if not self.is_following_topic(id):
            topic = Topic.query.filter_by(id=id).first()
            self.followed_topics.append(topic)

    def unfollow_topic(self, id):
        if self.is_following_topic(id):
            topic = Topic.query.filter_by(id=id).first()
            self.followed_topics.remove(topic)

    # Included many to many follower relationship
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic'
    )

    # Adding follower
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
    # Removing follower
    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
    # Cannot follow twice if already followed
    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    # Obtaining posts from followed users while having own post
    # in the timeline as well
    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.id.desc())

    blocked = db.relationship(
        'User', secondary=blocked_users,
        primaryjoin=(blocked_users.c.blocking_id == id),
        secondaryjoin=(blocked_users.c.blocked_id == id),
        backref=db.backref('blocked_users', lazy='dynamic'), lazy='dynamic'
        )
    
    # Blocking a user
    def block(self, user):
        if not self.is_blocking(user):
            self.blocked.append(user)
        if self.is_following(user):
            self.followed.remove(user)
    # Unblocking a user
    def unblock(self, user):
        if self.is_blocking(user):
            self.blocked.remove(user)
    # Function that checks if the user is already blocking someone
    def is_blocking(self, user):
        return self.blocked.filter(
        blocked_users.c.blocked_id == user.id).count() > 0        

    #db.relationship('Topic', secondary=user_topic, backref='followed_by', lazy='dynamic')

    liked = db.relationship('Post', secondary=liked_post,backref=db.backref('liked_post', lazy='dynamic'), lazy='dynamic'
    )
    # Relationship for liked exercises
    liked_workout_relationship = db.relationship('Workout', secondary=liked_exercise,backref=db.backref('liked_exercise', lazy='dynamic'), lazy='dynamic')
    
    # Relationship for disliked exercises
    disliked_workout_relationship = db.relationship('Workout', secondary=disliked_exercise,backref=db.backref('disliked_exercise', lazy='dynamic'), lazy='dynamic')

    # Relationship for upvoted exercises
    upvoted_workout_relationship = db.relationship('Workout', secondary=upvoted_exercise,backref=db.backref('upvoted_exercise', lazy='dynamic'), lazy='dynamic')
    
    # Relationship for downvoted exercises
    downvoted_workout_relationship = db.relationship('Workout', secondary=downvoted_exercise,backref=db.backref('downvoted_exercise', lazy='dynamic'), lazy='dynamic')

    # Relationship for adding nutritional goal
    nutritional_goal_relationship = db.relationship('Nutrition', secondary=added_nutrition_goals,backref=db.backref('add_nutr_goal', lazy='dynamic'), lazy='dynamic')

    # Adding goal
    def add_nutr_goal(self, nutrition):
        if not self.has_added_nutr_goal(nutrition):
            self.nutritional_goal_relationship.append(nutrition)

    # Removing goal
    def remove_nutr_goal(self, nutrition):
        if not self.has_added_nutr_goal(nutrition):
            self.nutritional_goal_relationship.remove(nutrition)
    
    def has_added_nutr_goal(self, nutrition):
            return self.nutritional_goal_relationship.filter(
            added_nutrition_goals.c.nutr_id == nutrition.id).count() > 0

    # Liking a post
    def like(self, post):
        if not self.is_liking(post):
            self.liked.append(post)
    # Unliking a post
    def unlike(self, post):
        if self.is_liking(post):
            self.liked.remove(post)

    # Function that checks if the user has already liked the post
    def is_liking(self, post):
        return self.liked.filter(
        liked_post.c.liked_id == post.id).count() > 0  

    # Liking an exercise
    def like_exercise(self, workout):
        if not self.is_liking_exercise(workout):
            self.liked_workout_relationship.append(workout)
    
    def dislike_exercise(self, workout):
        if not self.is_disliking_exercise(workout):
            self.disliked_workout_relationship.append(workout)
    
    # Removing like from a liked workout
    def remove_like(self, workout):
        if self.is_liking_exercise(workout):
            self.liked_workout_relationship.remove(workout)

    # Removing like from a liked workout
    def remove_dislike(self, workout):
        if self.is_disliking_exercise(workout):
            self.disliked_workout_relationship.remove(workout)

    # Function that checks if workout was already liked
    def is_liking_exercise(self, workout):
        return self.liked_workout_relationship.filter(
        liked_exercise.c.exercise_liked == workout.id).count() > 0

    # Function that checks if workout was already been disliked
    def is_disliking_exercise(self, workout):
        return self.disliked_workout_relationship.filter(
        disliked_exercise.c.exercise_disliked == workout.id).count() > 0

    def upvote_exercise(self, workout):
        if not self.upvoted_exercise(workout):
            self.upvoted_workout_relationship.append(workout)
    
    def downvote_exercise(self, workout):
        if not self.downvoted_exercise(workout):
            self.downvoted_workout_relationship.append(workout)
    
    def remove_upvote(self, workout):
        if self.upvoted_exercise(workout):
            self.upvoted_workout_relationship.remove(workout)

    def remove_downvote(self, workout):
        if self.downvoted_exercise(workout):
            self.downvoted_workout_relationship.remove(workout)

    def upvoted_exercise(self, workout):
        return self.upvoted_workout_relationship.filter(
        upvoted_exercise.c.exercise_upvoted == workout.id).count() > 0

    # Function that checks if workout was already been disliked
    def downvoted_exercise(self, workout):
        return self.downvoted_workout_relationship.filter(
        downvoted_exercise.c.exercise_downvoted == workout.id).count() > 0 

    saved = db.relationship('Post', secondary=saved_post,backref=db.backref('saved_post', lazy='dynamic'), lazy='dynamic', overlaps="saved_by,saved_posts")

    # Check if user saved post
    def has_saved(self, post):
        return self.saved.filter(
            saved_post.c.saved_id == post.id).count() > 0

    # Save a post
    def save(self, post):
        if not self.has_saved(post):
            self.saved.append(post)
    
    # Unsave a post
    def unsave(self, post):
        if self.has_saved(post):
            self.saved.remove(post)

    saved_workouts = db.relationship('Workout', secondary=saved_workout, backref='workout_saved_by', lazy='dynamic')

    # Check if user has saved workout
    def has_saved_workout(self, workout):
        return self.saved_workouts.filter(
            saved_workout.c.workout_id == workout.id).count() > 0
    
    # Save a workout
    def save_workout(self, workout):
        if not self.has_saved_workout(workout):
            self.saved_workouts.append(workout)

    # Unsave a workout
    def unsave_workout(self, workout):
        if self.has_saved_workout(workout):
            self.saved_workouts.remove(workout)

class Post(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    contents = db.Column(db.String(300))
    anonymous = db.Column(db.Boolean)
    likes = db.Column(db.Integer)
    filename = db.Column(db.String(50))
    data = db.Column(db.LargeBinary)
    tagged_topics = db.relationship('Topic', secondary=post_topic, backref='posts_tagged_with')
    comments = db.relationship('Commented', backref='post', passive_deletes=True)
    moderated = db.Column(db.Boolean)
    high_risk = db.Column(db.Boolean)
    precautions = db.Column(db.String(300))
    video_link = db.Column(db.String(2048))
    call_to_action = db.Column(db.String(2048)) 

class Topic(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    posts = db.relationship('Post', secondary=post_topic, backref='tags_mentioned', overlaps="posts_tagged_with,tagged_topics")
    users = db.relationship('User', secondary=user_topic, backref='tags_followed', overlaps="followed_by,followed_topics")

class Message(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    message = db.Column(db.String(500))

class Commented(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contents = db.Column(db.String(200))
    # author = db.relationship('User', secondary=post_comment, backref='user')
    # post_id = db.relationship('Post', secondary=post_comment, backref='post')
    author = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete="CASCADE"), nullable=False)

class Workout_Comment(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contents = db.Column(db.String(200))
    author = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    author_name = db.Column(db.String(50))
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id', ondelete="CASCADE"), nullable=False)

class Muscle(UserMixin, db.Model):
    name = db.Column(db.String(15), primary_key=True)

class Workout(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exercise_name = db.Column(db.String(15))
    description = db.Column(db.String(500))
    URL = db.Column(db.String(2048))
    video_link = db.Column(db.String(2048))
    muscle_groups = db.relationship('Muscle', secondary=workout_muscle_groups)
    comments = db.relationship('Workout_Comment', backref='post', passive_deletes=True)
    likes = db.Column(db.Integer)
    dislikes = db.Column(db.Integer)
    upvotes = db.Column(db.Integer)
    downvotes = db.Column(db.Integer)

class Nutrition(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.Integer)
    goal = db.Column(db.String(500))
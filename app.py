import os

from flask import Flask

#Hi gautam
def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Load in portion of app that is in auth.py
    try:
        from .auth import auth as auth_blueprint
    except ImportError:
        import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # Load in portion of app that is in main.py
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app

my_app = create_app()
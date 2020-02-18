import os

from flask import Flask, redirect, url_for

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'app.sqlite'),
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

    from . import db
    from app.routers import recipes, meals, ingredients, auth
    db.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(ingredients.bp)
    app.register_blueprint(recipes.bp)
    app.register_blueprint(meals.bp)

    @app.route('/')
    def index():
        """ Displays the index page accessible at '/'
        """
        return redirect(url_for('recipes.index'))

    return app

"""
Blueprint for recipes.

Views:
- Index (displays most recently added recipes)
- Create
- Update
- Recipe (shows recipe details)
- Delete (does not have a template)

TODO:
- modify create and update methods so that the POST inserts into recipeMealRelationship
- add search bar to ingredient drop down
- add add/remove links to control number of ingredients
"""

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db
import re

bp = Blueprint("recipes", __name__, url_prefix="/recipes")

def get_ingredients():
    res = []
    db = get_db()
    ings = db.execute(
        'SELECT *'
        ' FROM ingredient'
        ' ORDER BY name ASC'
    ).fetchall()
    for ing in ings:
        res.append(ing['name'])
    return sorted(res)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT *'
        ' FROM recipe'
    ).fetchall()
    return render_template('recipes/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
def no_ing():
    if request.method == 'POST':

        try: #this determines the number of ingredients
            number_ingredients = int(request.form['number'])
            error = None

            if not request.form['number']:
                error = "Number of ingredients is required."

            if error is not None:
                flash(error)

            else:
                quantities = []
                for q in range(1, number_ingredients+1):
                    quantities.append(q)
                return render_template('recipes/create-ing.html', ingredients=get_ingredients(), quantities=quantities)

        except: #this is the creation of recipe itself
            title = request.form['title']
            body = request.form['body']

            number_ingredients = int((len(request.form)-2) / 3)

            ingredients = [] #each entry: (ingredient, quantity, portion_size)

            temp = []
            for entry in request.form.keys():
                if entry == 'title' or entry == 'body':
                    if len(temp) != 0 and len(temp) % number_ingredients == 0:
                        ingredients.append(tuple(temp))
                    continue

                if len(temp) != 0 and len(temp) % number_ingredients == 0:
                    ingredients.append(tuple(temp))
                    temp = [request.form[entry]]
                else:
                    temp.append(request.form[entry])

            error = None

            db = get_db()

            if not title:
                error = 'Title is required.'

            if not body:
                error = "Instructions are required."

            if error is not None:
                flash(error)

            else:
                db.execute(
                    'INSERT INTO recipe (author_id, title, body)'
                    ' VALUES (?, ?, ?)',
                    (g.user['id'], title, body)
                )
                db.commit()
                return redirect(url_for('recipes.index'))

    return render_template('recipes/create.html')


@bp.route('/create-ing', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':

        title = request.form['title']
        body = request.form['body']

        error = None

        db = get_db()

        if not title:
            error = 'Title is required.'

        if not body:
            error = "Instructions are required."

        if error is not None:
            flash(error)

        else:
            db.execute(
                'INSERT INTO recipe (author_id, title, body)'
                ' VALUES (?, ?, ?)',
                (g.user['id'], title, body)
            )
            db.commit()
            return redirect(url_for('ingredients.index'))

    return render_template('recipes/create-ing.html', ingredients=get_ingredients(), quantity=quantity)

def get_recipe(name_key):
    recipe = get_db().execute(
        'SELECT *'
        ' FROM recipe'
        ' WHERE id = ?',
        (int(name_key),)
    ).fetchone()

    if recipe is None:
        abort(404, "{0} is not in the Ingredient table.".format(name_key))

    return recipe

@bp.route('/<name_key>/update', methods=('GET', 'POST'))
def update(name_key):

    recipe = get_recipe(name_key)

    if request.method == 'POST':

        title = request.form['title']
        body = request.form['body']

        error = None

        db = get_db()

        if not title:
            error = 'Title is required.'

        if not body:
            error = "Instructions are required."

        if error is not None:
            flash(error)

        else:
            db = get_db()
            db.execute(
                'UPDATE recipe SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, name_key)
            )
            db.commit()
            return redirect(url_for('recipes.index'))

    return render_template('recipes/update.html', recipe=recipe, ingredients=get_ingredients())

@bp.route('/<name_key>/delete', methods=('POST',))
def delete(name_key):
    get_recipe(name_key)
    db = get_db()
    db.execute('DELETE FROM recipe WHERE id = ?', (name_key,))
    db.commit()
    return redirect(url_for('recipes.index'))


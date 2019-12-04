"""
Blueprint for recipes.

Views:
- Index (displays most recently added ingredients)
- Create
- Update
- Recipe
- Delete (does not have a template)

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
        'SELECT title'
        ' FROM recipe'
        ' ORDER BY name ASC'
    ).fetchall()
    return render_template('recipes/index.html', posts=posts)

@bp.route('/create', methods=('GET', 'POST'))
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

    return render_template('recipes/create.html', ingredients = get_ingredients())

def get_ing(name_key):
    ing = get_db().execute(
        'SELECT name, name_key, portion_size, portion_size_unit, protein, fat, carbs, notes'
        ' FROM ingredient'
        ' WHERE name_key = ?',
        (name_key,)
    ).fetchone()

    if ing is None:
        abort(404, "{0} is not in the Ingredient table.".format(name))

    return ing

@bp.route('/<name_key>/update', methods=('GET', 'POST'))
def update(name_key):

    ingredient = get_ing(name_key)

    if request.method == 'POST':
        
        name = request.form['name']
        name_key = re.sub(r"\s+", "-", name).lower()
        portion_size = request.form['portion_size']
        portion_size_unit = request.form['portion_size_unit']
        protein = request.form['protein']
        fat = request.form['fat']
        carbs = request.form['carbs']
        notes = request.form['notes']
        
        error = None

        if not name:
            error = 'Title is required.'
        if not portion_size:
            error = 'Portion size is required.'
        if not portion_size_unit:
            error = 'Portion size unit is required.'
        if not protein:
            error = 'Protein content is required.'
        if not fat:
            error = 'Fat content is required.'
        if not carbs:
            error = 'Carbs content is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE ingredient SET name = ?, name_key = ?, portion_size = ?, portion_size_unit = ?, protein = ?, fat = ?, carbs = ?, notes = ?'
                ' WHERE name_key = ?',
                (name, name_key, portion_size, portion_size_unit, protein, fat, carbs, notes, name_key)
            )
            db.commit()
            return redirect(url_for('ingredients.index'))

    return render_template('ingredients/update.html', ingredient=ingredient)

@bp.route('/<name_key>/delete', methods=('POST',))
def delete(name_key):
    get_ing(name_key)
    db = get_db()
    db.execute('DELETE FROM ingredient WHERE name_key = ?', (name_key,))
    db.commit()
    return redirect(url_for('ingredients.index'))


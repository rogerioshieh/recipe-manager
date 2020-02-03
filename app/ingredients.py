"""
Blueprint for ingredients.

Views:
- Index (displays most recently added ingredients)
- Create
- Update
- Delete (does not have a template)

TODO:
- Figure out how to not display decimals
- Search bar?
"""

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db
import re

bp = Blueprint("ingredients", __name__, url_prefix="/ingredients")


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT name, name_key, portion_size, portion_size_unit, protein, fat, carbs, calories'
        ' FROM ingredient'
        ' ORDER BY name ASC'
    ).fetchall()
    # return jsonify(posts)
    return render_template('ingredients/index.html', posts=posts)


'''
This function converts a given unit to either grams or ml.
'''


def convert(unit, size):
    size = float(size)
    if unit == 'g' or unit == 'ml':
        return unit

    weights = {'kg', 'oz', 'lb'}
    volumes = {'cup', 'l', 'gal', 'T', 't'}

    if unit in weights:
        if unit == 'kg':
            res = size * 1000
        elif unit == 'oz':
            res = size * 28.35
        elif unit == 'lb':
            res = size * 454

    elif unit in volumes:
        if unit == 'cup':
            res = size * 236.58
        elif unit == 'l':
            res = size * 1000
        elif unit == 'gal':
            res = size * 3785.41
        elif unit == 'T':
            res = size * 15
        elif unit == 't':
            res = size * 5

    else:
        res = 0

    return res


@bp.route('/create', methods=('GET', 'POST'))
# @login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        name_key = re.sub(r"\s+", "-", name).lower()
        portion_size = request.form['portion_size']
        portion_size_unit = request.form['portion_size_unit']
        portion_converted = convert(portion_size_unit, portion_size)
        protein = request.form['protein']
        fat = request.form['fat']
        carbs = request.form['carbs']
        calories = request.form['calories']
        notes = request.form['notes']
        error = None

        db = get_db()

        # checks if ingredient is already in the database
        if len(db.execute('SELECT * FROM ingredient WHERE name_key = ?', (name_key,)).fetchall()) != 0:
            error = "Ingredient already in the database."

        if not name:
            error = 'Name is required.'

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

        if not calories:
            error = 'Total calories are required.'

        if error is not None:
            flash(error)

        else:
            db.execute(
                'INSERT INTO ingredient (name, name_key, portion_size, portion_size_unit, portion_converted, protein, fat, carbs, calories, notes)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (name, name_key, portion_size, portion_size_unit, portion_converted, protein, fat, carbs, calories, notes)
            )
            db.commit()
            return redirect(url_for('ingredients.index'))

    return render_template('ingredients/create.html')


def get_ing(name_key):
    ing = get_db().execute(
        'SELECT name, name_key, portion_size, portion_size_unit, portion_converted, protein, fat, carbs, calories, notes'
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
        portion_converted = convert(portion_size_unit, portion_size)
        protein = request.form['protein']
        fat = request.form['fat']
        carbs = request.form['carbs']
        calories = request.form['calories']
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
                'UPDATE ingredient SET name = ?, name_key = ?, portion_size = ?, '
                'portion_size_unit = ?, portion_converted = ?, protein = ?, fat = ?, carbs = ?, calories = ?, notes = ?'
                ' WHERE name_key = ?',
                (name, name_key, portion_size, portion_size_unit, portion_converted, protein, fat, carbs, calories, notes, name_key)
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

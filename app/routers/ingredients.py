"""
Blueprint for ingredients.

Views:
- Index (displays ingredients by tags, organized alphabetically)
- Create
- Update
- Delete (does not have a template)
"""

from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)
from app.routers.auth import login_required
from app.db import get_db
from app.helpers import convert, get_ing
import re

bp = Blueprint("ingredients", __name__, url_prefix="/ingredients")

__units__ = ['g', 'kg', 'oz', 'lb', 'cup', 'ml', 'l', 'gal', 'T', 't', 'in', 'unit']
__tags__ = ['carbs', 'fats', 'proteins', 'vegetables', 'legumes', 'fruit', 'nuts', 'sauces', 'dairy', 'spices', 'others']


@bp.route('/')
def index():
    db = get_db()
    ingredients_db = db.execute(
        'SELECT * FROM ingredient ORDER BY tag, name'
    ).fetchall()

    #gets the tag with most ingredients (will be used to build a table with empty elements)
    max_length = db.execute(
        'SELECT count(tag) as c FROM ingredient GROUP BY tag order by count(tag) DESC;'
    ).fetchone()['c']

    #creates empty lists which will be populated
    carbs, fats, proteins, vegetables, legumes, fruit, nuts, sauces, dairy, spices, others = ([] for i in range(11))

    #populate lists
    for ing in ingredients_db:
        if ing['tag'] == 'carbs':
            carbs.append(ing)
        elif ing['tag'] == 'fats':
            fats.append(ing)
        elif ing['tag'] == 'proteins':
            proteins.append(ing)
        elif ing['tag'] == 'vegetables':
            vegetables.append(ing)
        elif ing['tag'] == 'legumes':
            legumes.append(ing)
        elif ing['tag'] == 'fruit':
            fruit.append(ing)
        elif ing['tag'] == 'nuts':
            nuts.append(ing)
        elif ing['tag'] == 'sauces':
            sauces.append(ing)
        elif ing['tag'] == 'dairy':
            dairy.append(ing)
        elif ing['tag'] == 'spices':
            spices.append(ing)
        elif ing['tag'] == 'others':
            others.append(ing)

    ingredients = [carbs, fats, proteins, vegetables, legumes, fruit, nuts, sauces, dairy, spices, others]

    for ing in ingredients:
        while len(ing) < max_length:
            ing.append(None)

    #transpose the array so that it is organized in rows
    ingredients = [list(i) for i in zip(*ingredients)]

    return render_template('ingredients/index.html', ingredients=ingredients, tags=__tags__)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
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
        price = str(float(request.form['price']) * 100)
        price_size = request.form['price_size']
        price_size_unit = request.form['price_size_unit']
        tag = request.form['tag']
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
                'INSERT INTO ingredient (name, name_key, portion_size, portion_size_unit, portion_converted, protein, fat, carbs, calories, price, price_size, price_size_unit, tag, notes)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (name, name_key, portion_size, portion_size_unit, portion_converted, protein, fat, carbs, calories, price, price_size, price_size_unit, tag, notes)
            )
            db.commit()
            return redirect(url_for('ingredients.index'))

    return render_template('ingredients/create.html', units=__units__, tags=__tags__)


@bp.route('/<name_key>/update', methods=('GET', 'POST'))
@login_required
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
        price = str(float(request.form['price']) * 100)
        price_size = request.form['price_size']
        price_size_unit = request.form['price_size_unit']
        tag = request.form['tag']
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
                'UPDATE ingredient SET name = ?, name_key = ?, portion_size = ?, portion_size_unit = ?, portion_converted = ?, '
                'protein = ?, fat = ?, carbs = ?, calories = ?, price = ?, price_size = ?, price_size_unit = ?, tag = ?, notes = ?'
                ' WHERE id = ?',
                (name, name_key, portion_size, portion_size_unit, portion_converted, protein, fat,
                 carbs, calories, price, price_size, price_size_unit, tag, notes, ingredient['id'])
            )
            db.commit()
            return redirect(url_for('ingredients.index'))

    return render_template('ingredients/update.html', ingredient=ingredient, units=__units__, tags=__tags__)


@bp.route('/<name_key>/delete', methods=('GET', 'POST',))
def delete(name_key):
    ing = get_ing(name_key)
    db = get_db()
    db.execute('DELETE FROM ingredient WHERE name_key = ?', (name_key,))

    recipes = db.execute(
        'SELECT recipeID FROM recipeIngredientRelationship WHERE ingredientID = ?', (ing['id'],)
    ).fetchall()

    for recipe in recipes:
        db.execute('DELETE FROM recipe WHERE id = ?', (recipe['recipeID'],))
        db.execute('DELETE FROM recipeIngredientRelationship WHERE recipeID = ?', (recipe['recipeID'],))

    db.commit()
    return redirect(url_for('ingredients.index'))

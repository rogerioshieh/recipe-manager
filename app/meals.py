"""
Blueprint for recipes.

Views:
- Index (displays most recently added recipes)
- Create
- Update
- Recipe (shows recipe details)
- Delete (does not have a template)

TODO:
- add search bar to ingredient drop down
"""

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db
import re

bp = Blueprint("meals", __name__, url_prefix="/meals")

__tags__ = ['meal_prep', 'easy', 'weekend', 'brunch', 'other']

def get_recipes():

    res = []
    for recipe in get_db().execute('SELECT * FROM recipe ORDER BY title ASC').fetchall():
        res.append(recipe['title'])

    return sorted(res)


def get_meal(meal_id):

    meal = get_db().execute(
        'SELECT * FROM meal WHERE id = ?',
        (int(meal_id),)
    ).fetchone()

    return meal if meal is not None else abort(404, f"{meal_id} is not in the Meal table.")


def convert(unit, size):
    size = float(size)
    if unit == 'g' or unit == 'ml':
        return size

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


def get_macros_price(recipe, desired_servings):
    """
    :param desired_servings:
    :param recipe: SQL object
    :returns: list(list(int), list(int)) of carbs, fat, protein, calories
    """
    db = get_db()
    ings = db.execute(
        'SELECT * from recipeIngredientRelationship WHERE recipeID=(?)',
        (recipe['id'],)
    ).fetchall()

    servings = recipe['servings'] if recipe['servings'] else 1
    macro_totals = [0, 0, 0, 0]  # carbs, protein, fat, calories
    prices_total = 0
    res = []

    for ing in ings:
        ing_id = str(ing['ingredientID'])
        ing_db = db.execute('SELECT * FROM ingredient WHERE id=?',
                              (ing_id)).fetchone()

        macro_db = db.execute(
            'SELECT carbs, fat, protein, calories, portion_size, '
            'portion_size_unit, portion_converted FROM ingredient WHERE id=?',
            (ing_id)).fetchone()

        macros_ing = [macro_db['carbs'], macro_db['fat'],
                     macro_db['protein'], macro_db['calories']]

        quantity_g_ml = convert(ing['units'], ing['quantity'])
        ratio = macro_db['portion_converted'] / quantity_g_ml

        #updates macro_totals with recipe macros
        macro_totals = [x + (y / servings / ratio) for x, y in zip(macro_totals, macros_ing)]

        prices_total += ((ing_db['price'] / convert(ing_db['price_size_unit'], ing_db['price_size'])
                        ) * quantity_g_ml ) / (100 * servings)

    res.append([round(x * servings / desired_servings, 1) for x in macro_totals])
    res.append(round(prices_total * servings / desired_servings, 2))

    print(res)
    return res


@bp.route('/')
def index():
    db = get_db()
    meals_db = db.execute('SELECT title, id, tag FROM meal').fetchall()
    meals = []

    for i in range(len(meals_db)):
        meals.append([meals_db[i]['title'], meals_db[i]['id'], meals_db[i]['tag']])

    return render_template('meals/index.html', meals=meals)


'''
Displays a recipe given its index number.
==> recipe = [mealSQL, list(recipeSQL), ing names: list(str), 
macros_ing: list(int)[ing caloric values], macro_totals: list(int)]
'''
@bp.route('/<meal_id>/')
def display_meal(meal_id):
    db = get_db()
    meal = db.execute('SELECT * FROM meal WHERE id = ?', (meal_id,)).fetchone()

    if not meal:
        abort(404, f"{meal_id} is not in the Recipe table.")

    recipes = db.execute(
        'SELECT * FROM mealRecipeRelationship WHERE mealID=(?)', (meal_id,)
    ).fetchall()

    recipes_db = []

    # prevents division by 0 in case servings was not added correctly
    servings = recipes[0]['servings'] if recipes[0]['servings'] else 1
    macros_per_recipe = []  # list(list(int)) containing macros of each ingredient
    macro_totals = [0, 0, 0, 0]  # carbs, protein, fat, calories
    prices = []

    if recipes:
        for recipe in recipes:

            recipe_id = str(recipe['recipeID'])
            print(recipe_id)
            recipe_db = db.execute('SELECT * FROM recipe WHERE id=?',
                                  (recipe_id)).fetchone()
            recipes_db.append(recipe_db)

            temp = get_macros_price(recipe_db, servings)
            macros_per_recipe.append(temp[0])
            prices.append(temp[1])

            macro_totals = [round(x + y, 1) for x, y in zip(macro_totals, temp[0])]

    return render_template('meals/display.html', meal=meal, recipes=recipes_db,
                           servings=servings, macro_totals=macro_totals,
                           macros=macros_per_recipe, prices=[round(x, 2) for x in prices])


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':

        db = get_db()
        data = request.get_json()

        error = None

        if not data['title']:
            error = 'Title is required.'

        if not data['servings']:
            error = "Number of servings is required."

        if error is not None:
            flash(error)

        else:
            db.execute(
                'INSERT OR REPLACE INTO meal (author_id, title, notes, tag)'
                ' VALUES (?, ?, ?, ?)',
                (g.user['username'], data['title'], data['notes'], data['tag'])
            )

            meal_id = db.execute(
                'SELECT id FROM meal WHERE title=?',
                (data['title'],)
            ).fetchone()['id']

            for recipe in data['recipes']:
                recipe_id = db.execute(
                    'SELECT id from recipe WHERE title=(?)',
                    (recipe['title'],)).fetchone()['id']

                db.execute(
                    'INSERT or REPLACE INTO mealRecipeRelationship (mealID, recipeID, servings)'
                    ' VALUES (?, ?, ?)',
                    (meal_id, recipe_id, data['servings'])
                )

            db.commit()
            # https://stackoverflow.com/questions/199099/how-to-manage-a-redirect-request-after-a-jquery-ajax-call
            return redirect(url_for('meals.index'))

    return render_template('meals/create.html', recipes=get_recipes(), tags=__tags__)


@bp.route('/<meal_id>/update', methods=('GET', 'POST'))
def update(meal_id):
    if request.method == 'POST':

        db = get_db()
        data = request.get_json()
        print(data)

        error = None

        if not data['title']:
            error = 'Title is required.'

        if not data['servings']:
            error = "Number of servings is required."

        if error is not None:
            flash(error)

        else:

            db.execute('DELETE FROM meal where id=?', (meal_id,))

            db.execute('DELETE FROM mealRecipeRelationship where mealID=?',
                       (meal_id,))

            db.execute(
                'INSERT INTO meal (author_id, title, notes, tag)'
                ' VALUES (?, ?, ?, ?)',
                (g.user['username'], data['title'], data['notes'], data['tag'])
            )

            for recipe in data['recipes']:
                recipe_id = db.execute(
                    'SELECT id from recipe WHERE title=(?)',
                    (recipe['title'],)).fetchone()['id']

                db.execute(
                    'INSERT INTO mealRecipeRelationship (mealID, recipeID, servings)'
                    ' VALUES (?, ?, ?)',
                    (meal_id, recipe_id, data['servings'])
                )

            db.commit()
            return redirect(url_for('meals.index'))


    db = get_db()
    meal = get_meal(meal_id)

    # pre-populated entries
    recipes_db = db.execute(
        'SELECT recipeID, servings from mealRecipeRelationship'
        ' WHERE mealID=?',
        (meal_id,)
    ).fetchall()
    prepop_recipes = []
    servings = recipes_db[0]['servings']

    for recipe in recipes_db:
        recipe_name = db.execute(
            'SELECT title FROM recipe '
            'WHERE id = ?',
            (recipe['recipeID'],)
        ).fetchone()
        prepop_recipes.append(recipe_name['title'])

    return render_template('meals/update.html', meal=meal, prepop=prepop_recipes, servings=servings,
                           quantities=[i for i in range(1, len(prepop_recipes) + 1)],
                           recipes=get_recipes(), tags=__tags__, pageId=meal_id)


@bp.route('/<name_key>/delete', methods=('GET', 'POST',))
def delete(name_key):
    db = get_db()
    db.execute('DELETE FROM meal WHERE id = ?', (name_key,))
    db.execute('DELETE FROM mealRecipeRelationship WHERE recipeID = ?', (name_key,))
    db.commit()
    return redirect(url_for('meals.index'))
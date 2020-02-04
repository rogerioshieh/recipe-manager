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

__units__ = ['g', 'kg', 'oz', 'lb', 'cup', 'ml', 'l', 'gal', 'T', 't', 'in', 'unit']

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

def render_recipe(recipe_id):

    pass

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


def parse_ing(request_form):
    number_ingredients = int((len(request_form) - 2) / 3)
    number_ingredients = 2
    ingredients = []  # each entry: (ingredient, quantity, portion_size)
    temp = []

    for entry in request_form.keys():
        if entry == 'title' or entry == 'body':
            if len(temp) != 0 and len(temp) % number_ingredients == 0:
                ingredients.append(tuple(temp))
            continue

        if len(temp) != 0 and len(temp) % number_ingredients == 0:
            ingredients.append(tuple(temp))
            temp = [request_form[entry]]
        else:
            temp.append(request_form[entry])

    return ingredients


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT *'
        ' FROM recipe'
    ).fetchall()

    res = []
    nutritions = [] #per ing: [Carbs, Protein, Fat, Calories]

    for i in range(len(posts)):
        recipeID = posts[i]['id']
        servings = posts[i]['servings']
        temp = [posts[i]] #FORMAT [0:recipeSQL, 1:[ingSQL], 2:[ing names], 3:[ing caloric values], 4:[totals]
        temp.append(db.execute(
            'SELECT ingredientID, quantity, units'
            ' FROM recipeIngredientRelationship'
            ' WHERE recipeID=(?)', (recipeID,)
        ).fetchall())

        ing_names = []
        if temp[1]:
            nutrition_totals = [0, 0, 0, 0] #carbs, protein, fat, calories
            for ing in temp[1]:

                ing_id = str(ing['ingredientID'])

                ing_name = db.execute(
                    'SELECT name FROM ingredient WHERE id=?',
                    (ing_id)).fetchone()['name']
                ing_names.append(ing_name)

                nutrition = db.execute(
                    'SELECT carbs, fat, protein, calories, portion_size, '
                    'portion_size_unit, portion_converted FROM ingredient WHERE id=?',
                    (ing_id)).fetchone()

                if not servings: #prevents division by 0 in case servings was not added correctly
                    servings = 1

                quantity_g_ml = convert(ing['units'], ing['quantity'])
                ratio = nutrition['portion_converted'] / quantity_g_ml

                nutritions.append([
                    round(nutrition['carbs']/servings/ratio, 1),
                    round(nutrition['fat']/servings/ratio, 1),
                    round(nutrition['protein']/servings/ratio, 1),
                    round(nutrition['calories']/servings/ratio, 1)
                    ]
                )

                nutrition_totals[0] += round((nutrition['carbs']/ratio), 1)
                nutrition_totals[1] += round((nutrition['fat']/ratio), 1)
                nutrition_totals[2] += round((nutrition['protein']/ratio), 1)
                nutrition_totals[3] += round((nutrition['calories']/ratio), 1)

        temp.append(ing_names)
        temp.append(nutritions)
        temp.append(nutrition_totals)

        res.append(temp)

    return render_template('recipes/index.html', posts=res, nutritions=nutritions)


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

        if not data['instructions']:
            error = "Instructions are required."

        if error is not None:
            flash(error)

        else:
            db.execute(
                'INSERT INTO recipe (author_id, title, body, servings)'
                ' VALUES (?, ?, ?, ?)',
                (g.user['username'], data['title'], data['instructions'], data['servings'])
            )

            recipeID = db.execute(
                'SELECT id FROM recipe WHERE title=?',
                (data['title'],)
            ).fetchone()

            for ing in data['ingredients']:
                ingID = db.execute(
                    'SELECT id from ingredient WHERE name_key=(?)',
                    (re.sub(r"\s+", "-", ing['ingName']).lower(),)
                ).fetchone()

                db.execute(
                    'INSERT INTO recipeIngredientRelationship (recipeID, ingredientID, quantity, units)'
                    ' VALUES (?, ?, ?, ?)',
                    (recipeID['id'], ingID['id'], ing['quantity'], ing['portion'])
                )

            db.commit()
            #https://stackoverflow.com/questions/199099/how-to-manage-a-redirect-request-after-a-jquery-ajax-call
            return redirect(url_for('recipes.index'))

    return render_template('recipes/create.html', ingredients=get_ingredients(), units=__units__)

'''
@bp.route('/create-ing', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':

        title = request.form['title']
        body = request.form['body']
        servings = request.form['servings']

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
                'INSERT INTO recipe (author_id, title, body, servings)'
                ' VALUES (?, ?, ?)',
                (g.user['id'], title, body, servings)
            )
            db.commit()
            return redirect(url_for('ingredients.index'))

    return render_template('recipes/create.html', ingredients=get_ingredients())
'''


@bp.route('/<name_key>/update', methods=('GET', 'POST'))
def update(name_key):

    if request.method == 'POST':

        db = get_db()
        data = request.get_json()
        print(data)

        error = None

        if not data['title']:
            error = 'Title is required.'

        if not data['servings']:
            error = "Number of servings is required."

        if not data['instructions']:
            error = "Instructions are required."

        if error is not None:
            flash(error)

        else:
            recipeID = db.execute(
                'SELECT id FROM recipe WHERE title=?',
                (data['title'],)
            ).fetchone()

            db.execute(
                'DELETE FROM recipe where id=?',
                (recipeID['id'],)
            )

            db.execute(
                'delete from sqlite_sequence where name=?',
                ("recipe",)
            )

            db.execute(
                'DELETE FROM recipeIngredientRelationship '
                'where recipeID=?',
                (recipeID['id'],)
            )

            db.execute(
                'delete from sqlite_sequence where name=?',
                ("recipeIngredientRelationship",)
            )

            db.execute(
                'INSERT INTO recipe (author_id, title, body, servings)'
                ' VALUES (?, ?, ?, ?)',
                (g.user['username'], data['title'], data['instructions'], data['servings'])
            )

            for ing in data['ingredients']:
                ingID = db.execute(
                    'SELECT id from ingredient WHERE name_key=(?)',
                    (re.sub(r"\s+", "-", ing['ingName']).lower(),)
                ).fetchone()

                db.execute(
                    'INSERT INTO recipeIngredientRelationship (recipeID, ingredientID, quantity, units)'
                    ' VALUES (?, ?, ?, ?)',
                    (recipeID['id'], ingID['id'], ing['quantity'], ing['portion'])
                )

            db.commit()
            return redirect(url_for('recipes.index'))

    db = get_db()
    recipe = get_recipe(name_key)

    #pre-populated entries
    r_quantities = []
    r_units = []
    ings = db.execute(
        'SELECT ingredientID from recipeIngredientRelationship'
        ' WHERE recipeID=?',
        (recipe['id'],)
    ).fetchall()
    r_ings = []

    for ing in ings:
        ing_name = db.execute(
            'SELECT name FROM ingredient '
            'WHERE id = ?',
            (ing['ingredientID'],)
        ).fetchone()
        r_ings.append(ing_name['name'])

        quant = db.execute(
            'SELECT quantity FROM recipeIngredientRelationship'
            ' WHERE recipeID = ? '
            'AND ingredientID = ?',
            (name_key, ing['ingredientID'])
        ).fetchone()
        r_quantities.append(quant['quantity'])

        unit = db.execute(
            'SELECT units FROM recipeIngredientRelationship'
            ' WHERE recipeID = ? '
            'AND ingredientID = ?',
            (name_key, ing['ingredientID'])
        ).fetchone()
        r_units.append(unit['units'])

    pre_pop = {"quantity": r_quantities, "units": r_units, "ings": r_ings}

    return render_template('recipes/update.html', prepop=pre_pop, recipe=recipe,
                           quantities=[i for i in range(1, len(r_ings) + 1)],
                           ingredients=get_ingredients(), units=__units__, pageId=name_key)

@bp.route('/<name_key>/delete', methods=('GET', 'POST',))
def delete(name_key):
    get_recipe(name_key)
    db = get_db()
    db.execute('DELETE FROM recipe WHERE id = ?', (name_key,))
    db.commit()
    return redirect(url_for('recipes.index'))


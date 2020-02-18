"""
Blueprint for recipes.

Views:
- Index (displays recipes by tags, organized in alphabetical order)
- Create
- Update
- Display (shows recipe details)
- Delete (does not have a template)
"""

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from app.routers.auth import login_required
from app.db import get_db
from app.helpers import get_ingredients, get_recipe, convert, get_recipe_price
import re

bp = Blueprint("recipes", __name__, url_prefix="/recipes")

__units__ = ['g', 'kg', 'oz', 'lb', 'cup', 'ml', 'l', 'gal', 'T', 't', 'in', 'unit']
__tags__ = ['starches', 'proteins', 'beans', 'vegetables', 'dessert', 'sauces', 'spices', 'others']


@bp.route('/')
def index():
    db = get_db()

    if g.user:
        recipes_db = db.execute('SELECT * FROM recipe WHERE author_id=? ORDER BY tag, title',
                                (g.user['username'],)).fetchall()
    else:
        recipes_db = db.execute('SELECT * FROM recipe WHERE author_id=? ORDER BY tag, title',
                                ('demo_recipes',)).fetchall()

    if len(recipes_db) == 0:
        return render_template('recipes/index.html', recipes=recipes_db)

    #gets the tag with most recipes (will be used to build a table with empty elements)
    max_length = db.execute(
        'SELECT count(tag) as c FROM recipe GROUP BY tag order by count(tag) DESC;'
    ).fetchone()['c']

    starches, proteins, beans, vegetables, dessert, sauces, spices, others = ([] for i in range(8))
    starches_p, proteins_p, beans_p, vegetables_p, dessert_p, sauces_p, spices_p, others_p = ([] for i in range(8))

    for recipe in recipes_db: # populate lists
        if recipe['tag'] == 'starches':
            starches.append(recipe)
            starches_p.append(get_recipe_price(recipe['id']))
        elif recipe['tag'] == 'proteins':
            proteins.append(recipe)
            proteins_p.append(get_recipe_price(recipe['id']))
        elif recipe['tag'] == 'beans':
            beans.append(recipe)
            beans_p.append(get_recipe_price(recipe['id']))
        elif recipe['tag'] == 'vegetables':
            vegetables.append(recipe)
            vegetables_p.append(get_recipe_price(recipe['id']))
        elif recipe['tag'] == 'dessert':
            dessert.append(recipe)
            dessert_p.append(get_recipe_price(recipe['id']))
        elif recipe['tag'] == 'sauces':
            sauces.append(recipe)
            sauces_p.append(get_recipe_price(recipe['id']))
        elif recipe['tag'] == 'spices':
            spices.append(recipe)
            spices_p.append(get_recipe_price(recipe['id']))
        elif recipe['tag'] == 'others':
            others.append(recipe)
            others_p.append(get_recipe_price(recipe['id']))

    recipes = [starches, proteins, beans, vegetables, dessert, sauces, spices, others]
    prices = [starches_p, proteins_p, beans_p, vegetables_p, dessert_p, sauces_p, spices_p, others_p]

    for r in recipes: #padding so that every list has the same # of elements
        while len(r) < max_length:
            r.append(None)

    for p in prices: #padding so that every list has the same # of elements
        while len(p) < max_length:
            p.append(None)

    #transpose lists so HTML page populates table by row
    recipes = [list(i) for i in zip(*recipes)]
    prices = [list(i) for i in zip(*prices)]

    return render_template('recipes/index.html', recipes=recipes, tags=__tags__, prices=prices)


@bp.route('/<recipeID>/')
def display_recipe(recipeID):
    """
    Displays a recipe given its index number.
    ==> recipe = [recipeSQL, list(ingSQL), ing_names: list(str),
    macros_ing: list(int)[ing caloric values], macro_totals: list(int)]
    """
    db = get_db()
    recipe = db.execute('SELECT * from RECIPE where id = ?', (recipeID)).fetchall()

    if not recipe:
        abort(404, f"{recipeID} is not in the Recipe table.")

    recipe.append(db.execute(
        'SELECT ingredientID, quantity, units FROM recipeIngredientRelationship'
        ' WHERE recipeID=(?)', (recipeID,)
    ).fetchall())

    # prevents division by 0 in case servings was not added correctly
    servings = recipe[0]['servings'] if recipe[0]['servings'] else 1
    macros_recipe = []  # list(list(int)) containing macros of each ingredient
    ing_names = []  # list(str) of ingredient names
    macro_totals = [0, 0, 0, 0]  # carbs, protein, fat, calories
    prices = []

    if recipe[1]:
        for ing in recipe[1]:

            ing_id = str(ing['ingredientID'])
            ing_db = db.execute('SELECT * FROM ingredient WHERE id=?',
                                (ing_id,)).fetchone()
            ing_names.append(ing_db['name'])

            macro_db = db.execute(
                'SELECT carbs, fat, protein, calories, portion_size, '
                'portion_size_unit, portion_converted FROM ingredient WHERE id=?',
                (ing_id,)).fetchone()

            macros_ing = [macro_db['carbs'], macro_db['fat'],
                         macro_db['protein'], macro_db['calories']]

            quantity_g_ml = convert(ing['units'], ing['quantity'])
            if quantity_g_ml == 0:
                quantity_g_ml = 1
            ratio = macro_db['portion_converted'] / quantity_g_ml

            # appends a list of ingredient macros
            if ratio == 0:
                ratio = 1

            macros_recipe.append([round(x / servings / ratio, 1) for x in macros_ing])

            macro_totals = [x + (y / servings / ratio) for x, y in zip(macro_totals, macros_ing)]

            denominator = convert(ing_db['price_size_unit'], ing_db['price_size'])
            if denominator == 0:
                denominator = 1

            prices.append(((ing_db['price'] / denominator
                            ) * quantity_g_ml ) / (100 * servings))

    recipe.append(ing_names)
    recipe.append(macros_recipe)
    recipe.append([round(x, 1) for x in macro_totals])

    return render_template('recipes/display.html', recipe=recipe, total_price=round(sum(prices), 2),
                           nutritions=macros_recipe, prices=[round(x, 2) for x in prices])


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
            print(error)
            flash(error)

        else:
            db.execute(
                'INSERT OR REPLACE INTO recipe (author_id, title, body, servings, tag)'
                ' VALUES (?, ?, ?, ?, ?)',
                (g.user['username'], data['title'], data['instructions'], data['servings'], data['tag'])
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
                    'INSERT OR REPLACE INTO recipeIngredientRelationship (recipeID, ingredientID, quantity, units)'
                    ' VALUES (?, ?, ?, ?)',
                    (recipeID['id'], ingID['id'], ing['quantity'], ing['portion'])
                )

            db.commit()
            # https://stackoverflow.com/questions/199099/how-to-manage-a-redirect-request-after-a-jquery-ajax-call
            return redirect(url_for('recipes.index'))

    return render_template('recipes/create.html', ingredients=get_ingredients(), units=__units__, tags=__tags__)


@bp.route('/<recipeID>/update', methods=('GET', 'POST'))
@login_required
def update(recipeID):
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

            db.execute('DELETE FROM recipe where id=?', (recipeID,))

            db.execute('DELETE FROM recipeIngredientRelationship where recipeID=?',
                       (recipeID,))

            db.execute(
                'INSERT INTO recipe (author_id, title, body, servings, tag)'
                ' VALUES (?, ?, ?, ?, ?)',
                (g.user['username'], data['title'], data['instructions'], data['servings'], data['tag'])
            )

            for ing in data['ingredients']:
                ingID = db.execute(
                    'SELECT id from ingredient WHERE name_key=(?)',
                    (re.sub(r"\s+", "-", ing['ingName']).lower(),)
                ).fetchone()

                db.execute(
                    'INSERT INTO recipeIngredientRelationship (recipeID, ingredientID, quantity, units)'
                    ' VALUES (?, ?, ?, ?)',
                    (recipeID, ingID['id'], ing['quantity'], ing['portion'])
                )

            db.commit()
            return redirect(url_for('recipes.index'))

    db = get_db()
    recipe = get_recipe(recipeID)

    # pre-populated entries
    r_quantities = []
    r_units = []
    ings = db.execute(
        'SELECT ingredientID from recipeIngredientRelationship'
        ' WHERE recipeID=?',
        (recipeID,)
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
            (recipeID, ing['ingredientID'])
        ).fetchone()
        r_quantities.append(quant['quantity'])

        unit = db.execute(
            'SELECT units FROM recipeIngredientRelationship'
            ' WHERE recipeID = ? '
            'AND ingredientID = ?',
            (recipeID, ing['ingredientID'])
        ).fetchone()
        r_units.append(unit['units'])

    pre_pop = {"quantity": r_quantities, "units": r_units, "ings": r_ings}

    return render_template('recipes/update.html', prepop=pre_pop, recipe=recipe,
                           quantities=[i for i in range(1, len(r_ings) + 1)],
                           ingredients=get_ingredients(), units=__units__, tags=__tags__, pageId=recipeID)


@bp.route('/<name_key>/delete', methods=('POST',))
@login_required
def delete(name_key):
    db = get_db()
    db.execute('DELETE FROM recipe WHERE id = ?', (name_key,))
    db.execute('DELETE FROM recipeIngredientRelationship WHERE recipeID = ?', (name_key,))
    db.execute('DELETE FROM mealRecipeRelationship WHERE recipeID = ?', (name_key,))
    db.commit()
    return redirect(url_for('recipes.index'))

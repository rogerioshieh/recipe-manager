"""
Helper functions used by routers.
"""

from werkzeug.exceptions import abort
from app.db import get_db


def convert(unit, size):
    """
    Converts a given unit to grams or ml.
    :param unit: unit to be converted
    :type unit: str in ('kg', 'oz', 'lb', 'cup', 'l', 'gal', 'T', 't')
    :param size: how many servings
    @:returns res: int in g or ml
    """

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


def get_recipe_price(recipe_id):
    """
    Calculates total price of recipe, given its index.
    :param recipe_id: index of recipe
    :return: float (two decimals)
    """
    db = get_db()
    recipe = db.execute('SELECT * from RECIPE where id = ?', (recipe_id,)).fetchall()

    recipe.append(db.execute(
        'SELECT ingredientID, quantity, units FROM recipeIngredientRelationship'
        ' WHERE recipeID=(?)', (recipe_id,)).fetchall())

    servings = recipe[0]['servings'] if recipe[0]['servings'] else 1
    prices = []

    if recipe[1]:
        for ing in recipe[1]:
            ing_id = str(ing['ingredientID'])
            ing_db = db.execute('SELECT * FROM ingredient WHERE id=?',
                                (ing_id,)).fetchone()

            quantity_g_ml = convert(ing['units'], ing['quantity'])

            denominator = convert(ing_db['price_size_unit'], ing_db['price_size'])
            if denominator == 0:
                denominator = 1

            prices.append(((ing_db['price'] / denominator) * quantity_g_ml) / (100 * servings))

    return round(sum(prices), 2)


def get_macros_price(recipe, desired_servings):
    """
    Calculates macros and price of recipe given the number of desired servings.
    :param recipe: SQL object
    :param desired_servings: number of intended servings
    :type desired_servings: int
    :returns: list of two lists, first=macros (carbs, fat, protein, calories), second=prices
    :rtype: list(list(int), list(int))
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

        # updates macro_totals with recipe macros
        macro_totals = [x + (y / servings / ratio) for x, y in zip(macro_totals, macros_ing)]

        prices_total += ((ing_db['price'] / convert(ing_db['price_size_unit'], ing_db['price_size'])
                          ) * quantity_g_ml) / (100 * servings)

    res.append([round(x * servings / desired_servings, 1) for x in macro_totals])
    res.append(round(prices_total * servings / desired_servings, 2))

    return res


def get_meal_price(meal_id):
    """
    Calculates total price of meal, given its index.
    """
    db = get_db()
    servings = db.execute('SELECT servings FROM mealRecipeRelationship WHERE mealID=?', str(meal_id)).fetchone()['servings']

    recipe_ids = db.execute('SELECT * FROM mealRecipeRelationship WHERE mealID=?', str(meal_id)).fetchall()

    prices = []

    for recipe in recipe_ids:
        recipe_db = db.execute('SELECT * FROM recipe WHERE id=(?)', (recipe['recipeID'],)).fetchone()
        prices.append(get_macros_price(recipe_db, int(servings))[1])

    return sum(prices)


def get_ing(name_key):
    """
    Returns SQL object of ingredient given its index.
    """
    ing = get_db().execute('SELECT * FROM ingredient WHERE name_key = ?', (name_key,)).fetchone()

    if ing is None:
        abort(404, f"{name_key} is not in the Ingredient table.")

    return ing


def get_recipe(name_key):
    """
    Returns SQL object of recipe given its index.
    """
    recipe = get_db().execute(
        'SELECT *'
        ' FROM recipe'
        ' WHERE id = ?',
        (int(name_key),)
    ).fetchone()

    if recipe is None:
        abort(404, "{0} is not in the Ingredient table.".format(name_key))

    return recipe


def get_meal(meal_id):
    """
    Returns SQL object of meal given its index.
    """
    meal = get_db().execute(
        'SELECT * FROM meal WHERE id = ?',(int(meal_id),)
    ).fetchone()

    return meal if meal is not None else abort(404, f"{meal_id} is not in the Meal table.")


def get_ingredients():
    """
    Returns a list of ingredient names in alphabetical order.
    """
    res = []
    for ing in get_db().execute('SELECT * FROM ingredient ORDER BY name ASC').fetchall():
        res.append(ing['name'])

    return sorted(res)


def get_recipes():
    """
    Returns a list of recipe names in alphabetical order.
    """
    res = []
    for recipe in get_db().execute('SELECT * FROM recipe ORDER BY title ASC').fetchall():
        res.append(recipe['title'])

    return sorted(res)


def get_servings(meal_id):
    """
    Returns number of servings of a meal.
    """
    return get_db().execute('SELECT servings FROM mealRecipeRelationship WHERE mealID=?', (meal_id,)).fetchone()['servings']

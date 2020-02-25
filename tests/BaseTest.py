"""
Base class for used across all tests.
"""

from flask import Flask, session, redirect, url_for
from app import db
from flask_testing import TestCase
import os
import app.helpers as h


class BaseTest(TestCase):

    def create_app(self):

        self.app = Flask(__name__, template_folder='app/templates')
        self.app.config['TESTING'] = True
        self.app.config['USERNAME'] = 'unittest'
        self.app.config['PASSWORD'] = 'unittest'
        self.app.testing = True
        self.app.config.from_mapping(
            SECRET_KEY='dev',
            DATABASE=os.path.join(self.app.instance_path, 'test_app.sqlite'),
        )

        # ensure the instance folder exists
        try:
            os.makedirs(self.app.instance_path)
        except OSError:
            pass

        with self.app.app_context():
            db.init_app(self.app)
            db.init_db()
            self.db = db.get_db()

            from app.routers import recipes, meals, ingredients, auth

            self.app.register_blueprint(auth.bp)
            self.app.register_blueprint(ingredients.bp)
            self.app.register_blueprint(recipes.bp)
            self.app.register_blueprint(meals.bp)

            @self.app.route('/')
            def index():
                """ Displays the index page accessible at '/'
                """
                return redirect(url_for('recipes.index'))

            # adding ingredients

            # liquid ingredient
            ing1 = {'id': 1, 'name': "ing_unittest1_liquid", 'name_key': "ing_unittest1_liquid",
                    'portion_size': 4, 'portion_size_unit': "cup", 'portion_converted': h.convert("cup", 4),
                    'protein': 5.5, 'fat': 7.1, 'carbs': 20.5, 'calories': 98, 'price': 0 * 100,
                    'price_size': 0.01, 'price_size_unit': "gal", 'tag': "dairy", 'notes': "no notes"}
            # spice ingredient (macros are 0, price is based on units)
            ing2 = {'id': 2, 'name': "ing_unittest2_spice", 'name_key': "ing_unittest2_spice",
                    'portion_size': 2, 'portion_size_unit': "unit", 'portion_converted': h.convert("unit", 2),
                    'protein': 0, 'fat': 0, 'carbs': 0, 'calories': 0, 'price': 2.99 * 100,
                    'price_size': 2, 'price_size_unit': "unit", 'tag': "spices", 'notes': "no notes"}
            # solid ingredient
            ing3 = {'id': 3, 'name': "ing_unittest3_solid", 'name_key': "ing_unittest3_solid",
                    'portion_size': 355, 'portion_size_unit': "g", 'portion_converted': h.convert("g", 355),
                    'protein': 21.2, 'fat': 14, 'carbs': 133, 'calories': 257, 'price': 3.79 * 100,
                    'price_size': .5, 'price_size_unit': "kg", 'tag': "proteins", 'notes': "no notes"}
            # flour (cup measures are to be converted to grams, not volume)
            ing4 = {'id': 4, 'name': "ing_unittest4_cup", 'name_key': "ing_unittest4_cup",
                    'portion_size': 4, 'portion_size_unit': "cup", 'portion_converted': h.convert("cup", 4),
                    'protein': 5.2, 'fat': 23, 'carbs': 23, 'calories': 240, 'price': 3.04 * 100,
                    'price_size': 5, 'price_size_unit': "lb", 'tag': "carbs", 'notes': "no notes"}
            # onion (portion is unit but price is in lbs)
            ing5 = {'id': 5, 'name': "ing_unittest5_onion", 'name_key': "ing_unittest5_onion",
                    'portion_size': 2, 'portion_size_unit': "unit", 'portion_converted': h.convert("unit", 2),
                    'protein': 2, 'fat': 2, 'carbs': 2, 'calories': 17, 'price': 2.99 * 100,
                    'price_size': 5, 'price_size_unit': "lb", 'tag': "vegetables", 'notes': "no notes"}


            for ing in [ing1, ing2, ing3, ing4, ing5]:
                self.db.execute('INSERT INTO ingredient VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                               tuple(ing.values()))

            # adding recipes
            recipe1 = [
                {'id': 1, 'author_id': "unittest", 'title': "recipe_unittest1", 'body': "Empty body", 'servings': 3,
                 'tag': "beans"},
                [(ing2, 1, 't'), (ing3, 14, 'oz'), (ing5, 1, 'unit')]]
            recipe2 = [
                {'id': 2, 'author_id': "unittest", 'title': "recipe_unittest2", 'body': "Empty body", 'servings': 4,
                 'tag': "dessert"},
                [(ing2, 1, 'T'), (ing1, 6, 'oz'), (ing4, 280, 'g')]]

            for r, ings in [recipe1, recipe2]:
                self.db.execute('INSERT INTO recipe VALUES (?, ?, ?, ?, ?, ?)', tuple(r.values()))
                for ing in ings:
                    self.db.execute('INSERT INTO recipeIngredientRelationship (recipeID, ingredientID, quantity, units) '
                                   'VALUES (?, ?, ?, ?)', (r['id'], ing[0]['id'], ing[1], ing[2]))

            # adding meals
            meal1 = [{'id': 1, 'author_id': "unittest", 'title': "meal_unittest1", 'tag': "easy", 'notes': "None."},
                     [recipe1], 4]
            meal2 = [{'id': 2, 'author_id': "unittest", 'title': "meal_unittest2", 'tag': "brunch", 'notes': "None."},
                     [recipe1, recipe2], 3]

            for m, recipes, servings in [meal1, meal2]:
                self.db.execute('INSERT INTO meal VALUES (?, ?, ?, ?, ?)', tuple(m.values()))
                for r in recipes:
                    self.db.execute('INSERT INTO mealRecipeRelationship (mealID, recipeID, servings) '
                                   'VALUES (?, ?, ?)', (m['id'], r[0]['id'], servings))

            self.db.commit()
        return self.app

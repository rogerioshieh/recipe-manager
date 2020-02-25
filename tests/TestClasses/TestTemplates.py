import unittest
from app.tests.BaseTest import BaseTest
from app.tests.helpers_unittest import register, login, logout, create_ingredient, create_recipe


class TestTemplates(BaseTest):

    render_templates = False

    def test_register(self):
        """Make sure register user works."""
        app = self.create_app()
        c = app.test_client()

        # test response of register page
        c.get('/auth/register')
        self.assert_template_used("auth/register.html")

        # test registering user
        rv = register(c, app.config['USERNAME'], app.config['PASSWORD'])
        self.assert_status(rv, 200)

        # test registering user with the same name
        register(c, app.config['USERNAME'], app.config['PASSWORD'])
        self.assert_message_flashed(f"User {app.config['USERNAME']} is already registered.")

    def test_login_logout(self):
        """Make sure login and logout works."""

        app = self.create_app()
        c = app.test_client()

        register(c, app.config['USERNAME'], app.config['PASSWORD'])

        login(c, app.config['USERNAME'], app.config['PASSWORD'])
        self.assert_template_used("ingredients/index.html")

        logout(c)
        self.assert_template_used("recipes/index.html")

        login(c, app.config['USERNAME'] + 'x', app.config['PASSWORD'])
        self.assert_message_flashed("Incorrect username.")

        login(c, app.config['USERNAME'], app.config['PASSWORD'] + 'x')
        self.assert_message_flashed("Incorrect password.")

    def test_ingredients_index(self):
        """Make sure /ingredients returns ingredients/index.html"""
        app = self.create_app()

        c = app.test_client()

        c.get('/ingredients/', follow_redirects=True)
        self.assert_template_used("ingredients/index.html")

    def test_ingredients_create(self):
        """Make sure authentication is needed for creating ingredient"""
        app = self.create_app()
        c = app.test_client()

        # test if authorization is required to create an ingredient
        rv = c.get('/ingredients/create')
        self.assertRedirects(rv, "/auth/login")

        register(c, app.config["USERNAME"], app.config["PASSWORD"])
        login(c, app.config["USERNAME"], app.config["PASSWORD"])
        c.get('/ingredients/create')
        self.assert_template_used("ingredients/create.html")

        # tests if ingredient already in database
        create_ingredient(c, {'id': 1, 'name': "ing_unittest1_liquid", 'portion_size': 4, 'portion_size_unit': "cup",
                    'protein': 5.5, 'fat': 7.1, 'carbs': 20.5, 'calories': 98, 'price': 0,
                    'price_size': 0.01, 'price_size_unit': "gal", 'tag': "dairy", 'notes': "no notes"})
        self.assert_message_flashed("Ingredient already in the database.")

        # tests inserting new ingredient
        create_ingredient(c, {'id': 1, 'name': "XXXXX", 'portion_size': 4, 'portion_size_unit': "cup",
                              'protein': 5.5, 'fat': 7.1, 'carbs': 20.5, 'calories': 98, 'price': 0,
                              'price_size': 0.01, 'price_size_unit': "gal", 'tag': "dairy", 'notes': "no notes"})
        self.assert_template_used("ingredients/index.html")

    def test_ingredients_update(self):
        """Make sure authentication is needed for updating ingredient"""
        app = self.create_app()

        c = app.test_client()

        # tests if authorization is required
        rv = c.get('/ingredients/1/update')
        self.assertRedirects(rv, "/auth/login")

        register(c, app.config["USERNAME"], app.config["PASSWORD"])
        login(c, app.config["USERNAME"], app.config["PASSWORD"])
        c.get('/ingredients/ing_unittest1_liquid/update')
        self.assert_template_used("ingredients/update.html")

    def test_recipes_index(self):
        """Make sure /recipes returns recipes/index.html"""
        app = self.create_app()

        c = app.test_client()

        c.get('/recipes/', follow_redirects=True)
        self.assert_template_used("recipes/index.html")

    def test_recipes_create(self):
        """Make sure authentication is needed for creating recipe"""
        app = self.create_app()
        c = app.test_client()

        # test if authorization is required to create a recipe
        rv = c.get('/recipes/create')
        self.assertRedirects(rv, "/auth/login")

        # test recipe page
        register(c, app.config["USERNAME"], app.config["PASSWORD"])
        login(c, app.config["USERNAME"], app.config["PASSWORD"])
        c.get('/recipes/create')
        self.assert_template_used("recipes/create.html")

        # test adding recipe
        recipe = {'author_id': "unittest", 'title': "recipe_unittest2", 'body': "Empty body",
                  'servings': 4, 'tag': "dessert", 'ingredients': [{'ingName': "ing_unittest3_solid", 'quantity': 180, 'portion': 'g'}, {
                     'ingName': "ing_unittest1_liquid", 'quantity': 2, 'portion': 'cup'}]}
        with app.app_context():
            create_recipe(c, recipe)
            self.assert_template_used("recipes/index.html")


if __name__ == '__main__':
    unittest.main()

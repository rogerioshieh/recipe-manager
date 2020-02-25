"""
Helper methods used in testing.
"""

import json


def logout(client):
    return client.get('/auth/logout', follow_redirects=True)


def register(client, username, password):
    return client.post('/auth/register', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)


def login(client, username, password):
    return client.post('/auth/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)


def create_ingredient(client, ing):
    """
    Adds an ingredient on the database.
    :param client: Flask client
    :param ing: ingredient to be added
    :type ing: dict
    """
    return client.post('/ingredients/create', data=dict(
        id=ing['id'], name=ing['name'], portion_size = ing['portion_size'],
        portion_size_unit = ing['portion_size_unit'], protein = ing['protein'],fat = ing['fat'], carbs = ing['carbs'],
        calories = ing['calories'], price = ing['price'], price_size = ing['price_size'],
        price_size_unit = ing['price_size_unit'], tag = ing['tag'], notes = ing['notes']
    ), follow_redirects=True)


def create_recipe(client, r):
    return client.post('/recipes/create', json=dict(
        author_id=r['author_id'], title=r['title'], instructions=r['body'], servings=r['servings'], tag=r['tag'],
        ingredients=r['ingredients']
    ), follow_redirects=True)

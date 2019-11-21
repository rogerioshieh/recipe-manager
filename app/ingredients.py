"""
Blueprint for ingredients.

Views:
- Index (displays most recently added ingredients)
- Create
- Update
- Delete (does not have a template)
"""


from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db

bp = Blueprint("ingredients", __name__, url_prefix="/ingredients")


#TODO: edit the index function and index.html page  
def index():
    db = get_db()
    posts = db.execute(
        'SELECT title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)

@bp.route('/create', methods=('GET', 'POST'))
#@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        portion_size = request.form['portion_size']
        portion_size_unit = request.form['portion_size_unit']
        protein = request.form['protein']
        fat = request.form['fat']
        carbs = request.form['carbs']
        error = None

        if not title:
            error = 'Title is required.'

        elif not portion_size:
            error = 'Portion size is required.'

        elif not portion_size_unit:
            error = 'Portion size unit is required.'

        elif not protein:
            error = 'Protein content is required.'

        elif not fat:
            error = 'Fat content is required.'

        elif not carbs:
            error = 'Carbs content is required.'

        if error is not None:
            flash(error)

        else:
            db = get_db()
            db.execute(
                'INSERT INTO ingredient (title, portion_size, portion_size_unit, protein, fat, carbs)'
                ' VALUES (?, ?, ?, ?, ?, ?)',
                (title, portion_size, portion_size_unit, protein, fat, carbs)
            )
            db.commit()
            return redirect(url_for('ingredients.index'))

    return render_template('ingredients/create.html')


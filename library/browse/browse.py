from flask import Blueprint, render_template, request, redirect, url_for, session
from math import ceil
from better_profanity import profanity

from flask_wtf.form import FlaskForm
from wtforms.fields.core import RadioField
from wtforms.fields.simple import SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError
from library.home.home import FavouritesForm


import library.adapters.repository as repo
import library.browse.services as services

from library.authentication.authentication import login_required

browse_blueprint = Blueprint(
    'browse_bp', __name__)


@browse_blueprint.route('/browse', methods=['GET'])
def browse():
    books_per_page = 5

    page_num = request.args.get('page')  # cursor
    if page_num is None:
        page_num = 1
    else:
        page_num = int(page_num)

    # --------- Filtering ----------
    filter = request.args.get('filter')
    letter = request.args.get('letter')
    year = request.args.get('year')

    books = services.get_all_books(repo.repo_instance)
    if letter is not None:
        if filter == 'author':
            books = services.get_books_by_author_initial(letter, repo.repo_instance)
        elif filter == 'publisher':
            books = services.get_books_by_publisher_initial(letter, repo.repo_instance)
    if year is not None:
        if year == 'None':
            books = services.get_books_with_no_year(repo.repo_instance)
        else:
            year = int(year)
            books = services.get_books_by_year(year, repo.repo_instance)

    year_list = services.get_book_years(repo.repo_instance)

    # ----- NAVIGATION BUTTONS -----
    next_page_url = None
    prev_page_url = None
    first_page_url = None
    last_page_url = None

    if page_num - 1 > 0:
        prev_page_url = url_for('browse_bp.browse', filter=filter, letter=letter, year=year, page=page_num - 1)
        first_page_url = url_for('browse_bp.browse', filter=filter, letter=letter, year=year)
    if page_num * books_per_page < len(books):
        next_page_url = url_for('browse_bp.browse', filter=filter, letter=letter, year=year, page=page_num + 1)
        last_page_url = url_for('browse_bp.browse', filter=filter, letter=letter, year=year, page=ceil(len(books) / books_per_page))

    # -- Displaying limited amount of books per page --
    if books_per_page * page_num < len(books):
        books = books[(page_num - 1) * books_per_page: page_num * books_per_page]
    else:
        books = books[(page_num - 1) * books_per_page: len(books)]

    letters_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

    return render_template(
        'browse/browse.html',
        books=books,
        next_page_url=next_page_url,
        prev_page_url=prev_page_url,
        first_page_url=first_page_url,
        last_page_url=last_page_url,
        page=page_num,
        filter=filter,
        letters_list=letters_list,
        year_list=year_list
        
    )


@browse_blueprint.route('/book/<int:book_id>', methods=['GET', 'POST'])
def show_book(book_id: int):
    book = services.get_book(book_id, repo.repo_instance)
    stock = services.get_book_stock(book_id, repo.repo_instance)
    price = services.get_book_price(book_id, repo.repo_instance)
    reviews = services.get_all_reviews_of_book(book_id, repo.repo_instance)

    user_name = None
    if 'user_name' in session:
        user_name = session['user_name']
        book_in_favourites = services.book_in_user_favourites(user_name, book_id, repo.repo_instance)
    
    else:
        book_in_favourites = None
    form = FavouritesForm()

    if form.validate_on_submit():
        if book_in_favourites:
            services.remove_book_from_user_favourites(user_name, book_id, repo.repo_instance)
            return render_template(
            'browse/book.html',
            book=book,
            stock=stock,
            price=price,
            reviews=reviews,
            form=form,
            book_in_favourites=False
            )

        services.add_book_to_user_favourites(user_name, book_id, repo.repo_instance)
        form.submit.label.text = 'Remove from Favourites'
        return render_template(
            'browse/book.html',
            book=book,
            stock=stock,
            price=price,
            reviews=reviews,
            form=form,
            book_in_favourites=True
            )

    if book_in_favourites is False:
        form.submit.label.text = 'Add to Favourites'
    elif book_in_favourites is True:
        form.submit.label.text = 'Remove from Favourites'

    return render_template(
        'browse/book.html',
        book=book,
        stock=stock,
        price=price,
        reviews=reviews,
        form=form,
        book_in_favourites=book_in_favourites
    )


@browse_blueprint.route('/review/<int:book_id>', methods=['GET', 'POST'])
@login_required
def add_review(book_id: int):
    book = services.get_book(book_id, repo.repo_instance)
    form = ReviewForm()

    book_nonexistent = None
    review_form_empty = None

    if form.validate_on_submit():
        try:
            services.add_review(book_id, form.review_text.data, int(form.rating.data), repo.repo_instance)
            return redirect(url_for('browse_bp.show_book', book_id=book_id))
        except services.NonExistentBookException:
            book_nonexistent = 'Book does not exist'

        except services.ReviewFormInvalid:
            review_form_empty = 'Please fill in all fields before submitting'

    return render_template(
        'browse/review.html',
        book=book,
        book_error=book_nonexistent,
        form_error=review_form_empty,
        form=form
    )


class ProfanityFree:
    def __init__(self, message=None):
        if not message:
            message = u'Field must not contain profanity'
        self.message = message

    def __call__(self, form, field):
        if profanity.contains_profanity(field.data):
            raise ValidationError(self.message)


class ReviewForm(FlaskForm):
    rating = RadioField('rating', choices=[('5', ''), ('4', ''), ('3', ''), ('2', ''), ('1', '')])
    review_text = TextAreaField('Write a Review:', [
        ProfanityFree(message="Your review must not contain profanity.")
    ])
    submit = SubmitField('Submit Review')


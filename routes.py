from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from models import add_book, add_or_update_review, books_collection
from bson.objectid import ObjectId
import requests
import os
from urllib.parse import urlparse

routes = Blueprint('routes', __name__)

# Define the home route
@routes.route('/')
def home():
    return render_template('home.html')

# Route for adding books
@routes.route('/add-book', methods=['GET', 'POST'])
def add_new_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        summary = request.form['summary']
        page_count = int(request.form['page_count'])
        cover_image = request.form['cover_image'] # URL or file path for cover image

        book_id = add_book(title, author, genre, summary, page_count, cover_image)

        flash('Book added successfully!', 'success')
        return redirect(url_for('routes.book_details', book_id=str(book_id)))

    return render_template('add_book.html')

@routes.route('/book/<book_id>', methods=['GET', 'POST'])
def book_details(book_id):
    book = books_collection.find_one({"_id": ObjectId(book_id)})

    user_id = session.get('user_id')

    existing_review = None
    if user_id:
        existing_review = next((review for review in book.get("reviews", []) if review["user_id"] == user_id), None)

    if request.method == 'POST' and not existing_review:
        rating = int(request.form['rating'])
        review_text = request.form['review']
        date_read = request.form['date_read']

        add_or_update_review(book_id, user_id, session.get('username'), rating, review_text, date_read)

        flash('Review added successfully!', 'success')
        return redirect(url_for('routes.book_details', book_id=book_id))

    return render_template('book_details.html', book=book, existing_review=existing_review)

@routes.route('/book/<book_id>/edit-review', methods=['GET', 'POST'])
def edit_review(book_id):
    book = books_collection.find_one({"_id": ObjectId(book_id)})
    user_id = session.get('user_id')
    existing_review = next((review for review in book["reviews"] if review["user_id"] == user_id), None)

    if not existing_review:
        flash("You haven't reviewed this book yet!", "danger")
        return redirect(url_for('routes.book_details', book_id=book_id))
    
    if request.method == 'POST':
        rating = int(request.form['rating'])
        review_text = request.form['review']
        date_read = request.form['date_read']
        add_or_update_review(book_id, user_id, session.get('username'), rating, review_text, date_read)

        flash("Review updated successfully!", "success")
        return redirect(url_for('routes.book_details', book_id=book_id))
    
    return render_template('edit_review.html', book=book, review=existing_review)

@routes.route('/search', methods=['GET'])
def search_books():
    search_query = request.args.get('q', '').strip()

    if not search_query:
        flash("Please enter a search term.", "warning")
        return redirect(url_for('routes.home'))
    
    books = books_collection.find({
        "$or": [
            {"title": {"$regex": search_query, "$options": "i"}},
            {"author": {"$regex": search_query, "$options": "i"}}
        ]
    }).sort("author", 1)

    return render_template('search_results.html', books=books, query=search_query)

@routes.route('/my-reviews')
def my_reviews():
    user_id = session.get('user_id')

    if not user_id:
        flash("You must be logged in to view your reviews.", "warning")
        return redirect(url_for('auth.login'))
    
    reviewed_books = books_collection.find({
        "reviews.user_id": user_id
    })

    return render_template('my_reviews.html', books=reviewed_books)

@routes.route('/book/<book_id>/edit', methods=['GET', 'POST'])
def edit_book(book_id):
    book = books_collection.find_one({"_id": ObjectId(book_id)})

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        summary = request.form['summary']
        page_count = int(request.form['page_count'])
        cover_image = request.form['cover_image']

        # Directory to store images
        image_folder = os.path.join(current_app.root_path, 'static', 'images')
        os.makedirs(image_folder, exist_ok=True)

        local_image_path = book.get("cover_image", "")
        if cover_image:
            try:
                # Extract filename from URL
                parsed_url = urlparse(cover_image)
                filename = os.path.basename(parsed_url.path)

                # Save image locally
                local_image_path = os.path.join(image_folder, filename)
                response = requests.get(cover_image, stream=True)
                if response.status_code == 200:
                    with open(local_image_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    # Store only the relative path for usage in HTML
                    local_image_path = f"static/images/{filename}"
            except Exception as e:
                flash(f"Failed to download cover image: {e}", "danger")

        # Update the book document
        books_collection.update_one(
            {"_id": ObjectId(book_id)},
            {"$set": {
                "title": title,
                "author": author,
                "genre": genre,
                "summary": summary,
                "page_count": page_count,
                "cover_image": local_image_path
            }}
        )

        flash("Book updated successfully!", "success")
        return redirect(url_for('routes.book_details', book_id=book_id))
    
    return render_template('edit_book.html', book=book)

@routes.route('/books')
def books():
    books = books_collection.find().sort("author", 1)
    return render_template('books_list.html', books=books)

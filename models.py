from pymongo import MongoClient
from flask_bcrypt import Bcrypt
import os
from datetime import datetime
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
MONGO_KEY = os.getenv("MONGO_KEY")


# Connect to MongoDB
MONGO_URI = MONGO_KEY

client = MongoClient(MONGO_URI)
db = client["booksite"]
books_collection = db["books"]
users_collection = db["users"]

bcrypt = Bcrypt()

# User registration function
def register_user(username, password):
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    users_collection.insert_one({"username": username, "password": hashed_pw})

# User login function
def check_user_login(username, password):
    user = users_collection.find_one({"username": username})
    if user and bcrypt.check_password_hash(user["password"], password):
        return user
    return None

def add_book(title, author, genre, summary, page_count, cover_image=None):
    book = {
            "title": title,
            "author": author,
            "genre": genre,
            "summary": summary,
            "page_count": page_count,
            "cover_image": cover_image,
            "average_rating": 0.0,
            "number_of_ratings": 0,
            "reviews": []
    }
    return books_collection.insert_one(book).inserted_id
    

def add_or_update_review(book_id, user_id, username, rating, review_text, date_read):
    # Check if the user already reviewed the book
    book = books_collection.find_one({"_id": ObjectId(book_id)})
    existing_review = next((review for review in book["reviews"] if review["user_id"] == user_id), None)

    if existing_review:
        # If the user already has a review, update it instead of adding a new one
        books_collection.update_one(
            {"_id": ObjectId(book_id), "reviews.user_id": user_id},
            {"$set": {
                "reviews.$.review_text": review_text,
                "reviews.$.rating": rating,
                "reviews.$.date_read": date_read
            }}
        )
    else:
    # Add the review to the book's reviews array
        new_review = {
            "user_id": user_id,
            "username": username,
            "rating": rating,
            "review_text": review_text,
            "date_read": date_read
        }

        books_collection.update_one(
            {"_id": ObjectId(book_id)},
            {"$push": {"reviews": new_review}}
        )

    # Force re-fetch of data
    updated_book = books_collection.find_one({"_id": ObjectId(book_id)})

    # Ensure no divide by zero occurs
    number_of_reviews = len(updated_book.get("reviews", []))
    if number_of_reviews == 0:
        new_avg_rating = 0.0
    else:
        total_ratings = sum(review["rating"] for review in updated_book.get("reviews", []))
        new_avg_rating = total_ratings / number_of_reviews

    books_collection.update_one(
            {"_id": ObjectId(book_id)},
            {"$set": {"average_rating": new_avg_rating, "number_of_ratings": number_of_reviews}}
    )

    return "Review Updated" if existing_review else "Review added"

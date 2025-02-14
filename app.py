from routes import routes
from auth import auth
from flask import Flask, session, redirect, url_for
from models import db, books_collection, users_collection
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

app.register_blueprint(routes)
app.register_blueprint(auth, url_prefix='/auth')

@app.route('/')
def home():
    if 'user_id' in session:
        return f"Welcome {session['username']}!"
    return redirect(url_for('routes.home'))


if __name__ == "__main__":
    app.run(debug=True)

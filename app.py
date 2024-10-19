from flask_sqlalchemy import SQLAlchemy
import os
import uuid
from flask import Flask, redirect, request, url_for, render_template
from oauthlib.oauth2 import WebApplicationClient
import requests
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key in production

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///studentsData.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    token = db.Column(db.String(200), nullable=False)
    # profile_picture = db.Column(db.String(200), nullable=True)
    age = db.Column(db.String(10), nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    branch = db.Column(db.String(50), nullable=True)
    food_preference = db.Column(db.String(20), nullable=True)
    religion = db.Column(db.String(20), nullable=True)
    sleeping_time = db.Column(db.String(10), nullable=True)
    video_games = db.Column(db.String(10), nullable=True)
    languages = db.Column(db.String(200), nullable=True)

# Create the database tables
with app.app_context():
    db.create_all()

GOOGLE_CLIENT_ID = "1000069291221-63h0kl6ouo4dri4pfsfitronimnhcgm1.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

client = WebApplicationClient(GOOGLE_CLIENT_ID)

def generate_token(email):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, email))

@app.route("/")
def index():
    return render_template("register.html")

@app.route("/login")
def login():
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=url_for("callback", _external=True),
        scope=["openid", "email", "profile"],
    )

    return redirect(request_uri)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=url_for("callback", _external=True),
        code=code
    )

    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)

    userinfo_response = requests.get(uri, headers=headers, data=body)
    user_info = userinfo_response.json()

    user_token = generate_token(user_info['email'])

    # Check if user already exists
    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        # Redirect to form to fill out details
        return redirect(url_for("form", email=user_info['email'], token=user_token))

    # If user already exists, redirect to the dashboard
    return redirect(url_for('dashboard', email=user_info['email'], token=user_token))

@app.route("/form")
def form():
    email = request.args.get('email')
    token = request.args.get('token')
    
    # Check if the user has already submitted the form
    user = User.query.filter_by(email=email).first()
    if user and user.age and user.gender and user.branch:  # Check if data is already filled
        return redirect(url_for('dashboard', email=email, token=token))

    return render_template("form.html", email=email, token=token)

@app.route("/submit", methods=["POST"])
def submit():
    email = request.args.get('email')
    token = request.args.get("token")
    # Ensure email is in the form
    user = User.query.filter_by(email=email).first()
    if user is None:
        # Create a new user if one does not exist
        user = User(email=email, token=token)
        db.session.add(user)
    print(email,token)
    # Extract data from form
    user.name = request.form.get("name")
    user.age = request.form.get("age")
    user.gender = request.form.get("gender")
    user.branch = request.form.get("branch")
    user.food_preference = request.form.get("food_preference")
    user.religion = request.form.get("religion")
    user.sleeping_time = request.form.get("sleeping_time")
    user.video_games = request.form.get("video_games")
    user.languages = ', '.join(request.form.getlist("languages"))

    db.session.commit()
    # print(request.form.get("name"),request.form.get("branch"))
    print("just before return")
    return redirect(url_for('dashboard', email=email, token=token))


@app.route("/dashboard")
def dashboard():
    email = request.args.get('email')  # Access email from form
    token = request.args.get('token')  # Access token from form
    print("hello")
    user = User.query.filter_by(email=email).first()
    print(user,email,token)
    if not user:
        return redirect(url_for('index'))
    print("hello2")
    user_info = {
        "name": user.name,
        "email": user.email,
        "token": user.token,
        "age": user.age,
        "gender": user.gender,
        "branch": user.branch,
        "food_preference": user.food_preference,
        "religion": user.religion,
        "sleeping_time": user.sleeping_time,
        "video_games": user.video_games,
        "languages": user.languages.split(', ')  # Convert to list for rendering
    }
    
    return render_template("dashboard.html", user_info=user_info)

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, g
import sqlite3

app = Flask(__name__)

# SQLite database setup
DATABASE = 'form_data.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Create a table to store form data
def create_table():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS responses 
                        (token TEXT PRIMARY KEY, food_preference TEXT, religion TEXT, sleeping_time TEXT, video_games TEXT, languages TEXT)''')
        db.commit()

# Route to render the form
@app.route('/')
def form():
    # Example token; you can dynamically generate or pass it
    token = "123ABC"
    return render_template('form.html', token=token)

# Route to handle form submission
@app.route('/submit', methods=['POST'])
def submit_form():
    token = request.args.get('token')  # Primary key (Token) provided as an argument
    food_preference = request.form['food_preference']
    religion = request.form['religion']
    sleeping_time = request.form['sleeping_time']
    video_games = request.form['video_games']
    languages = ', '.join(request.form.getlist('languages'))  # Get all selected languages

    db = get_db()
    cursor = db.cursor()

    # Insert data into the database
    cursor.execute('INSERT INTO responses (token, food_preference, religion, sleeping_time, video_games, languages) VALUES (?, ?, ?, ?, ?, ?)', 
                   (token, food_preference, religion, sleeping_time, video_games, languages))
    db.commit()

    return "Form submitted successfully!"

if __name__ == '__main__':
    create_table()
    app.run(debug=True)

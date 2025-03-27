from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import webbrowser
import threading

# Flask App Initialization
app = Flask(__name__)

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'qwerty1234',  # Change this to your MySQL password
    'database': 'hostel_db'
}

# Function to get MySQL Connection
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

# Route for Home Page
@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('home.html', students=students)

# Add missing routes
@app.route('/registration')
def registration():
    return render_template('registration.html')  # Make sure registration.html exists in the templates folder

@app.route('/rooms')
def rooms():
    return render_template('rooms.html')

@app.route('/facilities')
def facilities():
    return render_template('facilities.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    threading.Timer(1.5, open_browser).start()  # Opens browser automatically after 1.5 seconds
    app.run(debug=True)

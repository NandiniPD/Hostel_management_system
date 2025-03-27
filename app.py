from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import webbrowser
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Set session duration
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = "filesystem"

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'qwerty1234',  # Change this to your MySQL password
    'database': 'hostel_db'
}

# Function to get MySQL Connection
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id, email, password, role):  
        self.id = id
        self.email = email
        self.password = password
        self.role = role  # Store role information


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check in students table
    cursor.execute("SELECT * FROM registered_students WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        role = "student"

    else:
        # Check in admin table (if applicable)
        cursor.execute("SELECT * FROM admins WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        role = "admin" if user_data else None

    cursor.close()
    conn.close()

    if user_data:
        return User(user_data['id'], user_data['email'], user_data['password'], role)  # Corrected role handling

    return None


# Home Route (Welcome Page)
@app.route('/')
def home():
    return render_template('welcome.html')

#login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if role == "student":
            cursor.execute("SELECT * FROM registered_students WHERE email = %s", (email,))
            student_data = cursor.fetchone()
            if student_data and check_password_hash(student_data['password'], password):
                user = User(student_data['id'], student_data['email'], student_data['password'], "student")
                login_user(user)
                flash("Login Successful! Redirecting to Student Dashboard...", "success")
                return redirect(url_for('student_dashboard'))
            else:
                flash("Invalid student credentials. Please try again or register.", "danger")

        elif role == "admin":
            admin_email = 'admin@gmail.com'
            admin_password = 'admin123'

            if email == admin_email and password == admin_password:
                user = User("admin", admin_email, admin_password, "admin")
                login_user(user)
                flash("Login Successful! Redirecting to Admin Dashboard...", "success")
                return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard
            else:
                flash("Invalid admin credentials. Please try again.", "danger")

        cursor.close()
        conn.close()

    return render_template('login.html')


# Welcome Page (Protected)
@app.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html', user=current_user)

#register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        dob = request.form['dob']
        room_preference = request.form['room_preference']
        guardian_name = request.form['guardian_name']
        guardian_contact = request.form['guardian_contact']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM registered_students WHERE email = %s", (email,))
        existing_registered_user = cursor.fetchone()

        if existing_registered_user:
            flash("You have already registered or applied.", "warning")
            return redirect(url_for('login'))

        cursor.execute(
            "INSERT INTO registered_students (name, email, phone, dob, room_preference, guardian_name, guardian_contact, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (name, email, phone, dob, room_preference, guardian_name, guardian_contact, hashed_password),
        )
        conn.commit()

        cursor.close()
        conn.close()

        flash("Registration submitted. You will be notified upon approval.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/room_Alloc')
def room_Alloc():
    return render_template('room_Alloc.html')

@app.route('/hostel_facilities')
def hostel_facilities():
    return render_template('hostel_facilities.html')

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    if current_user.is_authenticated:
        return render_template('student_dashboard.html', user=current_user)
    else:
        flash("You need to log in first!", "warning")
        return redirect(url_for('login'))
    
    
# Sample data for demonstration purposes
students = [
    {'name': 'John Doe', 'id': 12345, 'attendance': 95},
    {'name': 'Jane Smith', 'id': 12346, 'attendance': 88},
    {'name': 'Alice Brown', 'id': 12347, 'attendance': 92},
]

complaints = [
    {'student_name': 'John Doe', 'complaint': 'Missing assignments', 'status': 'Resolved'},
    {'student_name': 'Jane Smith', 'complaint': 'Library book issue', 'status': 'Unresolved'},
    {'student_name': 'Alice Brown', 'complaint': 'Technical issue with login', 'status': 'Resolved'},
]

fee_status = [
    {'student_name': 'John Doe', 'fee_status': 'Paid'},
    {'student_name': 'Jane Smith', 'fee_status': 'Pending'},
    {'student_name': 'Alice Brown', 'fee_status': 'Paid'},
]

rooms = [
    {'room_number': '101', 'status': 'Available'},
    {'room_number': '102', 'status': 'Occupied'},
    {'room_number': '103', 'status': 'Available'},
]

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/view_students')
def view_students():
    return render_template('view_students.html', students=students)

@app.route('/view_registration')
@login_required
def view_registration():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('admin_dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, phone, dob, room_preference, guardian_name, guardian_contact, registration_date FROM registered_students")
    students = cursor.fetchall()
    conn.close()

    return render_template('view_registration.html', students=students)


@app.route('/view_attendance')
def view_attendance():
    return render_template('view_attendance.html', students=students)

@app.route('/view_complaints')
def view_complaints():
    return render_template('view_complaints.html', complaints=complaints)

@app.route('/view_fee_status')
def view_fee_status():
    return render_template('view_fee_status.html', fee_status=fee_status)

@app.route('/view_room_aval')
def view_room_aval():
    return render_template('view_room_aval.html', rooms=rooms)


@app.route('/view_menu')
def view_menu():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM mess_menu")
    menu = cursor.fetchall()
    conn.close()
    return render_template('view_menu.html', menu=menu)

@app.route('/update_menu', methods=['POST'])
def update_menu():
    day = request.form['day']
    breakfast = request.form['breakfast']
    lunch = request.form['lunch']
    dinner = request.form['dinner']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE mess_menu 
        SET breakfast=%s, lunch=%s, dinner=%s 
        WHERE day=%s
    """, (breakfast, lunch, dinner, day))
    
    conn.commit()
    conn.close()
    return redirect(url_for('view_menu'))



@app.route('/attendance')
@login_required
def attendance():
    return render_template('attendance.html', user=current_user)

# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)


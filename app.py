from flask import Flask, request, redirect, render_template, session, flash
import pymysql
import bcrypt
import os
from flask import Flask, request, redirect, render_template, session, flash
import pymysql
import bcrypt
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_connection():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='Amar@3142',
        database='study_platform'
    )
    return connection

# Initial Home Route
@app.route('/')
def home():
    return render_template('home.html')  # Create this home.html file

# User Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        connection = get_connection()
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO users(username, password) VALUES (%s, %s)", (username, hashed_password))
                connection.commit()
        return redirect('/login')
    return render_template('register.html')

# User Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = get_connection()
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, password FROM users WHERE username=%s", (username,))
                user = cursor.fetchone()
                if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
                    session['user_id'] = user[0]  # Store user ID in session
                    return redirect('/dashboard')
                else:
                    flash('Invalid username or password')
        return redirect('/login')
    return render_template('login.html')

# Dashboard Route
@app.route('/dashboard')
def dashboard():
    user_id = session['user_id']
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            # Fetch problems submitted by the user
            cursor.execute("SELECT * FROM problems WHERE user_id=%s", (user_id,))
            my_problems = cursor.fetchall()
            
            # Fetch accepted problems
            cursor.execute("SELECT * FROM problems WHERE status='accepted'")
            problems = cursor.fetchall()
            
            # Fetch all problems
            cursor.execute("SELECT * FROM problems")
            all_problems = cursor.fetchall()

    return render_template('dashboard.html', problems=problems, my_problems=my_problems, all_problems=all_problems)

@app.route('/view_solution/<int:problem_id>')
def view_solution(problem_id):
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            # Fetch solutions for the given problem
            cursor.execute("SELECT solution_text, solution_image FROM solutions WHERE problem_id=%s", (problem_id,))
            solutions = cursor.fetchall()

    return render_template('view_solution.html', solutions=solutions)


# Problem Submission Route
@app.route('/submit_problem', methods=['GET', 'POST'])
def submit_problem():
    if request.method == 'POST':
        problem_text = request.form['problem_text']
        user_id = session['user_id']

        connection = get_connection()
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO problems(user_id, problem_text, status) VALUES (%s, %s, %s)", (user_id, problem_text, 'pending'))
                connection.commit()
        return redirect('/dashboard')
    return render_template('submit_problem.html')

# Admin Review Route
# Admin Review Route
@app.route('/admin/review')
def review_problems():
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            # Fetch all accepted and declined problems along with their status
            cursor.execute("SELECT id, problem_text, status FROM problems WHERE status IN ('accepted', 'declined')")
            verified_problems = cursor.fetchall()
    return render_template('admin_dashboard.html', verified_problems=verified_problems)


# Admin Accept Problem Route
# Admin Login Route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Example: Check if the username and password are correct
        if username == "admin" and password == "yb":  # Replace with your actual admin credentials
            session['is_admin'] = True  # Store admin status in session
            return redirect('/admin/dashboard')  # Redirect to admin dashboard
        else:
            flash('Invalid admin username or password')
            return redirect('/admin/login')

    return render_template('admin_login.html')

# Admin Dashboard Route
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):  # Check if the user is logged in as admin
        return redirect('/admin/login')
    
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM problems WHERE status='pending'")  # Get all pending problems
            problems = cursor.fetchall()
    return render_template('admin_dashboard.html', problems=problems)

# Admin Accept Problem Route
@app.route('/admin/accept/<int:problem_id>')
def accept_problem(problem_id):
    if not session.get('is_admin'):
        return redirect('/admin/login')
    
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE problems SET status='accepted' WHERE id=%s", (problem_id,))
            connection.commit()
    return redirect('/admin/dashboard')

# Admin Decline Problem Route
@app.route('/admin/decline/<int:problem_id>')
def decline_problem(problem_id):
    if not session.get('is_admin'):
        return redirect('/admin/login')
    
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE problems SET status='declined' WHERE id=%s", (problem_id,))
            connection.commit()
    return redirect('/admin/dashboard')



@app.route('/submit_solution/<int:problem_id>', methods=['GET', 'POST'])
def submit_solution(problem_id):
    if request.method == 'POST':
        user_id = session['user_id']
        solution_text = request.form['solution_text']
        solution_image = request.files.get('solution_image')

        # Define the directory for storing images
        images_dir = 'static/images'
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)  # Create directory if it doesn't exist

        # Save the image if it exists
        image_filename = None
        if solution_image:
            # Create a unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            image_filename = f"{timestamp}_{solution_image.filename}"
            image_path = os.path.join(images_dir, image_filename)
            solution_image.save(image_path)

        # Database connection
        connection = get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO solutions(problem_id, user_id, solution_text, solution_image) VALUES (%s, %s, %s, %s)",
                        (problem_id, user_id, solution_text, image_filename)
                    )
                    connection.commit()
            flash('Solution submitted successfully!')
        except Exception as e:
            flash('An error occurred while submitting your solution. Please try again.')
            print(e)  # Log the error for debugging purposes
        return redirect('/dashboard')

    return render_template('submit_solution.html', problem_id=problem_id)



# Admin Logout Route
@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)  # Remove admin status from session
    return redirect('/admin/login')

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user ID from session
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)

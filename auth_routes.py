# auth_routes.py

from flask import Blueprint,json,jsonify, render_template, redirect, session, request, flash,  send_from_directory, current_app
from werkzeug.utils import secure_filename
import os
from functions import *
from extensions import db

from services.db_doctors import *
from services.db_students import *
# تعريف الـ Blueprint
auth_bp = Blueprint('auth', __name__)

# --- دوال التحقق من الملفات (تم الإبقاء على الدالتين كما في الكود الأصلي) ---
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# الدالة الثانية كما هي في الكود الأصلي
def allowed_file(imgname):
    return '.' in imgname and \
           imgname.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- المسارات ---
@auth_bp.route('/')
@auth_bp.route('/home')
def index():
    return render_template('Home.html')

@auth_bp.route('/register-doc')
def get_reg_page():
    if not( check_if_isadmin()):
        data_to_flash = {
        'message': 'sorry,You dont have access',
        'role': 'security' 
        }
        flash(json.dumps(data_to_flash), 'danger')
        return redirect('/')
    else:
        return render_template('reg-maindoc.html')
@auth_bp.route('/register-doc', methods=['POST'])
def post_reg_page():
    if not(check_if_isadmin()):
        data_to_flash = {'message': 'Sorry, you do not have access.', 'role': 'security'}
        flash(json.dumps(data_to_flash), 'danger')
        return redirect('/')

    # --- Start of New Logic ---
    name = request.form.get('name')
    username = request.form.get('username')
    password = request.form.get('password')

    # 1. (Validation) Check if password is too short
    if len(password) < 8:
        error_data = {'message': 'Password must be at least 8 characters long.', 'role': 'warning'}
        flash(json.dumps(error_data), 'warning')
        return redirect('/register-doc')

    # 2. (Validation) Check if username already exists
    existing_user = Doctor.query.filter_by(username=username).first()
    if existing_user:
        error_data = {'message': f'Username "{username}" is already taken.', 'role': 'danger'}
        flash(json.dumps(error_data), 'danger')
        return redirect('/register-doc')

    # 3. If all checks pass, create the new doctor
    # Note: We are now only passing the required fields, others will be None or default.
    # IMPORTANT: You should implement password hashing here in the future.
    # hashed_password = generate_password_hash(password)
    new_doctor = Doctor(
        name=name,
        username=username,
        password=password, # Replace with hashed_password later
        isadmin=False, # Set defaults
        ismadmin=False,
        email=None, # Fields not in the form are set to None
        certificates=None,
        profile_pic=None
    )
    
    db.session.add(new_doctor)
    db.session.commit()

    # 4. Flash a success message
    success_data = {'message': f'Doctor "{name}" has been registered successfully.', 'role': 'user_action'}
    flash(json.dumps(success_data), 'success')
    return redirect('/')

# 5. New route for dynamic username checking with JavaScript
@auth_bp.route('/check-username', methods=['POST'])
def check_username():
    username = request.json.get('username')
    if not username:
        return jsonify({'exists': False})

    user = Doctor.query.filter_by(username=username).first()
    return jsonify({'exists': user is not None})



@auth_bp.route('/logout')
def logout():
    session.clear()
    data_to_flash = {
        'message': 'تم تسجيل الخروج بنجاح.',
        'role': 'user_action' 
    }
    flash(json.dumps(data_to_flash), 'success')

    return redirect("/")

@auth_bp.route('/login', methods=['GET'])
def login_get():
    if  (checkiflogged()):
        data_to_flash = {
        'message': 'You are already logged in',
        'role': 'user_action' 
        }
        flash(json.dumps(data_to_flash), 'info')
        return redirect('/')
    return render_template("logindoctors.html")

@auth_bp.route('/login', methods=['POST'])
def login_post():
    # 1. Check if user is already logged in
    if 'username' in session: # A more direct check
        data_to_flash = {'message': 'You are already logged in.', 'role': 'info'}
        flash(json.dumps(data_to_flash), 'info')
        return redirect('/')

    # 2. Get form data
    username = request.form.get('username')
    password = request.form.get('password')

    # 3. Find user in the database
    user_query = Doctor.getByUsername(username)
    # 4. (SECURITY FIX) Validate user and password in a secure way
    # This check now returns one generic error for both wrong user and wrong password
    # NOTE: The "user_query.password != password" part should be replaced with a hash check later.
    if not user_query or user_query.password != password:
        error_data = {
            'message': 'Invalid username or password.',
            'role': 'security'
        }
        flash(json.dumps(error_data), 'danger')
        return redirect('/login') # Redirect back to the login page itself

    # 5. (SUCCESS) Set session variables clearly
    session.permanent = True
    session["qq"] = True
    session['user_id'] = user_query.id   # Store user ID
    session['username'] = user_query.username # Store username from DB
    session['is_doctor'] = True
    session['isadmin'] = user_query.isadmin
    session['ismadmin'] = user_query.ismadmin
    session['role'] = 'Doctor'
    # 6. Flash success message and redirect
    success_data = {
        'message': f'Welcome back, {user_query.username}!',
        'role': 'user_action'
    }
    flash(json.dumps(success_data), 'success') # Use the 'success' category
    return redirect('/')



@auth_bp.route('/login-stu', methods=['GET'])
def login_stu():
    if  (checkiflogged()):
        data_to_flash = {
        'message': 'You are already logged in',
        'role': 'user_action' 
        }
        flash(json.dumps(data_to_flash), 'info')
        return redirect('/')
    return render_template("log-stu.html")

@auth_bp.route('/login-stu', methods=['POST'])
def login_stu_post():
    # 1. Get form data
    name = request.form.get('name')
    password = request.form.get('password')

    # 2. Find student in the database
    user_query = Student.getByname(name)

    # 3. (SECURITY FIX) Validate user and password securely
    # This now checks for both failure cases and gives one generic error.
    # The password check should be replaced with a hash check in the future.
    if not user_query or user_query.password != password:
        error_data = {
            'message': 'Invalid credentials provided.',
            'role': 'security'
        }
        flash(json.dumps(error_data), 'danger')
        # Redirect back to the student login page to show the error
        return redirect('/login-stu') 

    # 4. (SUCCESS) Set session variables correctly
    session.permanent = True
    
    # -- Using your original session names with corrected logic --
    # Store the name from the database, not the form, for consistency
    session['name'] = True
    session['id'] = user_query.id
    session['role'] = 'Student'
    # Store the name (which is the email/BN) under the 'email' key as intended
    session['email'] = user_query.id

    # The buggy if/else block has been completely removed.
    # --------------------------------------------------------

    # 5. Flash success message and redirect to the homepage
    success_data = {
        'message': f'Welcome, {user_query.name}!',
        'role': 'user_action'
    }
    flash(json.dumps(success_data), 'success')
    return redirect('/')





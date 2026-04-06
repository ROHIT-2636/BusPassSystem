from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import pymysql
import pymysql.cursors
import re
import os
import random
import string
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static')

# ---------- JINJA2 GLOBALS ----------
app.jinja_env.globals.update(now=datetime.now)

# ---------- SECRET KEY (ONLY ONCE) ----------
app.secret_key = 'bus_pass_secret_key_2024'

# ---------- FILE UPLOAD CONFIG ----------
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'pdf'}

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ---------- DATABASE CONFIG ----------
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '384834',
    'database': 'bus_pass_system',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**db_config)

# ---------- GENERATE UNIQUE PASS ID ----------
def generate_pass_id():
    return 'BP' + ''.join(random.choices(string.digits, k=8))

# ---------- STUDENT ROUTES ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        dob = request.form['dob']           
        register_no = request.form['register_no']
        password = request.form['password']
        college = request.form['college']
        course = request.form['course']
        year = request.form['year']
        phone = request.form['phone']
        address = request.form['address']
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                sql = '''INSERT INTO students 
                        (name, email, dob, register_no, password, college, course, year, phone, address) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                cursor.execute(sql, (name, email, dob, register_no, password, college, course, year, phone, address))
                connection.commit()
                flash('Registration successful! Please login.', 'success')
        except Exception as e:
            print(f"Signup error: {e}")
            flash('Registration failed! Email or Register No already exists.', 'danger')
            connection.rollback()
        finally:
            connection.close()
        
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM students WHERE email = %s AND password = %s', (email, password))
                student = cursor.fetchone()
        finally:
            connection.close()
        
        if student:
            session['loggedin'] = True
            session['student_id'] = student['id']
            session['name'] = student['name']
            session['email'] = student['email']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')
@app.route('/guidelines')
def guidelines():
    return render_template('guidelines.html')

@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM students WHERE id = %s', (session['student_id'],))
                student = cursor.fetchone()
                
                cursor.execute('SELECT * FROM pass_applications WHERE student_id = %s ORDER BY applied_date DESC', 
                             (session['student_id'],))
                passes = cursor.fetchall()
        finally:
            connection.close()
        
        return render_template('dashboard.html', student=student, passes=passes)
    return redirect(url_for('login'))

@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if 'loggedin' in session:
        return render_template('apply.html')
    return redirect(url_for('login'))

@app.route('/payment/<int:application_id>')
def payment(application_id):
    if 'loggedin' in session:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM pass_applications WHERE id = %s AND student_id = %s', 
                             (application_id, session['student_id']))
                application = cursor.fetchone()
        finally:
            connection.close()
        
        if application:
            return render_template('payment.html', application=application)
    return redirect(url_for('login'))

@app.route('/payment_success/<int:application_id>')
def payment_success(application_id):
    if 'loggedin' in session:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('UPDATE pass_applications SET payment_status = "paid" WHERE id = %s', 
                             (application_id,))
                connection.commit()
                
                cursor.execute('SELECT * FROM pass_applications WHERE id = %s', (application_id,))
                application = cursor.fetchone()
        finally:
            connection.close()
        
        return render_template('receipt.html', application=application)
    return redirect(url_for('login'))

@app.route('/submit_application', methods=['POST'])
def submit_application():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    print("="*50)
    print("SUBMIT APPLICATION CALLED")
    print("="*50)
    
    try:
        # Form data
        travel_from = request.form['travel_from']
        travel_to = request.form['travel_to']
        pass_type = request.form['pass_type']
        duration = request.form['duration']
        address_proof_type = request.form.get('address_proof_type', '')
        
        # Fee calculation
        if duration == '1 Month':
            fees = 500
        elif duration == '3 Months':
            fees = 1500
        else:
            fees = 3000
            
        unique_pass_id = generate_pass_id()
        
        # Handle file uploads
        college_id_file = None
        student_photo_file = None
        address_proof_file = None
        previous_pass_file = None
        
        # Bonafide Certificate upload (NEW)
        if 'bonafide' in request.files:
            file = request.files['bonafide']
            print(f"Bonafide file: {file.filename}")
            if file and file.filename:
                if allowed_file(file.filename):
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = secure_filename(f"bonafide_{session['student_id']}_{timestamp}_{file.filename}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    bonafide_file = filename
                    print(f"✅ Bonafide saved: {file_path}")
        # College ID upload
        if 'college_id' in request.files:
            file = request.files['college_id']
            if file and file.filename:
                if allowed_file(file.filename):
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = secure_filename(f"college_id_{session['student_id']}_{timestamp}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    college_id_file = filename
        
        # Student photo upload
        if 'student_photo' in request.files:
            file = request.files['student_photo']
            if file and file.filename:
                if allowed_file(file.filename):
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = secure_filename(f"photo_{session['student_id']}_{timestamp}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    student_photo_file = filename
        
        # Address proof upload
        if 'address_proof' in request.files:
            file = request.files['address_proof']
            if file and file.filename:
                if allowed_file(file.filename):
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = secure_filename(f"address_{session['student_id']}_{timestamp}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    address_proof_file = filename
        
        # Previous pass upload (optional)
        if 'previous_pass' in request.files:
            file = request.files['previous_pass']
            if file and file.filename:
                if allowed_file(file.filename):
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = secure_filename(f"previous_{session['student_id']}_{timestamp}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    previous_pass_file = filename
        
        # Save to database
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                sql = '''INSERT INTO pass_applications 
                        (student_id, unique_pass_id, travel_from, travel_to, pass_type, 
                         duration, fees, college_id_file, student_photo_file, 
                         address_proof_type, address_proof_file, previous_pass_file, bonafide_file,
                         application_status, payment_status) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                cursor.execute(sql, (
                    session['student_id'], unique_pass_id, travel_from, travel_to, 
                    pass_type, duration, fees +50 ,
                    college_id_file, student_photo_file,
                    address_proof_type, address_proof_file, previous_pass_file, bonafide_file,
                    'pending', 'pending'
                ))
                connection.commit()
                application_id = cursor.lastrowid
        except Exception as e:
            print(f"Database error: {e}")
            connection.rollback()
            raise e
        finally:
            connection.close()
        
        return redirect(url_for('payment', application_id=application_id))
    
    except Exception as e:
        print(f"Error in submit_application: {e}")
        import traceback
        traceback.print_exc()
        return "Error processing application. Check console for details.", 500

# ---------- STUDENT PROFILE EDIT ----------
# ---------- STUDENT PROFILE EDIT WITH PHOTO ----------
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    try:
        if request.method == 'POST':
            # Form data
            name = request.form['name']
            email = request.form['email']
            dob = request.form['dob']
            phone = request.form['phone']
            address = request.form['address']
            college = request.form['college']
            course = request.form['course']
            year = request.form['year']
            existing_photo = request.form.get('existing_photo', '')
            
            # Handle photo upload
            student_photo_file = existing_photo  # Default to existing photo
            
            if 'student_photo' in request.files:
                file = request.files['student_photo']
                if file and file.filename and allowed_file(file.filename):
                    # Delete old photo if exists
                    if existing_photo:
                        old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], existing_photo)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    
                    # Save new photo
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = secure_filename(f"profile_{session['student_id']}_{timestamp}_{file.filename}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    student_photo_file = filename
            
            # Database update
            with connection.cursor() as cursor:
                sql = '''UPDATE students 
                        SET name = %s, email = %s, dob = %s, phone = %s, address = %s,
                            college = %s, course = %s, year = %s, student_photo_file = %s
                        WHERE id = %s'''
                cursor.execute(sql, (name, email, dob, phone, address, college, course, year, student_photo_file, session['student_id']))
                connection.commit()
                
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        
        # GET request - fetch student data including photo
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM students WHERE id = %s', (session['student_id'],))
            student = cursor.fetchone()
            
    except Exception as e:
        print(f"Edit profile error: {e}")
        flash('Error updating profile!', 'danger')
        student = None
    finally:
        connection.close()
    
    return render_template('edit_profile.html', student=student)

@app.route('/check_status/<int:pass_id>')
def check_status(pass_id):
    if 'loggedin' in session:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT 
                        pa.*, 
                        s.name, 
                        s.dob,
                        s.register_no, 
                        s.college, 
                        s.course, 
                        s.year,
                        pa.student_photo_file,
                        pa.approved_date
                    FROM pass_applications pa
                    JOIN students s ON pa.student_id = s.id
                    WHERE pa.id = %s AND pa.student_id = %s
                ''', (pass_id, session['student_id']))
                pass_app = cursor.fetchone()
        finally:
            connection.close()
        
        if pass_app and pass_app['application_status'] == 'approved':
            if not pass_app.get('approved_date'):
                pass_app['approved_date'] = datetime.now()
            return render_template('download_pass.html', pass_app=pass_app)
        else:
            return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ---------- ADMIN ROUTES ----------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == 'admin123':
            session['admin_loggedin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_loggedin' in session:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # All applications with student details
                cursor.execute('''
                    SELECT pa.*, s.name, s.register_no, s.college 
                    FROM pass_applications pa 
                    JOIN students s ON pa.student_id = s.id 
                    ORDER BY pa.applied_date DESC
                ''')
                applications = cursor.fetchall()

                # Count statistics
                cursor.execute('SELECT COUNT(*) as total FROM pass_applications')
                total_applications = cursor.fetchone()['total']

                cursor.execute('SELECT COUNT(*) as approved FROM pass_applications WHERE application_status = "approved"')
                approved_count = cursor.fetchone()['approved']

                cursor.execute('SELECT COUNT(*) as pending FROM pass_applications WHERE application_status = "pending"')
                pending_count = cursor.fetchone()['pending']

                cursor.execute('SELECT COUNT(*) as rejected FROM pass_applications WHERE application_status = "rejected"')
                rejected_count = cursor.fetchone()['rejected']

                cursor.execute('SELECT COUNT(*) as paid FROM pass_applications WHERE payment_status = "paid"')
                paid_count = cursor.fetchone()['paid']

                cursor.execute('SELECT COUNT(*) as pending_payment FROM pass_applications WHERE payment_status = "pending"')
                pending_payment_count = cursor.fetchone()['pending_payment']

                cursor.execute('SELECT COUNT(*) as today FROM pass_applications WHERE DATE(applied_date) = CURDATE()')
                today_applications = cursor.fetchone()['today']

                cursor.execute('SELECT COUNT(*) as total FROM students')
                total_students = cursor.fetchone()['total']

        except Exception as e:
            print(f"Admin dashboard error: {e}")
            applications = []
            total_applications = approved_count = pending_count = rejected_count = paid_count = pending_payment_count = today_applications = total_students = 0
        finally:
            connection.close()

        return render_template('admin_dashboard.html',
                               applications=applications,
                               total_applications=total_applications,
                               approved_count=approved_count,
                               pending_count=pending_count,
                               rejected_count=rejected_count,
                               paid_count=paid_count,
                               pending_payment_count=pending_payment_count,
                               today_applications=today_applications,
                               total_students=total_students)
    return redirect(url_for('admin_login'))

# ---------- 🔥 FIXED: UPDATE STATUS ROUTE (REJECT 100% WORKING) ----------

@app.route('/admin/update_status/<int:app_id>/<status>')
def update_status(app_id, status):
    if 'admin_loggedin' in session:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('''
                    UPDATE pass_applications 
                    SET application_status = %s
                    WHERE id = %s
                ''', (status, app_id))
                connection.commit()
        finally:
            connection.close()
        
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

# ---------- ADMIN DELETE STUDENT ----------
@app.route('/admin/delete_student/<int:student_id>', methods=['POST'])
def admin_delete_student(student_id):
    if 'admin_loggedin' not in session:
        return redirect(url_for('admin_login'))
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM pass_applications WHERE student_id = %s', (student_id,))
            cursor.execute('DELETE FROM students WHERE id = %s', (student_id,))
            connection.commit()
            flash(f'Student ID {student_id} and all details deleted.', 'success')
    except Exception as e: 
        print(f"Delete error: {e}")
        flash('Error deleting student.', 'danger')
        connection.rollback()
    finally:
        connection.close()
    
    return redirect(url_for('admin_all_students'))

# ---------- ADMIN ALL STUDENTS ----------
@app.route('/admin/all_students')
def admin_all_students():
    if 'admin_loggedin' in session:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT 
                        s.*,
                        COUNT(pa.id) as total_applications,
                        SUM(CASE WHEN pa.application_status = 'approved' THEN 1 ELSE 0 END) as approved_applications,
                        SUM(CASE WHEN pa.application_status = 'pending' THEN 1 ELSE 0 END) as pending_applications,
                        MAX(pa.applied_date) as last_application_date
                    FROM students s
                    LEFT JOIN pass_applications pa ON s.id = pa.student_id
                    GROUP BY s.id
                    ORDER BY s.id DESC
                ''')
                students = cursor.fetchall()
                
                cursor.execute('SELECT COUNT(*) as total FROM students')
                total_students = cursor.fetchone()['total']
                
                cursor.execute('SELECT COUNT(DISTINCT student_id) as active FROM pass_applications')
                active_students = cursor.fetchone()['active']
                
        except Exception as e:
            print(f"Error in admin_all_students: {e}")
            students = []
            total_students = 0
            active_students = 0
        finally:
            connection.close()
        
        return render_template('admin_all_students.html', 
                             students=students, 
                             total_students=total_students,
                             active_students=active_students)
    return redirect(url_for('admin_login'))

# ---------- ADMIN PENDING APPLICATIONS ----------
@app.route('/admin/applications_remains')
def admin_applications_remains():
    if 'admin_loggedin' in session:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT 
                        pa.*,
                        s.name, 
                        s.register_no, 
                        s.college, 
                        s.course, 
                        s.year, 
                        s.email, 
                        s.phone, 
                        s.address
                    FROM pass_applications pa
                    JOIN students s ON pa.student_id = s.id
                    WHERE pa.application_status = 'pending'
                    AND pa.payment_status = 'paid'
                    ORDER BY pa.applied_date ASC
                ''')
                pending_applications = cursor.fetchall()
                
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_pending,
                        COUNT(DISTINCT student_id) as unique_students,
                        SUM(CASE WHEN DATE(pa.applied_date) = CURDATE() THEN 1 ELSE 0 END) as today_applications
                    FROM pass_applications pa
                    WHERE pa.application_status = 'pending'
                    AND pa.payment_status = 'paid'
                ''')
                stats = cursor.fetchone()
                
                for app in pending_applications:
                    app['documents_verified'] = all([
                        app.get('college_id_file'),
                        app.get('student_photo_file'),
                        app.get('address_proof_file')
                    ])
                
        except Exception as e:
            print(f"Error in admin_applications_remains: {e}")
            pending_applications = []
            stats = {'total_pending': 0, 'unique_students': 0, 'today_applications': 0}
        finally:
            connection.close()
        
        return render_template('admin_applications_remains.html', 
                             applications=pending_applications,
                             stats=stats)
    return redirect(url_for('admin_login'))

# ---------- ADMIN STUDENT DETAILS ----------
@app.route('/admin/student_details/<int:student_id>')
def admin_student_details(student_id):
    if 'admin_loggedin' in session:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM students WHERE id = %s', (student_id,))
                student = cursor.fetchone()
                
                cursor.execute('''
                    SELECT * FROM pass_applications 
                    WHERE student_id = %s 
                    ORDER BY applied_date DESC
                ''', (student_id,))
                applications = cursor.fetchall()
                
        finally:
            connection.close()
        
        if student:
            return render_template('admin_student_details.html', 
                                 student=student, 
                                 applications=applications)
        else:
            return redirect(url_for('admin_all_students'))
    
    return redirect(url_for('admin_login'))

# ---------- ADMIN VIEW APPLICATION ----------
@app.route('/admin/view_application/<int:app_id>')
def view_application(app_id):
    if 'admin_loggedin' in session:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT pa.*, s.name,  s.dob, s.register_no, s.college, s.course, 
                           s.year, s.email, s.phone, s.address
                    FROM pass_applications pa 
                    JOIN students s ON pa.student_id = s.id 
                    WHERE pa.id = %s
                ''', (app_id,))
                application = cursor.fetchone()
                
        finally:
            connection.close()
        
        if application:
            return render_template('view_application.html', app=application)
        else:
            return redirect(url_for('admin_dashboard'))
    
    return redirect(url_for('admin_login'))

# ---------- ADMIN SETTINGS ----------
@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if 'admin_loggedin' not in session:
        return redirect(url_for('admin_login'))
    
    connection = get_db_connection()
    try:
        if request.method == 'POST':
            for key, value in request.form.items():
                if key.startswith('setting_'):
                    setting_key = key.replace('setting_', '')
                    with connection.cursor() as cursor:
                        cursor.execute('''
                            UPDATE settings 
                            SET setting_value = %s 
                            WHERE setting_key = %s
                        ''', (value, setting_key))
                    connection.commit()
            
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('admin_settings'))
        
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM settings ORDER BY setting_key')
            settings_rows = cursor.fetchall()
            
        settings = {}
        for row in settings_rows:
            if '_' in row['setting_key']:
                category = row['setting_key'].split('_')[0]
            else:
                category = 'general'
            
            if category not in settings:
                settings[category] = []
            settings[category].append(row)
        
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) as total FROM students')
            total_students = cursor.fetchone()['total']
            cursor.execute('SELECT COUNT(*) as total FROM pass_applications')
            total_applications = cursor.fetchone()['total']
            cursor.execute('SELECT COUNT(*) as total FROM pass_applications WHERE application_status = "pending"')
            pending_applications = cursor.fetchone()['total']
            
    except Exception as e:
        print(f"Settings error: {e}")
        flash(f'Error: {str(e)}', 'danger')
        settings = {}
        total_students = total_applications = pending_applications = 0
    finally:
        connection.close()
    
    return render_template('admin_settings.html',
                         settings=settings,
                         total_students=total_students,
                         total_applications=total_applications,
                         pending_applications=pending_applications)

@app.route('/admin/settings/reset', methods=['POST'])
def admin_settings_reset():
    if 'admin_loggedin' not in session:
        return redirect(url_for('admin_login'))
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM settings')
            reset_default_settings(cursor)
            connection.commit()
        flash('Settings reset to defaults!', 'success')
    except Exception as e:
        flash(f'Reset failed: {str(e)}', 'danger')
    finally:
        connection.close()
    
    return redirect(url_for('admin_settings'))

def reset_default_settings(cursor):
    defaults = [
        ('system_name', 'Bus Pass Management System', 'text'),
        ('system_email', 'admin@buspass.com', 'email'),
        ('system_phone', '+91 1234567890', 'text'),
        ('system_address', 'College Campus, City', 'textarea'),
        ('processing_fee', '50', 'number'),
        ('pass_regular_1month', '500', 'number'),
        ('pass_regular_3months', '1500', 'number'),
        ('pass_regular_6months', '3000', 'number'),
        ('pass_premium_1month', '800', 'number'),
        ('pass_premium_3months', '2300', 'number'),
        ('pass_premium_6months', '4500', 'number'),
        ('pass_express_1month', '600', 'number'),
        ('pass_express_3months', '1750', 'number'),
        ('pass_express_6months', '3400', 'number'),
        ('max_file_size', '2', 'number'),
        ('allowed_extensions', 'jpg,jpeg,png,pdf', 'text'),
        ('require_previous_pass', '0', 'boolean'),
        ('enable_email_notifications', '1', 'boolean'),
        ('enable_sms_notifications', '0', 'boolean'),
        ('smtp_host', '', 'text'),
        ('smtp_port', '587', 'number'),
        ('smtp_user', '', 'text'),
        ('smtp_password', '', 'password'),
        ('auto_approve', '0', 'boolean'),
        ('require_verification', '1', 'boolean'),
        ('student_can_edit', '0', 'boolean'),
        ('max_applications_per_day', '3', 'number'),
        ('items_per_page', '10', 'number'),
        ('theme_color', 'primary', 'select'),
        ('date_format', 'd/m/Y', 'text'),
    ]
    for key, value, typ in defaults:
        cursor.execute(
            'INSERT INTO settings (setting_key, setting_value, setting_type) VALUES (%s, %s, %s)',
            (key, value, typ)
        )

@app.route('/admin/settings/cache/clear', methods=['POST'])
def admin_settings_clear_cache():
    if 'admin_loggedin' in session:
        flash('Cache cleared successfully!', 'success')
    return redirect(url_for('admin_settings'))

# ---------- MAIN ----------
if __name__ == '__main__':
    app.run(debug=True)
    
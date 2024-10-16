from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from flask_mysqldb import MySQL
from flask import flash
from flask import session
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import logging
from flask import current_app
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from flask import jsonify
import json
import mysql.connector
import random
import string


app = Flask(__name__)
app.secret_key = 'Roshan@1705'


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Roshan@1705'
app.config['MYSQL_DB'] = 'daycare'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'nrkr1708@gmail.com'
app.config['MAIL_PASSWORD'] = 'rjzp qvgl uqfk oajz'
app.config['MAIL_DEFAULT_SENDER'] = 'nrkr1708@gmail.com'

mysql = MySQL(app)
mail=Mail(app)

scheduler = BackgroundScheduler()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  

        
        query = "SELECT * FROM users WHERE username = %s AND password = %s AND role = %s"
        cur = mysql.connection.cursor()
        cur.execute(query, (username, password, role))
        user = cur.fetchone()

        if user:
            session['username'] = username
            session['role'] = user[3] 
            
            
            if user[3] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user[3] == 'parent':
                return redirect(url_for('parent_dashboard'))
        else:
            return 'Invalid username, password, or role', 400
            
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        child_id = request.form['child_id']
        
        cur = mysql.connection.cursor()
        query = "SELECT parent_email FROM child WHERE child_id = %s"
        cur.execute(query, (child_id,))
        result = cur.fetchone()
        parent_email = result[0] if result else None

        if parent_email:
           
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            
            
            msg = Message("Password Reset for Day Care Management", recipients=[parent_email])
            msg.body = f"Your temporary password is: {temp_password}\nPlease log in and change your password."
            mail.send(msg)
            update_query = "UPDATE users SET password = %s WHERE username = %s"
            cur.execute(update_query, (temp_password, parent_email))
            mysql.connection.commit()  

            flash("Password reset email sent. Please check your inbox.", "success")
            return redirect(url_for('login'))
        else:
            flash("Invalid child ID or parent email not found.", "danger")
            return redirect(url_for('forgot_password'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT child_id, name FROM child")
    children = cur.fetchall()
    return render_template('forgot_password.html', children=children)

@app.route('/reset_password', methods=['POST'])
def reset_password():
    username = request.form['username']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if new_password == confirm_password:
        cur = mysql.connection.cursor()
        query = "UPDATE users SET password = %s WHERE username = %s"
        cur.execute(query, (new_password, username))
        mysql.connection.commit()
        
        if cur.rowcount > 0: 
            flash("Your password has been updated successfully. Please log in with your new password.", "success")
        else:
            flash("Username not found. Please try again.", "danger")
        
        return redirect(url_for('login'))
    else:
        flash("Passwords do not match. Please try again.", "danger")
        return redirect(url_for('forgot_password'))  



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
        mysql.connection.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard/<role>')
def dashboard(role):
    if role == 'parent':
        return render_template('parent_dashboard.html')
    elif role == 'admin':
        return render_template('admin_dashboard.html')
    else:
        return redirect(url_for('login'))
    
@app.route('/parent_dashboard', endpoint='parent_dashboard')
def parent_dashboard():
    if session.get('role') == 'parent':
        return render_template('parent_dashboard.html')
    else:
        return 'Access denied', 400
    
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') == 'admin':
        return render_template('admin_dashboard.html')
    else:
        return 'Access denied', 400
    
@app.route('/fee_summary')
def fee_summary():
    return render_template('fee_summary.html')

@app.route('/add_child', methods=['GET', 'POST'])
def add_child():
    if session.get('role') in ['admin']:
        if request.method == 'POST':
            child_id = request.form['child_id']
            child_name = request.form['child_name']
            child_dob = request.form['child_dob']
            child_age = request.form['child_age']
            parent_contact = request.form['parent_contact']
            parent_email = request.form['parent_email']
            registration_date = request.form['registration_date']
        
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM child WHERE child_id = %s", (child_id,))
            existing_child = cur.fetchone()
        
            if existing_child:
                flash("Child ID already exists. Please use a different ID.")
                return redirect(url_for('add_child'))
        
            cur.execute("INSERT INTO child (child_id, name, dob, age, parent_contact_number, parent_email, registration_date) VALUES (%s, %s, %s, %s, %s, %s, %s)", (child_id, child_name, child_dob, child_age, parent_contact, parent_email, registration_date))
            mysql.connection.commit()
            flash("Child added successfully!")
            return redirect(url_for('child_details'))
        return render_template('add_child.html')
    else:
        return 'Access denied', 400

@app.route('/child_details')
def child_details():
    if session.get('role') in ['parent','admin']:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM child")
        children = cur.fetchall()
        return render_template('child_details.html', children=children)
    else:
        return 'Access denied', 400
    
@app.route('/edit_child/<int:child_id>', methods=['GET', 'POST'])
def edit_child(child_id):
    if session.get('role') in ['admin']:
        if request.method == 'POST':
            name = request.form['name']
            dob = request.form['dob']
            age = request.form['age']
            parent_contact_number = request.form['parent_contact_number']
            parent_email = request.form['parent_email']

            cur = mysql.connection.cursor()
            cur.execute("UPDATE child SET name=%s, dob=%s, age=%s, parent_contact_number=%s, parent_email=%s WHERE child_id=%s",
                        (name, dob, age, parent_contact_number, parent_email, child_id))
            mysql.connection.commit()
            flash('Child data has been successfully edited.', 'success')
            return redirect(url_for('child_details'))
        else:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM child WHERE child_id=%s", (child_id,))
            child = cur.fetchone()
            return render_template('edit_child.html', child=child)
    else:
        return 'Access denied', 400


@app.route('/delete_child/<int:child_id>')
def delete_child(child_id):
    if session.get('role') in ['admin']:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM child WHERE child_id=%s", (child_id,))
        mysql.connection.commit()
        flash('Child data has been successfully deleted.', 'success')
        return redirect(url_for('child_details'))
    else:
        return 'Access denied', 400

@app.route('/track_status', methods=['GET', 'POST'])
def track_status():
    if session.get('role') in ['admin']:
        if request.method == 'POST':
            child_id = request.form.get('child_id')
            babysitter_id = request.form.get('babysitter_id')
            current_datee = request.form.get('current_datee')
            in_time = request.form.get('in_time')
            out_time = request.form.get('out_time')
            total_hours = request.form.get('total_hours')
            fees_to_be_paid = request.form.get('fees_to_be_paid')
            fee_status = request.form.get('fee_status')
            attendance = request.form.get('attendance')
        
            # Insert data into the database
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO status (child_id, babysitter_id, current_datee, in_time, out_time, total_hours, fees_to_be_paid, fee_status, attendance) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                        (child_id, babysitter_id, current_datee, in_time, out_time, total_hours, fees_to_be_paid, fee_status, attendance))
            mysql.connection.commit()
            flash('Child data has been successfully added.', 'success')
            return redirect(url_for('status'))
        return render_template('add_status.html')
    else:
        return 'Access denied', 400

@app.route('/status')
def status():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM status")
    status = cur.fetchall()
    return render_template('track_status.html', status=status)


@app.route('/analytics')
def analytics():
    try:
        cur = mysql.connection.cursor()
        query = """
            SELECT child_id, SUM(total_hours) AS total_hours, current_datee, attendance
            FROM status
            GROUP BY child_id, current_datee, attendance
            ORDER BY current_datee;
        """
        cur.execute(query)
        data = cur.fetchall()
        attendanceData = []

        for row in data:
            attendanceData.append({
                'childId': row[0],
                'totalHours': row[1],
                'currentDate': row[2].strftime("%Y-%m-%d"),
                'attendance': row[3]
            })

        cur.close()

        return render_template('analytics.html', attendanceData=attendanceData)
    except Exception as e:
        print(f"Error fetching analytics data: {e}")
        return "An error occurred while fetching analytics data", 500
    
@app.route('/edit_status/<int:id>', methods=['GET', 'POST'])
def edit_status(id):
    if session.get('role') != 'admin':
        return 'Access Denied', 403
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM status WHERE status_id = %s", (id,))
    status = cur.fetchone()

    if request.method == 'POST':
        child_id = request.form.get('child_id')
        babysitter_id = request.form.get('babysitter_id')
        current_datee = request.form.get('current_datee')
        in_time = request.form.get('in_time')
        out_time = request.form.get('out_time')
        total_hours = request.form.get('total_hours')
        fees_to_be_paid = request.form.get('fees_to_be_paid')
        fee_status = request.form.get('fee_status')
        attendance = request.form.get('attendance')
        
        # Update status in database
        cur.execute("""
            UPDATE status SET child_id=%s, babysitter_id=%s, current_datee=%s, in_time=%s, out_time=%s, total_hours=%s, fees_to_be_paid=%s, fee_status=%s, attendance=%s
            WHERE status_id=%s
        """, (child_id, babysitter_id, current_datee, in_time, out_time, total_hours, fees_to_be_paid, fee_status, attendance, id))
        mysql.connection.commit()
        flash('Status has been successfully edited.', 'success')
        return redirect(url_for('status'))
    
    return render_template('edit_status.html', status=status)

@app.route('/delete_status/<int:id>', methods=['POST'])
def delete_status(id):
    if session.get('role') in ['admin']:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM status WHERE status_id = %s", (id,))
        mysql.connection.commit()
        cur.close()
    
        flash('Status has been successfully deleted.', 'success')
        return redirect(url_for('status'))
    else:
        return 'Access denied', 400

@app.route('/delete_status/<int:id>')
def confirm_delete(id):
    if session.get('role') in ['admin']:
        return render_template('delete_status.html', status_id=id)
    else:
        return 'Access denied', 400


@app.route('/babysitter_details')
def babysitter_details():
    if session.get('role') in ['parent', 'admin']:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM baby_sitter")
        babysitters = cur.fetchall()
        return render_template('babysitter_details.html', babysitters=babysitters)
    else:
        return 'Access denied', 400

@app.route('/add_babysitter', methods=['GET', 'POST'])
def add_babysitter():
    if session.get('role') in ['admin']:
        if request.method == 'POST':
            babysitter_id = request.form['babysitter_id']
            name = request.form['name']
            contact_number = request.form['contact_number']
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM baby_sitter WHERE babysitter_id = %s", (babysitter_id,))
            existing_babysitter = cur.fetchone()
        
            if existing_babysitter:
                flash("Babysitter ID already exists. Please use a different ID.")
                return redirect(url_for('add_babysitter'))
        
            cur.execute("INSERT INTO baby_sitter (babysitter_id, name, contact_number) VALUES (%s, %s, %s)", (babysitter_id, name, contact_number))
            mysql.connection.commit()
            flash("Babysitter added successfully!")
            return redirect(url_for('babysitter_details'))
        return render_template('add_babysitter.html')
    else:
        return 'Access denied', 400

@app.route('/edit_babysitter/<int:babysitter_id>', methods=['GET', 'POST'])
def edit_babysitter(babysitter_id):
    if session.get('role') != 'admin':
        return 'Access Denied', 403

    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name') 
        contact_number = request.form.get('contact_number')
        
    
        print(f"Form Data - Name: {name}, Contact: {contact_number}")

        # Update query
        cur.execute("UPDATE baby_sitter SET name = %s, contact_number = %s WHERE babysitter_id = %s", 
                    (name, contact_number, babysitter_id))
        mysql.connection.commit()

        flash("Babysitter details updated successfully!")
        return redirect(url_for('babysitter_details'))
    
    cur.execute("SELECT * FROM baby_sitter WHERE babysitter_id = %s", (babysitter_id,))
    babysitter = cur.fetchone()

    # Debugging
    print(f"Fetched Babysitter Data: {babysitter}")
    
    return render_template('edit_babysitter.html', babysitter=babysitter)


@app.route('/delete_babysitter/<int:babysitter_id>', methods=['POST'])
def delete_babysitter(babysitter_id):
    try:
        if session.get('role') == 'admin':
            cursor = mysql.connection.cursor()
            cursor.execute("DELETE FROM baby_sitter WHERE babysitter_id = %s", (babysitter_id,))
            mysql.connection.commit()
            cursor.close()
            return jsonify({"success": True, "message": "Babysitter deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Unauthorized access"})
    except Exception as e:
        print(f"Error deleting babysitter: {str(e)}")  # Log the error
        return jsonify({"success": False, "message": "An error occurred"})
    
def send_weekly_fees_email():
    with app.app_context():
        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM child")
        children = cur.fetchall()

        # Calculate total fees for each child for the past week and send email
        for child in children:
            child_id = child[0]
            parent_email = child[5]
            # Calculate the total fees for the past week
            start_date = datetime.now() - timedelta(days=7)
            cur.execute("SELECT SUM(fees_to_be_paid) FROM status WHERE child_id=%s AND current_datee >= %s", (child_id, start_date))
            total_fees = cur.fetchone()[0]

            # Send the email
            if total_fees is not None:
                msg = Message("Weekly Fees Summary",
                              sender='nrkr1708@gmail.com',
                              recipients=[parent_email])
                msg.body = f"Dear Parent, \nYour total daycare fees for the last week for your child {child[1]} is ${total_fees}. Please make the payment by scanning the attached UPI QR code or by logging in to the parent dashboard to track the status of your child."

                # Attach the QR code image
                with open('static/upi_qr_code.png', 'rb') as f:
                    msg.attach('upi_qr_code.png', 'image/png', f.read())

                try:
                    mail.send(msg)
                    print(f"Email sent successfully to {parent_email}")
                except Exception as e:
                    print(f"Error sending email to {parent_email}: {e}")

                print(f"Email sent successfully to {parent_email}")

scheduler = BackgroundScheduler()
scheduler.add_job(send_weekly_fees_email, 'cron', day_of_week='wed', hour=17,minute=39)
scheduler.start()


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
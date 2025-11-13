from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"


#  Initialize database (only create DB file if missing)
def init_db():
    if not os.path.exists("users.db"):
        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        surname TEXT,
                        email TEXT,
                        address TEXT,
                        username TEXT UNIQUE,
                        password TEXT,
                        user_type TEXT CHECK(user_type IN ('Patient', 'Doctor')) NOT NULL
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS doctors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        fullname TEXT,
                        password TEXT,
                        department TEXT,
                        experience TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS patients (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        age INTEGER,
                        gender TEXT,
                        department TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS appointments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_name TEXT,
                        doctor_name TEXT,
                        date TEXT,
                        time TEXT,
                        department TEXT
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS patient_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_name TEXT,
                        doctor_name TEXT,
                        visit_type TEXT,
                        test_done TEXT,
                        diagnosis TEXT,
                        prescription TEXT,
                        medicines TEXT,
                        created_at TEXT
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS doctor_availability (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        doctor_name TEXT,
                        date TEXT,
                        morning_slot TEXT,
                        evening_slot TEXT
                    )''')

        conn.commit()
        conn.close()
        print("Database initialized successfully.")


init_db()


# ---------------- Helper DB functions ----------------
def query_db(query, args=(), one=False):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(query, args)
    rv = c.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=()):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(query, args)
    conn.commit()
    lastrowid = c.lastrowid
    conn.close()
    return lastrowid


# ---------------- Authentication helpers ----------------
def check_login(username, password, user_type):
    # admin backdoor retained
    if username == "keha" and password == "keha" and user_type.lower() == "admin":
        return ("admin", "keha", "Admin")

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=? AND user_type=?", (username, password, user_type))
    user = c.fetchone()
    conn.close()
    return user


def user_exists(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user


def register_user(data):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (name, surname, email, address, username, password, user_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()


# ---------------- Public routes ----------------
@app.route('/')
def home():
    return render_template('index.html', current_year=datetime.now().year)


@app.route('/login', methods=['GET', 'POST'])
def login():
    user_type = request.args.get('user_type', 'User').capitalize()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = check_login(username, password, user_type)

        if user:
            flash(f"Welcome {user_type} {username}!", "success")
            if user_type.lower() == "admin":
                return redirect(url_for('admin_dashboard'))
            if user_type.lower() == "doctor":
                return redirect(url_for('doctor_dashboard', doctor_name=username))
            # patient
            return redirect(url_for('patient_dashboard', patient_username=username))
        else:
            flash("Invalid credentials. Please try again.", "danger")

    return render_template('login.html', user_type=user_type)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        address = request.form['address']
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']

        if user_exists(username):
            flash("Username already exists! Please choose another.", "danger")
        else:
            register_user((name, surname, email, address, username, password, user_type))
            flash("Registration successful! Please login now.", "success")
            return redirect(url_for('login', user_type=user_type))

    return render_template('register.html')


# ---------------- Admin (retained) ----------------
@app.route('/admin')
def admin_dashboard():
    search_query = request.args.get('search', '').strip().lower()

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    if search_query:
        c.execute("SELECT * FROM doctors WHERE LOWER(fullname) LIKE ? OR LOWER(department) LIKE ?",
                  (f"%{search_query}%", f"%{search_query}%"))
    else:
        c.execute("SELECT * FROM doctors")
    doctors = c.fetchall()

    if search_query:
        c.execute("SELECT * FROM patients WHERE LOWER(department) LIKE ?", (f"%{search_query}%",))
    else:
        c.execute("""
        SELECT id, name, surname, email, username 
        FROM users 
        WHERE user_type='Patient'
    """)
    patients = c.fetchall()

    if search_query:
        c.execute("""SELECT * FROM appointments 
                     WHERE LOWER(patient_name) LIKE ? OR LOWER(doctor_name) LIKE ? OR LOWER(department) LIKE ?""",
                  (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
    else:
        c.execute("SELECT * FROM appointments")
    appointments = c.fetchall()

    conn.close()
    return render_template('admin_dashboard.html', doctors=doctors, patients=patients, appointments=appointments, search_query=search_query)


# ---------------- Doctor dashboard ----------------
@app.route('/doctor_dashboard/<doctor_name>')
def doctor_dashboard(doctor_name):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("SELECT id, patient_name, date, time, department FROM appointments WHERE doctor_name=?", (doctor_name,))
    appointments = c.fetchall()

    c.execute("SELECT DISTINCT patient_name FROM appointments WHERE doctor_name=?", (doctor_name,))
    assigned_patients = [row[0] for row in c.fetchall()]

    conn.close()
    return render_template('doctor_dashboard.html', doctor_name=doctor_name, appointments=appointments, assigned_patients=assigned_patients)


# ---------------- Patient Dashboard (new) ----------------
@app.route('/patient_dashboard/<patient_username>')
def patient_dashboard(patient_username):

    # -------- Fetch patient user information --------
    user = query_db("""
        SELECT name, surname, username, email, address, password
        FROM users 
        WHERE username=? AND user_type='Patient'
    """, (patient_username,), one=True)

    if not user:
        display_name = patient_username
        user_data = ("", "", "", "", "")
    else:
        name, surname, username, email, address, password = user
        # Prepare display name
        display_name = f"{name} {surname}".strip() or username
        # Data to use in Edit Profile form
        user_data = (name, surname, email, address, password)

    # -------- Fetch upcoming appointments --------
    appointments = query_db("""
        SELECT id, doctor_name, department, date, time 
        FROM appointments 
        WHERE patient_name=? 
        ORDER BY date
    """, (display_name,))

    # -------- Fetch distinct departments --------
    departments = query_db("""
        SELECT DISTINCT department 
        FROM doctors 
        WHERE department IS NOT NULL
    """)

    # -------- Fetch doctors list --------
    doctors = query_db("""
        SELECT id, fullname, department, experience 
        FROM doctors 
        ORDER BY department, fullname
    """)

    # -------- Render template with all data --------
    return render_template(
        'patients_dashboard.html',
        patient_username=patient_username,
        display_name=display_name,
        appointments=appointments,
        departments=[d[0] for d in departments],
        doctors=doctors,
        user_data=user_data
    )
# ---------------- Patient actions: book, cancel, history AJAX ----------------
@app.route('/get_patient_history/<patient_name>')
def get_patient_history(patient_name):
    """
    Return patient history (HTML snippet) — used by AJAX in dashboard
    """
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""SELECT visit_type, test_done, diagnosis, prescription, medicines, created_at, doctor_name
                 FROM patient_history WHERE patient_name=? ORDER BY created_at DESC""", (patient_name,))
    rows = c.fetchall()
    conn.close()

    html = "<div class='p-3'><h5>Patient: {}</h5>".format(patient_name)
    if not rows:
        html += "<p>No history found.</p></div>"
        return html

    html += "<table class='table table-sm table-bordered'><thead><tr><th>#</th><th>Visit Type</th><th>Test Done</th><th>Diagnosis</th><th>Prescription</th><th>Medicines</th><th>Doctor</th><th>When</th></tr></thead><tbody>"
    for i, r in enumerate(rows, start=1):
        visit_type, test_done, diagnosis, prescription, medicines, created_at, doctor_name = r
        html += f"<tr><td>{i}</td><td>{visit_type or ''}</td><td>{test_done or ''}</td><td>{diagnosis or ''}</td><td>{prescription or ''}</td><td>{medicines or ''}</td><td>{doctor_name or ''}</td><td>{created_at or ''}</td></tr>"
    html += "</tbody></table></div>"
    return html


@app.route('/get_doctor_details/<int:doctor_id>')
def get_doctor_details(doctor_id):
    """
    Returns JSON with doctor details to fill modal.
    """
    d = query_db("SELECT id, fullname, department, experience FROM doctors WHERE id=?", (doctor_id,), one=True)
    if not d:
        return jsonify({"error": "Doctor not found"}), 404
    return jsonify({
        "id": d[0],
        "fullname": d[1],
        "department": d[2],
        "experience": d[3] or ""
    })


@app.route('/get_doctor_availability/<doctor_name>')
def get_doctor_availability(doctor_name):
    """
    Returns JSON list of availability rows for doctor_name.
    Shows actual timings entered by doctor.
    """
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT date, morning_slot, evening_slot FROM doctor_availability WHERE doctor_name=? ORDER BY date", (doctor_name,))
    rows = c.fetchall()
    conn.close()

    # Default to empty if not available
    if not rows:
        today = datetime.now().date()
        rows = [((today + timedelta(days=i)).strftime("%d/%m/%Y"), "", "") for i in range(7)]

    result = [{"date": r[0], "morning": (r[1] if r[1] != "Not Available" else ""), "evening": (r[2] if r[2] != "Not Available" else "")} for r in rows]
    
    return jsonify(result)




@app.route('/book_appointment_ajax', methods=['POST'])
def book_appointment_ajax():
    """
    Accepts JSON POST with: patient_username, patient_display_name, doctor_name, date, time, department
    Creates appointment record and returns success.
    """
    data = request.json or {}
    patient_username = data.get('patient_username')
    patient_display_name = data.get('patient_display_name')  # this is human-readable name stored in appointments
    doctor_name = data.get('doctor_name')
    date = data.get('date')
    time = data.get('time')
    department = data.get('department', '')

    if not (patient_display_name and doctor_name and date and time):
        return jsonify({"error": "Missing required fields"}), 400

    execute_db("INSERT INTO appointments (patient_name, doctor_name, date, time, department) VALUES (?, ?, ?, ?, ?)",
               (patient_display_name, doctor_name, date, time, department))

    return jsonify({"success": True, "message": "Appointment booked"})

# ---------------- Mark Appointment as Complete ----------------
@app.route('/mark_complete/<int:appointment_id>', methods=['POST'])
def mark_complete(appointment_id):
    doctor_name = request.form.get('doctor_name')

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Fetch appointment info
    c.execute("SELECT patient_name, doctor_name, department, date, time FROM appointments WHERE id=?", (appointment_id,))
    appointment = c.fetchone()

    if appointment:
        patient_name, doctor_name_db, department, date, time = appointment

        # Save it to patient_history table
        c.execute("""
            INSERT INTO patient_history (patient_name, doctor_name, visit_type, created_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (patient_name, doctor_name_db, "Consultation"))

        # Delete from appointments after completion
        c.execute("DELETE FROM appointments WHERE id=?", (appointment_id,))
        conn.commit()

    conn.close()
    flash("Appointment marked as complete!", "success")
    return redirect(url_for('doctor_dashboard', doctor_name=doctor_name or doctor_name_db))


# ---------------- Cancel Appointment ----------------
@app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    doctor_name = request.form.get('doctor_name')

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("DELETE FROM appointments WHERE id=?", (appointment_id,))
    conn.commit()
    conn.close()

    flash("Appointment canceled successfully!", "warning")
    return redirect(url_for('doctor_dashboard', doctor_name=doctor_name))


# ---------------- Doctor provide availability (existing route kept) ----------------
@app.route('/provide_availability/<doctor_name>', methods=['GET', 'POST'])
def provide_availability(doctor_name):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    if request.method == 'POST':
        # Replace availability for this doctor (simple)
        c.execute("DELETE FROM doctor_availability WHERE doctor_name=?", (doctor_name,))
        dates = request.form.getlist('date')
        morning_slots = request.form.getlist('morning_slot')
        evening_slots = request.form.getlist('evening_slot')

        for d, m, e in zip(dates, morning_slots, evening_slots):
            c.execute("INSERT INTO doctor_availability (doctor_name, date, morning_slot, evening_slot) VALUES (?, ?, ?, ?)",
                      (doctor_name, d, m, e))
        conn.commit()
        conn.close()
        flash("Availability saved successfully!", "success")
        return redirect(url_for('doctor_dashboard', doctor_name=doctor_name))

    today = datetime.now().date()
    week = [(today + timedelta(days=i)).strftime("%d/%m/%Y") for i in range(7)]
    c.execute("SELECT date, morning_slot, evening_slot FROM doctor_availability WHERE doctor_name=?", (doctor_name,))
    rows = c.fetchall()
    existing = {row[0]: {'morning': row[1], 'evening': row[2]} for row in rows}
    conn.close()
    # This renders a template for doctors to provide availability (not the patient booking UI).
    return render_template('provide_availability.html', doctor_name=doctor_name, week=week, existing=existing)


@app.route('/add_doctor', methods=['POST'])
def add_doctor():
    fullname = request.form['fullname']
    password = request.form['password']
    department = request.form['department']
    experience = request.form['experience']

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    #  No username/email generation — take the entered name as is
    c.execute("SELECT * FROM users WHERE name=?", (fullname,))
    existing_user = c.fetchone()

    if existing_user:
        flash("Doctor with this name already exists!", "danger")
    else:
        #  Insert directly using fullname
        c.execute("""
            INSERT INTO users (name, surname, email, address, username, password, user_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (fullname, "", "", "", fullname, password, "Doctor"))
        user_id = c.lastrowid

        # Add doctor details
        c.execute("""
            INSERT INTO doctors (user_id, fullname, password, department, experience)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, fullname, password, department, experience))

        conn.commit()
        flash("Doctor added successfully!", "success")

    conn.close()
    return redirect(url_for('admin_dashboard'))


#  Edit doctor info
@app.route('/edit_doctor/<int:doctor_id>', methods=['POST'])
def edit_doctor(doctor_id):
    fullname = request.form['fullname']
    password = request.form['password']
    department = request.form['department']
    experience = request.form['experience']

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE doctors SET fullname=?, password=?, department=?, experience=? WHERE id=?",
              (fullname, password, department, experience, doctor_id))
    conn.commit()
    conn.close()
    flash("Doctor updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))


#  Delete doctor
@app.route('/delete_doctor/<int:doctor_id>', methods=['POST'])
def delete_doctor(doctor_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("DELETE FROM doctors WHERE id=?", (doctor_id,))
    conn.commit()
    conn.close()
    flash("Doctor deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_patient/<int:user_id>', methods=['POST'])
def delete_patient(user_id):
    # delete from patients table (optional)
    execute_db("DELETE FROM patients WHERE user_id=?", (user_id,))

    # delete from users table
    execute_db("DELETE FROM users WHERE id=?", (user_id,))

    flash("Patient deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))


# ---------------- Additional helper for adding patient history (kept) ----------------
@app.route('/update_patient_history', methods=['POST'])
def update_patient_history():
    patient_name = request.form.get('patient_name')
    doctor_name = request.form.get('doctor_name')
    visit_type = request.form.get('visit_type')
    test_done = request.form.get('test_done')
    diagnosis = request.form.get('diagnosis')
    prescription = request.form.get('prescription')
    medicines = request.form.get('medicines')

    data = (
        patient_name,
        doctor_name,
        visit_type,
        test_done,
        diagnosis,
        prescription,
        medicines,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    execute_db("""INSERT INTO patient_history 
                 (patient_name, doctor_name, visit_type, test_done, diagnosis, prescription, medicines, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", data)
    flash("Patient history updated successfully!", "success")
    return redirect(request.referrer or url_for('doctor_dashboard', doctor_name=doctor_name))

@app.route('/update_patient_profile/<username>', methods=['POST'])
def update_patient_profile(username):
    name = request.form.get('name')
    surname = request.form.get('surname')
    email = request.form.get('email')
    address = request.form.get('address')
    password = request.form.get('password')

    execute_db("""
        UPDATE users 
        SET name=?, surname=?, email=?, address=?, password=?
        WHERE username=? AND user_type='Patient'
    """, (name, surname, email, address, password, username))

    flash("Profile updated successfully!", "success")
    return redirect(url_for('patient_dashboard', patient_username=username))


# ------------- Run app -------------
if __name__ == '__main__':
    app.run(debug=True)

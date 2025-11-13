Hospital Management System
A complete Flask + SQLite web application for managing patients, doctors, appointments, medical history & availability.

📌 Overview
The Hospital Management System is a full-stack web application built using:
Flask (Python backend)
SQLite (lightweight embedded database)
Jinja2 Templates
Bootstrap 5 UI
HTML / CSS / JS Fetch API


This system allows 3 roles:
👨‍⚕️ Admin
Manage doctors
View registered patients
View & delete appointments
Global search (doctor, patient, department)
Delete patient accounts


🧑‍⚕️ Doctor
View assigned patient appointments
Mark appointments as complete
Add patient history/medical records
Provide weekly availability (morning/evening slots)


🧑‍💼 Patient
Dashboard with profile & summary
Edit profile (name, email, address, password)
Book an appointment with a doctor
Check availability dynamically
View upcoming appointments
Cancel appointment
View complete medical history (AJAX popup)
Explore doctors by department



📁 Project Structure
/your-project
│── app.py                 # Main Flask app
│── users.db               # SQLite database (auto-generated)
│── templates/
│     ├── index.html
│     ├── login.html
│     ├── register.html
│     ├── admin_dashboard.html
│     ├── doctor_dashboard.html
│     ├── provide_availability.html
│     ├── patients_dashboard.html
│── static/
│     ├── css/
│     ├── js/
│── README.md
│── venv/ (optional, virtual env)


⚙️ Features
🔐 Authentication


Login for Admin, Doctor, Patient
Separate dashboards
Unique username validation
Registration for patients


🧑‍⚕️ Admin Panel
Add doctor
Edit doctor
Delete doctor
View all registered patients
Delete patient (from users + patients table)
View appointments
Search by name, department


🧑‍⚕️ Doctor Dashboard
View today’s appointments
Mark appointment as complete
Automatically move completed entries to Patient History
Add/update medical details (diagnosis, tests, prescription)
Provide availability (morning/evening slots for next 7 days)


🧑‍💼 Patient Dashboard
View your upcoming appointments
Cancel appointments
Check doctor availability
Book appointment (AJAX)
View medical history (AJAX modal)
Edit profile via modal
Explore doctors by department

🛠 Installation & Setup
1️⃣ Clone the repository
git clone https://github.com/yourusername/hospital-management.git
cd hospital-management

2️⃣ Create Virtual Environment
python -m venv venv
source venv/bin/activate     # macOS/Linux
venv\Scripts\activate        # Windows

3️⃣ Install Dependencies
pip install flask

(Flask uses built-in SQLite, so no DB driver required.)
4️⃣ Run the Application
python app.py

Server runs at:
http://127.0.0.1:5000


🗄 Database Schema
users
| id | name | surname | email | address | username | password | user_type |
doctors
| id | user_id | fullname | password | department | experience |
patients
| id | user_id | age | gender | department |
appointments
| id | patient_name | doctor_name | date | time | department |
patient_history
| id | patient_name | doctor_name | visit_type | test_done | diagnosis | prescription | medicines | created_at |
doctor_availability
| id | doctor_name | date | morning_slot | evening_slot |

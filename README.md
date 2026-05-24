# Sports Day Registration System

**Student:** [Your Full Name]
**Roll No:** [Your Roll Number]
**Semester:** BSCS 6th — Spring 2026
**Course:** Software Construction and Development

---

## How to Run

```bash
# 1. (Optional) Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the application
python app.py

# 4. Open in browser
#    http://127.0.0.1:5000
```

The database (`sports_day.db`) is created and seeded **automatically** on first run. No manual setup required.

---

## Admin Credentials

| Field    | Value                   |
|----------|-------------------------|
| Email    | admin@sportsday.edu     |
| Password | admin123                |

---

## Features Implemented

- [x] Student Registration & Login (with password hashing)
- [x] Session-based Authentication (manual, no Flask-Login)
- [x] Role-based Access: Admin vs Student
- [x] Flash messages throughout the application
- [x] Public Home Page listing active sports
- [x] Browse & Search Sports (by name / venue)
- [x] Sport Detail Page with full rules
- [x] Register for a Sport (with duplicate prevention)
- [x] JazzCash QR Payment Simulation
- [x] My Registrations Page (with colour-coded statuses)
- [x] Cancel Pending Registrations
- [x] Admin: Sports CRUD (Add / Edit / Delete / Toggle Active)
- [x] Admin: Cannot delete sport with active registrations
- [x] Admin: View All Registrations with Filters (status, sport, search)
- [x] Admin: Approve / Reject Payment Status
- [x] Admin: Dashboard with aggregate statistics
- [x] Jinja2 Template Inheritance (base.html)
- [x] Responsive UI with Bootstrap 5

## Bonus Features

- [x] Search bar on sports list (by name / venue)
- [x] Pagination on admin registrations page
- [x] Export registrations to CSV

---

## Project Structure

```
sports_day/
├── app.py                        # Main Flask application
├── database.py                   # DB init, get_db(), close_db()
├── sports_day.db                 # SQLite database (auto-created)
├── requirements.txt
├── README.md
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── images/jazzcash_qr.png
└── templates/
    ├── base.html
    ├── index.html
    ├── auth/
    │   ├── login.html
    │   └── register.html
    ├── student/
    │   ├── dashboard.html
    │   ├── sports_list.html
    │   ├── sport_detail.html
    │   ├── payment.html
    │   └── my_registrations.html
    └── admin/
        ├── dashboard.html
        ├── sports_list.html
        ├── sport_form.html
        └── registrations.html
```

---

## Database Tables

| Table          | Description                              |
|----------------|------------------------------------------|
| users          | Students and admin accounts              |
| sports         | Sports events with rules, fees, venues   |
| registrations  | Student–sport registrations + payments   |

---

## Technology Stack

| Technology            | Purpose                        |
|-----------------------|--------------------------------|
| Python 3.x + Flask    | Backend web framework          |
| SQLite3               | Relational database            |
| Jinja2                | HTML templating                |
| werkzeug.security     | Password hashing (pbkdf2)      |
| Bootstrap 5           | Responsive UI                  |
| HTML5 + CSS3 + JS     | Frontend                       |

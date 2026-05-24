"""
Sports Day Registration System
Flask Assignment — BSCS F23 | Software Construction & Development
University of the Punjab, Lahore
"""

import re
import csv
import io
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, g, Response
)
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db, close_db, init_db

# ---------------------------------------------------------------------------
# Vercel Writable SQLite Database Fix
# ---------------------------------------------------------------------------
import os
import shutil

DATABASE_NAME = "sports_day.db"
TEMP_DB_PATH = os.path.join("/tmp", DATABASE_NAME)

# Agar ye server Vercel par chal raha hai, to database ko writable folder (/tmp) mein copy karein
if os.path.exists(DATABASE_NAME) and not os.path.exists(TEMP_DB_PATH):
    shutil.copyfile(DATABASE_NAME, TEMP_DB_PATH)

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = 'SportsDayPunjabUniversity2026!SecretKey'
app.teardown_appcontext(close_db)


# ---------------------------------------------------------------------------
# Decorators / Helpers
# ---------------------------------------------------------------------------

def login_required(f):
    """Redirect to login if the user is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Redirect to login if the user is not an admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'admin':
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def validate_email(email: str) -> bool:
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', email))


def validate_phone(phone: str) -> bool:
    return bool(re.match(r'^03\d{9}$', phone))


# ---------------------------------------------------------------------------
# Public Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Public home page listing all active sports."""
    db = get_db()
    sports = db.execute(
        '''SELECT s.*,
                  (s.max_players - COUNT(r.id)) AS slots_remaining
           FROM sports s
           LEFT JOIN registrations r ON s.id = r.sport_id
           WHERE s.is_active = 1
           GROUP BY s.id
           ORDER BY s.event_date ASC'''
    ).fetchall()
    return render_template('index.html', sports=sports)


# ---------------------------------------------------------------------------
# Authentication Routes
# ---------------------------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Student self-registration."""
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        phone    = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        errors = []
        if not name:
            errors.append('Full name is required.')
        if not email or not validate_email(email):
            errors.append('A valid email address is required.')
        if not phone or not validate_phone(phone):
            errors.append('Phone must be a valid Pakistani number (03XXXXXXXXX).')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('auth/register.html',
                                   name=name, email=email, phone=phone)

        db = get_db()
        existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            flash('An account with this email already exists.', 'danger')
            return render_template('auth/register.html',
                                   name=name, email=email, phone=phone)

        hashed_pw = generate_password_hash(password)
        now = datetime.now().isoformat()
        db.execute(
            'INSERT INTO users (name, email, phone, password, role, created_at) VALUES (?,?,?,?,?,?)',
            (name, email, phone, hashed_pw, 'student', now)
        )
        db.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login for both students and admins."""
    if 'user_id' in session:
        return redirect(url_for('dashboard') if session['user_role'] == 'student' else url_for('admin_dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('auth/login.html', email=email)

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id']   = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            flash(f'Welcome back, {user["name"]}!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))

        flash('Invalid email or password.', 'danger')
        return render_template('auth/login.html', email=email)

    return render_template('auth/login.html')


@app.route('/logout')
def logout():
    """Clear session and redirect home."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ---------------------------------------------------------------------------
# Student Routes
# ---------------------------------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard():
    """Student dashboard with summary stats and recent registrations."""
    if session['user_role'] == 'admin':
        return redirect(url_for('admin_dashboard'))

    db = get_db()
    uid = session['user_id']

    stats = db.execute(
        '''SELECT
               COUNT(*) AS total,
               SUM(CASE WHEN payment_status = 'pending'  THEN 1 ELSE 0 END) AS pending,
               SUM(CASE WHEN payment_status = 'approved' THEN 1 ELSE 0 END) AS approved,
               SUM(CASE WHEN payment_status = 'rejected' THEN 1 ELSE 0 END) AS rejected
           FROM registrations WHERE user_id = ?''',
        (uid,)
    ).fetchone()

    registrations = db.execute(
        '''SELECT r.*, s.name AS sport_name, s.fee, s.venue, s.event_date
           FROM registrations r
           JOIN sports s ON r.sport_id = s.id
           WHERE r.user_id = ?
           ORDER BY r.registered_at DESC''',
        (uid,)
    ).fetchall()

    return render_template('student/dashboard.html', stats=stats, registrations=registrations)


@app.route('/sports')
@login_required
def sports_list():
    """Browse all active sports with registration status for current student."""
    if session['user_role'] == 'admin':
        return redirect(url_for('admin_sports'))

    db  = get_db()
    uid = session['user_id']
    search = request.args.get('q', '').strip()

    query = '''
        SELECT s.*,
               (s.max_players - COUNT(r.id)) AS slots_remaining,
               MAX(CASE WHEN r.user_id = ? THEN 1 ELSE 0 END) AS already_registered
        FROM sports s
        LEFT JOIN registrations r ON s.id = r.sport_id
        WHERE s.is_active = 1
    '''
    params = [uid]

    if search:
        query += ' AND (s.name LIKE ? OR s.venue LIKE ?)'
        params += [f'%{search}%', f'%{search}%']

    query += ' GROUP BY s.id ORDER BY s.event_date ASC'
    sports = db.execute(query, params).fetchall()

    return render_template('student/sports_list.html', sports=sports, search=search)


@app.route('/sports/<int:sport_id>', methods=['GET', 'POST'])
@login_required
def sport_detail(sport_id):
    """View sport details and register."""
    if session['user_role'] == 'admin':
        return redirect(url_for('admin_sports'))

    db  = get_db()
    uid = session['user_id']

    sport = db.execute(
        '''SELECT s.*,
                  (s.max_players - COUNT(r.id)) AS slots_remaining
           FROM sports s
           LEFT JOIN registrations r ON s.id = r.sport_id
           WHERE s.id = ?
           GROUP BY s.id''',
        (sport_id,)
    ).fetchone()

    if not sport:
        flash('Sport not found.', 'danger')
        return redirect(url_for('sports_list'))

    already = db.execute(
        'SELECT id FROM registrations WHERE user_id = ? AND sport_id = ?',
        (uid, sport_id)
    ).fetchone()

    if request.method == 'POST':
        if already:
            flash('You are already registered for this sport.', 'warning')
            return redirect(url_for('sport_detail', sport_id=sport_id))

        if sport['slots_remaining'] <= 0:
            flash('No slots remaining for this sport.', 'danger')
            return redirect(url_for('sport_detail', sport_id=sport_id))

        now = datetime.now().isoformat()
        db.execute(
            'INSERT INTO registrations (user_id, sport_id, payment_status, registered_at) VALUES (?,?,?,?)',
            (uid, sport_id, 'pending', now)
        )
        db.commit()

        reg = db.execute(
            'SELECT id FROM registrations WHERE user_id = ? AND sport_id = ?',
            (uid, sport_id)
        ).fetchone()

        flash('Successfully registered! Please complete your payment.', 'success')
        return redirect(url_for('payment', registration_id=reg['id']))

    return render_template('student/sport_detail.html', sport=sport, already=already)


@app.route('/pay/<int:registration_id>', methods=['GET', 'POST'])
@login_required
def payment(registration_id):
    """JazzCash payment simulation page."""
    db  = get_db()
    uid = session['user_id']

    reg = db.execute(
        '''SELECT r.*, s.name AS sport_name, s.fee
           FROM registrations r
           JOIN sports s ON r.sport_id = s.id
           WHERE r.id = ? AND r.user_id = ?''',
        (registration_id, uid)
    ).fetchone()

    if not reg:
        flash('Registration not found.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        txn_id = request.form.get('transaction_id', '').strip()
        if not txn_id:
            flash('Please enter your JazzCash Transaction ID.', 'danger')
            return render_template('student/payment.html', reg=reg)

        db.execute(
            "UPDATE registrations SET payment_ref = ?, payment_status = 'pending' WHERE id = ?",
            (txn_id, registration_id)
        )
        db.commit()
        flash('Payment reference submitted. Awaiting admin approval.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('student/payment.html', reg=reg)


@app.route('/my-registrations')
@login_required
def my_registrations():
    """List all registrations for the logged-in student."""
    db  = get_db()
    uid = session['user_id']

    registrations = db.execute(
        '''SELECT r.*, s.name AS sport_name, s.fee, s.venue, s.event_date
           FROM registrations r
           JOIN sports s ON r.sport_id = s.id
           WHERE r.user_id = ?
           ORDER BY r.registered_at DESC''',
        (uid,)
    ).fetchall()

    return render_template('student/my_registrations.html', registrations=registrations)


@app.route('/cancel/<int:registration_id>', methods=['POST'])
@login_required
def cancel_registration(registration_id):
    """Cancel a pending registration."""
    db  = get_db()
    uid = session['user_id']

    reg = db.execute(
        'SELECT * FROM registrations WHERE id = ? AND user_id = ?',
        (registration_id, uid)
    ).fetchone()

    if not reg:
        flash('Registration not found.', 'danger')
        return redirect(url_for('my_registrations'))

    if reg['payment_status'] != 'pending':
        flash('Only pending registrations can be cancelled.', 'warning')
        return redirect(url_for('my_registrations'))

    db.execute('DELETE FROM registrations WHERE id = ?', (registration_id,))
    db.commit()
    flash('Registration cancelled successfully.', 'success')
    return redirect(url_for('my_registrations'))


# ---------------------------------------------------------------------------
# Admin Routes
# ---------------------------------------------------------------------------

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with aggregate statistics."""
    db = get_db()

    stats = db.execute(
        '''SELECT
               (SELECT COUNT(*) FROM users WHERE role = 'student')            AS total_students,
               (SELECT COUNT(*) FROM sports)                                   AS total_sports,
               (SELECT COUNT(*) FROM registrations)                            AS total_registrations,
               (SELECT COUNT(*) FROM registrations WHERE payment_status='pending')  AS pending_payments,
               (SELECT COALESCE(SUM(s.fee),0)
                FROM registrations r JOIN sports s ON r.sport_id = s.id
                WHERE r.payment_status = 'approved')                           AS revenue
        '''
    ).fetchone()

    recent = db.execute(
        '''SELECT r.*, u.name AS student_name, u.email, s.name AS sport_name
           FROM registrations r
           JOIN users  u ON r.user_id  = u.id
           JOIN sports s ON r.sport_id = s.id
           ORDER BY r.registered_at DESC
           LIMIT 10'''
    ).fetchall()

    return render_template('admin/dashboard.html', stats=stats, recent=recent)


@app.route('/admin/sports')
@admin_required
def admin_sports():
    """List all sports with management actions."""
    db = get_db()
    sports = db.execute(
        '''SELECT s.*,
                  COUNT(r.id) AS reg_count
           FROM sports s
           LEFT JOIN registrations r ON s.id = r.sport_id
           GROUP BY s.id
           ORDER BY s.created_at DESC'''
    ).fetchall()
    return render_template('admin/sports_list.html', sports=sports)


@app.route('/admin/sports/add', methods=['GET', 'POST'])
@admin_required
def admin_add_sport():
    """Add a new sport."""
    if request.method == 'POST':
        data, errors = _parse_sport_form()
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('admin/sport_form.html', sport=data, action='Add')

        db = get_db()
        existing = db.execute('SELECT id FROM sports WHERE name = ?', (data['name'],)).fetchone()
        if existing:
            flash('A sport with this name already exists.', 'danger')
            return render_template('admin/sport_form.html', sport=data, action='Add')

        now = datetime.now().isoformat()
        db.execute(
            '''INSERT INTO sports (name, description, rules, fee, max_players, venue, event_date, is_active, created_at)
               VALUES (?,?,?,?,?,?,?,?,?)''',
            (data['name'], data['description'], data['rules'], data['fee'],
             data['max_players'], data['venue'], data['event_date'], 1, now)
        )
        db.commit()
        flash(f'Sport "{data["name"]}" added successfully.', 'success')
        return redirect(url_for('admin_sports'))

    return render_template('admin/sport_form.html', sport={}, action='Add')


@app.route('/admin/sports/edit/<int:sport_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_sport(sport_id):
    """Edit an existing sport."""
    db = get_db()
    sport = db.execute('SELECT * FROM sports WHERE id = ?', (sport_id,)).fetchone()
    if not sport:
        flash('Sport not found.', 'danger')
        return redirect(url_for('admin_sports'))

    if request.method == 'POST':
        data, errors = _parse_sport_form()
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('admin/sport_form.html', sport=data, action='Edit', sport_id=sport_id)

        conflict = db.execute(
            'SELECT id FROM sports WHERE name = ? AND id != ?', (data['name'], sport_id)
        ).fetchone()
        if conflict:
            flash('Another sport with this name already exists.', 'danger')
            return render_template('admin/sport_form.html', sport=data, action='Edit', sport_id=sport_id)

        db.execute(
            '''UPDATE sports SET name=?, description=?, rules=?, fee=?, max_players=?,
               venue=?, event_date=? WHERE id=?''',
            (data['name'], data['description'], data['rules'], data['fee'],
             data['max_players'], data['venue'], data['event_date'], sport_id)
        )
        db.commit()
        flash(f'Sport "{data["name"]}" updated successfully.', 'success')
        return redirect(url_for('admin_sports'))

    return render_template('admin/sport_form.html', sport=dict(sport), action='Edit', sport_id=sport_id)


@app.route('/admin/sports/delete/<int:sport_id>', methods=['POST'])
@admin_required
def admin_delete_sport(sport_id):
    """Delete a sport (only if no registrations exist)."""
    db = get_db()
    reg_count = db.execute(
        'SELECT COUNT(*) AS cnt FROM registrations WHERE sport_id = ?', (sport_id,)
    ).fetchone()['cnt']

    if reg_count > 0:
        flash('Cannot delete sport with active registrations.', 'danger')
        return redirect(url_for('admin_sports'))

    sport = db.execute('SELECT name FROM sports WHERE id = ?', (sport_id,)).fetchone()
    if sport:
        db.execute('DELETE FROM sports WHERE id = ?', (sport_id,))
        db.commit()
        flash(f'Sport "{sport["name"]}" deleted.', 'success')
    else:
        flash('Sport not found.', 'danger')

    return redirect(url_for('admin_sports'))


@app.route('/admin/sports/toggle/<int:sport_id>', methods=['POST'])
@admin_required
def admin_toggle_sport(sport_id):
    """Toggle a sport's active/inactive status."""
    db = get_db()
    sport = db.execute('SELECT * FROM sports WHERE id = ?', (sport_id,)).fetchone()
    if not sport:
        flash('Sport not found.', 'danger')
        return redirect(url_for('admin_sports'))

    new_status = 0 if sport['is_active'] else 1
    db.execute('UPDATE sports SET is_active = ? WHERE id = ?', (new_status, sport_id))
    db.commit()
    label = 'activated' if new_status else 'deactivated'
    flash(f'Sport "{sport["name"]}" {label}.', 'success')
    return redirect(url_for('admin_sports'))


@app.route('/admin/registrations')
@admin_required
def admin_registrations():
    """View all registrations with optional filters."""
    db     = get_db()
    status = request.args.get('status', '')
    sport  = request.args.get('sport', '')
    search = request.args.get('q', '')
    page   = max(1, int(request.args.get('page', 1)))
    per_page = 15

    base_query = '''
        SELECT r.*, u.name AS student_name, u.email,
               s.name AS sport_name, s.fee
        FROM registrations r
        JOIN users  u ON r.user_id  = u.id
        JOIN sports s ON r.sport_id = s.id
        WHERE 1=1
    '''
    params = []

    if status:
        base_query += ' AND r.payment_status = ?'
        params.append(status)
    if sport:
        base_query += ' AND s.id = ?'
        params.append(sport)
    if search:
        base_query += ' AND (u.name LIKE ? OR u.email LIKE ? OR s.name LIKE ?)'
        params += [f'%{search}%', f'%{search}%', f'%{search}%']

    total = db.execute(f'SELECT COUNT(*) AS cnt FROM ({base_query})', params).fetchone()['cnt']
    total_pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page

    registrations = db.execute(
        base_query + ' ORDER BY r.registered_at DESC LIMIT ? OFFSET ?',
        params + [per_page, offset]
    ).fetchall()

    sports_all = db.execute('SELECT id, name FROM sports ORDER BY name').fetchall()

    return render_template(
        'admin/registrations.html',
        registrations=registrations,
        sports_all=sports_all,
        filter_status=status,
        filter_sport=sport,
        search=search,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@app.route('/admin/payment/<int:registration_id>', methods=['POST'])
@admin_required
def admin_update_payment(registration_id):
    """Approve or reject a payment."""
    new_status = request.form.get('status', '')
    if new_status not in ('approved', 'rejected'):
        flash('Invalid status value.', 'danger')
        return redirect(url_for('admin_registrations'))

    db = get_db()
    db.execute(
        'UPDATE registrations SET payment_status = ? WHERE id = ?',
        (new_status, registration_id)
    )
    db.commit()
    flash(f'Payment status updated to {new_status}.', 'success')
    return redirect(url_for('admin_registrations',
                            status=request.args.get('status', ''),
                            sport=request.args.get('sport', ''),
                            page=request.args.get('page', 1)))


@app.route('/admin/registrations/export')
@admin_required
def admin_export_csv():
    """Export all registrations to CSV."""
    db = get_db()
    rows = db.execute(
        '''SELECT u.name AS student_name, u.email, u.phone,
                  s.name AS sport_name, s.fee, s.venue, s.event_date,
                  r.payment_ref, r.payment_status, r.registered_at
           FROM registrations r
           JOIN users  u ON r.user_id  = u.id
           JOIN sports s ON r.sport_id = s.id
           ORDER BY r.registered_at DESC'''
    ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student Name', 'Email', 'Phone', 'Sport', 'Fee (PKR)',
                     'Venue', 'Event Date', 'Transaction ID', 'Payment Status', 'Registered At'])
    for row in rows:
        writer.writerow(list(row))

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=registrations.csv'}
    )


# ---------------------------------------------------------------------------
# Helper: Parse sport form fields
# ---------------------------------------------------------------------------

def _parse_sport_form():
    """Parse and validate the sport add/edit form. Returns (data_dict, errors_list)."""
    name        = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    rules       = request.form.get('rules', '').strip()
    fee_str     = request.form.get('fee', '').strip()
    max_str     = request.form.get('max_players', '').strip()
    venue       = request.form.get('venue', '').strip()
    event_date  = request.form.get('event_date', '').strip()

    errors = []
    fee = 0.0
    max_players = 20

    if not name:
        errors.append('Sport name is required.')

    try:
        fee = float(fee_str)
        if fee < 0:
            errors.append('Fee must be a non-negative number.')
    except (ValueError, TypeError):
        errors.append('Fee must be a valid number.')

    try:
        max_players = int(max_str)
        if max_players < 1:
            errors.append('Max players must be a positive integer.')
    except (ValueError, TypeError):
        errors.append('Max players must be a valid integer.')

    data = dict(name=name, description=description, rules=rules,
                fee=fee_str, max_players=max_str, venue=venue, event_date=event_date)
    data['fee']         = fee
    data['max_players'] = max_players

    return data, errors


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

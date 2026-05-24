import os
import shutil
import sqlite3
from flask import g

DATABASE = 'sports_day.db'

# ---------------------------------------------------------------------------
# Vercel Dynamic Path Handler
# ---------------------------------------------------------------------------
# Agar server Vercel par hai to /tmp folder use hoga, warna local computer par normal file
if os.path.exists("/tmp"):
    TEMP_DATABASE = os.path.join("/tmp", DATABASE)
    # Agar original database maujood hai aur abhi tak /tmp mein copy nahi hui, to copy kar dein
    if os.path.exists(DATABASE) and not os.path.exists(TEMP_DATABASE):
        shutil.copyfile(DATABASE, TEMP_DATABASE)
    DB_PATH = TEMP_DATABASE
else:
    DB_PATH = DATABASE


def get_db():
    """Get a database connection, reusing the one on the Flask g object."""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)  # Use dynamically updated path
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Create all tables and seed initial data."""
    db = sqlite3.connect(DB_PATH)  # Use dynamically updated path
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")

    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            phone       TEXT    NOT NULL,
            password    TEXT    NOT NULL,
            role        TEXT    NOT NULL DEFAULT 'student',
            created_at  TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            description TEXT,
            rules       TEXT,
            fee         REAL    NOT NULL DEFAULT 0,
            max_players INTEGER DEFAULT 20,
            venue       TEXT,
            event_date  TEXT,
            is_active   INTEGER DEFAULT 1,
            created_at  TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS registrations (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL,
            sport_id       INTEGER NOT NULL,
            payment_ref    TEXT,
            payment_status TEXT    NOT NULL DEFAULT 'pending',
            registered_at  TEXT    NOT NULL,
            FOREIGN KEY (user_id)  REFERENCES users(id),
            FOREIGN KEY (sport_id) REFERENCES sports(id),
            UNIQUE (user_id, sport_id)
        );
    ''')
    db.commit()

    # Seed admin account
    from werkzeug.security import generate_password_hash
    from datetime import datetime
    now = datetime.now().isoformat()

    existing_admin = db.execute("SELECT id FROM users WHERE email = 'admin@sportsday.edu'").fetchone()
    if not existing_admin:
        db.execute(
            "INSERT INTO users (name, email, phone, password, role, created_at) VALUES (?,?,?,?,?,?)",
            ('Admin', 'admin@sportsday.edu', '03001234567',
             generate_password_hash('admin123'), 'admin', now)
        )
        db.commit()

    # Seed sports data
    existing_sports = db.execute("SELECT COUNT(*) as cnt FROM sports").fetchone()
    if existing_sports['cnt'] == 0:
        sports_data = [
            (
                'Cricket',
                'Classic bat-and-ball team sport played between two teams of eleven players.',
                '1. Each team must consist of exactly 11 players.\n2. All players must be enrolled BSCS students.\n3. Match format: 10 overs per side.\n4. Protective gear (helmet, pads) is mandatory for batsmen.\n5. No professional or outside players permitted.\n6. The umpire\'s decision is final.\n7. Disputes must be raised before the next ball is bowled.\n8. Registration fee must be paid before match day.',
                500, 22, 'Main Ground, Block A', '2026-06-15', 1, now
            ),
            (
                'Badminton (Singles)',
                'Fast-paced racket sport played one-on-one on an indoor court.',
                '1. Matches are best of 3 games, each up to 21 points.\n2. Players must bring their own rackets.\n3. Official shuttlecocks will be provided.\n4. Proper sports attire is mandatory.\n5. Coaching from the sidelines is not allowed.\n6. Service faults will be called by the referee.\n7. Players must report 15 minutes before their match.',
                300, 4, 'Indoor Court, Sports Complex', '2026-06-16', 1, now
            ),
            (
                'Table Tennis (Singles)',
                'Indoor racket sport played on a table divided by a net.',
                '1. Matches are best of 5 games, each up to 11 points.\n2. Players must bring their own paddles.\n3. Balls will be provided by the organizers.\n4. No coaching during match play.\n5. Players must be punctual; 5-minute grace period only.\n6. Service rules per ITTF regulations apply.',
                200, 2, 'Indoor Hall, Main Block', '2026-06-17', 1, now
            ),
            (
                'Basketball (5v5)',
                'Team sport played on a court where two teams of five compete to score baskets.',
                '1. Each team must have exactly 5 players on the court.\n2. Match duration: two 15-minute halves.\n3. Standard FIBA rules apply.\n4. All players must wear proper sports shoes.\n5. Physical contact beyond normal play will result in fouls.\n6. Three fouls result in disqualification of the player.\n7. Substitutions allowed only during dead-ball situations.',
                350, 10, 'Basketball Court, Block A', '2026-06-18', 1, now
            ),
            (
                'Football (7-a-side)',
                'Mini football tournament played with 7 players per side on a smaller pitch.',
                '1. Teams consist of 7 players including the goalkeeper.\n2. Match duration: two 20-minute halves.\n3. Rolling substitutions allowed.\n4. Slide tackles are strictly prohibited.\n5. Offside rule does not apply.\n6. Goal kicks replace corner kicks.\n7. Red and yellow card system in effect.',
                400, 14, 'Football Pitch, Sports Ground', '2026-06-19', 1, now
            ),
        ]
        db.executemany(
            "INSERT INTO sports (name, description, rules, fee, max_players, venue, event_date, is_active, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            sports_data
        )
        db.commit()

    db.close()

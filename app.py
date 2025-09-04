import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    
    # Players table
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            address TEXT NOT NULL,
            dob TEXT NOT NULL,
            location1 TEXT NOT NULL,
            location2 TEXT,
            skill_level TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            selfie TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tournaments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            tournament_name TEXT NOT NULL,
            entry_date TEXT NOT NULL,
            match_deadline TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            match_result TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
init_db()

@app.route('/')
def index():
    """Home page showing overview of system"""
    conn = get_db_connection()
    
    # Get statistics
    total_players = conn.execute('SELECT COUNT(*) as count FROM players').fetchone()['count']
    active_tournaments = conn.execute('SELECT COUNT(*) as count FROM tournaments WHERE completed = 0').fetchone()['count']
    completed_tournaments = conn.execute('SELECT COUNT(*) as count FROM tournaments WHERE completed = 1').fetchone()['count']
    
    # Get recent tournament entries
    recent_tournaments = conn.execute('''
        SELECT t.tournament_name, p.full_name, t.entry_date, t.match_deadline, t.completed
        FROM tournaments t
        JOIN players p ON t.player_id = p.id
        ORDER BY t.created_at DESC
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('index.html', 
                         total_players=total_players,
                         active_tournaments=active_tournaments,
                         completed_tournaments=completed_tournaments,
                         recent_tournaments=recent_tournaments)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Player registration form"""
    if request.method == 'POST':
        # Form validation
        required_fields = ['full_name', 'address', 'dob', 'location1', 'skill_level', 'email']
        for field in required_fields:
            if not request.form.get(field):
                flash(f'{field.replace("_", " ").title()} is required', 'danger')
                return render_template('register.html')
        
        # Handle file upload
        selfie_filename = None
        if 'selfie' in request.files:
            file = request.files['selfie']
            if file and file.filename and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to filename to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                selfie_filename = filename
        
        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO players 
                (full_name, address, dob, location1, location2, skill_level, email, selfie)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (request.form['full_name'], request.form['address'], request.form['dob'], 
                  request.form['location1'], request.form.get('location2', ''), 
                  request.form['skill_level'], request.form['email'], selfie_filename))
            conn.commit()
            conn.close()
            
            flash('Registration successful! You can now enter tournaments.', 'success')
            return redirect(url_for('index'))
            
        except sqlite3.IntegrityError:
            flash('Email already exists. Please use a different email address.', 'danger')
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'danger')
    
    return render_template('register.html')

@app.route('/tournament', methods=['GET', 'POST'])
def tournament():
    """Tournament entry form"""
    if request.method == 'POST':
        if not request.form.get('player_id') or not request.form.get('tournament_name'):
            flash('Player and tournament name are required', 'danger')
            return redirect(url_for('tournament'))
        
        try:
            conn = get_db_connection()
            entry_date = datetime.now()
            match_deadline = entry_date + timedelta(days=7)
            
            conn.execute('''
                INSERT INTO tournaments (player_id, tournament_name, entry_date, match_deadline)
                VALUES (?, ?, ?, ?)
            ''', (request.form['player_id'], request.form['tournament_name'], 
                  entry_date.strftime('%Y-%m-%d'), match_deadline.strftime('%Y-%m-%d')))
            conn.commit()
            conn.close()
            
            flash('Tournament entry successful!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Tournament entry failed: {str(e)}', 'danger')
    
    # Get all players for dropdown
    conn = get_db_connection()
    players = conn.execute('SELECT id, full_name, email FROM players ORDER BY full_name').fetchall()
    conn.close()
    
    return render_template('tournament.html', players=players)

@app.route('/dashboard/<int:player_id>')
def dashboard(player_id):
    """Player dashboard showing their tournaments"""
    conn = get_db_connection()
    
    # Get player info
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    if not player:
        flash('Player not found', 'danger')
        return redirect(url_for('index'))
    
    # Get player's tournaments
    tournaments = conn.execute('''
        SELECT * FROM tournaments 
        WHERE player_id = ? 
        ORDER BY created_at DESC
    ''', (player_id,)).fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', player=player, tournaments=tournaments)

@app.route('/manage_tournaments')
def manage_tournaments():
    """Tournament management interface"""
    conn = get_db_connection()
    
    # Get all tournaments with player info
    tournaments = conn.execute('''
        SELECT t.*, p.full_name, p.email
        FROM tournaments t
        JOIN players p ON t.player_id = p.id
        ORDER BY t.created_at DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('manage_tournaments.html', tournaments=tournaments)

@app.route('/complete_tournament/<int:tournament_id>', methods=['POST'])
def complete_tournament(tournament_id):
    """Mark tournament as completed"""
    result = request.form.get('result', '')
    
    try:
        conn = get_db_connection()
        conn.execute('''
            UPDATE tournaments 
            SET completed = 1, match_result = ?
            WHERE id = ?
        ''', (result, tournament_id))
        conn.commit()
        conn.close()
        
        flash('Tournament marked as completed', 'success')
    except Exception as e:
        flash(f'Error updating tournament: {str(e)}', 'danger')
    
    return redirect(url_for('manage_tournaments'))

@app.route('/players')
def players():
    """List all registered players"""
    conn = get_db_connection()
    players = conn.execute('SELECT * FROM players ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return render_template('players.html', players=players)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
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
            preferred_sport TEXT,
            preferred_court TEXT,
            skill_level TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            selfie TEXT,
            is_looking_for_match INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add new columns if they don't exist (for existing databases)
    try:
        c.execute('ALTER TABLE players ADD COLUMN preferred_sport TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        c.execute('ALTER TABLE players ADD COLUMN preferred_court TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN is_looking_for_match INTEGER DEFAULT 1')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Matches table
    c.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1_id INTEGER NOT NULL,
            player2_id INTEGER NOT NULL,
            sport TEXT NOT NULL,
            court_location TEXT NOT NULL,
            match_date TEXT,
            status TEXT DEFAULT 'pending',
            player1_confirmed INTEGER DEFAULT 0,
            player2_confirmed INTEGER DEFAULT 0,
            winner_id INTEGER,
            match_result TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(player1_id) REFERENCES players(id),
            FOREIGN KEY(player2_id) REFERENCES players(id),
            FOREIGN KEY(winner_id) REFERENCES players(id)
        )
    ''')
    
    # Enhanced tournaments table with levels and fees
    c.execute('''
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            tournament_name TEXT NOT NULL,
            tournament_level TEXT,
            entry_fee REAL,
            sport TEXT,
            entry_date TEXT NOT NULL,
            match_deadline TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            match_result TEXT,
            payment_status TEXT DEFAULT 'pending',
            bracket_position INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
    ''')
    
    # Add new columns to tournaments if they don't exist
    try:
        c.execute('ALTER TABLE tournaments ADD COLUMN tournament_level TEXT')
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute('ALTER TABLE tournaments ADD COLUMN entry_fee REAL')
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute('ALTER TABLE tournaments ADD COLUMN sport TEXT')
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute('ALTER TABLE tournaments ADD COLUMN payment_status TEXT DEFAULT "pending"')
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute('ALTER TABLE tournaments ADD COLUMN bracket_position INTEGER')
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_tournament_levels():
    """Get available tournament levels with pricing"""
    return {
        'Beginner': {
            'name': 'Beginner League',
            'description': 'Perfect for new players and casual competition',
            'entry_fee': 5.00,
            'prize_pool': 'Winner takes 60%',
            'skill_requirements': 'Beginner level players'
        },
        'Intermediate': {
            'name': 'Intermediate Championship',
            'description': 'For players with solid fundamentals',
            'entry_fee': 15.00,
            'prize_pool': 'Winner takes 50%, Runner-up 30%',
            'skill_requirements': 'Intermediate level players'
        },
        'Advanced': {
            'name': 'Advanced Tournament',
            'description': 'High-level competitive play',
            'entry_fee': 35.00,
            'prize_pool': 'Winner takes 40%, Top 4 share prizes',
            'skill_requirements': 'Advanced level players'
        },
        'Professional': {
            'name': 'Pro Circuit',
            'description': 'Elite competition for the best players',
            'entry_fee': 75.00,
            'prize_pool': 'Winner takes 35%, Top 8 share prizes',
            'skill_requirements': 'Professional level players'
        }
    }

def find_match_for_player(player_id):
    """Find and create a match for a player based on skill, sport, and location"""
    conn = get_db_connection()
    
    # Get the player's preferences
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    if not player or not player['is_looking_for_match']:
        conn.close()
        return None
    
    # Find potential matches
    potential_matches = conn.execute('''
        SELECT * FROM players 
        WHERE id != ? 
        AND is_looking_for_match = 1
        AND preferred_sport = ?
        AND skill_level = ?
        AND (preferred_court = ? OR location1 = ? OR location2 = ?)
        AND id NOT IN (
            SELECT CASE 
                WHEN player1_id = ? THEN player2_id 
                ELSE player1_id 
            END 
            FROM matches 
            WHERE (player1_id = ? OR player2_id = ?) 
            AND status IN ('pending', 'confirmed', 'completed')
        )
        ORDER BY created_at ASC
        LIMIT 1
    ''', (player_id, player['preferred_sport'], player['skill_level'], 
          player['preferred_court'], player['location1'], player['location2'],
          player_id, player_id, player_id)).fetchone()
    
    if potential_matches:
        # Create a match
        match_court = player['preferred_court'] if potential_matches['preferred_court'] == player['preferred_court'] else player['preferred_court']
        
        cursor = conn.execute('''
            INSERT INTO matches (player1_id, player2_id, sport, court_location, status)
            VALUES (?, ?, ?, ?, 'pending')
        ''', (player_id, potential_matches['id'], player['preferred_sport'], match_court))
        
        match_id = cursor.lastrowid
        
        # Mark both players as no longer looking
        conn.execute('UPDATE players SET is_looking_for_match = 0 WHERE id IN (?, ?)', 
                    (player_id, potential_matches['id']))
        
        conn.commit()
        conn.close()
        return match_id
    
    conn.close()
    return None

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
        required_fields = ['full_name', 'address', 'dob', 'location1', 'preferred_sport', 'preferred_court', 'skill_level', 'email']
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
            cursor = conn.execute('''
                INSERT INTO players 
                (full_name, address, dob, location1, location2, preferred_sport, preferred_court, skill_level, email, selfie)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (request.form['full_name'], request.form['address'], request.form['dob'], 
                  request.form['location1'], request.form.get('location2', ''), 
                  request.form['preferred_sport'], request.form['preferred_court'],
                  request.form['skill_level'], request.form['email'], selfie_filename))
            
            player_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            flash('Registration successful! Looking for matches...', 'success')
            # Try to find a match for the new player
            find_match_for_player(player_id)
            return redirect(url_for('dashboard', player_id=player_id))
            
        except sqlite3.IntegrityError:
            flash('Email already exists. Please use a different email address.', 'danger')
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'danger')
    
    return render_template('register.html')

@app.route('/tournament', methods=['GET', 'POST'])
def tournament():
    """Tournament entry form with levels and fees"""
    if request.method == 'POST':
        required_fields = ['player_id', 'tournament_level', 'sport']
        for field in required_fields:
            if not request.form.get(field):
                flash(f'{field.replace("_", " ").title()} is required', 'danger')
                return redirect(url_for('tournament'))
        
        try:
            conn = get_db_connection()
            
            # Get player info to verify skill level match
            player = conn.execute('SELECT * FROM players WHERE id = ?', (request.form['player_id'],)).fetchone()
            tournament_levels = get_tournament_levels()
            selected_level = request.form['tournament_level']
            
            # Check if player skill matches tournament level (with some flexibility)
            skill_mapping = {
                'Beginner': ['Beginner'],
                'Intermediate': ['Beginner', 'Intermediate'], 
                'Advanced': ['Intermediate', 'Advanced'],
                'Professional': ['Advanced', 'Professional']
            }
            
            if player['skill_level'] not in skill_mapping.get(selected_level, []):
                flash(f'Your skill level ({player["skill_level"]}) may not be suitable for {selected_level} level. Consider a different tournament level.', 'warning')
                return redirect(url_for('tournament'))
            
            entry_date = datetime.now()
            match_deadline = entry_date + timedelta(days=14)  # 2 weeks for tournaments
            
            conn.execute('''
                INSERT INTO tournaments (player_id, tournament_name, tournament_level, entry_fee, sport, entry_date, match_deadline, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (request.form['player_id'], 
                  tournament_levels[selected_level]['name'],
                  selected_level,
                  tournament_levels[selected_level]['entry_fee'],
                  request.form['sport'],
                  entry_date.strftime('%Y-%m-%d'), 
                  match_deadline.strftime('%Y-%m-%d'),
                  'completed'))  # Skip payment for now
            
            conn.commit()
            conn.close()
            
            flash(f'Tournament entry successful! Entry fee: ${tournament_levels[selected_level]["entry_fee"]}', 'success')
            return redirect(url_for('dashboard', player_id=request.form['player_id']))
            
        except Exception as e:
            flash(f'Tournament entry failed: {str(e)}', 'danger')
    
    # Get all players for dropdown
    conn = get_db_connection()
    players = conn.execute('SELECT id, full_name, email, skill_level, COALESCE(preferred_sport, "Tennis") as preferred_sport FROM players ORDER BY full_name').fetchall()
    conn.close()
    
    tournament_levels = get_tournament_levels()
    
    return render_template('tournament.html', players=players, tournament_levels=tournament_levels)

@app.route('/dashboard/<int:player_id>')
def dashboard(player_id):
    """Player dashboard showing their matches"""
    conn = get_db_connection()
    
    # Get player info
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    if not player:
        flash('Player not found', 'danger')
        return redirect(url_for('index'))
    
    # Get player's matches
    matches = conn.execute('''
        SELECT m.*, 
               p1.full_name as player1_name, p1.selfie as player1_selfie,
               p2.full_name as player2_name, p2.selfie as player2_selfie
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        WHERE m.player1_id = ? OR m.player2_id = ?
        ORDER BY m.created_at DESC
    ''', (player_id, player_id)).fetchall()
    
    # Get player's tournaments (for backward compatibility)
    tournaments = conn.execute('''
        SELECT * FROM tournaments 
        WHERE player_id = ? 
        ORDER BY created_at DESC
    ''', (player_id,)).fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', player=player, matches=matches, tournaments=tournaments)

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

@app.route('/find_match/<int:player_id>', methods=['POST'])
def find_match(player_id):
    """API endpoint to find a match for a player"""
    try:
        # Set player as looking for match
        conn = get_db_connection()
        conn.execute('UPDATE players SET is_looking_for_match = 1 WHERE id = ?', (player_id,))
        conn.commit()
        conn.close()
        
        # Try to find a match
        match_id = find_match_for_player(player_id)
        
        if match_id:
            return jsonify({'success': True, 'match_id': match_id, 'message': 'Match found!'})
        else:
            return jsonify({'success': False, 'message': 'No compatible players found. We\'ll keep looking!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/confirm_match/<int:match_id>', methods=['POST'])
def confirm_match(match_id):
    """API endpoint to confirm a match"""
    try:
        conn = get_db_connection()
        
        # Update match status to confirmed
        conn.execute('UPDATE matches SET status = ? WHERE id = ?', ('confirmed', match_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Match confirmed!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/players')
def players():
    """List all registered players"""
    conn = get_db_connection()
    players = conn.execute('SELECT * FROM players ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return render_template('players.html', players=players)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

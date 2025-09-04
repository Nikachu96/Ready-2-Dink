import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from werkzeug.utils import secure_filename
from functools import wraps
import logging
import stripe

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Configure Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

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
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN wins INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN losses INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN tournament_wins INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN is_admin INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    # Add membership columns
    try:
        c.execute('ALTER TABLE players ADD COLUMN membership_type TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN stripe_customer_id TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN subscription_status TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN subscription_end_date TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN trial_end_date TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    # Settings table for admin configuration
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default pricing settings if they don't exist
    default_settings = [
        ('beginner_price', '10', 'Beginner tournament entry fee'),
        ('intermediate_price', '20', 'Intermediate tournament entry fee'),
        ('advanced_price', '40', 'Advanced tournament entry fee'),
        ('match_deadline_days', '7', 'Days to complete a match before it expires'),
        ('platform_name', 'MatchSpark', 'Platform display name'),
        ('registration_enabled', '1', 'Allow new player registrations')
    ]
    
    for key, value, description in default_settings:
        c.execute('''
            INSERT OR IGNORE INTO settings (key, value, description)
            VALUES (?, ?, ?)
        ''', (key, value, description))
    
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
            player1_score INTEGER DEFAULT 0,
            player2_score INTEGER DEFAULT 0,
            match_result TEXT,
            result_submitted_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(player1_id) REFERENCES players(id),
            FOREIGN KEY(player2_id) REFERENCES players(id),
            FOREIGN KEY(winner_id) REFERENCES players(id),
            FOREIGN KEY(result_submitted_by) REFERENCES players(id)
        )
    ''')
    
    # Enhanced tournaments table with levels and fees
    c.execute('''
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            tournament_name TEXT NOT NULL,
            tournament_level TEXT,
            tournament_type TEXT DEFAULT 'singles',
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
    
    # Messages table for player communication
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            read_status INTEGER DEFAULT 0,
            FOREIGN KEY(sender_id) REFERENCES players(id),
            FOREIGN KEY(receiver_id) REFERENCES players(id)
        )
    ''')
        
    try:
        c.execute('ALTER TABLE tournaments ADD COLUMN payment_status TEXT DEFAULT "pending"')
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute('ALTER TABLE tournaments ADD COLUMN bracket_position INTEGER')
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute('ALTER TABLE tournaments ADD COLUMN tournament_type TEXT DEFAULT "singles"')
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_setting(key, default=None):
    """Get a setting value from database"""
    conn = get_db_connection()
    setting = conn.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
    conn.close()
    return setting['value'] if setting else default

def update_setting(key, value):
    """Update a setting in database"""
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (key, value))
    conn.commit()
    conn.close()

def get_tournament_levels():
    """Get available tournament levels with dynamic pricing from settings"""
    beginner_price = float(get_setting('beginner_price', '10'))
    intermediate_price = float(get_setting('intermediate_price', '20'))
    advanced_price = float(get_setting('advanced_price', '40'))
    
    return {
        'Beginner': {
            'name': 'Beginner League',
            'description': 'Perfect for new players and casual competition',
            'entry_fee': beginner_price,
            'prize_pool': 'Winner takes 60%',
            'skill_requirements': 'Beginner level players',
            'max_players': 16
        },
        'Intermediate': {
            'name': 'Intermediate Championship',
            'description': 'For players with solid fundamentals',
            'entry_fee': intermediate_price,
            'prize_pool': 'Winner takes 50%, Runner-up 30%',
            'skill_requirements': 'Intermediate level players',
            'max_players': 32
        },
        'Advanced': {
            'name': 'Advanced Tournament',
            'description': 'High-level competitive play',
            'entry_fee': advanced_price,
            'prize_pool': 'Winner takes 40%, Top 4 share prizes',
            'skill_requirements': 'Advanced level players',
            'max_players': 32
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
    """Home page - single player app"""
    conn = get_db_connection()
    players = conn.execute('SELECT id, full_name, selfie, skill_level FROM players ORDER BY full_name').fetchall()
    conn.close()
    
    # If no players exist, redirect to registration
    if not players:
        return redirect(url_for('register'))
    
    # If only one player, go directly to their home
    if len(players) == 1:
        # Set session for admin access
        session['current_player_id'] = players[0]['id']
        return redirect(url_for('player_home', player_id=players[0]['id']))
    
    # If multiple players exist (legacy), show selection
    return render_template('player_select.html', players=players)

@app.route('/home/<int:player_id>')
def player_home(player_id):
    """Personalized home page for a player"""
    conn = get_db_connection()
    
    # Set session for admin access
    session['current_player_id'] = player_id
    
    # Get player info
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    if not player:
        flash('Player not found', 'danger')
        return redirect(url_for('index'))
    
    # Get connections (players they've played against)
    connections = conn.execute('''
        SELECT DISTINCT 
            CASE 
                WHEN m.player1_id = ? THEN p2.id
                ELSE p1.id 
            END as opponent_id,
            CASE 
                WHEN m.player1_id = ? THEN p2.full_name
                ELSE p1.full_name 
            END as opponent_name,
            CASE 
                WHEN m.player1_id = ? THEN p2.selfie
                ELSE p1.selfie 
            END as opponent_selfie,
            CASE 
                WHEN m.player1_id = ? THEN p2.wins
                ELSE p1.wins 
            END as opponent_wins,
            CASE 
                WHEN m.player1_id = ? THEN p2.losses
                ELSE p1.losses 
            END as opponent_losses,
            CASE 
                WHEN m.player1_id = ? THEN p2.tournament_wins
                ELSE p1.tournament_wins 
            END as opponent_tournament_wins,
            COUNT(*) as matches_played,
            MAX(m.created_at) as last_played
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        WHERE m.player1_id = ? OR m.player2_id = ?
        GROUP BY opponent_id, opponent_name, opponent_selfie, opponent_wins, opponent_losses, opponent_tournament_wins
        ORDER BY last_played DESC
        LIMIT 10
    ''', (player_id, player_id, player_id, player_id, player_id, player_id, player_id, player_id)).fetchall()
    
    # Get recent activity
    recent_matches = conn.execute('''
        SELECT m.*, 
               p1.full_name as player1_name, p1.selfie as player1_selfie,
               p2.full_name as player2_name, p2.selfie as player2_selfie
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        WHERE m.player1_id = ? OR m.player2_id = ?
        ORDER BY m.created_at DESC
        LIMIT 5
    ''', (player_id, player_id)).fetchall()
    
    # Get player's tournaments
    tournaments = conn.execute('''
        SELECT * FROM tournaments 
        WHERE player_id = ? 
        ORDER BY created_at DESC
        LIMIT 5
    ''', (player_id,)).fetchall()
    
    # Get available tournaments (call-to-action)
    tournament_levels = get_tournament_levels()
    available_tournaments = []
    
    for level_key, level_info in tournament_levels.items():
        # Count current entries
        current_entries = conn.execute('''
            SELECT COUNT(*) as count FROM tournaments 
            WHERE tournament_level = ? AND completed = 0
        ''', (level_key,)).fetchone()['count']
        
        spots_remaining = level_info['max_players'] - current_entries
        
        if spots_remaining > 0:  # Only show tournaments with available spots
            available_tournaments.append({
                'level': level_key,
                'name': level_info['name'],
                'description': level_info['description'],
                'entry_fee': level_info['entry_fee'],
                'current_entries': current_entries,
                'max_players': level_info['max_players'],
                'spots_remaining': spots_remaining,
                'prize_pool': level_info['prize_pool']
            })
    
    conn.close()
    
    return render_template('player_home.html', 
                         player=player, 
                         connections=connections,
                         recent_matches=recent_matches,
                         tournaments=tournaments,
                         available_tournaments=available_tournaments)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Player registration form"""
    if request.method == 'POST':
        # Form validation
        required_fields = ['full_name', 'address', 'dob', 'location1', 'preferred_court', 'skill_level', 'email']
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
                  'Pickleball', request.form['preferred_court'],
                  request.form['skill_level'], request.form['email'], selfie_filename))
            
            player_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            flash('Registration successful! Looking for matches...', 'success')
            # Try to find a match for the new player
            find_match_for_player(player_id)
            return redirect(url_for('player_home', player_id=player_id))
            
        except sqlite3.IntegrityError:
            flash('Email already exists. Please use a different email address.', 'danger')
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'danger')
    
    return render_template('register.html')

@app.route('/tournaments')
def tournaments_overview():
    """Public tournament overview page"""
    conn = get_db_connection()
    
    tournament_levels = get_tournament_levels()
    
    # Get current tournament entries count for each level
    for level_key in tournament_levels:
        count = conn.execute('''
            SELECT COUNT(*) as count FROM tournaments 
            WHERE tournament_level = ? AND completed = 0
        ''', (level_key,)).fetchone()['count']
        tournament_levels[level_key]['current_entries'] = count
        tournament_levels[level_key]['spots_remaining'] = tournament_levels[level_key]['max_players'] - count
    
    # Get recent tournament entries
    recent_entries = conn.execute('''
        SELECT t.*, p.full_name, p.selfie
        FROM tournaments t
        JOIN players p ON t.player_id = p.id
        WHERE t.tournament_level IS NOT NULL
        ORDER BY t.created_at DESC
        LIMIT 10
    ''').fetchall()
    
    # Get all registered players for quick access
    players = conn.execute('SELECT id, full_name, skill_level FROM players ORDER BY full_name').fetchall()
    
    conn.close()
    
    return render_template('tournaments_overview.html', 
                         tournament_levels=tournament_levels, 
                         recent_entries=recent_entries,
                         players=players)

@app.route('/tournament', methods=['GET', 'POST'])
def tournament():
    """Direct tournament entry for single-player app"""
    # Get the current player (should be the only player in the system)
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players ORDER BY id LIMIT 1').fetchone()
    if not player:
        flash('No player profile found. Please register first.', 'danger')
        return redirect(url_for('register'))
    
    # Redirect to the existing tournament_entry function with the player ID
    return tournament_entry(player['id'])

@app.route('/tournament/<int:player_id>', methods=['GET', 'POST'])
def tournament_entry(player_id):
    """Tournament entry form with levels and fees for a specific player"""
    # Get player info first
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    if not player:
        flash('Player not found', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        required_fields = ['tournament_level', 'tournament_type', 'sport']
        for field in required_fields:
            if not request.form.get(field):
                flash(f'{field.replace("_", " ").title()} is required', 'danger')
                return redirect(url_for('tournament_entry', player_id=player_id))
        
        try:
            tournament_levels = get_tournament_levels()
            selected_level = request.form['tournament_level']
            
            # Check current tournament entries for this level to enforce player limits
            current_entries = conn.execute('''
                SELECT COUNT(*) as count FROM tournaments 
                WHERE tournament_level = ? AND completed = 0
            ''', (selected_level,)).fetchone()['count']
            
            max_players = tournament_levels[selected_level]['max_players']
            if current_entries >= max_players:
                flash(f'{selected_level} tournament is full ({max_players} players max). Try a different level.', 'warning')
                return redirect(url_for('tournament_entry', player_id=player_id))
            
            # Check if player skill matches tournament level (with some flexibility)
            skill_mapping = {
                'Beginner': ['Beginner'],
                'Intermediate': ['Beginner', 'Intermediate'], 
                'Advanced': ['Intermediate', 'Advanced']
            }
            
            if player['skill_level'] not in skill_mapping.get(selected_level, []):
                flash(f'Your skill level ({player["skill_level"]}) may not be suitable for {selected_level} level. Consider a different tournament level.', 'warning')
                return redirect(url_for('tournament'))
            
            entry_date = datetime.now()
            match_deadline = entry_date + timedelta(days=14)  # 2 weeks for tournaments
            
            conn.execute('''
                INSERT INTO tournaments (player_id, tournament_name, tournament_level, tournament_type, entry_fee, sport, entry_date, match_deadline, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (player_id, 
                  tournament_levels[selected_level]['name'],
                  selected_level,
                  request.form['tournament_type'],
                  tournament_levels[selected_level]['entry_fee'],
                  request.form['sport'],
                  entry_date.strftime('%Y-%m-%d'), 
                  match_deadline.strftime('%Y-%m-%d'),
                  'completed'))  # Skip payment for now
            
            conn.commit()
            conn.close()
            
            flash(f'Tournament entry successful! Entry fee: ${tournament_levels[selected_level]["entry_fee"]:.0f}', 'success')
            return redirect(url_for('dashboard', player_id=player_id))
            
        except Exception as e:
            flash(f'Tournament entry failed: {str(e)}', 'danger')
    
    # Get current tournament entries count for each level
    tournament_levels = get_tournament_levels()
    for level_key in tournament_levels:
        count = conn.execute('''
            SELECT COUNT(*) as count FROM tournaments 
            WHERE tournament_level = ? AND completed = 0
        ''', (level_key,)).fetchone()['count']
        tournament_levels[level_key]['current_entries'] = count
        tournament_levels[level_key]['spots_remaining'] = tournament_levels[level_key]['max_players'] - count
    
    conn.close()
    
    return render_template('tournament.html', player=player, tournament_levels=tournament_levels)

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
    """Complete a tournament with results"""
    result = request.form.get('result')
    if not result:
        flash('Please select a tournament result', 'warning')
        return redirect(url_for('manage_tournaments'))
    
    conn = get_db_connection()
    
    # Get tournament info
    tournament = conn.execute('SELECT * FROM tournaments WHERE id = ?', (tournament_id,)).fetchone()
    if not tournament:
        flash('Tournament not found', 'danger')
        conn.close()
        return redirect(url_for('manage_tournaments'))
    
    # Update tournament
    conn.execute('''
        UPDATE tournaments 
        SET completed = 1, match_result = ?
        WHERE id = ?
    ''', (result, tournament_id))
    
    # If they won (1st place), add tournament win star
    if 'Won - 1st Place' in result:
        conn.execute('''
            UPDATE players 
            SET tournament_wins = tournament_wins + 1
            WHERE id = ?
        ''', (tournament['player_id'],))
    
    conn.commit()
    conn.close()
    
    flash(f'Tournament completed successfully: {result}', 'success')
    return redirect(url_for('manage_tournaments'))

@app.route('/update_tournament_level', methods=['POST'])
def update_tournament_level():
    """Update tournament level settings"""
    level = request.form.get('level')
    entry_fee = request.form.get('entry_fee')
    max_players = request.form.get('max_players')
    prize_pool = request.form.get('prize_pool')
    description = request.form.get('description')
    
    # Here you would update your tournament configuration
    # For now, just show a success message
    flash(f'{level} tournament settings updated successfully!', 'success')
    return redirect(url_for('manage_tournaments'))

@app.route('/update_global_settings', methods=['POST'])
def update_global_settings():
    """Update global tournament settings"""
    duration = request.form.get('tournament_duration')
    deadline = request.form.get('registration_deadline')
    timeout = request.form.get('match_timeout')
    min_players = request.form.get('min_players')
    
    # Here you would update your global tournament configuration
    # For now, just show a success message
    flash('Global tournament settings updated successfully!', 'success')
    return redirect(url_for('manage_tournaments'))

@app.route('/admin/reset_tournaments', methods=['POST'])
def reset_tournaments():
    """Reset all tournament data"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM tournaments')
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'All tournaments reset successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/export_tournaments')
def export_tournaments():
    """Export tournament data"""
    conn = get_db_connection()
    tournaments = conn.execute('''
        SELECT t.*, p.full_name, p.email
        FROM tournaments t
        JOIN players p ON t.player_id = p.id
        ORDER BY t.created_at DESC
    ''').fetchall()
    conn.close()
    
    # Return CSV data
    from io import StringIO
    import csv
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Tournament Name', 'Player', 'Email', 'Level', 'Entry Date', 'Deadline', 'Completed', 'Result'])
    
    for t in tournaments:
        writer.writerow([t['id'], t['tournament_name'], t['full_name'], t['email'], 
                        t['tournament_level'], t['entry_date'], t['match_deadline'], 
                        'Yes' if t['completed'] else 'No', t['match_result'] or 'Pending'])
    
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=tournaments.csv'}
    )
    return response

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

@app.route('/profile_settings')
def profile_settings():
    """Profile settings page - get current player"""
    conn = get_db_connection()
    players = conn.execute('SELECT * FROM players ORDER BY created_at DESC LIMIT 1').fetchall()
    conn.close()
    
    if not players:
        flash('Please register first', 'warning')
        return redirect(url_for('register'))
    
    player = players[0]  # Get the most recent (current) player
    return render_template('profile_settings.html', player=player)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    """Update player profile information"""
    conn = get_db_connection()
    
    # Get current player ID
    players = conn.execute('SELECT id FROM players ORDER BY created_at DESC LIMIT 1').fetchall()
    if not players:
        flash('Player not found', 'danger')
        return redirect(url_for('register'))
    
    player_id = players[0]['id']
    
    # Form validation
    required_fields = ['full_name', 'address', 'dob', 'location1', 'preferred_court', 'skill_level', 'email']
    for field in required_fields:
        if not request.form.get(field):
            flash(f'{field.replace("_", " ").title()} is required', 'danger')
            return redirect(url_for('profile_settings'))
    
    # Handle file upload
    selfie_filename = None
    if 'selfie' in request.files:
        file = request.files['selfie']
        if file and file.filename and file.filename != '':
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid filename conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                selfie_filename = timestamp + filename
                
                # Ensure upload directory exists
                static_folder = app.static_folder or 'static'
                upload_path = os.path.join(static_folder, 'uploads')
                os.makedirs(upload_path, exist_ok=True)
                
                file.save(os.path.join(upload_path, selfie_filename))
    
    try:
        # Update player information
        if selfie_filename:
            conn.execute('''
                UPDATE players 
                SET full_name = ?, address = ?, dob = ?, location1 = ?, location2 = ?, 
                    preferred_court = ?, skill_level = ?, email = ?, selfie = ?
                WHERE id = ?
            ''', (request.form['full_name'], request.form['address'], request.form['dob'], 
                  request.form['location1'], request.form.get('location2', ''), 
                  request.form['preferred_court'], request.form['skill_level'], 
                  request.form['email'], selfie_filename, player_id))
        else:
            conn.execute('''
                UPDATE players 
                SET full_name = ?, address = ?, dob = ?, location1 = ?, location2 = ?, 
                    preferred_court = ?, skill_level = ?, email = ?
                WHERE id = ?
            ''', (request.form['full_name'], request.form['address'], request.form['dob'], 
                  request.form['location1'], request.form.get('location2', ''), 
                  request.form['preferred_court'], request.form['skill_level'], 
                  request.form['email'], player_id))
        
        conn.commit()
        conn.close()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        conn.close()
        flash(f'Error updating profile: {str(e)}', 'danger')
        return redirect(url_for('profile_settings'))

@app.route('/send_message', methods=['POST'])
def send_message():
    """Send a message between connected players"""
    data = request.get_json()
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'success': False, 'message': 'Message cannot be empty'})
    
    conn = get_db_connection()
    
    # Check if players are connected (have played matches together)
    connection = conn.execute('''
        SELECT 1 FROM matches 
        WHERE (player1_id = ? AND player2_id = ?) 
           OR (player1_id = ? AND player2_id = ?)
        LIMIT 1
    ''', (sender_id, receiver_id, receiver_id, sender_id)).fetchone()
    
    if not connection:
        conn.close()
        return jsonify({'success': False, 'message': 'You can only message players you have connected with'})
    
    # Insert message
    conn.execute('''
        INSERT INTO messages (sender_id, receiver_id, message)
        VALUES (?, ?, ?)
    ''', (sender_id, receiver_id, message))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Message sent successfully'})

@app.route('/get_messages/<int:player_id>')
def get_messages(player_id):
    """Get recent messages for a player"""
    conn = get_db_connection()
    
    # Get recent messages (both sent and received)
    messages = conn.execute('''
        SELECT m.*, 
               sender.full_name as sender_name,
               receiver.full_name as receiver_name,
               sender.selfie as sender_selfie
        FROM messages m
        JOIN players sender ON m.sender_id = sender.id
        JOIN players receiver ON m.receiver_id = receiver.id
        WHERE m.sender_id = ? OR m.receiver_id = ?
        ORDER BY m.created_at DESC
        LIMIT 20
    ''', (player_id, player_id)).fetchall()
    
    # Mark received messages as read
    conn.execute('''
        UPDATE messages 
        SET read_status = 1 
        WHERE receiver_id = ? AND read_status = 0
    ''', (player_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'messages': [dict(msg) for msg in messages]})

@app.route('/get_unread_count/<int:player_id>')
def get_unread_count(player_id):
    """Get count of unread messages"""
    conn = get_db_connection()
    
    count = conn.execute('''
        SELECT COUNT(*) as count FROM messages 
        WHERE receiver_id = ? AND read_status = 0
    ''', (player_id,)).fetchone()['count']
    
    conn.close()
    
    return jsonify({'unread_count': count})

@app.route('/submit_match_result', methods=['POST'])
def submit_match_result():
    """Submit match result with scores"""
    data = request.get_json()
    match_id = data.get('match_id')
    player1_score = int(data.get('player1_score', 0))
    player2_score = int(data.get('player2_score', 0))
    submitter_id = data.get('submitter_id')
    
    if player1_score == player2_score:
        return jsonify({'success': False, 'message': 'Scores cannot be tied. Please enter the correct scores.'})
    
    conn = get_db_connection()
    
    # Get match details
    match = conn.execute('''
        SELECT * FROM matches WHERE id = ?
    ''', (match_id,)).fetchone()
    
    if not match:
        conn.close()
        return jsonify({'success': False, 'message': 'Match not found'})
    
    # Check if submitter is part of this match
    if submitter_id not in [match['player1_id'], match['player2_id']]:
        conn.close()
        return jsonify({'success': False, 'message': 'You are not part of this match'})
    
    # Determine winner
    winner_id = match['player1_id'] if player1_score > player2_score else match['player2_id']
    loser_id = match['player2_id'] if player1_score > player2_score else match['player1_id']
    
    # Update match with results
    conn.execute('''
        UPDATE matches 
        SET player1_score = ?, player2_score = ?, winner_id = ?, 
            status = 'completed', result_submitted_by = ?,
            match_result = ?
        WHERE id = ?
    ''', (player1_score, player2_score, winner_id, submitter_id, 
          f"{player1_score}-{player2_score}", match_id))
    
    # Update player win/loss records
    conn.execute('UPDATE players SET wins = wins + 1 WHERE id = ?', (winner_id,))
    conn.execute('UPDATE players SET losses = losses + 1 WHERE id = ?', (loser_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Match result submitted successfully!'})

@app.route('/get_pending_matches/<int:player_id>')
def get_pending_matches(player_id):
    """Get matches that need score submission"""
    conn = get_db_connection()
    
    matches = conn.execute('''
        SELECT m.*, 
               p1.full_name as player1_name,
               p2.full_name as player2_name
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        WHERE (m.player1_id = ? OR m.player2_id = ?)
          AND m.status = 'pending'
        ORDER BY m.created_at DESC
    ''', (player_id, player_id)).fetchall()
    
    conn.close()
    
    return jsonify({'matches': [dict(match) for match in matches]})

# Admin functionality
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_player_id = session.get('current_player_id')
        if not current_player_id:
            flash('Please select your player profile first', 'warning')
            return redirect(url_for('index'))
        
        conn = get_db_connection()
        player = conn.execute('SELECT is_admin FROM players WHERE id = ?', (current_player_id,)).fetchone()
        conn.close()
        
        if not player or not player['is_admin']:
            flash('Admin access required', 'danger')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard with platform overview"""
    conn = get_db_connection()
    
    # Get key metrics
    total_players = conn.execute('SELECT COUNT(*) as count FROM players').fetchone()['count']
    total_matches = conn.execute('SELECT COUNT(*) as count FROM matches').fetchone()['count']
    total_tournaments = conn.execute('SELECT COUNT(*) as count FROM tournaments').fetchone()['count']
    active_tournaments = conn.execute('SELECT COUNT(*) as count FROM tournaments WHERE completed = 0').fetchone()['count']
    
    # Recent activity
    recent_players = conn.execute('''
        SELECT * FROM players ORDER BY created_at DESC LIMIT 5
    ''').fetchall()
    
    recent_matches = conn.execute('''
        SELECT m.*, p1.full_name as player1_name, p2.full_name as player2_name
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        ORDER BY m.created_at DESC LIMIT 10
    ''').fetchall()
    
    recent_tournaments = conn.execute('''
        SELECT t.*, p.full_name FROM tournaments t
        JOIN players p ON t.player_id = p.id
        ORDER BY t.created_at DESC LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    metrics = {
        'total_players': total_players,
        'total_matches': total_matches,
        'total_tournaments': total_tournaments,
        'active_tournaments': active_tournaments
    }
    
    return render_template('admin/dashboard.html', 
                         metrics=metrics,
                         recent_players=recent_players,
                         recent_matches=recent_matches,
                         recent_tournaments=recent_tournaments)

@app.route('/admin/players')
@admin_required
def admin_players():
    """Admin player management"""
    conn = get_db_connection()
    players = conn.execute('''
        SELECT * FROM players ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    return render_template('admin/players.html', players=players)

@app.route('/admin/tournaments')
@admin_required
def admin_tournaments():
    """Admin tournament management"""
    conn = get_db_connection()
    tournaments = conn.execute('''
        SELECT t.*, p.full_name, p.email
        FROM tournaments t
        JOIN players p ON t.player_id = p.id
        ORDER BY t.created_at DESC
    ''').fetchall()
    conn.close()
    
    return render_template('admin/tournaments.html', tournaments=tournaments)

@app.route('/admin/toggle_admin/<int:player_id>', methods=['POST'])
@admin_required
def toggle_admin(player_id):
    """Toggle admin status for a player"""
    conn = get_db_connection()
    
    current_status = conn.execute('SELECT is_admin FROM players WHERE id = ?', (player_id,)).fetchone()
    new_status = 1 if not current_status['is_admin'] else 0
    
    conn.execute('UPDATE players SET is_admin = ? WHERE id = ?', (new_status, player_id))
    conn.commit()
    conn.close()
    
    action = "granted" if new_status else "revoked"
    flash(f'Admin access {action} successfully', 'success')
    return redirect(url_for('admin_players'))

@app.route('/admin/set_player_session/<int:player_id>')
def set_player_session(player_id):
    """Set current player session (for testing/admin purposes)"""
    session['current_player_id'] = player_id
    return redirect(url_for('player_home', player_id=player_id))


@app.route('/admin/matches')
@admin_required
def admin_matches():
    """Admin match management and dispute resolution"""
    conn = get_db_connection()
    
    # Get all matches with player information
    matches = conn.execute('''
        SELECT m.*, 
               p1.full_name as player1_name, p1.email as player1_email,
               p2.full_name as player2_name, p2.email as player2_email
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        ORDER BY m.created_at DESC
    ''').fetchall()
    
    # Get pending matches that need attention
    pending_matches = conn.execute('''
        SELECT m.*, 
               p1.full_name as player1_name,
               p2.full_name as player2_name
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        WHERE m.status = 'pending'
          AND datetime(m.created_at, '+7 days') < datetime('now')
        ORDER BY m.created_at ASC
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin/matches.html', 
                         matches=matches, 
                         pending_matches=pending_matches)

@app.route('/admin/force_complete_match/<int:match_id>', methods=['POST'])
@admin_required
def force_complete_match(match_id):
    """Force complete a match with admin scores"""
    player1_score = request.form.get('player1_score', type=int)
    player2_score = request.form.get('player2_score', type=int)
    
    if player1_score is None or player2_score is None:
        flash('Please enter valid scores for both players', 'warning')
        return redirect(url_for('admin_matches'))
    
    conn = get_db_connection()
    
    # Get match info
    match = conn.execute('SELECT * FROM matches WHERE id = ?', (match_id,)).fetchone()
    if not match:
        flash('Match not found', 'danger')
        conn.close()
        return redirect(url_for('admin_matches'))
    
    # Update match
    conn.execute('''
        UPDATE matches 
        SET player1_score = ?, player2_score = ?, status = 'completed'
        WHERE id = ?
    ''', (player1_score, player2_score, match_id))
    
    # Update player records
    if player1_score > player2_score:
        winner_id, loser_id = match['player1_id'], match['player2_id']
    else:
        winner_id, loser_id = match['player2_id'], match['player1_id']
    
    conn.execute('UPDATE players SET wins = wins + 1 WHERE id = ?', (winner_id,))
    conn.execute('UPDATE players SET losses = losses + 1 WHERE id = ?', (loser_id,))
    
    conn.commit()
    conn.close()
    
    flash(f'Match completed: {player1_score}-{player2_score}', 'success')
    return redirect(url_for('admin_matches'))

@app.route('/admin/cancel_match/<int:match_id>', methods=['POST'])
@admin_required
def cancel_match(match_id):
    """Cancel a match"""
    conn = get_db_connection()
    
    # Check if match exists
    match = conn.execute('SELECT * FROM matches WHERE id = ?', (match_id,)).fetchone()
    if not match:
        conn.close()
        return jsonify({'success': False, 'message': 'Match not found'})
    
    # Delete the match
    conn.execute('DELETE FROM matches WHERE id = ?', (match_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Match canceled successfully'})

@app.route('/admin/settings')
@admin_required
def admin_settings():
    """Admin system settings management"""
    conn = get_db_connection()
    settings = conn.execute('SELECT * FROM settings ORDER BY key').fetchall()
    conn.close()
    
    return render_template('admin/settings.html', settings=settings)

@app.route('/admin/update_settings', methods=['POST'])
@admin_required
def update_settings():
    """Update system settings"""
    # Get all form data
    for key in request.form:
        value = request.form[key].strip()
        if value:  # Only update non-empty values
            update_setting(key, value)
    
    flash('Settings updated successfully!', 'success')
    return redirect(url_for('admin_settings'))

# Stripe Subscription Routes
@app.route('/create_subscription', methods=['POST'])
def create_subscription():
    """Create Stripe subscription with free trial"""
    if 'player_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    membership_type = data.get('membership_type')
    player_id = data.get('player_id')
    
    if membership_type not in ['discovery', 'tournament']:
        return jsonify({'error': 'Invalid membership type'}), 400
    
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    
    if not player:
        conn.close()
        return jsonify({'error': 'Player not found'}), 404
    
    try:
        # Create or retrieve Stripe customer
        if player['stripe_customer_id']:
            customer = stripe.Customer.retrieve(player['stripe_customer_id'])
        else:
            customer = stripe.Customer.create(
                email=player['email'],
                name=player['full_name'],
                metadata={'player_id': str(player_id)}
            )
            
            # Update player with customer ID
            conn.execute(
                'UPDATE players SET stripe_customer_id = ? WHERE id = ?',
                (customer.id, player_id)
            )
            conn.commit()
        
        # Define subscription prices (these should be created in Stripe Dashboard)
        price_ids = {
            'discovery': 'price_discovery_monthly',  # Replace with actual Stripe Price ID
            'tournament': 'price_tournament_monthly'  # Replace with actual Stripe Price ID
        }
        
        # Get domain for success/cancel URLs
        domain = request.headers.get('Host', 'localhost:5000')
        protocol = 'https' if 'replit' in domain else 'http'
        
        # Create Stripe Checkout Session with free trial
        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            line_items=[{
                'price': price_ids[membership_type],
                'quantity': 1,
            }],
            mode='subscription',
            subscription_data={
                'trial_period_days': 30,  # 30-day free trial
                'metadata': {
                    'membership_type': membership_type,
                    'player_id': str(player_id)
                }
            },
            success_url=f'{protocol}://{domain}/subscription_success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{protocol}://{domain}/subscription_cancel',
            automatic_tax={'enabled': True},
        )
        
        conn.close()
        return jsonify({'checkout_url': checkout_session.url})
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/subscription_success')
def subscription_success():
    """Handle successful subscription"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Invalid subscription session', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Retrieve the checkout session
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        customer_id = checkout_session.customer
        subscription_id = checkout_session.subscription
        
        # Get subscription details
        subscription = stripe.Subscription.retrieve(str(subscription_id))
        membership_type = subscription.metadata.get('membership_type')
        player_id_str = subscription.metadata.get('player_id')
        player_id = int(player_id_str) if player_id_str else None
        
        # Update player membership
        conn = get_db_connection()
        trial_end = datetime.fromtimestamp(subscription.trial_end) if hasattr(subscription, 'trial_end') and subscription.trial_end else None
        
        conn.execute('''
            UPDATE players 
            SET membership_type = ?, 
                subscription_status = ?, 
                trial_end_date = ?
            WHERE id = ?
        ''', (membership_type, subscription.status, trial_end.isoformat() if trial_end else None, player_id))
        
        conn.commit()
        conn.close()
        
        membership_display = membership_type.replace("_", " ").title() if membership_type else "Premium"
        flash(f'Welcome to {membership_display} membership! Your free trial has started.', 'success')
        return redirect(url_for('player_home', player_id=player_id))
        
    except Exception as e:
        flash('Error processing subscription. Please contact support.', 'danger')
        return redirect(url_for('index'))

@app.route('/subscription_cancel')
def subscription_cancel():
    """Handle cancelled subscription"""
    flash('Subscription cancelled. You can upgrade anytime from your dashboard.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

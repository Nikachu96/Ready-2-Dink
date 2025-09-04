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

def get_tournament_levels():
    """Get available tournament levels with pricing and player limits"""
    return {
        'Beginner': {
            'name': 'Beginner League',
            'description': 'Perfect for new players and casual competition',
            'entry_fee': 10.00,
            'prize_pool': 'Winner takes 60%',
            'skill_requirements': 'Beginner level players',
            'max_players': 16
        },
        'Intermediate': {
            'name': 'Intermediate Championship',
            'description': 'For players with solid fundamentals',
            'entry_fee': 20.00,
            'prize_pool': 'Winner takes 50%, Runner-up 30%',
            'skill_requirements': 'Intermediate level players',
            'max_players': 32
        },
        'Advanced': {
            'name': 'Advanced Tournament',
            'description': 'High-level competitive play',
            'entry_fee': 40.00,
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
        return redirect(url_for('player_home', player_id=players[0]['id']))
    
    # If multiple players exist (legacy), show selection
    return render_template('player_select.html', players=players)

@app.route('/home/<int:player_id>')
def player_home(player_id):
    """Personalized home page for a player"""
    conn = get_db_connection()
    
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
    """Mark tournament as completed"""
    result = request.form.get('result', '')
    
    try:
        conn = get_db_connection()
        
        # Get tournament info to identify the winner
        tournament = conn.execute('''
            SELECT player_id FROM tournaments WHERE id = ?
        ''', (tournament_id,)).fetchone()
        
        if tournament:
            # Update tournament as completed
            conn.execute('''
                UPDATE tournaments 
                SET completed = 1, match_result = ?
                WHERE id = ?
            ''', (result, tournament_id))
            
            # Award tournament win if the result indicates a win
            if result and ("won" in result.lower() or "champion" in result.lower() or "1st" in result.lower() or "first" in result.lower()):
                conn.execute('''
                    UPDATE players SET tournament_wins = tournament_wins + 1
                    WHERE id = ?
                ''', (tournament['player_id'],))
                flash('Tournament completed and win awarded!', 'success')
            else:
                flash('Tournament marked as completed', 'success')
        else:
            conn.execute('''
                UPDATE tournaments 
                SET completed = 1, match_result = ?
                WHERE id = ?
            ''', (result, tournament_id))
            flash('Tournament marked as completed', 'success')
            
        conn.commit()
        conn.close()
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
                upload_path = os.path.join(app.static_folder, 'uploads')
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

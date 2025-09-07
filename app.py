import os
import sqlite3
import json
import requests
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

# Add custom Jinja filter for JSON parsing
def from_json_filter(value):
    """Custom Jinja filter to parse JSON strings"""
    try:
        return json.loads(value) if value else {}
    except:
        return {}

app.jinja_env.filters['from_json'] = from_json_filter

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

def require_disclaimers_accepted(f):
    """Decorator to ensure player has accepted disclaimers before accessing routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract player_id from URL parameters
        player_id = kwargs.get('player_id') or request.form.get('player_id')
        
        if player_id:
            conn = get_db_connection()
            player = conn.execute('SELECT disclaimers_accepted FROM players WHERE id = ?', (player_id,)).fetchone()
            conn.close()
            
            if player and not player['disclaimers_accepted']:
                flash('Please accept our terms and disclaimers to continue using Ready 2 Dink', 'warning')
                return redirect(url_for('show_disclaimers', player_id=player_id))
        
        return f(*args, **kwargs)
    return decorated_function

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
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN disclaimers_accepted INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN tournament_rules_accepted INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN ranking_points INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN push_subscription TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN notifications_enabled INTEGER DEFAULT 1')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN free_tournament_entries INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    # Add availability columns
    try:
        c.execute('ALTER TABLE players ADD COLUMN availability_schedule TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN time_preference TEXT DEFAULT "Flexible"')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    # Add preferred court columns (replacing location fields)
    try:
        c.execute('ALTER TABLE players ADD COLUMN preferred_court_1 TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN preferred_court_2 TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN court1_coordinates TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN court2_coordinates TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE matches ADD COLUMN notification_sent INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE tournaments ADD COLUMN tournament_notification_sent INTEGER DEFAULT 0')
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
        ('platform_name', 'Ready 2 Dink', 'Platform display name'),
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
    # Create tournament instances table (defines individual tournaments)
    c.execute('''
        CREATE TABLE IF NOT EXISTS tournament_instances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            skill_level TEXT NOT NULL,
            entry_fee REAL NOT NULL,
            max_players INTEGER DEFAULT 32,
            current_players INTEGER DEFAULT 0,
            status TEXT DEFAULT 'open',
            start_date TEXT,
            end_date TEXT,
            winner_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(winner_id) REFERENCES players(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            tournament_instance_id INTEGER NOT NULL,
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
            FOREIGN KEY(player_id) REFERENCES players(id),
            FOREIGN KEY(tournament_instance_id) REFERENCES tournament_instances(id)
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
    
    # Tournament matches table for bracket management
    c.execute('''
        CREATE TABLE IF NOT EXISTS tournament_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_instance_id INTEGER NOT NULL,
            round_number INTEGER NOT NULL,
            match_number INTEGER NOT NULL,
            player1_id INTEGER,
            player2_id INTEGER,
            winner_id INTEGER,
            player1_score TEXT,
            player2_score TEXT,
            status TEXT DEFAULT 'pending',
            scheduled_date TEXT,
            completed_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tournament_instance_id) REFERENCES tournament_instances(id),
            FOREIGN KEY(player1_id) REFERENCES players(id),
            FOREIGN KEY(player2_id) REFERENCES players(id),
            FOREIGN KEY(winner_id) REFERENCES players(id)
        )
    ''')
    
    # Ambassador program table
    c.execute('''
        CREATE TABLE IF NOT EXISTS ambassadors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL UNIQUE,
            referral_code TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'active',
            referrals_count INTEGER DEFAULT 0,
            qualified_referrals INTEGER DEFAULT 0,
            lifetime_membership_granted INTEGER DEFAULT 0,
            state_territory TEXT,
            application_date TEXT DEFAULT CURRENT_TIMESTAMP,
            qualification_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
    ''')
    
    # Ambassador referrals tracking table
    c.execute('''
        CREATE TABLE IF NOT EXISTS ambassador_referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ambassador_id INTEGER NOT NULL,
            referred_player_id INTEGER NOT NULL,
            referral_code TEXT NOT NULL,
            membership_type TEXT,
            qualified INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            qualified_at TEXT,
            FOREIGN KEY(ambassador_id) REFERENCES ambassadors(id),
            FOREIGN KEY(referred_player_id) REFERENCES players(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection with row factory and timeout"""
    conn = sqlite3.connect('app.db', timeout=20.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrent access
    conn.execute('PRAGMA journal_mode=WAL')
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

def award_points(player_id, points, reason):
    """Award points to a player and log the reason"""
    conn = get_db_connection()
    
    # Update player's points
    conn.execute('''
        UPDATE players 
        SET ranking_points = ranking_points + ?
        WHERE id = ?
    ''', (points, player_id))
    
    conn.commit()
    conn.close()
    
    # Log the point award for debugging
    logging.info(f"Awarded {points} points to player {player_id} for {reason}")

def get_tournament_points(result):
    """Get points based on tournament result"""
    points_map = {
        'Winner (1st Place)': 400,
        'Runner-up (2nd Place)': 200,
        'Semi-finalist (3rd/4th Place)': 100,
        'Quarter-finalist': 40
    }
    
    # Handle variations in result strings
    for key, points in points_map.items():
        if key.lower() in result.lower():
            return points
    
    # Handle specific result formats
    if '1st' in result or 'winner' in result.lower() or 'won' in result.lower():
        return 400
    elif '2nd' in result or 'runner' in result.lower():
        return 200
    elif '3rd' in result or '4th' in result or 'semi' in result.lower():
        return 100
    elif 'quarter' in result.lower():
        return 40
    
    return 0  # No points for early elimination

def get_player_ranking(player_id):
    """Get player's current ranking position"""
    conn = get_db_connection()
    
    # Get all players ordered by points (descending), then by wins
    players = conn.execute('''
        SELECT id, ranking_points, wins
        FROM players 
        WHERE ranking_points > 0 OR wins > 0
        ORDER BY ranking_points DESC, wins DESC
    ''').fetchall()
    
    conn.close()
    
    # Find player's position
    for rank, player in enumerate(players, 1):
        if player['id'] == player_id:
            return rank
    
    return None  # Player not ranked yet

def get_leaderboard(limit=10):
    """Get top players by ranking points"""
    conn = get_db_connection()
    
    leaderboard = conn.execute('''
        SELECT id, full_name, ranking_points, wins, losses, tournament_wins, selfie
        FROM players 
        WHERE ranking_points > 0 OR wins > 0
        ORDER BY ranking_points DESC, wins DESC, losses ASC
        LIMIT ?
    ''', (limit,)).fetchall()
    
    conn.close()
    
    return leaderboard

def is_player_birthday(player_dob):
    """Check if it's the player's birthday today"""
    if not player_dob:
        return False
    
    try:
        # Parse the date in MM-DD-YYYY format
        from datetime import datetime
        today = datetime.now()
        
        # Try to parse the date in MM-DD-YYYY format first
        try:
            birthday = datetime.strptime(player_dob, '%m-%d-%Y')
        except ValueError:
            # Fallback to YYYY-MM-DD format if that's how it's stored
            birthday = datetime.strptime(player_dob, '%Y-%m-%d')
        
        # Check if month and day match today
        return today.month == birthday.month and today.day == birthday.day
    except Exception:
        return False

def perform_annual_points_reset():
    """Perform annual ranking points reset while maintaining lifetime rankings"""
    from datetime import datetime
    conn = get_db_connection()
    
    # First, update lifetime rankings based on current performance
    update_lifetime_rankings()
    
    # Reset all ranking points to 0
    conn.execute('UPDATE players SET ranking_points = 0')
    
    # Update reset timestamp for all players
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute('UPDATE players SET last_points_reset = ?', (current_time,))
    
    conn.commit()
    conn.close()
    
    logging.info("Annual ranking points reset completed")
    return True

def update_lifetime_rankings():
    """Update lifetime rankings based on current achievements"""
    conn = get_db_connection()
    
    # Get all players ordered by current performance
    players = conn.execute('''
        SELECT id, ranking_points, wins, tournament_wins, career_high_points
        FROM players 
        ORDER BY ranking_points DESC, tournament_wins DESC, wins DESC
    ''').fetchall()
    
    # Update lifetime rankings and career high points
    for rank, player in enumerate(players, 1):
        current_points = player['ranking_points'] or 0
        career_high = player['career_high_points'] or 0
        
        # Update career high if current points are higher
        new_career_high = max(current_points, career_high)
        
        conn.execute('''
            UPDATE players 
            SET lifetime_ranking = ?, career_high_points = ?
            WHERE id = ?
        ''', (rank, new_career_high, player['id']))
    
    conn.commit()
    conn.close()
    
    logging.info("Lifetime rankings updated")

def check_annual_reset_needed():
    """Check if annual reset is needed (call this periodically)"""
    from datetime import datetime
    conn = get_db_connection()
    
    # Check if we're in January and no reset has happened this year
    current_year = datetime.now().year
    
    # Get the most recent reset date
    last_reset = conn.execute('''
        SELECT last_points_reset FROM players 
        WHERE last_points_reset IS NOT NULL 
        ORDER BY last_points_reset DESC 
        LIMIT 1
    ''').fetchone()
    
    conn.close()
    
    if last_reset:
        last_reset_year = datetime.strptime(last_reset['last_points_reset'], '%Y-%m-%d %H:%M:%S').year
        if current_year > last_reset_year and datetime.now().month == 1:
            return True
    elif datetime.now().month == 1:  # No reset has ever happened and it's January
        return True
    
    return False

def get_player_ranking_with_lifetime(player_id):
    """Get both current and lifetime ranking for a player"""
    current_ranking = get_player_ranking(player_id)
    
    conn = get_db_connection()
    player = conn.execute('''
        SELECT lifetime_ranking, career_high_points, last_points_reset
        FROM players 
        WHERE id = ?
    ''', (player_id,)).fetchone()
    conn.close()
    
    return {
        'current_ranking': current_ranking,
        'lifetime_ranking': player['lifetime_ranking'] if player else None,
        'career_high_points': player['career_high_points'] if player else 0,
        'last_reset': player['last_points_reset'] if player else None
    }

def send_push_notification(player_id, message, title="Ready 2 Dink"):
    """Send push notification to a player"""
    conn = get_db_connection()
    
    player = conn.execute('''
        SELECT push_subscription, notifications_enabled, full_name
        FROM players 
        WHERE id = ? AND notifications_enabled = 1 AND push_subscription IS NOT NULL
    ''', (player_id,)).fetchone()
    
    conn.close()
    
    if not player or not player['push_subscription']:
        logging.info(f"No push subscription found for player {player_id}")
        return False
    
    try:
        subscription_info = json.loads(player['push_subscription'])
        
        # For demo purposes, we'll simulate sending a notification
        # In production, you would use a service like Firebase Cloud Messaging
        logging.info(f"Sending push notification to {player['full_name']}: {message}")
        
        # Here you would implement actual push notification sending
        # using a service like Firebase, OneSignal, or Web Push Protocol
        
        return True
    except Exception as e:
        logging.error(f"Failed to send push notification: {e}")
        return False

def schedule_match_notifications():
    """Send notifications for upcoming matches"""
    conn = get_db_connection()
    
    # Get matches happening in the next 2 hours
    upcoming_time = datetime.now() + timedelta(hours=2)
    
    matches = conn.execute('''
        SELECT m.*, p1.full_name as player1_name, p2.full_name as player2_name,
               p1.id as player1_id, p2.id as player2_id
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        WHERE m.status = 'pending' 
        AND m.match_date <= ? 
        AND m.match_date >= ?
        AND m.notification_sent != 1
    ''', (upcoming_time.strftime('%Y-%m-%d %H:%M'), 
          datetime.now().strftime('%Y-%m-%d %H:%M'))).fetchall()
    
    for match in matches:
        # Send notification to both players
        message1 = f"Your match with {match['player2_name']} is starting soon!"
        message2 = f"Your match with {match['player1_name']} is starting soon!"
        
        send_push_notification(match['player1_id'], message1, "Match Reminder")
        send_push_notification(match['player2_id'], message2, "Match Reminder")
        
        # Mark notification as sent
        conn.execute('''
            UPDATE matches SET notification_sent = 1 WHERE id = ?
        ''', (match['id'],))
    
    conn.commit()
    conn.close()

def schedule_tournament_notifications():
    """Send notifications for tournament updates"""
    conn = get_db_connection()
    
    # Get tournaments that are starting soon
    upcoming_time = datetime.now() + timedelta(hours=24)
    
    tournaments = conn.execute('''
        SELECT t.*, p.full_name, p.id as player_id, ti.name as tournament_name
        FROM tournaments t
        JOIN players p ON t.player_id = p.id
        JOIN tournament_instances ti ON t.tournament_instance_id = ti.id
        WHERE t.completed = 0 
        AND t.match_deadline <= ?
        AND t.tournament_notification_sent != 1
    ''', (upcoming_time.strftime('%Y-%m-%d'),)).fetchall()
    
    for tournament in tournaments:
        message = f"Your {tournament['tournament_name']} tournament is starting tomorrow! Get ready to compete!"
        send_push_notification(tournament['player_id'], message, "Tournament Starting")
        
        # Mark notification as sent
        conn.execute('''
            UPDATE tournaments SET tournament_notification_sent = 1 WHERE id = ?
        ''', (tournament['id'],))
    
    conn.commit()
    conn.close()

def get_tournament_levels():
    """Get available tournament levels with dynamic pricing from settings"""
    beginner_price = float(get_setting('beginner_price', '20'))
    intermediate_price = float(get_setting('intermediate_price', '25'))
    advanced_price = float(get_setting('advanced_price', '30'))
    championship_price = float(get_setting('championship_price', '30'))
    
    # Get max players from settings
    beginner_max = int(get_setting('beginner_max_players', '32'))
    intermediate_max = int(get_setting('intermediate_max_players', '32'))
    advanced_max = int(get_setting('advanced_max_players', '32'))
    championship_max = int(get_setting('championship_max_players', '128'))
    
    def calculate_prizes(entry_fee, max_players):
        """Calculate prize breakdown for top 4 finishers"""
        total_fees = entry_fee * max_players
        prize_pool = total_fees * 0.70  # 70% goes to prizes, 30% platform revenue
        return {
            '1st': prize_pool * 0.50,  # 50% of prize pool (35% of total fees)
            '2nd': prize_pool * 0.30,  # 30% of prize pool (21% of total fees)
            '3rd': prize_pool * 0.12,  # 12% of prize pool (8.4% of total fees)
            '4th': prize_pool * 0.08,  # 8% of prize pool (5.6% of total fees)
            'platform_revenue': total_fees * 0.30  # 30% platform revenue
        }
    
    def calculate_championship_prizes(entry_fee, max_players):
        """Calculate detailed prize breakdown for championship tournament (top 20)"""
        total_fees = entry_fee * max_players  # $30 * 128 = $3,840
        prize_pool = total_fees * 0.70  # $2,688 prize pool
        return {
            '1st': 800, '2nd': 480, '3rd': 300, '4th': 200, '5th': 160,
            '6th': 120, '7th': 100, '8th': 80, '9th': 72, '10th': 64,
            '11th': 56, '12th': 48, '13th': 44, '14th': 40, '15th': 36,
            '16th': 32, '17th': 32, '18th': 32, '19th': 16, '20th': 16,
            'platform_revenue': total_fees * 0.30
        }
    
    beginner_prizes = calculate_prizes(beginner_price, beginner_max)
    intermediate_prizes = calculate_prizes(intermediate_price, intermediate_max)
    advanced_prizes = calculate_prizes(advanced_price, advanced_max)
    championship_prizes = calculate_championship_prizes(championship_price, championship_max)
    
    return {
        'Beginner': {
            'name': 'The B League',
            'description': 'Perfect for new players and casual competition',
            'entry_fee': beginner_price,
            'prize_pool': f"1st: ${beginner_prizes['1st']:.0f} • 2nd: ${beginner_prizes['2nd']:.0f} • 3rd: ${beginner_prizes['3rd']:.0f} • 4th: ${beginner_prizes['4th']:.0f}",
            'prize_breakdown': beginner_prizes,
            'skill_requirements': 'Beginner level players',
            'max_players': beginner_max
        },
        'Intermediate': {
            'name': 'The Inter League',
            'description': 'For players with solid fundamentals',
            'entry_fee': intermediate_price,
            'prize_pool': f"1st: ${intermediate_prizes['1st']:.0f} • 2nd: ${intermediate_prizes['2nd']:.0f} • 3rd: ${intermediate_prizes['3rd']:.0f} • 4th: ${intermediate_prizes['4th']:.0f}",
            'prize_breakdown': intermediate_prizes,
            'skill_requirements': 'Intermediate level players',
            'max_players': intermediate_max
        },
        'Advanced': {
            'name': 'The Z League',
            'description': 'High-level competitive play',
            'entry_fee': advanced_price,
            'prize_pool': f"1st: ${advanced_prizes['1st']:.0f} • 2nd: ${advanced_prizes['2nd']:.0f} • 3rd: ${advanced_prizes['3rd']:.0f} • 4th: ${advanced_prizes['4th']:.0f}",
            'prize_breakdown': advanced_prizes,
            'skill_requirements': 'Advanced level players',
            'max_players': advanced_max
        },
        'Championship': {
            'name': 'The Big Dink',
            'subtitle': 'The Hill',
            'description': 'Elite championship tournament for top players',
            'entry_fee': championship_price,
            'prize_pool': "Total Prize Pool: $2,688 • 1st Place: $800 • Top 20 Finishers Paid",
            'prize_breakdown': championship_prizes,
            'skill_requirements': 'All skill levels welcome',
            'max_players': championship_max,
            'special_notes': 'Championship tournament with detailed prize distribution for top 20 finishers'
        },
        'Invitational': {
            'name': 'The Championship',
            'description': 'End of year tournament, invitation only, top 16 ranked players - Best of 5 Sets',
            'entry_fee': 0,
            'prize_pool': 'Details to come',
            'prize_breakdown': {},
            'skill_requirements': 'Invitation only - Top 16 ranked players',
            'max_players': 16,
            'special_notes': 'Invitation-only tournament for elite players - Premium best of 5 sets format'
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

def send_email_notification(to_email, subject, message_body, from_email=None):
    """Send email notification using SendGrid"""
    try:
        import os
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        # Use environment variable for from email, with fallback
        if not from_email:
            from_email = os.environ.get('FROM_EMAIL', 'noreply@ready2dink.com')
        
        # If domain isn't verified yet, use a test approach
        # We'll temporarily use a verified test pattern
        
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logging.warning("SendGrid API key not configured. Email notification skipped.")
            return False
            
        sg = SendGridAPIClient(api_key)
        mail = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=message_body
        )
        
        response = sg.send(mail)
        logging.info(f"Email sent successfully to {to_email}. Status: {response.status_code}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

def send_admin_notification(subject, message_body):
    """Send notification to admin email"""
    # Get admin email from environment or use default
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@ready2dink.com')
    return send_email_notification(admin_email, subject, message_body)

def send_contact_form_notification(name, email, subject, message, player_info=""):
    """Send notification when contact form is submitted"""
    email_subject = f"📩 New Contact Form Submission: {subject}"
    email_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #3F567F 0%, #D174D2 100%); padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">Ready 2 Dink Contact Form</h2>
            <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">New message received</p>
        </div>
        
        <div style="padding: 30px; background: white; border-left: 4px solid #3F567F;">
            <h3 style="color: #3F567F; margin-top: 0;">Message Details</h3>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>From:</strong> {name}</p>
                <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
                <p><strong>Subject:</strong> {subject}</p>
            </div>
            
            <h4 style="color: #3F567F;">Message:</h4>
            <div style="background: #ffffff; border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
                <p style="white-space: pre-wrap;">{message}</p>
            </div>
            
            {f'<h4 style="color: #3F567F;">Player Information:</h4><div style="background: #f0f8ff; border: 1px solid #3F567F; padding: 15px; border-radius: 8px;"><pre style="margin: 0; font-family: monospace;">{player_info}</pre></div>' if player_info else ''}
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 14px;">
                    Reply directly to this email to respond to {name} at {email}
                </p>
            </div>
        </div>
    </div>
    """
    return send_admin_notification(email_subject, email_body)

def send_new_registration_notification(player_data):
    """Send notification when new player registers"""
    email_subject = f"🎾 New Player Registration: {player_data['full_name']}"
    email_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">Ready 2 Dink New Registration</h2>
            <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">A new player has joined!</p>
        </div>
        
        <div style="padding: 30px; background: white; border-left: 4px solid #10B981;">
            <h3 style="color: #10B981; margin-top: 0;">Player Details</h3>
            
            <div style="background: #f0fdf4; border: 1px solid #10B981; padding: 20px; border-radius: 8px;">
                <p><strong>Name:</strong> {player_data['full_name']}</p>
                <p><strong>Email:</strong> <a href="mailto:{player_data['email']}">{player_data['email']}</a></p>
                <p><strong>Skill Level:</strong> <span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px;">{player_data['skill_level']}</span></p>
                <p><strong>Location:</strong> {player_data['location1']}</p>
                <p><strong>Preferred Court:</strong> {player_data['preferred_court']}</p>
                <p><strong>Address:</strong> {player_data['address']}</p>
                <p><strong>Date of Birth:</strong> {player_data['dob']}</p>
                {f"<p><strong>Secondary Location:</strong> {player_data['location2']}</p>" if player_data.get('location2') else ''}
            </div>
            
            <div style="margin-top: 30px; text-align: center;">
                <p style="color: #666;">
                    <strong>Total Players:</strong> Check your admin dashboard for the latest count
                </p>
                <a href="#" style="background: #10B981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block; margin-top: 10px;">
                    View Admin Dashboard
                </a>
            </div>
        </div>
    </div>
    """
    return send_admin_notification(email_subject, email_body)

@app.context_processor
def inject_user_context():
    """Make current user admin status available to all templates"""
    current_player_id = session.get('current_player_id')
    is_admin = False
    
    if current_player_id:
        conn = get_db_connection()
        player = conn.execute('SELECT is_admin FROM players WHERE id = ?', (current_player_id,)).fetchone()
        conn.close()
        if player:
            is_admin = bool(player['is_admin'])
    
    return dict(current_user_is_admin=is_admin, current_player_id=current_player_id)

@app.route('/logout')
def logout():
    """Clear all session data and redirect to home"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/')
def index():
    """Home page - check if user is logged in, otherwise show landing page"""
    # Debug: Log session contents
    logging.info(f"Session contents: {dict(session)}")
    
    # If user is already logged in, redirect to their dashboard
    if 'current_player_id' in session:
        return redirect(url_for('player_home', player_id=session['current_player_id']))
    
    # For new visitors, show the landing page (not redirect to register)
    return render_template('landing.html')

@app.route('/home/<int:player_id>')
@require_disclaimers_accepted
def player_home(player_id):
    """Personalized home page for a player"""
    conn = get_db_connection()
    
    # Set session for logged in user
    session['current_player_id'] = player_id
    session['player_id'] = player_id  # For consistency
    
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
    
    # Get all open tournament instances ordered by price (lowest to highest)
    open_tournaments = conn.execute('''
        SELECT * FROM tournament_instances 
        WHERE status = 'open' AND current_players < max_players
        ORDER BY entry_fee ASC, created_at
    ''').fetchall()
    
    for tournament in open_tournaments:
        spots_remaining = tournament['max_players'] - tournament['current_players']
        level_info = tournament_levels.get(tournament['skill_level'], {})
        
        available_tournaments.append({
            'id': tournament['id'],
            'level': tournament['skill_level'],
            'name': tournament['name'],
            'description': level_info.get('description', 'Tournament'),
            'entry_fee': tournament['entry_fee'],
            'current_entries': tournament['current_players'],
            'max_players': tournament['max_players'],
            'spots_remaining': spots_remaining,
            'prize_pool': f"1st: ${tournament['entry_fee'] * tournament['max_players'] * 0.7 * 0.5:.0f} • 2nd: ${tournament['entry_fee'] * tournament['max_players'] * 0.7 * 0.3:.0f} • 3rd: ${tournament['entry_fee'] * tournament['max_players'] * 0.7 * 0.12:.0f} • 4th: ${tournament['entry_fee'] * tournament['max_players'] * 0.7 * 0.08:.0f}"
        })
    
    # Get player's tournaments with bracket info
    player_tournaments = conn.execute('''
        SELECT t.*, ti.name as tournament_instance_name, ti.status as tournament_status,
               ti.id as tournament_instance_id
        FROM tournaments t
        JOIN tournament_instances ti ON t.tournament_instance_id = ti.id
        WHERE t.player_id = ? 
        ORDER BY t.created_at DESC
        LIMIT 5
    ''', (player_id,)).fetchall()
    
    conn.close()
    
    # Get player's ranking and leaderboard
    player_ranking = get_player_ranking(player_id)
    leaderboard = get_leaderboard(10)
    
    # Check if it's the player's birthday
    is_birthday = is_player_birthday(player['dob'])
    
    return render_template('player_home.html', 
                         player=player, 
                         connections=connections,
                         recent_matches=recent_matches,
                         tournaments=tournaments,
                         player_tournaments=player_tournaments,
                         available_tournaments=available_tournaments,
                         player_ranking=player_ranking,
                         leaderboard=leaderboard,
                         is_birthday=is_birthday)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Player registration form"""
    if request.method == 'POST':
        logging.info(f"=== REGISTRATION POST REQUEST RECEIVED ===")
        logging.info(f"Form data keys: {list(request.form.keys())}")
        logging.info(f"Files: {list(request.files.keys())}")
        # Form validation
        required_fields = ['full_name', 'address', 'zip_code', 'city', 'state', 'dob', 'skill_level', 'email']
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
            logging.info(f"Attempting registration for: {request.form['full_name']} ({request.form['email']})")
            conn = get_db_connection()
            cursor = conn.execute('''
                INSERT INTO players 
                (full_name, address, zip_code, city, state, dob, preferred_sport, skill_level, email, selfie)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (request.form['full_name'], request.form['address'], 
                  request.form['zip_code'], request.form['city'], request.form['state'],
                  request.form['dob'], 'Pickleball', 
                  request.form['skill_level'], request.form['email'], selfie_filename))
            
            player_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Send email notification to admin about new registration
            player_data = {
                'full_name': request.form['full_name'],
                'email': request.form['email'],
                'skill_level': request.form['skill_level'],
                'location1': request.form['location1'],
                'location2': request.form.get('location2', ''),
                'preferred_court': request.form['preferred_court'],
                'address': request.form['address'],
                'dob': request.form['dob']
            }
            
            email_sent = send_new_registration_notification(player_data)
            
            if email_sent:
                logging.info(f"New registration email notification sent successfully for {player_data['full_name']}")
            else:
                logging.warning(f"Failed to send email notification for new registration: {player_data['full_name']}")
            
            flash('Registration successful! Please review and accept our terms and disclaimers to continue.', 'success')
            return redirect(url_for('show_disclaimers', player_id=player_id))
            
        except sqlite3.IntegrityError as e:
            logging.error(f"Registration failed - Email already exists: {request.form['email']} - {str(e)}")
            flash('Email already exists. Please use a different email address.', 'danger')
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e).lower():
                logging.error(f"Database lock error during registration for {request.form['email']}: {str(e)}")
                flash('Registration temporarily unavailable due to high traffic. Please try again in a moment.', 'warning')
            else:
                logging.error(f"Database operational error during registration: {str(e)}")
                flash(f'Registration failed: Database error. Please try again.', 'danger')
        except Exception as e:
            logging.error(f"Registration failed for {request.form['full_name']}: {str(e)}")
            flash(f'Registration failed: {str(e)}', 'danger')
    
    return render_template('register.html')

@app.route('/disclaimers/<int:player_id>')
def show_disclaimers(player_id):
    """Show disclaimers page for a newly registered player"""
    # Verify player exists and hasn't already accepted disclaimers
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    conn.close()
    
    if not player:
        flash('Player not found', 'danger')
        return redirect(url_for('index'))
    
    if player['disclaimers_accepted']:
        flash('You have already accepted the terms and disclaimers', 'info')
        return redirect(url_for('player_home', player_id=player_id))
    
    return render_template('disclaimers.html', player_id=player_id)

@app.route('/accept-disclaimers', methods=['POST'])
def accept_disclaimers():
    """Handle disclaimer acceptance"""
    player_id = request.form.get('player_id')
    accept_terms = request.form.get('accept_terms')
    
    if not player_id or not accept_terms:
        flash('You must accept the terms and disclaimers to continue', 'danger')
        return redirect(url_for('show_disclaimers', player_id=player_id))
    
    try:
        conn = get_db_connection()
        conn.execute('UPDATE players SET disclaimers_accepted = 1 WHERE id = ?', (player_id,))
        conn.commit()
        conn.close()
        
        flash('Thank you for accepting our terms! Welcome to Ready 2 Dink!', 'success')
        # Try to find a match for the new player now that they've accepted terms
        find_match_for_player(int(player_id))
        return redirect(url_for('player_home', player_id=player_id))
        
    except Exception as e:
        flash(f'Error accepting disclaimers: {str(e)}', 'danger')
        return redirect(url_for('show_disclaimers', player_id=player_id))

@app.route('/tournament-rules/<int:player_id>')
def show_tournament_rules(player_id):
    """Show tournament rules page before tournament entry"""
    # Verify player exists
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    conn.close()
    
    if not player:
        flash('Player not found', 'danger')
        return redirect(url_for('index'))
    
    if player['tournament_rules_accepted']:
        flash('You have already accepted the tournament rules', 'info')
        return redirect(url_for('tournament_entry', player_id=player_id))
    
    return render_template('tournament_rules.html', player_id=player_id)

@app.route('/accept-tournament-rules', methods=['POST'])
def accept_tournament_rules():
    """Handle tournament rules acceptance"""
    player_id = request.form.get('player_id')
    accept_rules = request.form.get('accept_tournament_rules')
    redirect_to_tournament = request.form.get('redirect_to_tournament')
    
    if not player_id or not accept_rules:
        flash('You must accept the tournament rules to continue', 'danger')
        return redirect(url_for('show_tournament_rules', player_id=player_id))
    
    try:
        conn = get_db_connection()
        conn.execute('UPDATE players SET tournament_rules_accepted = 1 WHERE id = ?', (player_id,))
        conn.commit()
        conn.close()
        
        flash('Tournament rules accepted! You can now enter tournaments.', 'success')
        
        if redirect_to_tournament:
            return redirect(url_for('tournament_entry', player_id=player_id))
        else:
            return redirect(url_for('player_home', player_id=player_id))
        
    except Exception as e:
        flash(f'Error accepting tournament rules: {str(e)}', 'danger')
        return redirect(url_for('show_tournament_rules', player_id=player_id))

def generate_tournament_bracket(tournament_instance_id):
    """Generate bracket for a tournament instance"""
    conn = get_db_connection()
    
    # Get all players in this tournament
    players = conn.execute('''
        SELECT t.*, p.full_name, p.selfie 
        FROM tournaments t
        JOIN players p ON t.player_id = p.id
        WHERE t.tournament_instance_id = ?
        ORDER BY t.created_at
    ''', (tournament_instance_id,)).fetchall()
    
    if len(players) < 2:
        conn.close()
        return False
    
    # Assign bracket positions
    for i, player in enumerate(players, 1):
        conn.execute('UPDATE tournaments SET bracket_position = ? WHERE id = ?', 
                    (i, player['id']))
    
    # Calculate number of rounds needed
    num_players = len(players)
    import math
    max_rounds = math.ceil(math.log2(num_players)) if num_players > 1 else 1
    
    # Generate first round matches
    matches_created = []
    
    # Pair players for first round
    for i in range(0, len(players), 2):
        player1 = players[i]
        player2 = players[i + 1] if i + 1 < len(players) else None
        
        match_number = (i // 2) + 1
        
        cursor = conn.execute('''
            INSERT INTO tournament_matches 
            (tournament_instance_id, round_number, match_number, player1_id, player2_id, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (tournament_instance_id, 1, match_number, player1['player_id'], 
              player2['player_id'] if player2 else None,
              'pending' if player2 else 'bye'))
        
        matches_created.append(cursor.lastrowid)
    
    # Generate empty matches for subsequent rounds
    current_matches = len(matches_created)
    for round_num in range(2, max_rounds + 1):
        matches_in_round = current_matches // 2
        if matches_in_round == 0:
            break
            
        for match_num in range(1, matches_in_round + 1):
            cursor = conn.execute('''
                INSERT INTO tournament_matches 
                (tournament_instance_id, round_number, match_number, status)
                VALUES (?, ?, ?, ?)
            ''', (tournament_instance_id, round_num, match_num, 'pending'))
            
        current_matches = matches_in_round
    
    # Update tournament instance status
    conn.execute('UPDATE tournament_instances SET status = ? WHERE id = ?', 
                ('active', tournament_instance_id))
    
    conn.commit()
    conn.close()
    return True

@app.route('/tournament-bracket/<int:tournament_instance_id>')
def view_tournament_bracket(tournament_instance_id):
    """View tournament bracket"""
    conn = get_db_connection()
    
    # Get tournament instance
    tournament = conn.execute('SELECT * FROM tournament_instances WHERE id = ?', 
                             (tournament_instance_id,)).fetchone()
    if not tournament:
        flash('Tournament not found', 'danger')
        return redirect(url_for('tournaments_overview'))
    
    # Check if current player is in this tournament
    current_player_id = session.get('current_player_id')
    player_entry = None
    if current_player_id:
        player_entry = conn.execute('''
            SELECT * FROM tournaments 
            WHERE player_id = ? AND tournament_instance_id = ?
        ''', (current_player_id, tournament_instance_id)).fetchone()
    
    # Get tournament matches with player details
    matches = conn.execute('''
        SELECT tm.*,
               p1.full_name as player1_name, p1.selfie as player1_selfie,
               p2.full_name as player2_name, p2.selfie as player2_selfie
        FROM tournament_matches tm
        LEFT JOIN players p1 ON tm.player1_id = p1.id
        LEFT JOIN players p2 ON tm.player2_id = p2.id
        WHERE tm.tournament_instance_id = ?
        ORDER BY tm.round_number, tm.match_number
    ''', (tournament_instance_id,)).fetchall()
    
    # Group matches by round
    matches_by_round = {}
    max_rounds = 0
    for match in matches:
        round_num = match['round_number']
        if round_num not in matches_by_round:
            matches_by_round[round_num] = []
        matches_by_round[round_num].append(match)
        max_rounds = max(max_rounds, round_num)
    
    conn.close()
    
    return render_template('tournament_bracket.html',
                         tournament=tournament,
                         matches=matches,
                         matches_by_round=matches_by_round,
                         max_rounds=max_rounds,
                         player_entry=player_entry,
                         current_player_id=current_player_id)

@app.route('/leaderboard')
def leaderboard():
    """Display player leaderboard"""
    leaderboard_players = get_leaderboard(50)  # Top 50 players
    
    return render_template('leaderboard.html', leaderboard=leaderboard_players)

@app.route('/subscribe-notifications', methods=['POST'])
def subscribe_notifications():
    """Handle push notification subscription"""
    if 'player_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    data = request.get_json()
    subscription = data.get('subscription')
    
    if not subscription:
        return jsonify({'success': False, 'message': 'No subscription data'})
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE players 
        SET push_subscription = ?, notifications_enabled = 1
        WHERE id = ?
    ''', (json.dumps(subscription), session['player_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Notifications enabled successfully!'})

@app.route('/unsubscribe-notifications', methods=['POST'])
def unsubscribe_notifications():
    """Handle push notification unsubscription"""
    if 'player_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE players 
        SET notifications_enabled = 0
        WHERE id = ?
    ''', (session['player_id'],))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Notifications disabled successfully!'})

@app.route('/notification-status')
def notification_status():
    """Get current notification status for player"""
    if 'player_id' not in session:
        return jsonify({'enabled': False, 'subscribed': False})
    
    conn = get_db_connection()
    player = conn.execute('''
        SELECT notifications_enabled, push_subscription
        FROM players 
        WHERE id = ?
    ''', (session['player_id'],)).fetchone()
    conn.close()
    
    if not player:
        return jsonify({'enabled': False, 'subscribed': False})
    
    return jsonify({
        'enabled': bool(player['notifications_enabled']),
        'subscribed': bool(player['push_subscription'])
    })

@app.route('/send-test-notification', methods=['POST'])
def send_test_notification():
    """Send a test notification to the current player"""
    if 'player_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    success = send_push_notification(
        session['player_id'], 
        "This is a test notification from Ready 2 Dink! You're all set to receive match and tournament updates.",
        "Test Notification"
    )
    
    if success:
        return jsonify({'success': True, 'message': 'Test notification sent!'})
    else:
        return jsonify({'success': False, 'message': 'Failed to send notification. Make sure notifications are enabled.'})

@app.route('/trigger-notifications', methods=['POST'])
def trigger_notifications():
    """Manual trigger for notifications (admin/testing)"""
    schedule_match_notifications()
    schedule_tournament_notifications()
    return jsonify({'success': True, 'message': 'Notifications triggered successfully'})

@app.route('/service-worker.js')
def service_worker():
    """Serve the service worker file"""
    return app.send_static_file('sw.js')

@app.route('/notification-settings')
def notification_settings():
    """Notification settings page"""
    if 'player_id' not in session:
        return redirect(url_for('index'))
    
    return render_template('notification_settings.html')

@app.route('/ranking-info')
def ranking_info():
    """Ranking system information page"""
    return render_template('ranking_info.html')

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
    
    # Get tournament instances (like upcoming championship)
    tournament_instances = conn.execute('''
        SELECT * FROM tournament_instances 
        WHERE status IN ('open', 'upcoming')
        ORDER BY 
            CASE 
                WHEN status = 'open' THEN 1 
                WHEN status = 'upcoming' THEN 2 
            END,
            created_at DESC
    ''').fetchall()
    
    # Get custom tournaments created by users
    custom_tournaments = conn.execute('''
        SELECT ct.*, p.full_name as organizer_name, p.selfie as organizer_selfie
        FROM custom_tournaments ct
        JOIN players p ON ct.organizer_id = p.id
        WHERE ct.status = 'open' 
        AND datetime(ct.registration_deadline) > datetime('now')
        ORDER BY ct.created_at DESC
    ''').fetchall()
    
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
                         tournament_instances=tournament_instances,
                         custom_tournaments=custom_tournaments,
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
@require_disclaimers_accepted
def tournament_entry(player_id):
    """Tournament entry form with levels and fees for a specific player"""
    # Get player info first
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    if not player:
        flash('Player not found', 'danger')
        return redirect(url_for('index'))
    
    # Check if player has accepted tournament rules
    if not player['tournament_rules_accepted']:
        flash('Please read and accept the tournament rules before entering tournaments', 'warning')
        return redirect(url_for('show_tournament_rules', player_id=player_id))
    
    if request.method == 'POST':
        required_fields = ['tournament_instance_id', 'tournament_type']
        tournament_type = request.form.get('tournament_type')
        
        # Add partner_id to required fields if doubles
        if tournament_type == 'doubles':
            required_fields.append('partner_id')
            
        for field in required_fields:
            if not request.form.get(field):
                flash(f'{field.replace("_", " ").title()} is required', 'danger')
                return redirect(url_for('tournament_entry', player_id=player_id))
        
        try:
            # Get tournament instance ID from form
            tournament_instance_id = request.form.get('tournament_instance_id')
            if not tournament_instance_id:
                flash('Please select a specific tournament to join.', 'danger')
                return redirect(url_for('tournament_entry', player_id=player_id))
                
            # Get tournament instance details
            tournament_instance = conn.execute('''
                SELECT * FROM tournament_instances WHERE id = ? AND status = 'open'
            ''', (tournament_instance_id,)).fetchone()
            
            if not tournament_instance:
                flash('Tournament not found or no longer accepting registrations.', 'danger')
                return redirect(url_for('tournament_entry', player_id=player_id))
            
            # Check if tournament is full
            if tournament_instance['current_players'] >= tournament_instance['max_players']:
                flash(f'This tournament is full ({tournament_instance["max_players"]} players max).', 'warning')
                return redirect(url_for('tournament_entry', player_id=player_id))
            
            # Check if player already entered THIS specific tournament (allow multiple tournaments)
            existing_entry = conn.execute('''
                SELECT COUNT(*) as count FROM tournaments 
                WHERE player_id = ? AND tournament_instance_id = ?
            ''', (player_id, tournament_instance_id)).fetchone()['count']
            
            if existing_entry > 0:
                flash('You are already registered for this tournament.', 'warning')
                return redirect(url_for('tournament_entry', player_id=player_id))
            
            # Calculate entry fee (add $10 for doubles)
            base_fee = tournament_instance['entry_fee']
            entry_fee = base_fee + 10 if tournament_type == 'doubles' else base_fee
            
            # Check if Ambassador can use free entry (excluding The Hill)
            free_entry_used = False
            is_the_hill = 'The Hill' in tournament_instance.get('name', '') or 'Big Dink' in tournament_instance.get('name', '')
            
            if player['free_tournament_entries'] and player['free_tournament_entries'] > 0 and not is_the_hill:
                # Ambassador has free entries available and this isn't The Hill
                entry_fee = 10 if tournament_type == 'doubles' else 0  # Only partner fee for doubles
                free_entry_used = True
            
            # Handle doubles partner invitation
            partner_id = None
            if tournament_type == 'doubles':
                partner_id = request.form.get('partner_id')
                
                # Verify partner exists and has played with this player
                partner = conn.execute('SELECT * FROM players WHERE id = ?', (partner_id,)).fetchone()
                if not partner:
                    flash('Selected partner not found.', 'danger')
                    return redirect(url_for('tournament_entry', player_id=player_id))
                
                # Check if they've played together
                connection = conn.execute('''
                    SELECT 1 FROM matches 
                    WHERE (player1_id = ? AND player2_id = ?) 
                       OR (player1_id = ? AND player2_id = ?)
                    LIMIT 1
                ''', (player_id, partner_id, partner_id, player_id)).fetchone()
                
                if not connection:
                    flash('You can only invite players you have played with before.', 'danger')
                    return redirect(url_for('tournament_entry', player_id=player_id))

            # Check if player skill matches tournament level (with some flexibility)
            skill_mapping = {
                'Beginner': ['Beginner'],
                'Intermediate': ['Beginner', 'Intermediate'], 
                'Advanced': ['Intermediate', 'Advanced']
            }
            
            tournament_skill = tournament_instance['skill_level']
            if player['skill_level'] not in skill_mapping.get(tournament_skill, []):
                flash(f'Your skill level ({player["skill_level"]}) may not be suitable for {tournament_skill} level. Consider a different tournament.', 'warning')
                return redirect(url_for('tournament_entry', player_id=player_id))
            
            entry_date = datetime.now()
            match_deadline = entry_date + timedelta(days=14)  # 2 weeks for tournaments
            
            # Update free entries count if used
            if free_entry_used:
                conn.execute('''
                    UPDATE players SET free_tournament_entries = free_tournament_entries - 1
                    WHERE id = ?
                ''', (player_id,))
            
            # Insert tournament entry
            conn.execute('''
                INSERT INTO tournaments (player_id, tournament_instance_id, tournament_name, tournament_level, tournament_type, entry_fee, sport, entry_date, match_deadline, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (player_id, 
                  tournament_instance_id,
                  tournament_instance['name'],
                  tournament_instance['skill_level'],
                  tournament_type,
                  entry_fee,
                  'Pickleball',
                  entry_date.strftime('%Y-%m-%d'), 
                  match_deadline.strftime('%Y-%m-%d'),
                  'pending_partner' if tournament_type == 'doubles' and partner_id else 'completed'))
            
            # Get the tournament entry ID for partner invitation
            tournament_entry_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            
            # Send partner invitation for doubles
            if tournament_type == 'doubles' and partner_id:
                # Create partner invitation record
                conn.execute('''
                    INSERT INTO partner_invitations 
                    (tournament_entry_id, inviter_id, invitee_id, tournament_name, entry_fee, status, created_at)
                    VALUES (?, ?, ?, ?, ?, 'pending', datetime('now'))
                ''', (tournament_entry_id, player_id, partner_id, tournament_instance['name'], entry_fee))
                
                # Send notification to partner
                partner = conn.execute('SELECT * FROM players WHERE id = ?', (partner_id,)).fetchone()
                message = f"{player['full_name']} has invited you to play doubles in {tournament_instance['name']}! Entry fee: ${entry_fee} (your share: ${entry_fee}). Check your invitations to accept."
                
                # Send push notification
                send_push_notification(partner_id, message, "Doubles Tournament Invitation")
                
                if free_entry_used:
                    remaining_entries = player['free_tournament_entries'] - 1
                    flash(f'FREE Ambassador entry used! Partner invitation sent to {partner["full_name"]}. You have {remaining_entries} free entries remaining.', 'success')
                else:
                    flash(f'Tournament entry submitted! Partner invitation sent to {partner["full_name"]}. They need to accept and pay their fee to confirm the doubles team.', 'success')
            else:
                if free_entry_used:
                    remaining_entries = player['free_tournament_entries'] - 1
                    flash(f'FREE Ambassador entry used! Successfully entered tournament! You have {remaining_entries} free entries remaining. Good luck!', 'success')
                else:
                    flash('Successfully entered tournament! Good luck!', 'success')

            conn.commit()
            conn.close()
            
            return redirect(url_for('dashboard', player_id=player_id))
            
        except Exception as e:
            flash(f'Tournament entry failed: {str(e)}', 'danger')
    
    # Get all available tournament instances ordered by price (lowest to highest)  
    available_tournaments = conn.execute('''
        SELECT * FROM tournament_instances 
        WHERE status = 'open' AND current_players < max_players
        ORDER BY entry_fee ASC, created_at
    ''').fetchall()
    
    tournament_levels = get_tournament_levels()
    tournaments_list = []
    
    for tournament in available_tournaments:
        spots_remaining = tournament['max_players'] - tournament['current_players']
        level_info = tournament_levels.get(tournament['skill_level'], {})
        
        tournaments_list.append({
            'id': tournament['id'],
            'name': tournament['name'],
            'skill_level': tournament['skill_level'],
            'entry_fee': tournament['entry_fee'],
            'current_players': tournament['current_players'],
            'max_players': tournament['max_players'],
            'spots_remaining': spots_remaining,
            'description': level_info.get('description', 'Tournament'),
            'prize_pool': f"1st: ${tournament['entry_fee'] * tournament['max_players'] * 0.7 * 0.5:.0f} • 2nd: ${tournament['entry_fee'] * tournament['max_players'] * 0.7 * 0.3:.0f} • 3rd: ${tournament['entry_fee'] * tournament['max_players'] * 0.7 * 0.12:.0f} • 4th: ${tournament['entry_fee'] * tournament['max_players'] * 0.7 * 0.08:.0f}"
        })

    # Get player's connections for partner selection
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
            COUNT(*) as matches_played,
            MAX(m.created_at) as last_played
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        WHERE m.player1_id = ? OR m.player2_id = ?
        GROUP BY opponent_id, opponent_name
        ORDER BY last_played DESC
        LIMIT 10
    ''', (player_id, player_id, player_id, player_id)).fetchall()

    conn.close()
    
    return render_template('tournament.html', player=player, tournaments_list=tournaments_list, connections=connections)

@app.route('/dashboard/<int:player_id>')
@require_disclaimers_accepted
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
    
    # Get player's tournaments with tournament instance info
    tournaments = conn.execute('''
        SELECT t.*, ti.name as tournament_instance_name, ti.status as tournament_status,
               ti.id as tournament_instance_id
        FROM tournaments t
        JOIN tournament_instances ti ON t.tournament_instance_id = ti.id
        WHERE t.player_id = ? 
        ORDER BY t.created_at DESC
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
    
    # Award tournament points based on result
    tournament_points = get_tournament_points(result)
    if tournament_points > 0:
        award_points(tournament['player_id'], tournament_points, f'Tournament result: {result}')
    
    # Send notification about tournament completion and points earned
    if tournament_points > 0:
        points_message = f"🏆 Tournament complete! You finished as {result.lower()} and earned {tournament_points} ranking points!"
        send_push_notification(tournament['player_id'], points_message, "Tournament Results")
    
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
    
    # Update tournament settings in database
    if level == 'Beginner':
        update_setting('beginner_price', entry_fee)
        if max_players:
            update_setting('beginner_max_players', max_players)
        if description:
            update_setting('beginner_description', description)
    elif level == 'Intermediate':
        update_setting('intermediate_price', entry_fee)
        if max_players:
            update_setting('intermediate_max_players', max_players)
        if description:
            update_setting('intermediate_description', description)
    elif level == 'Advanced':
        update_setting('advanced_price', entry_fee)
        if max_players:
            update_setting('advanced_max_players', max_players)
        if description:
            update_setting('advanced_description', description)
    
    flash(f'{level} tournament settings updated successfully! Entry fee: ${entry_fee}', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/update_global_settings', methods=['POST'])
def update_global_settings():
    """Update global tournament settings"""
    duration = request.form.get('tournament_duration')
    deadline = request.form.get('registration_deadline')
    timeout = request.form.get('match_timeout')
    min_players = request.form.get('min_players')
    
    # Update global tournament settings in database
    if duration:
        update_setting('tournament_duration', duration)
    if deadline:
        update_setting('registration_deadline', deadline)
    if timeout:
        update_setting('match_timeout', timeout)
    if min_players:
        update_setting('min_players', min_players)
    
    flash('Global tournament settings updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

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

@app.route('/update_app_config', methods=['POST'])
def update_app_config():
    """Update app configuration settings"""
    app_name = request.form.get('app_name')
    support_email = request.form.get('support_email')
    max_upload_size = request.form.get('max_upload_size')
    
    # Here you would update your app configuration
    # For now, just show a success message
    flash('App configuration updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/find_match/<int:player_id>', methods=['POST'])
@require_disclaimers_accepted
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

@app.route('/update-availability/<int:player_id>', methods=['POST'])
def update_availability(player_id):
    """Update player availability schedule"""
    if 'player_id' not in session or session['player_id'] != player_id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Get form data
        availability_data = {
            'monday': {
                'available': 'monday' in request.form,
                'time_slots': request.form.getlist('monday_time')
            },
            'tuesday': {
                'available': 'tuesday' in request.form,
                'time_slots': request.form.getlist('tuesday_time')
            },
            'wednesday': {
                'available': 'wednesday' in request.form,
                'time_slots': request.form.getlist('wednesday_time')
            },
            'thursday': {
                'available': 'thursday' in request.form,
                'time_slots': request.form.getlist('thursday_time')
            },
            'friday': {
                'available': 'friday' in request.form,
                'time_slots': request.form.getlist('friday_time')
            },
            'saturday': {
                'available': 'saturday' in request.form,
                'time_slots': request.form.getlist('saturday_time')
            },
            'sunday': {
                'available': 'sunday' in request.form,
                'time_slots': request.form.getlist('sunday_time')
            }
        }
        
        time_preference = request.form.get('time_preference', 'Flexible')
        
        # Convert to JSON string for database storage
        availability_json = json.dumps(availability_data)
        
        # Update database
        conn = get_db_connection()
        conn.execute('''
            UPDATE players 
            SET availability_schedule = ?, time_preference = ? 
            WHERE id = ?
        ''', (availability_json, time_preference, player_id))
        conn.commit()
        conn.close()
        
        flash('Availability schedule updated successfully!', 'success')
        
    except Exception as e:
        logging.error(f"Error updating availability for player {player_id}: {str(e)}")
        flash('Error updating availability. Please try again.', 'danger')
    
    return redirect(url_for('player_home', player_id=player_id))

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
    required_fields = ['full_name', 'address', 'zip_code', 'city', 'state', 'dob', 'skill_level', 'email']
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
                SET full_name = ?, address = ?, zip_code = ?, city = ?, state = ?, 
                    dob = ?, skill_level = ?, email = ?, selfie = ?
                WHERE id = ?
            ''', (request.form['full_name'], request.form['address'], 
                  request.form['zip_code'], request.form['city'], request.form['state'],
                  request.form['dob'], request.form['skill_level'], 
                  request.form['email'], selfie_filename, player_id))
        else:
            conn.execute('''
                UPDATE players 
                SET full_name = ?, address = ?, zip_code = ?, city = ?, state = ?,
                    dob = ?, skill_level = ?, email = ?
                WHERE id = ?
            ''', (request.form['full_name'], request.form['address'], 
                  request.form['zip_code'], request.form['city'], request.form['state'],
                  request.form['dob'], request.form['skill_level'], 
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
    
    # Award 10 points to the winner
    award_points(winner_id, 10, 'Match victory')
    
    # Send notification to winner about points earned
    conn = get_db_connection()
    winner = conn.execute('SELECT full_name FROM players WHERE id = ?', (winner_id,)).fetchone()
    loser = conn.execute('SELECT full_name FROM players WHERE id = ?', (loser_id,)).fetchone()
    conn.close()
    
    if winner and loser:
        winner_message = f"🏆 Victory! You beat {loser['full_name']} and earned 10 ranking points!"
        loser_message = f"Good game against {winner['full_name']}! Keep practicing and you'll get them next time!"
        
        send_push_notification(winner_id, winner_message, "Match Result")
        send_push_notification(loser_id, loser_message, "Match Result")
    
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

@app.route('/create_tournament', methods=['POST'])
@admin_required
def create_tournament():
    """Create a new tournament instance"""
    name = request.form.get('name')
    skill_level = request.form.get('skill_level')
    entry_fee = float(request.form.get('entry_fee', 0))
    max_players = int(request.form.get('max_players', 32))
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO tournament_instances (name, skill_level, entry_fee, max_players)
        VALUES (?, ?, ?, ?)
    ''', (name, skill_level, entry_fee, max_players))
    conn.commit()
    conn.close()
    
    flash(f'Tournament "{name}" created successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/create_custom_tournament', methods=['POST'])
def create_custom_tournament():
    """Create a custom user tournament with Stripe integration"""
    current_player_id = session.get('current_player_id')
    if not current_player_id:
        return jsonify({'success': False, 'message': 'Please log in to create tournaments'})
    
    try:
        # Get form data
        tournament_name = request.form.get('tournament_name')
        description = request.form.get('description')
        location = request.form.get('location')
        max_players_str = request.form.get('max_players')
        entry_fee_str = request.form.get('entry_fee')
        format_type = request.form.get('format')
        start_date = request.form.get('start_date')
        registration_deadline = request.form.get('registration_deadline')
        
        # Convert and validate numeric fields
        if not max_players_str or not entry_fee_str:
            return jsonify({'success': False, 'message': 'Player count and entry fee are required'})
        
        max_players = int(max_players_str)
        entry_fee = float(entry_fee_str)
        
        # Validate required fields
        if not all([tournament_name, location, max_players, entry_fee, format_type, start_date, registration_deadline]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        # Create Stripe product and price for payments
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        # Create Stripe product
        stripe_product = stripe.Product.create(
            name=f"{tournament_name} - Entry Fee",
            description=f"Entry fee for {tournament_name} tournament at {location}"
        )
        
        # Create Stripe price (in cents)
        stripe_price = stripe.Price.create(
            unit_amount=int(entry_fee * 100),  # Convert to cents
            currency='usd',
            product=stripe_product.id,
        )
        
        # Calculate prize pool (70% to winners, 30% house cut)
        house_cut = 0.30
        prize_pool = entry_fee * max_players * (1 - house_cut)
        
        # Insert tournament into database
        conn = get_db_connection()
        cursor = conn.execute('''
            INSERT INTO custom_tournaments 
            (organizer_id, tournament_name, description, location, max_players, 
             entry_fee, format, house_cut, prize_pool, start_date, 
             registration_deadline, stripe_product_id, stripe_price_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (current_player_id, tournament_name, description, location, max_players,
              entry_fee, format_type, house_cut, prize_pool, start_date,
              registration_deadline, stripe_product.id, stripe_price.id))
        
        tournament_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logging.info(f"Custom tournament created: {tournament_name} by player {current_player_id}")
        
        return jsonify({
            'success': True, 
            'message': 'Tournament created successfully!',
            'tournament_name': tournament_name,
            'tournament_id': tournament_id
        })
        
    except Exception as e:
        logging.error(f"Error creating custom tournament: {e}")
        return jsonify({'success': False, 'message': f'Error creating tournament: {str(e)}'})

@app.route('/join_custom_tournament/<int:tournament_id>')
def join_custom_tournament(tournament_id):
    """Join a custom tournament with payment"""
    current_player_id = session.get('current_player_id')
    if not current_player_id:
        flash('Please log in to join tournaments', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    
    # Get tournament details
    tournament = conn.execute('''
        SELECT ct.*, p.full_name as organizer_name
        FROM custom_tournaments ct
        JOIN players p ON ct.organizer_id = p.id
        WHERE ct.id = ? AND ct.status = 'open'
    ''', (tournament_id,)).fetchone()
    
    if not tournament:
        flash('Tournament not found or no longer accepting registrations', 'danger')
        return redirect(url_for('tournaments_overview'))
    
    # Check if tournament is full
    if tournament['current_entries'] >= tournament['max_players']:
        flash('This tournament is full', 'warning')
        return redirect(url_for('tournaments_overview'))
    
    # Check if player already joined
    existing_entry = conn.execute('''
        SELECT * FROM custom_tournament_entries 
        WHERE tournament_id = ? AND player_id = ?
    ''', (tournament_id, current_player_id)).fetchone()
    
    if existing_entry:
        flash('You are already registered for this tournament', 'info')
        return redirect(url_for('tournaments_overview'))
    
    conn.close()
    
    # Create Stripe checkout session
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        YOUR_DOMAIN = os.environ.get('REPLIT_DEV_DOMAIN') if os.environ.get('REPLIT_DEPLOYMENT') != '' else (os.environ.get('REPLIT_DOMAINS', '').split(',')[0] if os.environ.get('REPLIT_DOMAINS') else 'localhost:5000')
        
        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                'price': tournament['stripe_price_id'],
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'https://{YOUR_DOMAIN}/tournament_payment_success/{tournament_id}?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'https://{YOUR_DOMAIN}/tournaments',
            metadata={
                'tournament_id': tournament_id,
                'player_id': current_player_id,
                'tournament_type': 'custom'
            }
        )
        
        if checkout_session.url:
            return redirect(checkout_session.url, code=303)
        else:
            flash('Error creating payment session. Please try again.', 'danger')
            return redirect(url_for('tournaments_overview'))
        
    except Exception as e:
        logging.error(f"Error creating checkout session: {e}")
        flash('Error processing payment. Please try again.', 'danger')
        return redirect(url_for('tournaments_overview'))

@app.route('/tournament_payment_success/<int:tournament_id>')
def tournament_payment_success(tournament_id):
    """Handle successful tournament payment"""
    session_id = request.args.get('session_id')
    current_player_id = session.get('current_player_id')
    
    if not session_id or not current_player_id:
        flash('Invalid payment session', 'danger')
        return redirect(url_for('tournaments_overview'))
    
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        # Retrieve the checkout session
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        if checkout_session.payment_status == 'paid':
            conn = get_db_connection()
            
            # Add player to tournament
            conn.execute('''
                INSERT INTO custom_tournament_entries 
                (tournament_id, player_id, payment_status, stripe_payment_id)
                VALUES (?, ?, 'paid', ?)
            ''', (tournament_id, current_player_id, checkout_session.payment_intent))
            
            # Update tournament current entries count
            conn.execute('''
                UPDATE custom_tournaments 
                SET current_entries = current_entries + 1
                WHERE id = ?
            ''', (tournament_id,))
            
            conn.commit()
            conn.close()
            
            flash('Successfully joined the tournament!', 'success')
            
        else:
            flash('Payment was not completed', 'warning')
            
    except Exception as e:
        logging.error(f"Error processing tournament payment success: {e}")
        flash('Error confirming payment. Please contact support.', 'danger')
    
    return redirect(url_for('tournaments_overview'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard with platform overview"""
    conn = get_db_connection()
    
    # Get existing tournament instances for management
    existing_tournaments = conn.execute('''
        SELECT * FROM tournament_instances 
        ORDER BY skill_level, created_at
    ''').fetchall()
    
    # Get key metrics
    total_players = conn.execute('SELECT COUNT(*) as count FROM players').fetchone()['count']
    total_matches = conn.execute('SELECT COUNT(*) as count FROM matches').fetchone()['count']
    total_tournaments = conn.execute('SELECT COUNT(*) as count FROM tournaments').fetchone()['count']
    active_tournaments = conn.execute('SELECT COUNT(*) as count FROM tournaments WHERE completed = 0').fetchone()['count']
    
    # Get detailed player metrics by skill level
    beginner_players = conn.execute('SELECT COUNT(*) as count FROM players WHERE skill_level = "Beginner"').fetchone()['count']
    intermediate_players = conn.execute('SELECT COUNT(*) as count FROM players WHERE skill_level = "Intermediate"').fetchone()['count']
    advanced_players = conn.execute('SELECT COUNT(*) as count FROM players WHERE skill_level = "Advanced"').fetchone()['count']
    
    # Get tournament financial metrics
    tournament_levels = get_tournament_levels()
    total_revenue = 0
    total_payouts = 0
    
    for level_key, level_info in tournament_levels.items():
        entry_fee = level_info['entry_fee']
        
        # Count entries for this level
        level_entries = conn.execute('''
            SELECT COUNT(*) as count FROM tournaments 
            WHERE tournament_level = ?
        ''', (level_key,)).fetchone()['count']
        
        # Calculate revenue for this level
        level_revenue = level_entries * entry_fee
        total_revenue += level_revenue
        
        # Calculate payouts (70% of revenue goes to winners, 30% platform revenue)
        level_payouts = level_revenue * 0.7
        total_payouts += level_payouts
    
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
        'active_tournaments': active_tournaments,
        'beginner_players': beginner_players,
        'intermediate_players': intermediate_players,
        'advanced_players': advanced_players,
        'total_revenue': total_revenue,
        'total_payouts': total_payouts,
        'net_revenue': total_revenue - total_payouts
    }
    
    return render_template('admin/dashboard.html', 
                         metrics=metrics,
                         recent_players=recent_players,
                         recent_matches=recent_matches,
                         recent_tournaments=recent_tournaments,
                         existing_tournaments=existing_tournaments)

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

@app.route('/update_tournament_instance', methods=['POST'])
@admin_required
def update_tournament_instance():
    """Update individual tournament instance"""
    tournament_id = request.form.get('tournament_id')
    name = request.form.get('name')
    entry_fee = float(request.form.get('entry_fee', 0))
    max_players = int(request.form.get('max_players', 32))
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE tournament_instances 
        SET name = ?, entry_fee = ?, max_players = ?
        WHERE id = ?
    ''', (name, entry_fee, max_players, tournament_id))
    conn.commit()
    conn.close()
    
    flash(f'Tournament updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

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

@app.route('/setup_first_admin')
def setup_first_admin():
    """One-time setup to make first registered player an admin"""
    conn = get_db_connection()
    
    # Check if any admin already exists
    admin_exists = conn.execute('SELECT COUNT(*) as count FROM players WHERE is_admin = 1').fetchone()
    
    if admin_exists['count'] > 0:
        flash('Admin already exists in system', 'warning')
        return redirect(url_for('index'))
    
    # Get first registered player
    first_player = conn.execute('SELECT * FROM players ORDER BY created_at ASC LIMIT 1').fetchone()
    
    if not first_player:
        flash('No players registered yet. Register first, then visit this link.', 'info')
        return redirect(url_for('register'))
    
    # Make first player an admin
    conn.execute('UPDATE players SET is_admin = 1 WHERE id = ?', (first_player['id'],))
    conn.commit()
    conn.close()
    
    # Set them as current player
    session['current_player_id'] = first_player['id']
    
    flash(f'Admin access granted to {first_player["full_name"]}! You can now access the admin panel.', 'success')
    return redirect(url_for('admin_dashboard'))


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
        
        # Track referral conversion if applicable
        track_referral_conversion(player_id, membership_type)
        
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

# Ambassador Program Routes
@app.route('/become_ambassador', methods=['GET', 'POST'])
def become_ambassador():
    """Apply to become an Ambassador"""
    if 'player_id' not in session:
        flash('Please log in to apply for the Ambassador program', 'warning')
        return redirect(url_for('index'))
    
    player_id = session['player_id']
    
    if request.method == 'POST':
        state_territory = request.form.get('state_territory', '').strip()
        
        if not state_territory:
            flash('Please specify which state/territory you want to represent', 'danger')
            return render_template('become_ambassador.html')
        
        # Generate unique referral code
        import string
        import random
        referral_code = 'R2D' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Check if already an ambassador
        conn = get_db_connection()
        existing = conn.execute('SELECT id FROM ambassadors WHERE player_id = ?', (player_id,)).fetchone()
        
        if existing:
            flash('You are already registered as an Ambassador!', 'info')
            conn.close()
            return redirect(url_for('ambassador_dashboard'))
        
        # Create ambassador record
        conn.execute('''
            INSERT INTO ambassadors (player_id, referral_code, state_territory)
            VALUES (?, ?, ?)
        ''', (player_id, referral_code, state_territory))
        
        conn.commit()
        conn.close()
        
        flash(f'Welcome to the R2D Ambassador Program! Your referral code is: {referral_code}', 'success')
        return redirect(url_for('ambassador_dashboard'))
    
    return render_template('become_ambassador.html')

@app.route('/ambassador_dashboard')
def ambassador_dashboard():
    """Ambassador dashboard showing referral progress"""
    if 'player_id' not in session:
        return redirect(url_for('index'))
    
    player_id = session['player_id']
    
    conn = get_db_connection()
    
    # Get ambassador info
    ambassador = conn.execute('''
        SELECT * FROM ambassadors WHERE player_id = ?
    ''', (player_id,)).fetchone()
    
    if not ambassador:
        flash('You are not registered as an Ambassador. Apply now!', 'info')
        return redirect(url_for('become_ambassador'))
    
    # Get referral stats
    referrals = conn.execute('''
        SELECT ar.*, p.full_name, p.membership_type, p.created_at as signup_date
        FROM ambassador_referrals ar
        JOIN players p ON ar.referred_player_id = p.id
        WHERE ar.ambassador_id = ?
        ORDER BY ar.created_at DESC
    ''', (ambassador['id'],)).fetchall()
    
    # Get qualified count
    qualified_count = conn.execute('''
        SELECT COUNT(*) as count FROM ambassador_referrals 
        WHERE ambassador_id = ? AND qualified = 1
    ''', (ambassador['id'],)).fetchone()['count']
    
    conn.close()
    
    progress_percentage = min((qualified_count / 20) * 100, 100)
    
    return render_template('ambassador_dashboard.html', 
                         ambassador=ambassador,
                         referrals=referrals, 
                         qualified_count=qualified_count,
                         progress_percentage=progress_percentage)

@app.route('/referral/<referral_code>')
def referral_signup(referral_code):
    """Handle referral link sign-ups"""
    conn = get_db_connection()
    ambassador = conn.execute('''
        SELECT * FROM ambassadors WHERE referral_code = ?
    ''', (referral_code,)).fetchone()
    conn.close()
    
    if not ambassador:
        flash('Invalid referral code', 'danger')
        return redirect(url_for('index'))
    
    # Store referral code in session for registration
    session['referral_code'] = referral_code
    session['ambassador_id'] = ambassador['id']
    
    flash(f'Welcome! You were referred by one of our Ambassadors. Complete registration to help them earn their lifetime membership!', 'info')
    return redirect(url_for('register'))

def track_referral_conversion(player_id, membership_type):
    """Track when a referral gets tournament membership"""
    if 'ambassador_id' not in session:
        return
    
    ambassador_id = session['ambassador_id']
    referral_code = session.get('referral_code', '')
    
    # Only count tournament membership as qualified referral
    if membership_type != 'tournament':
        return
    
    conn = get_db_connection()
    
    # Record the referral
    conn.execute('''
        INSERT INTO ambassador_referrals 
        (ambassador_id, referred_player_id, referral_code, membership_type, qualified, qualified_at)
        VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
    ''', (ambassador_id, player_id, referral_code, membership_type))
    
    # Update ambassador qualified count
    conn.execute('''
        UPDATE ambassadors 
        SET qualified_referrals = qualified_referrals + 1,
            referrals_count = referrals_count + 1
        WHERE id = ?
    ''', (ambassador_id,))
    
    # Check if ambassador reached 20 qualified referrals
    ambassador = conn.execute('''
        SELECT qualified_referrals, player_id FROM ambassadors WHERE id = ?
    ''', (ambassador_id,)).fetchone()
    
    if ambassador['qualified_referrals'] >= 20:
        # Grant lifetime tournament membership and 5 free tournament entries
        conn.execute('''
            UPDATE ambassadors SET lifetime_membership_granted = 1, qualification_date = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (ambassador_id,))
        
        conn.execute('''
            UPDATE players 
            SET membership_type = 'tournament', 
                subscription_status = 'ambassador_lifetime',
                free_tournament_entries = 5
            WHERE id = ?
        ''', (ambassador['player_id']))
        
        # Send notification to ambassador
        send_push_notification(ambassador['player_id'], 
                             'Congratulations! You\'ve earned lifetime tournament membership + 5 FREE tournament entries by referring 20 members!',
                             'Ambassador Achievement Unlocked!')
    
    conn.commit()
    conn.close()
    
    # Clear session referral data
    session.pop('ambassador_id', None)
    session.pop('referral_code', None)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form for players to reach out"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # Basic validation
        if not all([name, email, subject, message]):
            flash('Please fill out all fields', 'danger')
            return render_template('contact.html')
        
        # Get player info if logged in
        player_info = ""
        if 'player_id' in session:
            conn = get_db_connection()
            player = conn.execute('SELECT * FROM players WHERE id = ?', (session['player_id'],)).fetchone()
            conn.close()
            if player:
                membership_type = player['membership_type'] if 'membership_type' in player.keys() else 'Free'
                player_info = f"\n\nPlayer Details:\nID: {player['id']}\nName: {player['full_name']}\nEmail: {player['email']}\nMembership: {membership_type}\nLocation: {player['location1']}"
        
        try:
            # Log the message
            logging.info(f"Contact Form Submission:\nFrom: {name} ({email})\nSubject: {subject}\nMessage: {message}{player_info}")
            
            # Send email notification to admin
            email_sent = send_contact_form_notification(name, email, subject, message, player_info)
            
            if email_sent:
                logging.info(f"Contact form email notification sent successfully for {name}")
            else:
                logging.warning(f"Failed to send email notification for contact form submission from {name}")
            
            flash('Thank you for your message! We\'ll get back to you soon.', 'success')
            return redirect(url_for('contact'))
            
        except Exception as e:
            logging.error(f"Contact form error: {e}")
            flash('There was an issue sending your message. Please try again later.', 'danger')
    
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

import os
import sqlite3
import psycopg2
import psycopg2.extras
import json
import requests
import math
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response, make_response
from werkzeug.utils import secure_filename
from functools import wraps
import logging
import stripe
from haversine import haversine, Unit

# Import Random Matchup Engine
try:
    from services.random_matchup_engine import start_random_matchup_engine
    RANDOM_MATCHUP_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Random Matchup Engine not available: {e}")
    RANDOM_MATCHUP_AVAILABLE = False

# Configure logging - only enable debug logging in development
if os.environ.get('FLASK_ENV') == 'development' or os.environ.get('DEBUG') == '1':
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

# Distance calculation functions
def estimate_coordinates_from_location(location_text):
    """
    Estimate coordinates from location text using basic city/state mappings.
    This is a simple fallback for when exact GPS coordinates aren't available.
    """
    if not location_text:
        return None, None
    
    # Common city coordinates for basic estimation (lat, lon)
    city_coordinates = {
        # New York Area
        'manhattan': (40.7831, -73.9712),
        'brooklyn': (40.6782, -73.9442),
        'queens': (40.7282, -73.7949),
        'bronx': (40.8448, -73.8648),
        'new york': (40.7589, -73.9851),
        'nyc': (40.7589, -73.9851),
        
        # Major US Cities
        'los angeles': (34.0522, -118.2437),
        'chicago': (41.8781, -87.6298),
        'houston': (29.7604, -95.3698),
        'phoenix': (33.4484, -112.0740),
        'philadelphia': (39.9526, -75.1652),
        'san antonio': (29.4241, -98.4936),
        'san diego': (32.7157, -117.1611),
        'dallas': (32.7767, -96.7970),
        'san jose': (37.3382, -121.8863),
        'austin': (30.2672, -97.7431),
        'jacksonville': (30.3322, -81.6557),
        'fort worth': (32.7555, -97.3308),
        'columbus': (39.9612, -82.9988),
        'san francisco': (37.7749, -122.4194),
        'charlotte': (35.2271, -80.8431),
        'indianapolis': (39.7684, -86.1581),
        'seattle': (47.6062, -122.3321),
        'denver': (39.7392, -104.9903),
        'boston': (42.3601, -71.0589),
        'el paso': (31.7619, -106.4850),
        'detroit': (42.3314, -83.0458),
        'nashville': (36.1627, -86.7816),
        'portland': (45.5152, -122.6784),
        'oklahoma city': (35.4676, -97.5164),
        'las vegas': (36.1699, -115.1398),
        'louisville': (38.2527, -85.7585),
        'baltimore': (39.2904, -76.6122),
        'milwaukee': (43.0389, -87.9065),
        'albuquerque': (35.0844, -106.6504),
        'tucson': (32.2226, -110.9747),
        'fresno': (36.7378, -119.7871),
        'sacramento': (38.5816, -121.4944),
        'kansas city': (39.0997, -94.5786),
        'mesa': (33.4152, -111.8315),
        'atlanta': (33.7490, -84.3880),
        'omaha': (41.2565, -95.9345),
        'colorado springs': (38.8339, -104.8214),
        'raleigh': (35.7796, -78.6382),
        'miami': (25.7617, -80.1918),
        'cleveland': (41.4993, -81.6944),
        'tulsa': (36.1540, -95.9928),
        'oakland': (37.8044, -122.2711),
        'minneapolis': (44.9778, -93.2650),
        'wichita': (37.6872, -97.3301),
        'arlington': (32.7357, -97.1081),
        'new orleans': (29.9511, -90.0715),
        'bakersfield': (35.3733, -119.0187),
        'tampa': (27.9506, -82.4572),
        'honolulu': (21.3099, -157.8581),
        'anaheim': (33.8366, -117.9143),
        'aurora': (39.7294, -104.8319),
        'santa ana': (33.7455, -117.8677),
        'st. louis': (38.6270, -90.1994),
        'riverside': (33.9533, -117.3962),
        'corpus christi': (27.8006, -97.3964),
        'lexington': (38.0406, -84.5037),
        'pittsburgh': (40.4406, -79.9959),
        'anchorage': (61.2181, -149.9003),
        'stockton': (37.9577, -121.2908),
        'cincinnati': (39.1031, -84.5120),
        'st. paul': (44.9537, -93.0900),
        'toledo': (41.6528, -83.5379),
        'newark': (40.7357, -74.1724),
        'greensboro': (36.0726, -79.7920),
        'plano': (33.0198, -96.6989),
        'henderson': (36.0395, -114.9817),
        'lincoln': (40.8136, -96.7026),
        'buffalo': (42.8864, -78.8784),
        'jersey city': (40.7178, -74.0431),
        'chula vista': (32.6401, -117.0842),
        'fort wayne': (41.0793, -85.1394),
        'orlando': (28.5383, -81.3792),
        'st. petersburg': (27.7676, -82.6403),
        'chandler': (33.3062, -111.8413),
        'laredo': (27.5306, -99.4803),
        'norfolk': (36.8468, -76.2852),
        'durham': (35.9940, -78.8986),
        'madison': (43.0731, -89.4012),
        'lubbock': (33.5779, -101.8552),
        'irvine': (33.6846, -117.8265),
        'winston-salem': (36.0999, -80.2442),
        'glendale': (33.5387, -112.1860),
        'garland': (32.9126, -96.6389),
        'hialeah': (25.8576, -80.2781),
        'reno': (39.5296, -119.8138),
        'chesapeake': (36.7682, -76.2875),
        'gilbert': (33.3528, -111.7890),
        'baton rouge': (30.4515, -91.1871),
        'irving': (32.8140, -96.9489),
        'scottsdale': (33.4942, -111.9261),
        'north las vegas': (36.1989, -115.1175),
        'fremont': (37.5485, -121.9886),
        'boise': (43.6150, -116.2023),
        'richmond': (37.5407, -77.4360),
        'san bernardino': (34.1083, -117.2898),
        'birmingham': (33.5186, -86.8104),
        'spokane': (47.6587, -117.4260),
        'rochester': (43.1566, -77.6088),
        'des moines': (41.5868, -93.6250),
        'modesto': (37.6391, -120.9969),
        'fayetteville': (36.0726, -94.1574),
        'tacoma': (47.2529, -122.4443),
        'oxnard': (34.1975, -119.1771),
        'fontana': (34.0922, -117.4350),
        'columbus': (32.4609, -84.9877),
        'montgomery': (32.3617, -86.2792),
        'moreno valley': (33.9425, -117.2297),
        'shreveport': (32.5252, -93.7502),
        'aurora': (41.7606, -88.3201),
        'yonkers': (40.9312, -73.8988),
        'akron': (41.0814, -81.5190),
        'huntington beach': (33.6595, -117.9988),
        'little rock': (34.7465, -92.2896),
        'augusta': (33.4735, -82.0105),
        'amarillo': (35.2220, -101.8313),
        'glendale': (34.1425, -118.2551),
        'mobile': (30.6954, -88.0399),
        'grand rapids': (42.9634, -85.6681),
        'salt lake city': (40.7608, -111.8910),
        'tallahassee': (30.4518, -84.2807),
        'huntsville': (34.7304, -86.5861),
        'grand prairie': (32.7460, -96.9978),
        'knoxville': (35.9606, -83.9207),
        'worcester': (42.2626, -71.8023),
        'newport news': (37.0871, -76.4730),
        'brownsville': (25.9018, -97.4975),
        'overland park': (38.9822, -94.6708),
        'santa clarita': (34.3917, -118.5426),
        'providence': (41.8240, -71.4128),
        'garden grove': (33.7739, -117.9414),
        'chattanooga': (35.0456, -85.3097),
        'oceanside': (33.1959, -117.3795),
        'jackson': (32.2988, -90.1848),
        'fort lauderdale': (26.1224, -80.1373),
        'santa rosa': (38.4404, -122.7144),
        'rancho cucamonga': (34.1064, -117.5931),
        'port st. lucie': (27.2939, -80.3501),
        'tempe': (33.4255, -111.9400),
        'ontario': (34.0633, -117.6509),
        'vancouver': (45.6387, -122.6615),
        'cape coral': (26.5629, -81.9495),
        'sioux falls': (43.5446, -96.7311),
        'springfield': (39.7817, -89.6501),
        'peoria': (40.6936, -89.5890),
        'pembroke pines': (26.0073, -80.2962),
        'elk grove': (38.4088, -121.3716),
        'corona': (33.8753, -117.5664),
        'lancaster': (34.6868, -118.1542),
        'eugene': (44.0521, -123.0868),
        'palmdale': (34.5794, -118.1165),
        'salinas': (36.6777, -121.6555),
        'springfield': (37.2153, -93.2982),
        'pasadena': (34.1478, -118.1445),
        'fort collins': (40.5853, -105.0844),
        'hayward': (37.6688, -122.0808),
        'pomona': (34.0555, -117.7500),
        'cary': (35.7915, -78.7811),
        'rockford': (42.2711, -89.0940),
        'alexandria': (38.8048, -77.0469),
        'escondido': (33.1192, -117.0864),
        'mckinney': (33.1972, -96.6397),
        'kansas city': (39.1142, -94.6275),
        'joliet': (41.5250, -88.0817),
        'sunnyvale': (37.3688, -122.0363)
    }
    
    location_lower = location_text.lower().strip()
    
    # Try direct city lookup
    if location_lower in city_coordinates:
        return city_coordinates[location_lower]
    
    # Try to extract city from "City, State" format
    if ',' in location_lower:
        city_part = location_lower.split(',')[0].strip()
        if city_part in city_coordinates:
            return city_coordinates[city_part]
    
    # If no match found, return None
    return None, None

def calculate_distance_between_players(player1_data, player2_data):
    """
    Calculate distance in miles between two players using their location data.
    Returns distance in miles or None if calculation isn't possible.
    """
    try:
        # First try using exact GPS coordinates
        lat1, lon1 = player1_data.get('latitude'), player1_data.get('longitude')
        lat2, lon2 = player2_data.get('latitude'), player2_data.get('longitude')
        
        # If both players have exact coordinates, use those
        if lat1 is not None and lon1 is not None and lat2 is not None and lon2 is not None:
            lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
            distance = haversine((lat1, lon1), (lat2, lon2), unit=Unit.MILES)
            return round(distance, 1)
        
        # Fall back to estimated coordinates from location text
        if lat1 is None or lon1 is None:
            lat1, lon1 = estimate_coordinates_from_location(player1_data.get('location1'))
        
        if lat2 is None or lon2 is None:
            lat2, lon2 = estimate_coordinates_from_location(player2_data.get('location1'))
        
        # If we have coordinates for both players, calculate distance
        if lat1 is not None and lon1 is not None and lat2 is not None and lon2 is not None:
            lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
            distance = haversine((lat1, lon1), (lat2, lon2), unit=Unit.MILES)
            return round(distance, 1)
        
        # If we can't calculate distance, return None
        return None
        
    except Exception as e:
        logging.error(f"Error calculating distance: {e}")
        return None

def get_distance_from_current_player(player_data, current_player_id):
    """
    Calculate distance from current logged-in player to another player.
    Returns formatted distance string or None.
    """
    if not current_player_id or not player_data:
        return None
    
    try:
        conn = get_db_connection()
        current_player = conn.execute(
            'SELECT latitude, longitude, location1 FROM players WHERE id = ?', 
            (current_player_id,)
        ).fetchone()
        conn.close()
        
        if not current_player:
            return None
        
        distance = calculate_distance_between_players(
            dict(current_player), 
            dict(player_data)
        )
        
        if distance is not None:
            if distance < 1:
                return "< 1 mile away"
            elif distance < 10:
                return f"~{distance} miles away"
            else:
                return f"~{int(distance)} miles away"
        
        return None
        
    except Exception as e:
        logging.error(f"Error getting distance from current player: {e}")
        return None

# Email configuration for SendGrid
def send_admin_credentials_email(full_name, email, username, password, login_url):
    """Send admin login credentials via email"""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_key:
            logging.error("SendGrid API key not found")
            return False
        
        # Create email content
        subject = "Ready 2 Dink - Admin Access Credentials"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #3F567F 0%, #D174D2 100%); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">Ready 2 Dink</h1>
                <p style="color: white; margin: 5px 0;">Admin Portal Access</p>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #333;">Hello {full_name},</h2>
                
                <p>You have been granted admin access to the Ready 2 Dink platform. Here are your login credentials:</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #3F567F; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #3F567F;">Login Information</h3>
                    <p><strong>Username:</strong> {username}</p>
                    <p><strong>Temporary Password:</strong> {password}</p>
                    <p><strong>Login URL:</strong> <a href="{login_url}">{login_url}</a></p>
                </div>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #856404;">⚠️ Important Security Notice</h4>
                    <ul style="color: #856404; margin: 0;">
                        <li>You will be required to change your password on first login</li>
                        <li>Keep these credentials secure and do not share them</li>
                        <li>Contact your administrator if you have any issues</li>
                    </ul>
                </div>
                
                <p>As an admin, you'll have access to:</p>
                <ul>
                    <li>Tournament management</li>
                    <li>Player oversight</li>
                    <li>Financial dashboard</li>
                    <li>Platform analytics</li>
                </ul>
                
                <p>Thank you for joining the Ready 2 Dink team!</p>
            </div>
            
            <div style="background: #333; color: white; padding: 15px; text-align: center; font-size: 12px;">
                Ready 2 Dink Admin Portal - Confidential
            </div>
        </div>
        """
        
        message = Mail(
            from_email='admin@ready2dink.com',
            to_emails=email,
            subject=subject,
            html_content=html_content
        )
        
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        
        logging.info(f"Email sent successfully to {email}, status code: {response.status_code}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send email to {email}: {str(e)}")
        return False

def send_nda_confirmation_email(player_data, signature, nda_date, ip_address):
    """Send NDA confirmation email to admin with signed agreement details"""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_key:
            logging.error("SendGrid API key not found")
            return False
        
        # Admin email - using verified address
        admin_email = "admin@ready2dink.com"
        
        subject = f"NDA Signed: {player_data['full_name']} - Ready 2 Dink Beta"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: #f8f9fa;">
            <div style="background: linear-gradient(135deg, #1a1a2e 0%, #2d1b69 100%); padding: 25px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Ready 2 Dink</h1>
                <p style="color: #E0563F; margin: 5px 0; font-size: 16px; font-weight: bold;">NDA SIGNED NOTIFICATION</p>
            </div>
            
            <div style="padding: 30px; background: white;">
                <div style="background: #e8f5e8; border-left: 4px solid #28a745; padding: 15px; margin-bottom: 20px;">
                    <h2 style="color: #28a745; margin: 0; font-size: 18px;">✅ New NDA Signature Received</h2>
                </div>
                
                <h3 style="color: #333; border-bottom: 2px solid #E0563F; padding-bottom: 10px;">Signatory Information</h3>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background: #f8f9fa;">
                        <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold; width: 30%;">Full Name:</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{player_data['full_name']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">Email:</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{player_data['email']}</td>
                    </tr>
                    <tr style="background: #f8f9fa;">
                        <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">Username:</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{player_data['username']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">Phone:</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{player_data.get('phone', 'Not provided')}</td>
                    </tr>
                    <tr style="background: #f8f9fa;">
                        <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">City:</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{player_data.get('city', 'Not provided')}, {player_data.get('state', 'Not provided')}</td>
                    </tr>
                </table>
                
                <h3 style="color: #333; border-bottom: 2px solid #D174D2; padding-bottom: 10px;">Signature Details</h3>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background: #f8f9fa;">
                        <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold; width: 30%;">Digital Signature:</td>
                        <td style="padding: 12px; border: 1px solid #ddd; font-family: 'Courier New', monospace; color: #E0563F; font-weight: bold;">{signature}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">Date & Time:</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{nda_date}</td>
                    </tr>
                    <tr style="background: #f8f9fa;">
                        <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">IP Address:</td>
                        <td style="padding: 12px; border: 1px solid #ddd; font-family: 'Courier New', monospace;">{ip_address}</td>
                    </tr>
                </table>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0;">
                    <h4 style="color: #856404; margin: 0 0 10px 0;">🔒 Legal Record</h4>
                    <p style="margin: 0; color: #856404; font-size: 14px;">
                        This email serves as a legal record of the NDA acceptance. The signatory has agreed to maintain confidentiality 
                        of all Ready 2 Dink beta information for a period of 3 years or until public launch.
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="color: #6c757d; font-size: 14px;">
                        This is an automated notification from Ready 2 Dink Beta Testing System<br>
                        Generated on {datetime.now().strftime('%Y-%m-%d at %I:%M %p')}
                    </p>
                </div>
            </div>
            
            <div style="background: #343a40; padding: 20px; text-align: center;">
                <p style="color: #adb5bd; margin: 0; font-size: 12px;">
                    © 2024 Ready 2 Dink. All rights reserved. | Beta Testing Platform
                </p>
            </div>
        </div>
        """
        
        # Create the email with verified sender
        message = Mail(
            from_email='admin@ready2dink.com',  # Use verified sender
            to_emails=admin_email,
            subject=subject,
            html_content=html_content
        )
        
        # Send the email
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        
        if response.status_code == 202:
            logging.info(f"NDA confirmation email sent successfully for player {player_data.get('username', 'unknown')}")
            return True
        else:
            logging.error(f"Failed to send NDA email. Status: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"Error sending NDA confirmation email: {e}")
        return False

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
if not app.secret_key:
    raise RuntimeError("SESSION_SECRET environment variable must be set")

# Add custom Jinja filter for JSON parsing
def from_json_filter(value):
    """Custom Jinja filter to parse JSON strings"""
    try:
        return json.loads(value) if value else {}
    except:
        return {}

app.jinja_env.filters['from_json'] = from_json_filter

# Add distance calculation filter
def distance_from_current_player_filter(player_data):
    """Custom Jinja filter to calculate distance from current player"""
    current_player_id = session.get('current_player_id')
    if not current_player_id:
        return None
    return get_distance_from_current_player(player_data, current_player_id)

app.jinja_env.filters['distance_from_current'] = distance_from_current_player_filter

# Configure Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Start Random Matchup Engine background service
if RANDOM_MATCHUP_AVAILABLE:
    try:
        start_random_matchup_engine()
        logging.info("Random Matchup Engine started successfully")
    except Exception as e:
        logging.error(f"Failed to start Random Matchup Engine: {e}")
else:
    logging.info("Random Matchup Engine disabled or not available")

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
            player = conn.execute('SELECT disclaimers_accepted, test_account FROM players WHERE id = ?', (player_id,)).fetchone()
            conn.close()
            
            # Skip validation for test accounts
            if player and player['test_account']:
                return f(*args, **kwargs)
                
            if player and not player['disclaimers_accepted']:
                flash('Please accept our terms and disclaimers to continue using Ready 2 Dink', 'warning')
                return redirect(url_for('show_disclaimers', player_id=player_id))
        
        return f(*args, **kwargs)
    return decorated_function

def generate_unique_referral_code():
    """Generate a unique referral code for any user"""
    import string
    import random
    return 'R2D' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def generate_referral_codes_for_existing_users(cursor):
    """Generate referral codes for all existing users who don't have them"""
    # Get all users without referral codes
    users_without_codes = cursor.execute('''
        SELECT id, full_name FROM players WHERE referral_code IS NULL
    ''').fetchall()
    
    for user in users_without_codes:
        attempts = 0
        max_attempts = 10
        
        while attempts < max_attempts:
            code = generate_unique_referral_code()
            try:
                cursor.execute('''
                    UPDATE players SET referral_code = ? WHERE id = ?
                ''', (code, user[0]))
                logging.info(f"Generated referral code {code} for user {user[1]} (ID: {user[0]})")
                break
            except sqlite3.IntegrityError:
                # Code already exists, try again
                attempts += 1
                
        if attempts >= max_attempts:
            logging.error(f"Failed to generate unique referral code for user {user[1]} (ID: {user[0]})")

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
        
    # Add first_name and last_name columns for better name handling
    try:
        c.execute('ALTER TABLE players ADD COLUMN first_name TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN last_name TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    # Add ranking points for player rankings
    try:
        c.execute('ALTER TABLE players ADD COLUMN ranking_points INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    # Add COPPA compliance fields for underage players
    try:
        c.execute('ALTER TABLE players ADD COLUMN guardian_email TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN account_status TEXT DEFAULT "active"')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN guardian_consent_required INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN guardian_consent_date TEXT DEFAULT NULL')
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
        
    # Add permission columns for new membership system
    try:
        c.execute('ALTER TABLE players ADD COLUMN can_search_players INTEGER DEFAULT 1')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN can_send_challenges INTEGER DEFAULT 1')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN can_receive_challenges INTEGER DEFAULT 1')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN can_join_tournaments INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN can_view_leaderboard INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN can_view_premium_stats INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN test_account INTEGER DEFAULT 0')
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
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN job_title TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN admin_level TEXT DEFAULT "staff"')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN username TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN password_hash TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN must_change_password INTEGER DEFAULT 0')
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
        
    # Add unique 4-digit player ID
    try:
        c.execute('ALTER TABLE players ADD COLUMN player_id TEXT UNIQUE DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    # Add tournament credits for refunds
    try:
        c.execute('ALTER TABLE players ADD COLUMN tournament_credits DECIMAL(10,2) DEFAULT 0.00')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    # Add payout preference for tournament winnings
    try:
        c.execute('ALTER TABLE players ADD COLUMN payout_preference TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    # Add payout account information columns
    try:
        c.execute('ALTER TABLE players ADD COLUMN paypal_email TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN venmo_username TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN zelle_info TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    # Add NDA tracking columns for test users
    try:
        c.execute('ALTER TABLE players ADD COLUMN nda_accepted INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN nda_accepted_date TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN nda_signature TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN nda_ip_address TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    # Add GPS and location-based matching columns for players
    try:
        c.execute('ALTER TABLE players ADD COLUMN latitude REAL DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN longitude REAL DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN search_radius_miles INTEGER DEFAULT 15')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN zip_code TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN city TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN state TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    # Add universal referral code field for all users
    try:
        c.execute('ALTER TABLE players ADD COLUMN referral_code TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    # Add phone number column for SMS notifications
    try:
        c.execute('ALTER TABLE players ADD COLUMN phone_number TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    # Add match preference columns for team system
    try:
        c.execute('ALTER TABLE players ADD COLUMN match_preference TEXT DEFAULT "singles"')  # singles, doubles_with_partner, doubles_need_partner
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE players ADD COLUMN current_team_id INTEGER DEFAULT NULL')
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
    
    # Bank settings table for admin business account configuration
    c.execute('''
        CREATE TABLE IF NOT EXISTS bank_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_name TEXT,
            account_holder_name TEXT,
            account_type TEXT CHECK (account_type IN ('checking', 'savings', 'business')),
            routing_number TEXT,
            account_number TEXT,
            business_name TEXT,
            business_address TEXT,
            business_phone TEXT,
            business_email TEXT,
            stripe_account_id TEXT,
            payout_method TEXT DEFAULT 'manual' CHECK (payout_method IN ('manual', 'stripe_connect', 'ach')),
            auto_payout_enabled INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER,
            FOREIGN KEY (updated_by) REFERENCES players(id)
        )
    ''')

    # Credit transactions table for tournament refunds
    c.execute('''
        CREATE TABLE IF NOT EXISTS credit_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL CHECK (transaction_type IN ('credit_issued', 'credit_used')),
            amount DECIMAL(10,2) NOT NULL,
            description TEXT NOT NULL,
            tournament_id INTEGER,
            admin_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players(id),
            FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
            FOREIGN KEY (admin_id) REFERENCES players(id)
        )
    ''')
    
    # Tournament payouts table for managing prize winnings
    c.execute('''
        CREATE TABLE IF NOT EXISTS tournament_payouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            tournament_instance_id INTEGER NOT NULL,
            tournament_name TEXT NOT NULL,
            placement TEXT NOT NULL,
            prize_amount DECIMAL(10,2) NOT NULL,
            payout_method TEXT,
            payout_account TEXT,
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'paid', 'failed')),
            admin_notes TEXT,
            paid_by INTEGER,
            paid_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players(id),
            FOREIGN KEY (tournament_instance_id) REFERENCES tournament_instances(id),
            FOREIGN KEY (paid_by) REFERENCES players(id)
        )
    ''')
    
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
    
    # Add validation columns for two-step score validation
    try:
        c.execute('ALTER TABLE matches ADD COLUMN player1_validated INTEGER DEFAULT 0')
    except Exception:
        pass  # Column already exists
    
    try:
        c.execute('ALTER TABLE matches ADD COLUMN player2_validated INTEGER DEFAULT 0')
    except Exception:
        pass  # Column already exists
    
    try:
        c.execute('ALTER TABLE matches ADD COLUMN player1_skill_feedback TEXT')
    except Exception:
        pass  # Column already exists
    
    try:
        c.execute('ALTER TABLE matches ADD COLUMN player2_skill_feedback TEXT')
    except Exception:
        pass  # Column already exists
    
    try:
        c.execute('ALTER TABLE matches ADD COLUMN validation_status TEXT DEFAULT "pending"')
    except Exception:
        pass  # Column already exists
        
    # Add match type field to distinguish singles vs doubles matches
    try:
        c.execute('ALTER TABLE matches ADD COLUMN match_type TEXT DEFAULT "singles"')
    except Exception:
        pass  # Column already exists
        
    # Create match_teams table to track team members for all match types
    c.execute('''
        CREATE TABLE IF NOT EXISTS match_teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            team_number INTEGER NOT NULL,  -- 1 or 2 to identify which team
            player_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(match_id) REFERENCES matches(id),
            FOREIGN KEY(player_id) REFERENCES players(id),
            UNIQUE(match_id, player_id)  -- Each player can only be on one team per match
        )
    ''')
    
    # Create teams table for permanent player partnerships
    c.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1_id INTEGER NOT NULL,
            player2_id INTEGER NOT NULL,
            team_name TEXT,
            status TEXT DEFAULT 'active',  -- active, inactive, dissolved
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NOT NULL,  -- who initiated the team
            FOREIGN KEY(player1_id) REFERENCES players(id),
            FOREIGN KEY(player2_id) REFERENCES players(id),
            FOREIGN KEY(created_by) REFERENCES players(id),
            UNIQUE(player1_id, player2_id)
        )
    ''')
    
    # Create team invitations table for team formation
    c.execute('''
        CREATE TABLE IF NOT EXISTS team_invitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inviter_id INTEGER NOT NULL,
            invitee_id INTEGER NOT NULL,
            invitation_message TEXT,
            status TEXT DEFAULT 'pending',  -- pending, accepted, rejected, expired
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            responded_at TEXT,
            expires_at TEXT,
            FOREIGN KEY(inviter_id) REFERENCES players(id),
            FOREIGN KEY(invitee_id) REFERENCES players(id)
        )
    ''')
    
    # Add GPS location columns to tournament_instances for existing installations
    try:
        c.execute('ALTER TABLE tournament_instances ADD COLUMN latitude REAL DEFAULT NULL')
    except Exception:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE tournament_instances ADD COLUMN longitude REAL DEFAULT NULL')
    except Exception:
        pass  # Column already exists
        
    try:
        c.execute('ALTER TABLE tournament_instances ADD COLUMN join_radius_miles INTEGER DEFAULT 25')
    except Exception:
        pass  # Column already exists
    
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
            latitude REAL DEFAULT NULL,
            longitude REAL DEFAULT NULL,
            join_radius_miles INTEGER DEFAULT 25,
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
    
    # Universal referrals tracking table for all users (not just ambassadors)
    c.execute('''
        CREATE TABLE IF NOT EXISTS universal_referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_player_id INTEGER NOT NULL,
            referred_player_id INTEGER NOT NULL,
            referral_code TEXT NOT NULL,
            referrer_type TEXT DEFAULT 'regular' CHECK (referrer_type IN ('regular', 'ambassador')),
            membership_type TEXT,
            qualified INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            qualified_at TEXT,
            reward_granted INTEGER DEFAULT 0,
            reward_granted_at TEXT,
            FOREIGN KEY(referrer_player_id) REFERENCES players(id),
            FOREIGN KEY(referred_player_id) REFERENCES players(id)
        )
    ''')
    
    # Partner invitations table for doubles tournaments
    c.execute('''
        CREATE TABLE IF NOT EXISTS partner_invitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_entry_id INTEGER NOT NULL,
            inviter_id INTEGER NOT NULL,
            invitee_id INTEGER NOT NULL,
            tournament_name TEXT NOT NULL,
            entry_fee REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            responded_at TEXT,
            FOREIGN KEY(tournament_entry_id) REFERENCES tournaments(id),
            FOREIGN KEY(inviter_id) REFERENCES players(id),
            FOREIGN KEY(invitee_id) REFERENCES players(id)
        )
    ''')
    
    # Notifications table for all app notifications
    c.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            data TEXT,
            read_status INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
    ''')
    
    # Match scheduling table for tournament match planning
    c.execute('''
        CREATE TABLE IF NOT EXISTS match_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_match_id INTEGER NOT NULL,
            proposer_id INTEGER NOT NULL,
            proposed_location TEXT,
            proposed_at TEXT NOT NULL,
            confirmation_status TEXT DEFAULT 'pending' CHECK (confirmation_status IN ('pending', 'confirmed', 'rejected', 'counter_proposed')),
            confirmed_by INTEGER,
            confirmed_at TEXT,
            counter_proposal_id INTEGER,
            deadline_at TEXT NOT NULL,
            forfeit_status TEXT DEFAULT NULL CHECK (forfeit_status IN (NULL, 'player1_forfeit', 'player2_forfeit', 'double_forfeit')),
            forfeit_reason TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tournament_match_id) REFERENCES tournament_matches(id),
            FOREIGN KEY(proposer_id) REFERENCES players(id),
            FOREIGN KEY(confirmed_by) REFERENCES players(id),
            FOREIGN KEY(counter_proposal_id) REFERENCES match_schedules(id)
        )
    ''')
    
    # Create unique constraint to prevent multiple confirmed schedules per match
    c.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_match_schedules_confirmed 
        ON match_schedules(tournament_match_id) 
        WHERE confirmation_status = 'confirmed'
    ''')
    
    # Create indexes for performance
    c.execute('''CREATE INDEX IF NOT EXISTS idx_match_schedules_tournament_match ON match_schedules(tournament_match_id)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_match_schedules_proposer ON match_schedules(proposer_id)''')
    
    # Score submissions table for match result approval workflow
    c.execute('''
        CREATE TABLE IF NOT EXISTS score_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_match_id INTEGER NOT NULL,
            submitter_id INTEGER NOT NULL,
            opponent_id INTEGER NOT NULL,
            submitted_score TEXT NOT NULL,
            winner_id INTEGER NOT NULL,
            approval_status TEXT DEFAULT 'pending' CHECK (approval_status IN ('pending', 'approved', 'disputed', 'auto_approved')),
            approved_by INTEGER,
            approved_at TEXT,
            dispute_reason TEXT,
            auto_approval_deadline_at TEXT,
            admin_resolution TEXT,
            resolved_by INTEGER,
            resolved_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tournament_match_id) REFERENCES tournament_matches(id),
            FOREIGN KEY(submitter_id) REFERENCES players(id),
            FOREIGN KEY(opponent_id) REFERENCES players(id),
            FOREIGN KEY(winner_id) REFERENCES players(id),
            FOREIGN KEY(approved_by) REFERENCES players(id),
            FOREIGN KEY(resolved_by) REFERENCES players(id)
        )
    ''')
    
    # Create unique constraint to prevent multiple pending submissions per match
    c.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_score_submissions_pending 
        ON score_submissions(tournament_match_id) 
        WHERE approval_status IN ('pending', 'disputed')
    ''')
    
    # Create indexes for performance
    c.execute('''CREATE INDEX IF NOT EXISTS idx_score_submissions_tournament_match ON score_submissions(tournament_match_id)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_score_submissions_submitter ON score_submissions(submitter_id)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_score_submissions_status ON score_submissions(approval_status)''')
    
    # Match reminders table for tracking notification history
    c.execute('''
        CREATE TABLE IF NOT EXISTS match_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_match_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            reminder_type TEXT NOT NULL CHECK (reminder_type IN ('bracket_generated', 'match_scheduled', 'deadline_24h', 'deadline_12h', 'deadline_2h', 'forfeit_warning', 'score_submission_reminder')),
            notification_method TEXT DEFAULT 'in_app' CHECK (notification_method IN ('in_app', 'email', 'sms', 'all')),
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            delivery_status TEXT DEFAULT 'pending' CHECK (delivery_status IN ('sent', 'failed', 'pending')),
            external_id TEXT,
            error_message TEXT,
            FOREIGN KEY(tournament_match_id) REFERENCES tournament_matches(id),
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
    ''')
    
    # Create composite index to prevent duplicate reminders and improve performance
    c.execute('''CREATE INDEX IF NOT EXISTS idx_match_reminders_composite ON match_reminders(tournament_match_id, player_id, reminder_type)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_match_reminders_status ON match_reminders(delivery_status)''')
    
    # Create default tournament instances if none exist
    existing_tournaments = c.execute('SELECT COUNT(*) as count FROM tournament_instances').fetchone()[0]
    
    if existing_tournaments == 0:
        # Create tournament instances for each level
        tournaments_to_create = [
            ('The B League Weekly', 'Beginner', 20, 32),
            ('Rookie Rumble', 'Beginner', 20, 32),
            ('Intermediate Challenge', 'Intermediate', 25, 32),
            ('Mid-Level Mashup', 'Intermediate', 25, 32),
            ('Advanced Showdown', 'Advanced', 30, 32),
            ('Elite Competition', 'Advanced', 30, 32),
            ('Big Dink Championship', 'Championship', 30, 128),
            ('The Hill Premium', 'Championship', 50, 64)
        ]
        
        for name, skill_level, entry_fee, max_players in tournaments_to_create:
            c.execute('''
                INSERT INTO tournament_instances (name, skill_level, entry_fee, max_players, status)
                VALUES (?, ?, ?, ?, 'open')
            ''', (name, skill_level, entry_fee, max_players))
        
        print(f"Created {len(tournaments_to_create)} default tournament instances")
    
    # CRITICAL FIX: Create database indexes BEFORE generating referral codes
    # This prevents failures if duplicate codes exist in the system
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_players_referral_code_unique ON players(referral_code) WHERE referral_code IS NOT NULL')
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_universal_referrals_pair_unique ON universal_referrals(referrer_player_id, referred_player_id)')
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_universal_referrals_referred_unique ON universal_referrals(referred_player_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_universal_referrals_code ON universal_referrals(referral_code)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_universal_referrals_qualified ON universal_referrals(qualified)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_universal_referrals_referrer_id ON universal_referrals(referrer_player_id)')
    
    # NOW generate referral codes for all existing users who don't have them
    try:
        generate_referral_codes_for_existing_users(c)
    except Exception as e:
        logging.error(f"Error generating referral codes: {e}")
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection with dict cursor"""
    import sqlite3
    conn = sqlite3.connect('app.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraints
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def get_pg_connection():
    """Get PostgreSQL database connection with dict cursor"""
    import psycopg2
    import psycopg2.extras
    conn = psycopg2.connect(
        os.environ.get('DATABASE_URL'),
        cursor_factory=psycopg2.extras.RealDictCursor
    )
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

def award_points(player_id, points, reason, conn=None):
    """Award points to a player and log the reason
    
    Args:
        player_id: Player ID to award points to
        points: Number of points to award
        reason: Reason for awarding points (for logging)
        conn: Optional database connection to use (for transaction atomicity)
    """
    should_close_conn = False
    
    if conn is None:
        conn = get_db_connection()
        should_close_conn = True
    
    # Update player's points
    conn.execute('''
        UPDATE players 
        SET ranking_points = ranking_points + ?
        WHERE id = ?
    ''', (points, player_id))
    
    # Only commit and close if we created the connection
    if should_close_conn:
        conn.commit()
        conn.close()
    
    # Log the point award for debugging
    logging.info(f"Awarded {points} points to player {player_id} for {reason}")

def get_tournament_round_name(round_number, total_rounds):
    """Map round number to tournament stage name"""
    if total_rounds == 1:
        return "Final"
    elif round_number == total_rounds:
        return "Final"
    elif round_number == total_rounds - 1:
        return "Semi-final"
    elif round_number == total_rounds - 2:
        return "Quarter-final"
    else:
        return "First round"

def get_progressive_tournament_points(round_number, total_rounds, include_first_round=False):
    """Get points for winning a specific tournament round in progressive system"""
    stage = get_tournament_round_name(round_number, total_rounds)
    
    # Progressive point system
    points_map = {
        'Final': 400,
        'Semi-final': 100,
        'Quarter-final': 40,
        'First round': 10 if include_first_round else 0
    }
    
    points = points_map.get(stage, 0)
    logging.info(f"Round {round_number}/{total_rounds} ({stage}): {points} points")
    return points

def submit_tournament_match_result(tournament_match_id, player1_sets_won, player2_sets_won, match_score, submitter_id):
    """Submit result for a tournament match and award progressive points with transaction safety"""
    try:
        # Validate input
        if player1_sets_won == player2_sets_won:
            return {'success': False, 'message': 'Tournament matches cannot be tied.'}
        
        conn = get_db_connection()
        
        # Start transaction for race condition protection
        conn.execute('BEGIN IMMEDIATE')  # IMMEDIATE lock prevents concurrent modifications
        logging.info(f"Started transaction for tournament match {tournament_match_id} submission by player {submitter_id}")
        
        # Get tournament match details with lock to prevent race conditions
        match = conn.execute('''
            SELECT tm.*, ti.name as tournament_name
            FROM tournament_matches tm
            JOIN tournament_instances ti ON tm.tournament_instance_id = ti.id
            WHERE tm.id = ?
        ''', (tournament_match_id,)).fetchone()
        
        if not match:
            conn.rollback()
            conn.close()
            return {'success': False, 'message': 'Tournament match not found'}
        
        # Check if submitter is part of this match
        if submitter_id not in [match['player1_id'], match['player2_id']]:
            conn.rollback()
            conn.close()
            return {'success': False, 'message': 'You are not part of this match'}
        
        # Idempotency check: Prevent double submissions
        if match['status'] == 'completed':
            conn.rollback()
            conn.close()
            logging.warning(f"Attempted double submission for completed match {tournament_match_id} by player {submitter_id}")
            return {'success': False, 'message': 'This match has already been completed'}
        
        # Determine winner
        winner_id = match['player1_id'] if player1_sets_won > player2_sets_won else match['player2_id']
        loser_id = match['player2_id'] if player1_sets_won > player2_sets_won else match['player1_id']
        
        # ROUND CLASSIFICATION FIX: Calculate total rounds using bracket size and math.log2
        # Get tournament instance details and actual number of players
        tournament_info = conn.execute('''
            SELECT ti.max_players, COUNT(DISTINCT p.id) as actual_players
            FROM tournament_instances ti
            LEFT JOIN tournament_participants tp ON ti.id = tp.tournament_instance_id
            LEFT JOIN players p ON tp.player_id = p.id
            WHERE ti.id = ?
            GROUP BY ti.id, ti.max_players
        ''', (match['tournament_instance_id'],)).fetchone()
        
        if tournament_info and tournament_info['actual_players'] > 0:
            import math
            # Use actual players for accurate round calculation
            num_players = tournament_info['actual_players']
            total_rounds = math.ceil(math.log2(num_players)) if num_players > 1 else 1
            logging.info(f"Tournament {match['tournament_instance_id']}: {num_players} players, calculated {total_rounds} total rounds")
        else:
            # Fallback to MAX(round_number) if tournament info unavailable
            max_round = conn.execute('''
                SELECT MAX(round_number) as max_round
                FROM tournament_matches 
                WHERE tournament_instance_id = ?
            ''', (match['tournament_instance_id'],)).fetchone()
            total_rounds = max_round['max_round'] if max_round else 1
            logging.warning(f"Using fallback round calculation for tournament {match['tournament_instance_id']}: {total_rounds} rounds")
        
        # Update tournament match with results
        conn.execute('''
            UPDATE tournament_matches 
            SET player1_score = ?, player2_score = ?, winner_id = ?, 
                status = 'completed', completed_date = datetime('now')
            WHERE id = ?
        ''', (f"{player1_sets_won} sets", f"{player2_sets_won} sets", winner_id, tournament_match_id))
        
        # DOUBLES TEAM SCORING: Update win/loss records for all team members
        # Get team members for both winner and loser (pass connection to reuse transaction)
        winner_team_members = get_tournament_team_members(tournament_match_id, winner_id, conn)
        loser_team_members = get_tournament_team_members(tournament_match_id, loser_id, conn)
        
        # Calculate points for tournament win
        points_awarded = get_progressive_tournament_points(match['round_number'], total_rounds, include_first_round=True)
        round_name = get_tournament_round_name(match['round_number'], total_rounds)
        points_description = f'{round_name} win in {match["tournament_name"]}'
        
        # Update records for all winning team members
        for player_id in winner_team_members:
            update_player_match_record(player_id, True, points_awarded, points_description, conn)
        
        # Update records for all losing team members  
        for player_id in loser_team_members:
            update_player_match_record(player_id, False, 0, "", conn)
        
        logging.info(f"Tournament match {tournament_match_id}: Updated {len(winner_team_members)} winning players, {len(loser_team_members)} losing players")
        
        # Advance winner to next round if not final
        if match['round_number'] < total_rounds:
            advance_tournament_bracket(match['tournament_instance_id'], match['round_number'], match['match_number'], winner_id)
        
        # Commit transaction - all database operations successful
        conn.commit()
        logging.info(f"Successfully submitted tournament match {tournament_match_id}, winner: {winner_id}, points awarded: {points_awarded}")
        conn.close()
        
        # Get winner name for notifications (separate connection for notifications)
        conn = get_db_connection()
        winner = conn.execute('SELECT full_name FROM players WHERE id = ?', (winner_id,)).fetchone()
        loser = conn.execute('SELECT full_name FROM players WHERE id = ?', (loser_id,)).fetchone()
        conn.close()
        
        # Send notifications
        if winner and loser:
            round_name = get_tournament_round_name(match['round_number'], total_rounds)
            sets_result = f"{player1_sets_won}-{player2_sets_won}" if winner_id == match['player1_id'] else f"{player2_sets_won}-{player1_sets_won}"
            
            if points_awarded > 0:
                winner_message = f"🏆 {round_name} Victory! You beat {loser['full_name']} ({sets_result}) and earned {points_awarded} ranking points!"
            else:
                winner_message = f"🏆 {round_name} Victory! You beat {loser['full_name']} ({sets_result}) and advance to the next round!"
            
            loser_message = f"Good match against {winner['full_name']} in the {round_name} ({match_score})! Keep training for the next tournament!"
            
            send_push_notification(winner_id, winner_message, "Tournament Match Result")
            send_push_notification(loser_id, loser_message, "Tournament Match Result")
        
        return {
            'success': True, 
            'message': f'Tournament match result submitted! {winner["full_name"] if winner else "Winner"} advances to next round.',
            'points_awarded': points_awarded,
            'round_name': get_tournament_round_name(match['round_number'], total_rounds)
        }
        
    except Exception as e:
        # Rollback transaction on any error
        try:
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            logging.error(f"Transaction rolled back for tournament match {tournament_match_id} due to error: {e}")
        except:
            pass  # Connection might already be closed
        logging.error(f"Error in submit_tournament_match_result: {e}")
        return {'success': False, 'message': f'Server error: {str(e)}'}

def advance_tournament_bracket(tournament_instance_id, current_round, current_match_number, winner_id):
    """Advance winner to next round in tournament bracket"""
    try:
        conn = get_db_connection()
        
        # Start transaction
        conn.execute('BEGIN IMMEDIATE')
        
        # Calculate next round and match position
        next_round = current_round + 1
        next_match_number = (current_match_number + 1) // 2
        
        # Check if next round match exists
        next_match = conn.execute('''
            SELECT * FROM tournament_matches 
            WHERE tournament_instance_id = ? AND round_number = ? AND match_number = ?
        ''', (tournament_instance_id, next_round, next_match_number)).fetchone()
        
        match_to_notify = None
        
        if next_match:
            # Determine if winner goes to player1 or player2 slot
            if current_match_number % 2 == 1:  # Odd match numbers go to player1
                conn.execute('''
                    UPDATE tournament_matches 
                    SET player1_id = ? 
                    WHERE id = ?
                ''', (winner_id, next_match['id']))
            else:  # Even match numbers go to player2
                conn.execute('''
                    UPDATE tournament_matches 
                    SET player2_id = ? 
                    WHERE id = ?
                ''', (winner_id, next_match['id']))
            
            # Check if both players are now assigned to next match
            updated_match = conn.execute('''
                SELECT * FROM tournament_matches 
                WHERE id = ?
            ''', (next_match['id'],)).fetchone()
            
            if updated_match['player1_id'] and updated_match['player2_id']:
                # Both players assigned, match is ready
                conn.execute('''
                    UPDATE tournament_matches 
                    SET status = 'ready' 
                    WHERE id = ?
                ''', (next_match['id'],))
                logging.info(f"Tournament match {next_match['id']} is now ready with both players assigned")
                
                # Store match for notification after successful commit
                match_to_notify = next_match['id']
        
        # Commit the bracket advancement first
        conn.commit()
        conn.close()
        
        # Send notifications and create match schedules after successful commit
        if match_to_notify:
            try:
                # Create match schedule record for the new match
                create_match_schedule_record(match_to_notify)
                
                # Send notifications to both players about their new match
                send_tournament_match_notification(match_to_notify, 'bracket_generated')
            except Exception as e:
                logging.error(f"Failed to send notification for advanced match {match_to_notify}: {e}")
        
    except Exception as e:
        logging.error(f"Error advancing tournament bracket: {e}")
        try:
            if 'conn' in locals():
                conn.rollback()
                conn.close()
        except:
            pass  # Connection might already be closed

def set_user_permissions(player_id, membership_type):
    """Set user permissions based on membership type"""
    conn = get_db_connection()
    
    if membership_type == 'free_search':
        # Free Search permissions
        conn.execute('''
            UPDATE players SET 
                can_search_players = 1,
                can_send_challenges = 1,
                can_receive_challenges = 1,
                can_join_tournaments = 0,
                can_view_leaderboard = 0,
                can_view_premium_stats = 0
            WHERE id = ?
        ''', (player_id,))
    elif membership_type == 'premium':
        # Premium permissions
        conn.execute('''
            UPDATE players SET 
                can_search_players = 1,
                can_send_challenges = 1,
                can_receive_challenges = 1,
                can_join_tournaments = 1,
                can_view_leaderboard = 1,
                can_view_premium_stats = 1
            WHERE id = ?
        ''', (player_id,))
    
    conn.commit()
    conn.close()

def check_user_permission(player_id, permission):
    """Check if a user has a specific permission"""
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute(f'SELECT {permission} FROM players WHERE id = %s', (player_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[permission]:
        return True
    return False

def check_and_handle_trial_expiry(player_id):
    """Check if a user's trial has expired and downgrade if necessary"""
    from datetime import datetime
    
    conn = get_db_connection()
    player = conn.execute('''
        SELECT id, trial_end_date, subscription_status, membership_type 
        FROM players WHERE id = ?
    ''', (player_id,)).fetchone()
    
    if not player:
        conn.close()
        return False
    
    # Skip if user doesn't have a trial end date or is already on a paid plan
    if not player['trial_end_date'] or player['subscription_status'] == 'active':
        conn.close()
        return False
    
    # Check if trial has expired
    try:
        trial_end = datetime.fromisoformat(player['trial_end_date'])
        if datetime.now() > trial_end and player['subscription_status'] == 'trialing':
            # Trial has expired, downgrade to Free Search
            conn.execute('''
                UPDATE players SET 
                    membership_type = 'free_search',
                    subscription_status = 'expired',
                    can_search_players = 1,
                    can_send_challenges = 1, 
                    can_receive_challenges = 1,
                    can_join_tournaments = 0,
                    can_view_leaderboard = 0,
                    can_view_premium_stats = 0
                WHERE id = ?
            ''', (player_id,))
            conn.commit()
            conn.close()
            logging.info(f"Trial expired for player {player_id}, downgraded to Free Search")
            return True
    except Exception as e:
        logging.error(f"Error checking trial expiry for player {player_id}: {e}")
    
    conn.close()
    return False

def check_bulk_trial_expiry():
    """Check all users for trial expiry - can be run as a batch job"""
    from datetime import datetime
    
    conn = get_db_connection()
    expired_trials = conn.execute('''
        SELECT id FROM players 
        WHERE trial_end_date IS NOT NULL 
        AND subscription_status = 'trialing'
        AND datetime(trial_end_date) < datetime('now')
    ''').fetchall()
    
    count = 0
    for player in expired_trials:
        if check_and_handle_trial_expiry(player['id']):
            count += 1
    
    conn.close()
    logging.info(f"Processed {count} expired trials in bulk check")
    return count

def require_permission(permission):
    """Decorator to require specific permissions for route access"""
    from functools import wraps
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_player_id = session.get('current_player_id')
            if not current_player_id:
                flash('Please log in first', 'warning')
                return redirect(url_for('player_login'))
            
            # Check if user is admin - admins bypass all permission checks
            conn = get_pg_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT is_admin FROM players WHERE id = %s', (current_player_id,))
            player = cursor.fetchone()
            conn.close()
            
            if player and player.get('is_admin'):
                return f(*args, **kwargs)  # Admin bypass
            
            # Check and handle trial expiry first
            check_and_handle_trial_expiry(current_player_id)
            
            # Check if user has the required permission
            if not check_user_permission(current_player_id, permission):
                flash('This feature requires a Premium membership. Upgrade to access all features!', 'warning')
                return redirect(url_for('membership_payment_page', membership_type='premium'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_admin():
    """Decorator to require admin access"""
    from functools import wraps
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_player_id = session.get('current_player_id')
            if not current_player_id:
                flash('Please log in first', 'warning')
                return redirect(url_for('player_login'))
            
            # Check if user is admin
            conn = get_pg_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT is_admin FROM players WHERE id = %s', (current_player_id,))
            player = cursor.fetchone()
            conn.close()
            
            if not player or not player.get('is_admin'):
                flash('Admin access required', 'danger')
                return redirect(url_for('player_home', player_id=current_player_id))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_tournament_team_members(tournament_match_id, player_id, conn=None):
    """Get all team members for a tournament doubles match"""
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
    
    try:
        # Get the tournament match details and check if it's a doubles tournament
        match = conn.execute('''
            SELECT tm.*, ti.name as tournament_name, ti.tournament_type
            FROM tournament_matches tm
            JOIN tournament_instances ti ON tm.tournament_instance_id = ti.id
            WHERE tm.id = ?
        ''', (tournament_match_id,)).fetchone()
        
        if not match:
            logging.warning(f"Tournament match {tournament_match_id} not found")
            return [player_id]
        
        team_members = [player_id]
        
        # Only look for partners if this is a doubles tournament
        if match.get('tournament_type') == 'doubles':
            # Get the tournament entry for the current player
            tournament_entry = conn.execute('''
                SELECT t.id
                FROM tournaments t
                WHERE t.player_id = ? AND t.tournament_instance_id = ?
            ''', (player_id, match['tournament_instance_id'])).fetchone()
            
            if tournament_entry:
                # Find partner via accepted invitations
                partner = conn.execute('''
                    SELECT invitee_id as partner_id
                    FROM partner_invitations pi
                    JOIN tournaments t ON pi.tournament_entry_id = t.id
                    WHERE pi.tournament_entry_id = ? AND pi.status = 'accepted' AND pi.inviter_id = ?
                        AND t.tournament_instance_id = ?
                    UNION
                    SELECT inviter_id as partner_id
                    FROM partner_invitations pi  
                    JOIN tournaments t ON pi.tournament_entry_id = t.id
                    WHERE pi.tournament_entry_id = ? AND pi.status = 'accepted' AND pi.invitee_id = ?
                        AND t.tournament_instance_id = ?
                ''', (tournament_entry['id'], player_id, match['tournament_instance_id'],
                      tournament_entry['id'], player_id, match['tournament_instance_id'])).fetchone()
                
                if partner:
                    team_members.append(partner['partner_id'])
                    logging.info(f"Found doubles partner for player {player_id}: {partner['partner_id']}")
                else:
                    logging.warning(f"No accepted partner found for player {player_id} in doubles tournament {match['tournament_instance_id']}")
        
        logging.info(f"Tournament match {tournament_match_id}: Player {player_id} team members: {team_members}")
        return team_members
        
    except Exception as e:
        logging.error(f"Error getting tournament team members for match {tournament_match_id}, player {player_id}: {e}")
        return [player_id]
    finally:
        if should_close:
            conn.close()

def get_match_team_members(match_id, player_id):
    """Get all team members for a regular match using the match_teams system"""
    conn = get_db_connection()
    
    try:
        # First check if this match has team data in match_teams table
        player_team = conn.execute('''
            SELECT team_number FROM match_teams 
            WHERE match_id = ? AND player_id = ?
        ''', (match_id, player_id)).fetchone()
        
        if player_team:
            # Get all players on the same team
            team_members = conn.execute('''
                SELECT player_id FROM match_teams 
                WHERE match_id = ? AND team_number = ?
            ''', (match_id, player_team['team_number'])).fetchall()
            
            team_member_ids = [member['player_id'] for member in team_members]
            logging.info(f"Match {match_id}: Found {len(team_member_ids)} team members for player {player_id}")
            return team_member_ids
        else:
            # Fallback: For matches without team data (legacy matches), return just the individual player
            logging.info(f"Match {match_id}: No team data found, treating as singles for player {player_id}")
            return [player_id]
            
    except Exception as e:
        logging.error(f"Error getting match team members for match {match_id}, player {player_id}: {e}")
        return [player_id]
    finally:
        conn.close()

def create_match_teams(match_id, player1_id, player2_id, match_type="singles", player1_partner_id=None, player2_partner_id=None, conn=None):
    """Create team entries in match_teams table for a match"""
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
        
    try:
        # Clear any existing team data for this match (for idempotency)
        conn.execute('DELETE FROM match_teams WHERE match_id = ?', (match_id,))
        
        if match_type == "doubles":
            # Team 1: player1 + partner
            conn.execute('INSERT INTO match_teams (match_id, team_number, player_id) VALUES (?, ?, ?)', 
                        (match_id, 1, player1_id))
            if player1_partner_id:
                conn.execute('INSERT INTO match_teams (match_id, team_number, player_id) VALUES (?, ?, ?)', 
                            (match_id, 1, player1_partner_id))
            
            # Team 2: player2 + partner  
            conn.execute('INSERT INTO match_teams (match_id, team_number, player_id) VALUES (?, ?, ?)', 
                        (match_id, 2, player2_id))
            if player2_partner_id:
                conn.execute('INSERT INTO match_teams (match_id, team_number, player_id) VALUES (?, ?, ?)', 
                            (match_id, 2, player2_partner_id))
        else:
            # Singles: each player is their own team
            conn.execute('INSERT INTO match_teams (match_id, team_number, player_id) VALUES (?, ?, ?)', 
                        (match_id, 1, player1_id))
            conn.execute('INSERT INTO match_teams (match_id, team_number, player_id) VALUES (?, ?, ?)', 
                        (match_id, 2, player2_id))
        
        logging.info(f"Created match teams for match {match_id}: {match_type} with {4 if match_type == 'doubles' else 2} players")
        
    except Exception as e:
        logging.error(f"Error creating match teams for match {match_id}: {e}")
        raise
    finally:
        if should_close:
            conn.close()

def backfill_existing_matches_as_singles():
    """Backfill existing matches without team data as singles matches"""
    try:
        conn = get_db_connection()
        
        # Find matches that don't have team data yet
        matches_without_teams = conn.execute('''
            SELECT m.id, m.player1_id, m.player2_id 
            FROM matches m
            LEFT JOIN match_teams mt ON m.id = mt.match_id
            WHERE mt.match_id IS NULL
        ''').fetchall()
        
        backfilled_count = 0
        for match in matches_without_teams:
            # Set match type to singles if not already set
            conn.execute('UPDATE matches SET match_type = ? WHERE id = ?', ('singles', match['id']))
            
            # Create team entries for singles match
            create_match_teams(match['id'], match['player1_id'], match['player2_id'], 'singles', conn=conn)
            backfilled_count += 1
        
        conn.commit()
        conn.close()
        logging.info(f"Backfilled {backfilled_count} existing matches as singles")
        return backfilled_count
        
    except Exception as e:
        logging.error(f"Error backfilling existing matches: {e}")
        return 0

def create_team(player1_id, player2_id, created_by, team_name=None):
    """Create a new team between two players"""
    try:
        conn = get_db_connection()
        
        # Check if either player is already in a team
        existing_team = conn.execute('''
            SELECT * FROM teams 
            WHERE (player1_id = ? OR player2_id = ?) 
            OR (player1_id = ? OR player2_id = ?) 
            AND status = 'active'
        ''', (player1_id, player1_id, player2_id, player2_id)).fetchone()
        
        if existing_team:
            conn.close()
            return {'success': False, 'message': 'One of the players is already in an active team'}
        
        # Create the team (ensure consistent ordering with lower ID first)
        if player1_id > player2_id:
            player1_id, player2_id = player2_id, player1_id
            
        cursor = conn.execute('''
            INSERT INTO teams (player1_id, player2_id, team_name, created_by)
            VALUES (?, ?, ?, ?)
        ''', (player1_id, player2_id, team_name, created_by))
        
        team_id = cursor.lastrowid
        
        # Update both players' current_team_id
        conn.execute('UPDATE players SET current_team_id = ? WHERE id = ?', (team_id, player1_id))
        conn.execute('UPDATE players SET current_team_id = ? WHERE id = ?', (team_id, player2_id))
        
        conn.commit()
        conn.close()
        
        logging.info(f"Team {team_id} created between players {player1_id} and {player2_id}")
        return {'success': True, 'team_id': team_id}
        
    except Exception as e:
        logging.error(f"Error creating team: {e}")
        return {'success': False, 'message': 'Failed to create team'}

def send_team_invitation(inviter_id, invitee_id, message=""):
    """Send a team invitation to another player"""
    try:
        conn = get_db_connection()
        
        # Check if inviter already has an active team
        inviter = conn.execute('''
            SELECT current_team_id FROM players WHERE id = ?
        ''', (inviter_id,)).fetchone()
        
        if inviter and inviter['current_team_id']:
            conn.close()
            return {'success': False, 'message': 'You are already in a team'}
        
        # Check if invitee already has an active team
        invitee = conn.execute('''
            SELECT current_team_id FROM players WHERE id = ?
        ''', (invitee_id,)).fetchone()
        
        if invitee and invitee['current_team_id']:
            conn.close()
            return {'success': False, 'message': 'This player is already in a team'}
        
        # Check for existing pending invitation between these players
        existing = conn.execute('''
            SELECT id FROM team_invitations 
            WHERE ((inviter_id = ? AND invitee_id = ?) OR (inviter_id = ? AND invitee_id = ?))
            AND status = 'pending'
        ''', (inviter_id, invitee_id, invitee_id, inviter_id)).fetchone()
        
        if existing:
            conn.close()
            return {'success': False, 'message': 'There is already a pending invitation between you and this player'}
        
        # Create the invitation
        cursor = conn.execute('''
            INSERT INTO team_invitations (inviter_id, invitee_id, invitation_message)
            VALUES (?, ?, ?)
        ''', (inviter_id, invitee_id, message))
        
        invitation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Send notification
        inviter_name = get_player_name(inviter_id)
        send_push_notification(
            invitee_id,
            f"🤝 Team Invitation from {inviter_name}! They want to form a doubles team with you.",
            "Team Invitation"
        )
        
        logging.info(f"Team invitation {invitation_id} sent from {inviter_id} to {invitee_id}")
        return {'success': True, 'invitation_id': invitation_id}
        
    except Exception as e:
        logging.error(f"Error sending team invitation: {e}")
        return {'success': False, 'message': 'Failed to send team invitation'}

def accept_team_invitation(invitation_id, player_id):
    """Accept a team invitation or random match challenge"""
    try:
        conn = get_db_connection()
        
        # Get invitation details
        invitation = conn.execute('''
            SELECT * FROM team_invitations 
            WHERE id = ? AND invitee_id = ? AND status = 'pending'
        ''', (invitation_id, player_id)).fetchone()
        
        if not invitation:
            conn.close()
            return {'success': False, 'message': 'Invalid invitation'}
        
        # Check if this is a random match invitation
        if invitation.get('source') == 'random' and invitation.get('meta_json'):
            return handle_random_match_acceptance(invitation, player_id, conn)
        
        # Original team formation logic
        # Check if either player is already in a team
        player1_team = conn.execute('SELECT current_team_id FROM players WHERE id = ?', (invitation['inviter_id'],)).fetchone()
        player2_team = conn.execute('SELECT current_team_id FROM players WHERE id = ?', (player_id,)).fetchone()
        
        if (player1_team and player1_team['current_team_id']) or (player2_team and player2_team['current_team_id']):
            conn.close()
            return {'success': False, 'message': 'One of you is already in a team'}
        
        # Create the team
        team_result = create_team(invitation['inviter_id'], player_id, invitation['inviter_id'])
        
        if not team_result['success']:
            conn.close()
            return team_result
        
        # Update invitation status
        conn.execute('''
            UPDATE team_invitations 
            SET status = 'accepted', responded_at = ?
            WHERE id = ?
        ''', (datetime.now(), invitation_id))
        
        conn.commit()
        conn.close()
        
        # Send confirmation notifications
        invitee_name = get_player_name(player_id)
        inviter_name = get_player_name(invitation['inviter_id'])
        
        send_push_notification(
            invitation['inviter_id'],
            f"🎉 {invitee_name} accepted your team invitation! You are now teammates.",
            "Team Formed"
        )
        
        return {'success': True, 'team_id': team_result['team_id']}
        
    except Exception as e:
        logging.error(f"Error accepting team invitation: {e}")
        return {'success': False, 'message': 'Failed to accept invitation'}

def handle_random_match_acceptance(invitation, player_id, conn):
    """Handle acceptance of random match challenges"""
    try:
        import json
        meta_data = json.loads(invitation.get('meta_json', '{}'))
        match_type = meta_data.get('type', 'singles')
        
        if match_type == 'singles':
            # Create singles match
            player_ids = meta_data.get('players', [])
            if len(player_ids) != 2:
                conn.close()
                return {'success': False, 'message': 'Invalid singles match data'}
            
            cursor = conn.cursor()
            
            # Create match record
            cursor.execute('''
                INSERT INTO matches (player1_id, player2_id, sport, court_location, status, created_at)
                VALUES (%s, %s, 'pickleball', 'TBD', 'scheduled', %s)
                RETURNING id
            ''', (player_ids[0], player_ids[1], datetime.now()))
            
            match_result = cursor.fetchone()
            match_id = match_result['id']
            
            # Update invitation status
            cursor.execute('''
                UPDATE team_invitations 
                SET status = 'accepted', responded_at = %s
                WHERE id = %s
            ''', (datetime.now(), invitation['id']))
            
            conn.commit()
            
            # Send notifications to both players
            player1_name = get_player_name(player_ids[0])
            player2_name = get_player_name(player_ids[1])
            
            send_push_notification(
                player_ids[0],
                f"🏓 Match confirmed! You have a singles match with {player2_name}.",
                "Match Scheduled"
            )
            
            send_push_notification(
                player_ids[1],
                f"🏓 Match confirmed! You have a singles match with {player1_name}.",
                "Match Scheduled"
            )
            
            conn.close()
            logging.info(f"Random singles match created: {player1_name} vs {player2_name}")
            return {'success': True, 'match_id': match_id, 'type': 'singles'}
            
        elif match_type == 'doubles':
            # Create doubles match
            team1 = meta_data.get('team1', [])
            team2 = meta_data.get('team2', [])
            all_players = meta_data.get('all_players', [])
            
            if len(team1) != 2 or len(team2) != 2 or len(all_players) != 4:
                conn.close()
                return {'success': False, 'message': 'Invalid doubles match data'}
            
            cursor = conn.cursor()
            
            # Create match record (using team1[0] and team2[0] as primary players)
            cursor.execute('''
                INSERT INTO matches (player1_id, player2_id, sport, court_location, status, created_at)
                VALUES (%s, %s, 'pickleball', 'TBD', 'scheduled', %s)
                RETURNING id
            ''', (team1[0], team2[0], datetime.now()))
            
            match_result = cursor.fetchone()
            match_id = match_result['id']
            
            # Update invitation status
            cursor.execute('''
                UPDATE team_invitations 
                SET status = 'accepted', responded_at = %s
                WHERE id = %s
            ''', (datetime.now(), invitation['id']))
            
            conn.commit()
            
            # Send notifications to all 4 players
            team1_names = [get_player_name(pid) for pid in team1]
            team2_names = [get_player_name(pid) for pid in team2]
            
            for pid in all_players:
                if pid in team1:
                    partner_name = team1_names[1] if pid == team1[0] else team1_names[0]
                    opponents = f"{team2_names[0]} & {team2_names[1]}"
                    message = f"🏓 Doubles match confirmed! You and {partner_name} vs {opponents}."
                else:
                    partner_name = team2_names[1] if pid == team2[0] else team2_names[0]
                    opponents = f"{team1_names[0]} & {team1_names[1]}"
                    message = f"🏓 Doubles match confirmed! You and {partner_name} vs {opponents}."
                
                send_push_notification(pid, message, "Match Scheduled")
            
            conn.close()
            logging.info(f"Random doubles match created: {team1_names} vs {team2_names}")
            return {'success': True, 'match_id': match_id, 'type': 'doubles'}
        
        else:
            conn.close()
            return {'success': False, 'message': 'Unknown match type'}
            
    except Exception as e:
        conn.close()
        logging.error(f"Error handling random match acceptance: {e}")
        return {'success': False, 'message': 'Failed to create match'}

def reject_team_invitation(invitation_id, player_id):
    """Reject a team invitation"""
    try:
        logging.info(f"🚫 REJECT FUNCTION: invitation_id={invitation_id}, player_id={player_id}")
        
        conn = get_db_connection()
        
        # Check if invitation exists first
        invitation_check = conn.execute('''
            SELECT * FROM team_invitations WHERE id = ? AND invitee_id = ? AND status = 'pending'
        ''', (invitation_id, player_id)).fetchone()
        
        logging.info(f"🚫 INVITATION CHECK: {invitation_check}")
        
        # Update invitation status
        result = conn.execute('''
            UPDATE team_invitations 
            SET status = 'rejected', responded_at = datetime('now')
            WHERE id = ? AND invitee_id = ? AND status = 'pending'
        ''', (invitation_id, player_id))
        
        logging.info(f"🚫 UPDATE RESULT: rowcount={result.rowcount}")
        
        if result.rowcount == 0:
            conn.close()
            return {'success': False, 'message': 'Invalid invitation'}
        
        # Get invitation details for notification
        invitation = conn.execute('''
            SELECT inviter_id FROM team_invitations WHERE id = ?
        ''', (invitation_id,)).fetchone()
        
        conn.commit()
        conn.close()
        
        # Notify inviter
        invitee_name = get_player_name(player_id)
        send_push_notification(
            invitation['inviter_id'],
            f"{invitee_name} declined your team invitation.",
            "Team Invitation Declined"
        )
        
        return {'success': True}
        
    except Exception as e:
        logging.error(f"Error rejecting team invitation: {e}")
        return {'success': False, 'message': 'Failed to reject invitation'}

def get_player_team(player_id):
    """Get player's current team information"""
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT t.*, 
                   p1.full_name as player1_name, p1.selfie as player1_selfie,
                   p2.full_name as player2_name, p2.selfie as player2_selfie
            FROM teams t
            JOIN players p1 ON t.player1_id = p1.id
            JOIN players p2 ON t.player2_id = p2.id
            WHERE (t.player1_id = %s OR t.player2_id = %s) AND t.status = 'active'
        ''', (player_id, player_id))
        
        team = cur.fetchone()
        conn.close()
        return dict(team) if team else None
        
    except Exception as e:
        logging.error(f"Error getting player team: {e}")
        return None

def get_player_team_invitations(player_id):
    """Get pending team formation/pair-up requests for a player (NOT singles challenges)"""
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        
        # Only get actual team formation requests, exclude singles challenges
        cur.execute('''
            SELECT ti.*, p.full_name as inviter_name, p.selfie as inviter_selfie
            FROM team_invitations ti
            JOIN players p ON ti.inviter_id = p.id
            WHERE ti.invitee_id = %s AND ti.status = 'pending'
            AND (ti.meta_json::jsonb->>'type' != 'singles' OR ti.meta_json IS NULL)
            ORDER BY ti.created_at DESC
        ''', (player_id,))
        
        invitations = cur.fetchall()
        conn.close()
        return [dict(inv) for inv in invitations]
        
    except Exception as e:
        logging.error(f"Error getting team invitations: {e}")
        return []

def get_player_match_challenges(player_id):
    """Get pending singles match challenges for a player"""
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        
        # Only get singles match challenges
        cur.execute('''
            SELECT ti.*, p.full_name as challenger_name, p.selfie as challenger_selfie
            FROM team_invitations ti
            JOIN players p ON ti.inviter_id = p.id
            WHERE ti.invitee_id = %s AND ti.status = 'pending'
            AND ti.meta_json::jsonb->>'type' = 'singles'
            ORDER BY ti.created_at DESC
        ''', (player_id,))
        
        challenges = cur.fetchall()
        conn.close()
        return [dict(challenge) for challenge in challenges]
        
    except Exception as e:
        logging.error(f"Error getting match challenges: {e}")
        return []

def get_player_name(player_id):
    """Get player's full name"""
    try:
        conn = get_db_connection()
        player = conn.execute('SELECT full_name FROM players WHERE id = ?', (player_id,)).fetchone()
        conn.close()
        return player['full_name'] if player else 'Unknown Player'
    except:
        return 'Unknown Player'

def update_player_match_record(player_id, is_winner, points_awarded=0, points_description="", conn=None):
    """Update an individual player's match record with wins/losses and points"""
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
    
    try:
        if is_winner:
            conn.execute('UPDATE players SET wins = wins + 1 WHERE id = ?', (player_id,))
            if points_awarded > 0:
                award_points(player_id, points_awarded, points_description, conn)
        else:
            conn.execute('UPDATE players SET losses = losses + 1 WHERE id = ?', (player_id,))
        
        logging.info(f"Updated player {player_id}: {'win' if is_winner else 'loss'}, points: {points_awarded}")
        
    except Exception as e:
        logging.error(f"Error updating player {player_id} match record: {e}")
        raise e
    finally:
        if should_close:
            conn.close()

def get_tournament_points(result):
    """Get points based on tournament result - DEPRECATED in favor of progressive system"""
    # This function is now deprecated since we award points progressively
    # However, keeping it for backward compatibility with existing tournament completion logic
    
    # If using progressive system, players should already have their points
    # This function now returns 0 to avoid double-awarding points
    logging.warning(f"get_tournament_points called with result '{result}' - this function is deprecated in favor of progressive point system")
    return 0

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

def get_leaderboard(limit=10, skill_level=None):
    """Get top players by ranking points, optionally filtered by skill level"""
    conn = get_db_connection()
    
    if skill_level:
        leaderboard = conn.execute('''
            SELECT id, full_name, ranking_points, wins, losses, tournament_wins, selfie, skill_level
            FROM players 
            WHERE (ranking_points > 0 OR wins > 0) AND skill_level = ?
            ORDER BY ranking_points DESC, wins DESC, losses ASC
            LIMIT ?
        ''', (skill_level, limit)).fetchall()
    else:
        leaderboard = conn.execute('''
            SELECT id, full_name, ranking_points, wins, losses, tournament_wins, selfie, skill_level
            FROM players 
            WHERE ranking_points > 0 OR wins > 0
            ORDER BY ranking_points DESC, wins DESC, losses ASC
            LIMIT ?
        ''', (limit,)).fetchall()
    
    conn.close()
    
    return leaderboard

def calculate_distance_haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two GPS coordinates using the Haversine formula.
    
    The Haversine formula calculates the great-circle distance between two points 
    on a sphere given their latitude and longitude coordinates.
    
    Args:
        lat1 (float): Latitude of the first point in decimal degrees
        lon1 (float): Longitude of the first point in decimal degrees  
        lat2 (float): Latitude of the second point in decimal degrees
        lon2 (float): Longitude of the second point in decimal degrees
        
    Returns:
        float: Distance between the two points in miles, or None if coordinates are invalid
        
    Example:
        >>> distance = calculate_distance_haversine(40.7128, -74.0060, 34.0522, -118.2437)  # NYC to LA
        >>> print(f"Distance: {distance:.2f} miles")
        Distance: 2445.55 miles
    """
    try:
        # Input validation - check for None/null values
        if any(coord is None for coord in [lat1, lon1, lat2, lon2]):
            logging.debug("One or more coordinates are None")
            return None
            
        # Convert to float if they aren't already
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        
        # Validate coordinate ranges
        if not (-90 <= lat1 <= 90) or not (-90 <= lat2 <= 90):
            logging.warning(f"Invalid latitude values: lat1={lat1}, lat2={lat2}")
            return None
            
        if not (-180 <= lon1 <= 180) or not (-180 <= lon2 <= 180):
            logging.warning(f"Invalid longitude values: lon1={lon1}, lon2={lon2}")
            return None
        
        # If coordinates are identical, distance is 0
        if lat1 == lat2 and lon1 == lon2:
            return 0.0
            
        # Earth's radius in miles
        R = 3959.0
        
        # Convert decimal degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Calculate differences
        delta_lat = lat2_rad - lat1_rad
        delta_lon = lon2_rad - lon1_rad
        
        # Haversine formula
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        # Calculate distance
        distance = R * c
        
        logging.debug(f"Distance calculated: {distance:.2f} miles between ({lat1}, {lon1}) and ({lat2}, {lon2})")
        return distance
        
    except (ValueError, TypeError) as e:
        logging.error(f"Error calculating distance: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in calculate_distance_haversine: {e}")
        return None

def get_coordinates_from_zip_code(zip_code):
    """
    Get latitude and longitude coordinates from a ZIP code using a free geocoding service.
    
    Args:
        zip_code (str): US ZIP code (5 digits)
        
    Returns:
        tuple: (latitude, longitude) as floats, or (None, None) if not found
        
    Example:
        >>> lat, lng = get_coordinates_from_zip_code("90210")
        >>> print(f"Beverly Hills, CA: {lat}, {lng}")
    """
    try:
        if not zip_code or len(str(zip_code).strip()) != 5:
            logging.warning(f"Invalid ZIP code format: {zip_code}")
            return None, None
        
        zip_code = str(zip_code).strip()
        
        # Use Nominatim (OpenStreetMap) free geocoding service
        url = f"https://nominatim.openstreetmap.org/search"
        params = {
            'q': f"{zip_code}, USA",
            'format': 'json',
            'limit': 1,
            'countrycodes': 'us'
        }
        headers = {
            'User-Agent': 'Ready2Dink/1.0 (contact@ready2dink.com)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0:
            lat = float(data[0]['lat'])
            lng = float(data[0]['lon'])
            logging.debug(f"ZIP {zip_code} converted to coordinates: {lat}, {lng}")
            return lat, lng
        else:
            logging.warning(f"No coordinates found for ZIP code: {zip_code}")
            return None, None
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching coordinates for ZIP {zip_code}: {e}")
        return None, None
    except (ValueError, KeyError, TypeError) as e:
        logging.error(f"Error parsing coordinates for ZIP {zip_code}: {e}")
        return None, None
    except Exception as e:
        logging.error(f"Unexpected error converting ZIP {zip_code} to coordinates: {e}")
        return None, None

def validate_tournament_join_gps(user_latitude, user_longitude, tournament_instance, player_id=None):
    """
    Validate if user is within allowed radius to join a tournament based on GPS coordinates.
    
    Args:
        user_latitude (float): User's current latitude
        user_longitude (float): User's current longitude
        tournament_instance (dict/Row): Tournament instance with location data
        player_id (int, optional): Player ID for logging purposes
        
    Returns:
        dict: {
            'allowed': bool,           # True if user can join tournament
            'distance_miles': float,   # Actual distance to tournament (if calculated)
            'max_distance': float,     # Maximum allowed distance
            'error_message': str,      # User-friendly error message (if not allowed)
            'reason': str             # Technical reason for validation result
        }
    """
    try:
        # Input validation
        if user_latitude is None or user_longitude is None:
            logging.warning(f"GPS validation failed - missing user coordinates (player: {player_id})")
            return {
                'allowed': False,
                'distance_miles': None,
                'max_distance': None,
                'error_message': 'Location information is required to join tournaments. Please enable location services and try again.',
                'reason': 'missing_user_coordinates'
            }
        
        if not tournament_instance:
            logging.error(f"GPS validation failed - invalid tournament instance (player: {player_id})")
            return {
                'allowed': False,
                'distance_miles': None,
                'max_distance': None,
                'error_message': 'Tournament information is invalid. Please try again.',
                'reason': 'invalid_tournament'
            }
        
        # Check if tournament has GPS coordinates
        tournament_lat = tournament_instance.get('latitude')
        tournament_lng = tournament_instance.get('longitude')
        
        if tournament_lat is None or tournament_lng is None:
            logging.warning(f"Tournament {tournament_instance.get('name')} has no GPS coordinates - allowing join (player: {player_id})")
            return {
                'allowed': True,
                'distance_miles': None,
                'max_distance': None,
                'error_message': None,
                'reason': 'tournament_no_location'
            }
        
        # Calculate distance between user and tournament
        distance = calculate_distance_haversine(
            user_latitude, user_longitude,
            tournament_lat, tournament_lng
        )
        
        if distance is None:
            logging.error(f"GPS validation failed - could not calculate distance (player: {player_id}, tournament: {tournament_instance.get('name')})")
            return {
                'allowed': False,
                'distance_miles': None,
                'max_distance': None,
                'error_message': 'Unable to verify your location. Please check your GPS settings and try again.',
                'reason': 'distance_calculation_failed'
            }
        
        # Get tournament join radius (default 25 miles)
        join_radius = tournament_instance.get('join_radius_miles', 25)
        
        # Log the validation attempt for security auditing
        tournament_name = tournament_instance.get('name', 'Unknown Tournament')
        logging.info(f"GPS validation: Player {player_id} at ({user_latitude:.6f}, {user_longitude:.6f}) "
                    f"trying to join '{tournament_name}' at ({tournament_lat:.6f}, {tournament_lng:.6f}). "
                    f"Distance: {distance:.2f} miles, Max allowed: {join_radius} miles")
        
        # Check if user is within allowed radius
        if distance <= join_radius:
            logging.info(f"GPS validation PASSED - Player {player_id} within {join_radius} miles of {tournament_name}")
            return {
                'allowed': True,
                'distance_miles': round(distance, 2),
                'max_distance': join_radius,
                'error_message': None,
                'reason': 'within_radius'
            }
        else:
            # User is outside allowed radius
            logging.warning(f"GPS validation BLOCKED - Player {player_id} is {distance:.2f} miles from {tournament_name} "
                          f"(max allowed: {join_radius} miles)")
            
            error_message = (f"You are outside the tournament area. You are {distance:.1f} miles away, "
                           f"but this tournament only allows players within {join_radius} miles. "
                           f"Tournaments can be created anywhere in the world, but players can only see and join tournaments near them.")
            
            return {
                'allowed': False,
                'distance_miles': round(distance, 2),
                'max_distance': join_radius,
                'error_message': error_message,
                'reason': 'outside_radius'
            }
        
    except Exception as e:
        logging.error(f"Unexpected error in GPS validation (player: {player_id}): {e}")
        return {
            'allowed': False,
            'distance_miles': None,
            'max_distance': None,
            'error_message': 'Location verification failed due to a technical error. Please try again.',
            'reason': 'validation_error'
        }

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
        logging.debug(f"Sending push notification to player ID {player['id']}: {message}")
        
        # Here you would implement actual push notification sending
        # using a service like Firebase, OneSignal, or Web Push Protocol
        
        return True
    except Exception as e:
        logging.error(f"Failed to send push notification: {e}")
        return False

def send_tournament_match_notification(tournament_match_id, notification_type, custom_message=None):
    """Send notifications to both players in a tournament match with idempotency"""
    try:
        conn = get_db_connection()
        
        # Check if notifications have already been sent for this match and type
        existing_notifications = conn.execute('''
            SELECT player_id FROM match_reminders 
            WHERE tournament_match_id = ? AND reminder_type = ? AND delivery_status = 'sent'
        ''', (tournament_match_id, notification_type)).fetchall()
        
        if len(existing_notifications) >= 2:  # Both players already notified
            logging.info(f"Notifications already sent for match {tournament_match_id}, type {notification_type}")
            conn.close()
            return True
        
        # Get list of already notified players
        already_notified = {row['player_id'] for row in existing_notifications}
        
        # Get match and player details with notification preferences
        match_info = conn.execute('''
            SELECT tm.*, ti.name as tournament_name,
                   p1.full_name as player1_name, p1.email as player1_email, p1.phone_number as player1_phone,
                   p1.notifications_enabled as player1_notifications_enabled,
                   p2.full_name as player2_name, p2.email as player2_email, p2.phone_number as player2_phone,
                   p2.notifications_enabled as player2_notifications_enabled
            FROM tournament_matches tm
            JOIN tournament_instances ti ON tm.tournament_instance_id = ti.id
            JOIN players p1 ON tm.player1_id = p1.id
            LEFT JOIN players p2 ON tm.player2_id = p2.id
            WHERE tm.id = ?
        ''', (tournament_match_id,)).fetchone()
        
        if not match_info:
            logging.error(f"Tournament match {tournament_match_id} not found")
            return False
        
        # Skip if it's a bye match (no player2)
        if not match_info['player2_id']:
            logging.info(f"Skipping notification for bye match {tournament_match_id}")
            return True
        
        # Prepare notification messages based on type
        if notification_type == 'bracket_generated':
            title = f"Tournament Bracket Generated - {match_info['tournament_name']}"
            if custom_message:
                message_template = custom_message
            else:
                message_template = f"🏆 Your match in {match_info['tournament_name']} has been scheduled! You'll face {{opponent}} in Round {match_info['round_number']}. You have 7 days to coordinate and complete your match. Use the 'Plan Match' feature to schedule your game!"
        
        elif notification_type == 'match_scheduled':
            title = f"Match Scheduled - {match_info['tournament_name']}"
            message_template = custom_message or "Your tournament match has been scheduled! Check the details in your tournament dashboard."
        
        elif notification_type == 'deadline_reminder':
            title = f"Match Deadline Reminder - {match_info['tournament_name']}"
            message_template = custom_message or "⏰ Your tournament match deadline is approaching! Please complete your match soon to avoid forfeit."
            
        else:
            logging.error(f"Unknown notification type: {notification_type}")
            return False
        
        # Send notifications to both players
        for player_num in [1, 2]:
            player_id = match_info[f'player{player_num}_id']
            player_name = match_info[f'player{player_num}_name']
            player_email = match_info[f'player{player_num}_email']
            player_phone = match_info[f'player{player_num}_phone']
            player_notifications_enabled = match_info[f'player{player_num}_notifications_enabled']
            opponent_name = match_info[f'player{3-player_num}_name']  # Get the other player
            
            # Skip if player has notifications disabled
            if not player_notifications_enabled:
                logging.info(f"Skipping notification for player {player_name} - notifications disabled")
                continue
            
            # Skip if player already notified (idempotency check)
            if player_id in already_notified:
                logging.info(f"Player {player_name} already notified for match {tournament_match_id}, type {notification_type}")
                continue
            
            # Personalize message with opponent name
            personalized_message = message_template.format(opponent=opponent_name)
            
            delivery_status = 'sent'
            notification_methods = []
            
            # Send in-app notification
            try:
                conn.execute('''
                    INSERT INTO notifications (player_id, type, title, message, data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (player_id, 'tournament_match', title, personalized_message, 
                      json.dumps({'tournament_match_id': tournament_match_id, 'tournament_name': match_info['tournament_name']})))
                notification_methods.append('in_app')
                logging.info(f"In-app notification sent to {player_name}")
            except Exception as e:
                logging.error(f"Failed to send in-app notification to {player_name}: {e}")
                delivery_status = 'failed'
            
            # Send email if available
            if player_email:
                try:
                    email_html = f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h2 style="color: #00f5ff;">{title}</h2>
                        <p>Hi {player_name},</p>
                        <p>{personalized_message}</p>
                        <p><strong>Tournament:</strong> {match_info['tournament_name']}</p>
                        <p><strong>Round:</strong> {match_info['round_number']}</p>
                        <p><strong>Opponent:</strong> {opponent_name}</p>
                        <p>Log in to Ready 2 Dink to coordinate your match scheduling!</p>
                        <p>Best of luck,<br>The Ready 2 Dink Team</p>
                    </div>
                    """
                    email_sent = send_email_notification(player_email, title, email_html)
                    if email_sent:
                        notification_methods.append('email')
                        logging.info(f"Email notification sent to {player_name} ({player_email})")
                    else:
                        logging.warning(f"Failed to send email to {player_name}")
                        if delivery_status != 'failed':
                            delivery_status = 'partial'
                except Exception as e:
                    logging.error(f"Failed to send email to {player_name}: {e}")
                    if delivery_status != 'failed':
                        delivery_status = 'partial'
            
            # Record the notification in match_reminders table (idempotency protection)
            try:
                import sqlite3
                notification_method = 'all' if len(notification_methods) > 1 else (notification_methods[0] if notification_methods else 'none')
                
                # Insert with unique constraint handling for concurrency safety
                try:
                    conn.execute('''
                        INSERT INTO match_reminders (tournament_match_id, player_id, reminder_type, notification_method, delivery_status)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (tournament_match_id, player_id, notification_type, notification_method, delivery_status))
                except sqlite3.IntegrityError:
                    # Unique constraint violation - another process already sent notification, this is OK
                    logging.info(f"Notification already recorded for player {player_id}, match {tournament_match_id}, type {notification_type}")
                    # Update delivery status in case the previous attempt failed
                    conn.execute('''
                        UPDATE match_reminders 
                        SET delivery_status = ?, notification_method = ?, sent_at = CURRENT_TIMESTAMP
                        WHERE tournament_match_id = ? AND player_id = ? AND reminder_type = ?
                    ''', (delivery_status, notification_method, tournament_match_id, player_id, notification_type))
                    
            except Exception as e:
                logging.error(f"Failed to record reminder for player {player_id}: {e}")
        
        conn.commit()
        conn.close()
        logging.info(f"Tournament match notifications sent for match {tournament_match_id}, type: {notification_type}")
        return True
        
    except Exception as e:
        logging.error(f"Error sending tournament match notification: {e}")
        return False

def create_match_schedule_record(tournament_match_id):
    """Create initial match schedule record with 7-day deadline"""
    try:
        from datetime import datetime, timedelta
        
        conn = get_db_connection()
        
        # Calculate deadline (7 days from now)
        deadline_at = (datetime.now() + timedelta(days=7)).isoformat()
        
        # Get the match details to determine which player should be the initial proposer
        match = conn.execute('''
            SELECT player1_id, player2_id FROM tournament_matches WHERE id = ?
        ''', (tournament_match_id,)).fetchone()
        
        if not match or not match['player2_id']:  # Skip bye matches
            conn.close()
            return True
        
        # Create initial schedule record with player1 as proposer
        conn.execute('''
            INSERT INTO match_schedules (
                tournament_match_id, proposer_id, proposed_at, deadline_at, 
                confirmation_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (tournament_match_id, match['player1_id'], 
              datetime.now().isoformat(), deadline_at, 'pending', 
              datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        logging.info(f"Created match schedule record for tournament match {tournament_match_id} with 7-day deadline")
        return True
        
    except Exception as e:
        logging.error(f"Error creating match schedule record: {e}")
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

def suggest_match_time(player1, player2):
    """Suggest a match time based on both players' availability"""
    try:
        from datetime import datetime, timedelta
        import json
        
        # Get player availability schedules
        p1_schedule = json.loads(player1['availability_schedule']) if player1['availability_schedule'] else {}
        p2_schedule = json.loads(player2['availability_schedule']) if player2['availability_schedule'] else {}
        
        # Days of the week to check (next 7 days)
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        # Find overlapping available times
        suggested_times = []
        
        for day in days:
            p1_day = p1_schedule.get(day, {})
            p2_day = p2_schedule.get(day, {})
            
            # If both players are available this day
            if (p1_day.get('available') and p2_day.get('available')):
                p1_times = set(p1_day.get('time_slots', []))
                p2_times = set(p2_day.get('time_slots', []))
                
                # Find common time slots
                common_times = p1_times.intersection(p2_times) if p2_times else p1_times
                
                if common_times:
                    for time_slot in common_times:
                        suggested_times.append(f"{day.title()} {time_slot}")
                elif p1_times and not p2_schedule:  # Player 2 has no schedule, use Player 1's
                    for time_slot in p1_times:
                        suggested_times.append(f"{day.title()} {time_slot}")
        
        # If no specific overlapping times found, provide default suggestions
        if not suggested_times:
            # Check time preferences
            p1_pref = player1['time_preference'] if player1['time_preference'] else 'Flexible'
            p2_pref = player2['time_preference'] if player2['time_preference'] else 'Flexible' 
            
            if p1_pref == p2_pref and p1_pref != 'Flexible':
                return f"This week - {p1_pref}"
            else:
                return "This week - Flexible timing (coordinate with opponent)"
        
        # Return the first suggested time
        return suggested_times[0] if suggested_times else "This week - Flexible timing"
        
    except Exception as e:
        logging.error(f"Error suggesting match time: {e}")
        return "This week - Flexible timing"

def get_filtered_compatible_players(player_id, match_type="", skill_level="", distance=None):
    """Get list of compatible players with filters applied"""
    conn = get_db_connection()
    
    # Get the player's preferences and location
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    if not player or not player['is_looking_for_match']:
        conn.close()
        return []
    
    # Get player's coordinates for distance filtering
    player_lat = player['latitude']
    player_lng = player['longitude']
    
    # Build the SQL query with filters
    base_query = '''
        SELECT id, full_name as name, first_name, last_name, location1 as location, skill_level, preferred_court, 
               wins, losses, ranking_points, selfie, latitude, longitude, gender, search_radius_miles as travel_radius
        FROM players 
        WHERE id != ? 
        AND is_looking_for_match = 1
    '''
    params = [player_id]
    
    # Apply skill level filter
    if skill_level:
        base_query += " AND skill_level = ?"
        params.append(skill_level)
    else:
        # Default to same or adjacent skill levels if no filter specified
        skill_levels = ['Beginner', 'Intermediate', 'Advanced']
        try:
            current_skill_idx = skill_levels.index(player['skill_level'])
            # Include current level and adjacent levels
            adjacent_skills = [player['skill_level']]
            if current_skill_idx > 0:
                adjacent_skills.append(skill_levels[current_skill_idx - 1])
            if current_skill_idx < len(skill_levels) - 1:
                adjacent_skills.append(skill_levels[current_skill_idx + 1])
            
            placeholders = ','.join(['?' for _ in adjacent_skills])
            base_query += f" AND skill_level IN ({placeholders})"
            params.extend(adjacent_skills)
        except ValueError:
            # If skill level not in standard list, just use exact match
            base_query += " AND skill_level = ?"
            params.append(player['skill_level'])
    
    # Apply discoverability filter based on match type
    if match_type == "singles":
        base_query += " AND (discoverability_preference = 'singles' OR discoverability_preference = 'both' OR discoverability_preference IS NULL)"
    elif match_type == "doubles":
        base_query += " AND (discoverability_preference = 'doubles' OR discoverability_preference = 'both' OR discoverability_preference IS NULL)"
    # If no match_type specified, show all players (backward compatibility)
    
    base_query += " ORDER BY ranking_points DESC, wins DESC, created_at ASC"
    
    compatible_players = conn.execute(base_query, params).fetchall()
    
    # Calculate distances and apply distance filter
    filtered_players = []
    for p in compatible_players:
        player_data = dict(p)
        player_data['name'] = p['full_name'] 
        player_data['location'] = p['location1']
        
        # Calculate distance if both players have GPS coordinates
        if player_lat and player_lng and p['latitude'] and p['longitude']:
            distance_miles = calculate_distance(player_lat, player_lng, p['latitude'], p['longitude'])
            player_data['distance_miles'] = round(distance_miles, 1)
            
            # Apply distance filter
            if distance and distance_miles > distance:
                continue  # Skip this player if they're too far
                
            # Check if opponent is within player's travel radius 
            player_travel_radius = player['travel_radius'] if player['travel_radius'] else 25
            opponent_travel_radius = p['travel_radius'] if p['travel_radius'] else 25
            
            # Use the more restrictive radius
            max_allowed_distance = min(player_travel_radius, opponent_travel_radius)
            if distance_miles > max_allowed_distance:
                continue  # Skip if outside mutual travel range
                
        elif distance:
            # If no GPS and distance filter is applied, skip this player
            continue
        
        filtered_players.append(player_data)
    
    conn.close()
    logging.info(f"Filtered search for player {player_id}: Found {len(filtered_players)} compatible players with filters: match_type={match_type}, skill_level={skill_level}, distance={distance}")
    return filtered_players

def get_compatible_players(player_id):
    """Get list of compatible players using GPS-based distance filtering"""
    conn = get_db_connection()
    
    # Get the player's preferences and location
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    if not player or not player['is_looking_for_match']:
        conn.close()
        return []
    
    # Get player's travel radius (default 25 miles if not set)
    player_travel_radius = player['search_radius_miles'] if player['search_radius_miles'] is not None else 25
    player_lat = player['latitude']
    player_lng = player['longitude']
    
    # If player has no GPS coordinates, fallback to more inclusive matching
    if player_lat is None or player_lng is None:
        logging.warning(f"Player {player_id} has no GPS coordinates, using flexible fallback matching")
        
        # More flexible fallback - match by skill level and general area, not exact location
        # This makes it easier to find matches when GPS isn't available
        query = '''
            SELECT id, full_name as name, first_name, last_name, location1 as location, skill_level, preferred_court, 
                   wins, losses, ranking_points, selfie, latitude, longitude, gender, search_radius_miles as travel_radius
            FROM players 
            WHERE id != ? 
            AND is_looking_for_match = 1
            AND skill_level = ?
            ORDER BY ranking_points DESC, wins DESC, created_at ASC
        '''
        
        params = [player_id, player['skill_level']]
        compatible_players = conn.execute(query, params).fetchall()
        
        # If no matches with same skill level, try adjacent skill levels for more options
        if not compatible_players:
            skill_levels = ['Beginner', 'Intermediate', 'Advanced']
            current_skill_idx = skill_levels.index(player['skill_level']) if player['skill_level'] in skill_levels else 1
            
            # Try one level up or down
            adjacent_skills = []
            if current_skill_idx > 0:
                adjacent_skills.append(skill_levels[current_skill_idx - 1])
            if current_skill_idx < len(skill_levels) - 1:
                adjacent_skills.append(skill_levels[current_skill_idx + 1])
            
            for skill in adjacent_skills:
                query = '''
                    SELECT id, full_name as name, first_name, last_name, location1 as location, skill_level, preferred_court, 
                           wins, losses, ranking_points, selfie, latitude, longitude, gender, search_radius_miles as travel_radius
                    FROM players 
                    WHERE id != ? 
                    AND is_looking_for_match = 1
                    AND skill_level = ?
                    ORDER BY ranking_points DESC, wins DESC, created_at ASC
                    LIMIT 5
                '''
                adjacent_players = conn.execute(query, [player_id, skill]).fetchall()
                compatible_players.extend(adjacent_players)
                if compatible_players:  # Stop if we found some matches
                    break
        
    else:
        # GPS-based matching - get all players with same skill level and GPS coordinates
        query = '''
            SELECT id, full_name as name, first_name, last_name, location1 as location, skill_level, preferred_court, 
                   wins, losses, ranking_points, selfie, latitude, longitude, gender, search_radius_miles as travel_radius
            FROM players 
            WHERE id != ? 
            AND is_looking_for_match = 1
            AND skill_level = ?
            AND latitude IS NOT NULL 
            AND longitude IS NOT NULL
            ORDER BY ranking_points DESC, wins DESC, created_at ASC
        '''
        
        all_players = conn.execute(query, (player_id, player['skill_level'])).fetchall()
        
        # Filter by distance using GPS coordinates and both players' travel radius
        compatible_players = []
        for candidate in all_players:
            distance = calculate_distance_haversine(
                player_lat, player_lng,
                candidate['latitude'], candidate['longitude']
            )
            
            if distance is not None:
                # Check if distance is within BOTH players' travel radius
                candidate_travel_radius = candidate['travel_radius'] if candidate['travel_radius'] is not None else 25
                
                # Player must be within both their own travel radius AND the candidate's travel radius
                if distance <= player_travel_radius and distance <= candidate_travel_radius:
                    # Add distance and travel radius info to the player record
                    candidate_dict = dict(candidate)
                    candidate_dict['distance_miles'] = round(distance, 1)
                    candidate_dict['candidate_travel_radius'] = candidate_travel_radius
                    compatible_players.append(candidate_dict)
        
        # Sort by distance (closest first), then by ranking
        compatible_players.sort(key=lambda x: (x['distance_miles'], -x['ranking_points']))
        
        logging.info(f"GPS-based matching for player {player_id}: found {len(compatible_players)} players within travel radius (user: {player_travel_radius} miles)")
    
    # Convert to list of dictionaries
    players_list = []
    for p in compatible_players:
        # Use first_name if available, otherwise fall back to full_name
        display_name = p['first_name'] if p['first_name'] else p['name'].split()[0] if p['name'] else 'Unknown'
        
        player_data = {
            'id': p['id'],
            'name': display_name,
            'full_name': p['name'],
            'first_name': p['first_name'],
            'last_name': p['last_name'],
            'location': p['location'],
            'skill_level': p['skill_level'],
            'preferred_court': p['preferred_court'],
            'wins': p['wins'] or 0,
            'losses': p['losses'] or 0,
            'ranking_points': p['ranking_points'] or 0,
            'selfie': p['selfie'],
            'gender': p['gender'] if 'gender' in p else 'prefer_not_to_say',
            'travel_radius': p['travel_radius'] if 'travel_radius' in p else 25
        }
        
        # Add distance and candidate travel radius if available (for GPS-based matches)
        if 'distance_miles' in p:
            player_data['distance_miles'] = p['distance_miles']
        if 'candidate_travel_radius' in p:
            player_data['candidate_travel_radius'] = p['candidate_travel_radius']
        
        players_list.append(player_data)
    
    conn.close()
    return players_list

def find_match_for_player(player_id):
    """Find and create a match for a player using GPS-based distance filtering"""
    conn = get_db_connection()
    
    # Get the player's preferences and location
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    if not player or not player['is_looking_for_match']:
        conn.close()
        return None
    
    # Get player's search radius and GPS coordinates
    search_radius = player.get('search_radius_miles', 15)
    player_lat = player.get('latitude')
    player_lng = player.get('longitude')
    
    # If player has GPS coordinates, use GPS-based matching
    if player_lat is not None and player_lng is not None:
        # Get all players with same skill level and GPS coordinates
        query = '''
            SELECT * FROM players 
            WHERE id != ? 
            AND is_looking_for_match = 1
            AND skill_level = ?
            AND latitude IS NOT NULL 
            AND longitude IS NOT NULL
            ORDER BY created_at ASC
        '''
        
        all_candidates = conn.execute(query, (player_id, player['skill_level'])).fetchall()
        
        # Filter by distance and find first match within radius
        for candidate in all_candidates:
            distance = calculate_distance_haversine(
                player_lat, player_lng,
                candidate['latitude'], candidate['longitude']
            )
            
            if distance is not None and distance <= search_radius:
                potential_matches = candidate
                break
        else:
            potential_matches = None  # No matches found within radius
    
    else:
        # Fallback to text-based matching for players without GPS coordinates
        logging.warning(f"Player {player_id} has no GPS coordinates, using fallback matching for automatic match creation")
        
        if player['preferred_court']:
            location_condition = "(preferred_court = ? OR location1 = ? OR location2 = ?)"
            location_params = [player['preferred_court'], player['location1'], player['location2']]
        else:
            location_condition = "(location1 = ? OR location2 = ?)"
            location_params = [player['location1'], player['location2']]
        
        query = f'''
            SELECT * FROM players 
            WHERE id != ? 
            AND is_looking_for_match = 1
            AND skill_level = ?
            AND {location_condition}
            ORDER BY created_at ASC
            LIMIT 1
        '''
        
        params = [player_id, player['skill_level']] + location_params
        potential_matches = conn.execute(query, params).fetchone()
    
    if potential_matches:
        # Create a match
        # Determine court location - use shared court if both prefer same court, otherwise use a default
        if (player['preferred_court'] and potential_matches['preferred_court'] and 
            player['preferred_court'] == potential_matches['preferred_court']):
            match_court = player['preferred_court']
        elif player['preferred_court']:
            match_court = player['preferred_court']
        elif potential_matches['preferred_court']:
            match_court = potential_matches['preferred_court']
        else:
            # Default to the first player's location if no preferred courts
            match_court = player['location1'] or 'Local Court'
        
        # Set default sport to Pickleball if preferred_sport is NULL
        match_sport = player['preferred_sport'] if player['preferred_sport'] else 'Pickleball'
        
        # Generate a suggested match time based on availability
        suggested_time = suggest_match_time(player, potential_matches)
        
        cursor = conn.execute('''
            INSERT INTO matches (player1_id, player2_id, sport, court_location, status, scheduled_time)
            VALUES (?, ?, ?, ?, 'pending', ?)
        ''', (player_id, potential_matches['id'], match_sport, match_court, suggested_time))
        
        match_id = cursor.lastrowid
        
        # Keep both players available for more matches (don't mark as no longer looking)
        
        conn.commit()
        conn.close()
        return match_id
    
    conn.close()
    return None

def create_direct_challenge(challenger_id, target_id, proposed_location=None, proposed_date=None, proposed_time=None):
    """Create a direct challenge between two specific players"""
    try:
        conn = get_db_connection()
        
        # Check if both players exist
        challenger = conn.execute('SELECT * FROM players WHERE id = ?', (challenger_id,)).fetchone()
        target = conn.execute('SELECT * FROM players WHERE id = ?', (target_id,)).fetchone()
        
        if not challenger or not target:
            conn.close()
            return None
            
        # Allow unlimited challenges - removed restriction check
            
        # Use proposed location and time if provided, otherwise fall back to automatic logic
        if proposed_location:
            match_court = proposed_location
        elif (challenger['preferred_court'] and target['preferred_court'] and 
              challenger['preferred_court'] == target['preferred_court']):
            match_court = challenger['preferred_court']
        elif challenger['preferred_court']:
            match_court = challenger['preferred_court']
        elif target['preferred_court']:
            match_court = target['preferred_court']
        else:
            match_court = challenger['location1'] or 'Local Court'
        
        # Use proposed date/time if provided, otherwise suggest match time
        if proposed_date and proposed_time:
            # Combine date and time into a proper datetime string
            scheduled_time = f"{proposed_date} {proposed_time}"
        else:
            scheduled_time = suggest_match_time(challenger, target)
        
        # Create the match (default to singles for now)
        cursor = conn.execute('''
            INSERT INTO matches (player1_id, player2_id, sport, court_location, scheduled_time, status, created_at, match_type)
            VALUES (?, ?, 'Pickleball', ?, ?, 'pending', datetime('now'), 'singles')
        ''', (challenger_id, target_id, match_court, scheduled_time))
        
        match_id = cursor.lastrowid
        
        # Create team entries for the match
        create_match_teams(match_id, challenger_id, target_id, 'singles', conn=conn)
        
        conn.commit()
        conn.close()
        
        return match_id
        
    except Exception as e:
        logging.error(f"Error creating direct challenge: {str(e)}")
        return None

# Initialize database
init_db()

def send_email_notification(to_email, subject, message_body, from_email=None):
    """Send email notification using SendGrid"""
    try:
        import os
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        # Use environment variable for from email, with fallback to verified sender
        if not from_email:
            from_email = os.environ.get('FROM_EMAIL', 'admin@ready2dink.com')
        
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

def send_guardian_consent_email(guardian_email, player_name, player_id):
    """Send guardian consent form for COPPA compliance"""
    try:
        consent_url = f"https://ready2dink.com/guardian-consent/{player_id}"
        
        subject = f"🛡️ Parental Consent Required - Ready 2 Dink Authorization for {player_name}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: white;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #3F567F 0%, #D174D2 100%); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Ready 2 Dink</h1>
                <p style="color: white; margin: 5px 0; font-size: 16px;">Parental Consent Authorization Required</p>
            </div>
            
            <!-- Official Form Content -->
            <div style="padding: 30px; background: white; border: 2px solid #3F567F;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #333; margin: 0; font-size: 20px; font-weight: bold;">Parental Consent Authorization Form</h2>
                    <h3 style="color: #333; margin: 5px 0; font-size: 16px;">For Children Under 13 – Ready 2 Dink</h3>
                    <p style="color: #666; font-style: italic; margin: 15px 0;">
                        In compliance with the Children's Online Privacy Protection Act (COPPA), parental consent is required 
                        before a child under 13 can use Ready 2 Dink.
                    </p>
                </div>

                <!-- Child Information Section -->
                <div style="margin: 30px 0; padding: 20px; background: #f8f9fa; border-left: 4px solid #3F567F;">
                    <h4 style="color: #3F567F; margin-top: 0;">Child Information</h4>
                    <p style="margin: 10px 0;"><strong>Child's Full Name:</strong> {player_name}</p>
                    <p style="margin: 10px 0;"><strong>Child's Date of Birth:</strong> [From Registration Form]</p>
                </div>

                <!-- Parent/Guardian Information Section -->
                <div style="margin: 30px 0; padding: 20px; background: #f0f8ff; border-left: 4px solid #0066cc;">
                    <h4 style="color: #0066cc; margin-top: 0;">Parent/Guardian Information</h4>
                    <p style="margin: 10px 0;"><strong>Parent/Guardian Full Name:</strong> [To be completed in form]</p>
                    <p style="margin: 10px 0;"><strong>Relationship to Child:</strong> [To be completed in form]</p>
                    <p style="margin: 10px 0;"><strong>Email Address:</strong> {guardian_email}</p>
                    <p style="margin: 10px 0;"><strong>Phone Number:</strong> [To be completed in form]</p>
                </div>

                <!-- Information We Collect Section -->
                <div style="margin: 30px 0; padding: 20px; background: #fff3cd; border-left: 4px solid #ffc107;">
                    <h4 style="color: #856404; margin-top: 0;">Information We Collect</h4>
                    <p style="color: #856404;">By authorizing your child's account, you acknowledge that Ready 2 Dink will collect:</p>
                    <ul style="color: #856404; margin: 15px 0;">
                        <li>Profile photo (selfie)</li>
                        <li>Date of birth</li>
                        <li>Preferred play locations</li>
                        <li>Match results, tournament participation, and skill ratings</li>
                    </ul>
                    <p style="color: #856404; margin: 15px 0;"><strong>This information is used only to:</strong></p>
                    <ul style="color: #856404; margin: 15px 0;">
                        <li>Connect players by skill level and location</li>
                        <li>Organize tournaments and track results</li>
                        <li>Maintain a safe and fair community</li>
                    </ul>
                    <p style="color: #856404; font-weight: bold;">
                        We do not sell or share your child's personal information with third parties for marketing.
                    </p>
                </div>

                <!-- Parent/Guardian Rights Section -->
                <div style="margin: 30px 0; padding: 20px; background: #e7f3ff; border-left: 4px solid #007bff;">
                    <h4 style="color: #007bff; margin-top: 0;">Parent/Guardian Rights</h4>
                    <p style="color: #007bff;">As the parent/guardian, you have the right to:</p>
                    <ul style="color: #007bff; margin: 15px 0;">
                        <li>Review the information we collect from your child</li>
                        <li>Request deletion of your child's data</li>
                        <li>Withdraw consent and terminate your child's account at any time</li>
                    </ul>
                    <p style="color: #007bff;">
                        Requests can be made by emailing <a href="mailto:support@ready2dink.com" style="color: #007bff;">support@ready2dink.com</a>
                    </p>
                </div>

                <!-- Authorization Section -->
                <div style="margin: 30px 0; padding: 20px; background: #d4edda; border-left: 4px solid #28a745;">
                    <h4 style="color: #155724; margin-top: 0;">Authorization</h4>
                    <p style="color: #155724; margin: 15px 0;">
                        <strong>☐ I Consent</strong> – I authorize my child to create and use a Ready 2 Dink account.<br>
                        <strong>☐ I Do Not Consent</strong> – I do not authorize account creation.
                    </p>
                </div>

                <!-- Call to Action -->
                <div style="text-align: center; margin: 40px 0; padding: 30px; background: #f8f9fa; border-radius: 8px;">
                    <h3 style="color: #333; margin-bottom: 15px;">Complete Authorization Online</h3>
                    <p style="color: #666; margin: 15px 0;">
                        Click the button below to access the secure digital consent form and provide your authorization.
                    </p>
                    <a href="{consent_url}" 
                       style="background: #3F567F; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 15px 0; font-weight: bold; font-size: 16px;">
                        🛡️ Complete Consent Form
                    </a>
                    <p style="color: #666; font-size: 14px; margin-top: 15px;">
                        Your child's account will remain pending until you complete this authorization.
                    </p>
                </div>

                <!-- Important Notice -->
                <div style="background: #f8d7da; padding: 15px; border-radius: 8px; border-left: 4px solid #dc3545; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #721c24;">⚠️ Important</h4>
                    <p style="color: #721c24; margin: 0; font-size: 14px;">
                        This consent form was sent because someone indicated they are 13 years old or younger when registering. 
                        If this was submitted in error or you have concerns, please contact our support team immediately at 
                        <a href="mailto:support@ready2dink.com" style="color: #721c24;">support@ready2dink.com</a>
                    </p>
                </div>

                <!-- Footer -->
                <div style="margin-top: 30px; padding-top: 20px; border-top: 2px solid #ddd; text-align: center;">
                    <p style="color: #666; font-size: 14px; margin: 10px 0;">
                        <strong>Questions?</strong> Contact us at <a href="mailto:support@ready2dink.com">support@ready2dink.com</a>
                    </p>
                    <p style="color: #666; font-size: 12px; margin: 5px 0;">
                        Ready 2 Dink | Connecting Pickleball Players Safely<br>
                        This form complies with the Children's Online Privacy Protection Act (COPPA)
                    </p>
                </div>
            </div>
        </div>
        """
        
        return send_email_notification(guardian_email, subject, html_content)
        
    except Exception as e:
        logging.error(f"Failed to send guardian consent email: {e}")
        return False

def send_new_registration_notification(player_data):
    """Send notification when new player registers"""
    guardian_status = ""
    if player_data.get('guardian_email'):
        guardian_status = f"""
        <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h4 style="margin-top: 0; color: #856404;">🛡️ COPPA Compliance</h4>
            <p style="color: #856404; margin: 0;"><strong>Guardian Email:</strong> {player_data['guardian_email']}</p>
            <p style="color: #856404; margin: 0;"><strong>Account Status:</strong> {player_data['account_status'].upper()}</p>
            <p style="color: #856404; margin: 0;"><em>Awaiting guardian consent for underage player</em></p>
        </div>
        """
    
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
            
            {guardian_status}
            
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
    # Check both session keys used in the app
    current_player_id = session.get('player_id') or session.get('pending_player_id') or session.get('current_player_id')
    is_admin = False
    
    # Debug logging
    # Only log session info in debug mode for development
    if app.debug and os.environ.get('FLASK_ENV') == 'development':
        logging.debug(f"Context processor: user authenticated: {bool(current_player_id)}")
    
    if current_player_id:
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT is_admin FROM players WHERE id = %s', (current_player_id,))
        player = cursor.fetchone()
        conn.close()
        if player:
            is_admin = bool(player['is_admin'])
            logging.info(f"Context processor: Player found, is_admin = {is_admin}")
        else:
            logging.warning(f"Context processor: No player found with ID {current_player_id}")
    
    context = dict(current_user_is_admin=is_admin, current_player_id=current_player_id)
    logging.info(f"Context processor: Returning context = {context}")
    return context


@app.route('/logout')
def logout():
    """Clear all session data and redirect to home"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/login')
def player_login():
    """Display player login page"""
    return render_template('player_login.html')

@app.route('/login', methods=['POST'])
def player_login_post():
    """Handle player login form submission"""
    from werkzeug.security import check_password_hash
    
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Username and password are required', 'danger')
        return redirect(url_for('player_login'))
    
    conn = get_pg_connection()
    
    try:
        cursor = conn.cursor()
        # Find player by username
        cursor.execute('''
            SELECT id, full_name, username, password_hash, is_admin
            FROM players 
            WHERE username = %s
        ''', (username,))
        player = cursor.fetchone()
        
        if not player:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('player_login'))
        
        # Check password
        if not player['password_hash'] or not check_password_hash(player['password_hash'], password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('player_login'))
        
        # Login successful - set session
        session['current_player_id'] = player['id']
        session['player_id'] = player['id']  # For consistency
        
        # flash(f'Welcome back, {player["full_name"]}!', 'success')
        
        # Check NDA acceptance for regular users
        if not player['is_admin']:
            # Check if NDA has been signed
            cursor.execute('''
                SELECT nda_accepted FROM players WHERE id = %s
            ''', (player['id'],))
            nda_status = cursor.fetchone()
            
            if not nda_status or not nda_status['nda_accepted']:
                # NDA not signed - redirect to NDA page
                conn.close()
                return redirect(url_for('nda_required'))
        
        conn.close()
        
        # Redirect to appropriate dashboard
        if player['is_admin']:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('player_home', player_id=player['id']))
        
    except Exception as e:
        flash(f'Login error: {str(e)}', 'danger')
        if conn:
            conn.close()
        return redirect(url_for('player_login'))

@app.route('/')
def index():
    """Home page - check if user is logged in, otherwise show landing page"""
    # Debug: Log session contents
    # Session contents logging disabled for security in production
    
    # If user is already logged in, redirect to their dashboard
    if 'current_player_id' in session:
        player_id = session['current_player_id']
        # Check if player still exists and has accepted disclaimers
        conn = get_db_connection()
        player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
        conn.close()
        
        if player:
            # Check disclaimers first
            if not player['disclaimers_accepted'] and not player['test_account']:
                return redirect(url_for('show_disclaimers', player_id=player_id))
            
            # Then check NDA for non-admin users (only if disclaimers are done)
            if not player['is_admin'] and not player['nda_accepted']:
                return redirect(url_for('nda_required'))
            
            # All checks passed, redirect to home
            return redirect(url_for('player_home', player_id=player_id))
    
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
    
    # Check and handle trial expiry for this user
    check_and_handle_trial_expiry(player_id)
    
    # Get player info (refresh after potential trial expiry update)
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
            CASE 
                WHEN m.player1_id = ? THEN p2.latitude
                ELSE p1.latitude 
            END as opponent_latitude,
            CASE 
                WHEN m.player1_id = ? THEN p2.longitude
                ELSE p1.longitude 
            END as opponent_longitude,
            CASE 
                WHEN m.player1_id = ? THEN p2.location1
                ELSE p1.location1 
            END as opponent_location1,
            COUNT(*) as matches_played,
            MAX(m.created_at) as last_played
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        WHERE m.player1_id = ? OR m.player2_id = ?
        GROUP BY opponent_id, opponent_name, opponent_selfie, opponent_wins, opponent_losses, opponent_tournament_wins, opponent_latitude, opponent_longitude, opponent_location1
        ORDER BY last_played DESC
        LIMIT 10
    ''', (player_id, player_id, player_id, player_id, player_id, player_id, player_id, player_id, player_id, player_id, player_id)).fetchall()
    
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
    
    # Get team invitations (pair-up requests) and match challenges separately
    team_invitations = get_player_team_invitations(player_id)
    match_challenges = get_player_match_challenges(player_id)
    
    return render_template('player_home.html', 
                         player=player, 
                         connections=connections,
                         recent_matches=recent_matches,
                         tournaments=tournaments,
                         player_tournaments=player_tournaments,
                         team_invitations=team_invitations,
                         match_challenges=match_challenges,
                         available_tournaments=available_tournaments,
                         player_ranking=player_ranking,
                         leaderboard=leaderboard,
                         is_birthday=is_birthday,
                         current_player_id=player_id)

@app.route('/challenges')
def challenges():
    """Display challenges page for the current player"""
    # Check if user is logged in
    if 'player_id' not in session:
        flash('Please log in to view challenges', 'warning')
        return redirect(url_for('player_login'))
    
    player_id = session['player_id']
    conn = get_db_connection()
    
    # Verify player exists
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    if not player:
        flash('Player not found', 'danger')
        return redirect(url_for('player_login'))
    
    # Get incoming challenges (matches where this player is player2 and status is pending/counter_proposed)
    incoming_challenges = conn.execute('''
        SELECT m.*, 
               p1.full_name as challenger_name, 
               p1.selfie as challenger_selfie,
               p1.skill_level as challenger_skill,
               p1.wins as challenger_wins,
               p1.losses as challenger_losses
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        WHERE m.player2_id = ? 
        AND m.status IN ('pending', 'counter_proposed')
        ORDER BY m.created_at DESC
    ''', (player_id,)).fetchall()
    
    # Get outgoing challenges (matches where this player is player1 and status is pending/counter_proposed)
    outgoing_challenges = conn.execute('''
        SELECT m.*, 
               p2.full_name as opponent_name, 
               p2.selfie as opponent_selfie,
               p2.skill_level as opponent_skill,
               p2.wins as opponent_wins,
               p2.losses as opponent_losses
        FROM matches m
        JOIN players p2 ON m.player2_id = p2.id
        WHERE m.player1_id = ? 
        AND m.status IN ('pending', 'counter_proposed')
        ORDER BY m.created_at DESC
    ''', (player_id,)).fetchall()
    
    # Get confirmed matches - separate upcoming from past due (need score submission)
    from datetime import datetime
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    confirmed_matches = conn.execute('''
        SELECT m.*, 
               CASE 
                   WHEN m.player1_id = ? THEN p2.full_name
                   ELSE p1.full_name 
               END as opponent_name,
               CASE 
                   WHEN m.player1_id = ? THEN p2.selfie
                   ELSE p1.selfie 
               END as opponent_selfie,
               CASE 
                   WHEN m.player1_id = ? THEN p2.skill_level
                   ELSE p1.skill_level 
               END as opponent_skill,
               CASE 
                   WHEN datetime(m.scheduled_time) <= datetime('now') THEN 'past_due'
                   ELSE 'upcoming'
               END as time_status
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        WHERE (m.player1_id = ? OR m.player2_id = ?)
        AND m.status = 'confirmed'
        ORDER BY m.created_at DESC
        LIMIT 10
    ''', (player_id, player_id, player_id, player_id, player_id)).fetchall()
    
    # Get completed matches (match history)
    completed_matches = conn.execute('''
        SELECT m.*, 
               CASE 
                   WHEN m.player1_id = ? THEN p2.full_name
                   ELSE p1.full_name 
               END as opponent_name,
               CASE 
                   WHEN m.player1_id = ? THEN p2.selfie
                   ELSE p1.selfie 
               END as opponent_selfie,
               CASE 
                   WHEN m.player1_id = ? THEN p2.skill_level
                   ELSE p1.skill_level 
               END as opponent_skill,
               CASE 
                   WHEN m.winner_id = ? THEN 'won'
                   ELSE 'lost'
               END as result
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        WHERE (m.player1_id = ? OR m.player2_id = ?)
        AND m.status = 'completed'
        ORDER BY m.created_at DESC
        LIMIT 20
    ''', (player_id, player_id, player_id, player_id, player_id, player_id)).fetchall()
    
    # Get all available players for challenging (excluding current player and those with pending challenges)
    existing_challenges_query = '''
        SELECT DISTINCT 
            CASE 
                WHEN player1_id = ? THEN player2_id
                ELSE player1_id
            END as opponent_id
        FROM matches 
        WHERE (player1_id = ? OR player2_id = ?)
        AND status IN ('pending', 'counter_proposed', 'confirmed')
    '''
    
    existing_challenge_ids = [row[0] for row in conn.execute(existing_challenges_query, (player_id, player_id, player_id)).fetchall()]
    
    # Build exclusion list
    exclude_ids = [player_id] + existing_challenge_ids
    placeholders = ','.join(['?'] * len(exclude_ids))
    
    available_players = conn.execute(f'''
        SELECT id, full_name, skill_level, selfie, wins, losses, ranking_points,
               preferred_court, location1
        FROM players 
        WHERE id NOT IN ({placeholders})
        AND is_looking_for_match = 1
        ORDER BY skill_level, ranking_points DESC, wins DESC
        LIMIT 50
    ''', exclude_ids).fetchall()
    
    conn.close()
    
    response = make_response(render_template('challenges.html',
                         player=player,
                         incoming_challenges=incoming_challenges,
                         outgoing_challenges=outgoing_challenges,
                         confirmed_matches=confirmed_matches,
                         completed_matches=completed_matches,
                         available_players=available_players))
    
    # Add cache-busting headers to prevent stale data display
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    
    return response

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Player registration form"""
    if request.method == 'POST':
        logging.info(f"=== REGISTRATION POST REQUEST RECEIVED ===")
        logging.info(f"Form data keys: {list(request.form.keys())}")
        logging.info(f"Files: {list(request.files.keys())}")
        # Form validation for simplified registration
        required_fields = ['first_name', 'last_name', 'email', 'dob', 'username', 'password', 'confirm_password', 'zip_code']
        for field in required_fields:
            if not request.form.get(field):
                flash(f'{field.replace("_", " ").title()} is required', 'danger')
                return render_template('register.html', form_data=request.form)
        
        # Validate password match
        if request.form['password'] != request.form['confirm_password']:
            flash('Passwords do not match', 'danger')
            return render_template('register.html', form_data=request.form)
        
        # Validate password length
        if len(request.form['password']) < 6:
            flash('Password must be at least 6 characters long', 'danger')
            return render_template('register.html', form_data=request.form)
        
        # Check if username is already taken
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM players WHERE username = %s', (request.form['username'],))
        existing_username = cursor.fetchone()
        if existing_username:
            conn.close()
            flash('Username already taken. Please choose a different username.', 'danger')
            return render_template('register.html', form_data=request.form)
        
        # Hash password for security
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash(request.form['password'])
        
        # Process location data
        user_latitude = request.form.get('latitude', '').strip() 
        user_longitude = request.form.get('longitude', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        location_method = request.form.get('location_method', 'zip').strip()
        
        # Convert coordinates to float if they exist
        latitude = None
        longitude = None
        location_source = 'zip'
        
        if location_method == 'gps' and user_latitude and user_longitude:
            try:
                latitude = float(user_latitude)
                longitude = float(user_longitude)
                location_source = 'gps'
                logging.info(f"Registration: GPS coordinates provided - {latitude}, {longitude}")
            except (ValueError, TypeError):
                logging.warning(f"Registration: Invalid GPS coordinates provided, falling back to ZIP")
        
        # If no GPS coordinates, try to get coordinates from ZIP code
        if latitude is None and zip_code:
            try:
                lat, lng = get_coordinates_from_zip_code(zip_code)
                if lat is not None and lng is not None:
                    latitude = lat
                    longitude = lng
                    location_source = 'zip'
                    logging.info(f"Registration: Converted ZIP {zip_code} to coordinates - {latitude}, {longitude}")
                else:
                    logging.warning(f"Registration: Could not convert ZIP {zip_code} to coordinates")
            except Exception as e:
                logging.error(f"Registration: Error converting ZIP to coordinates: {e}")
        
        # Check if guardian consent is required (COPPA compliance)
        guardian_email = request.form.get('guardian_email', '').strip()
        requires_consent = bool(guardian_email)
        account_status = 'pending' if requires_consent else 'active'
        
        try:
            logging.info(f"Attempting registration for: {request.form['first_name']} {request.form['last_name']} ({request.form['email']})")
            
            # Calculate age for logging
            dob_str = request.form['dob']
            try:
                from datetime import datetime
                dob_parts = dob_str.split('-')
                birth_date = datetime(int(dob_parts[2]), int(dob_parts[0]), int(dob_parts[1]))
                today = datetime.now()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                logging.info(f"Player age: {age}, Guardian consent required: {requires_consent}")
            except:
                logging.warning(f"Could not calculate age from DOB: {dob_str}")
            
            conn = get_pg_connection()
            cursor = conn.cursor()
            full_name = f"{request.form['first_name']} {request.form['last_name']}"
            # Create location description from ZIP code or coordinates
            if latitude is not None and longitude is not None:
                location_description = f"GPS Location ({latitude:.4f}, {longitude:.4f})"
                if zip_code:
                    location_description = f"ZIP {zip_code} Area ({latitude:.4f}, {longitude:.4f})"
            else:
                location_description = f"ZIP {zip_code}" if zip_code else "Location not provided"
            
            # Generate referral code for new user
            new_user_referral_code = generate_unique_referral_code()
            
            # Set 30-day trial for new users
            from datetime import datetime, timedelta
            trial_end_date = (datetime.now() + timedelta(days=30)).isoformat()
            
            cursor.execute('''
                INSERT INTO players 
                (first_name, last_name, full_name, email, dob, username, password_hash, preferred_sport, 
                 guardian_email, account_status, guardian_consent_required, test_account, 
                 address, location1, skill_level, latitude, longitude, search_radius_miles, referral_code,
                 membership_type, trial_end_date, subscription_status,
                 can_search_players, can_send_challenges, can_receive_challenges, can_join_tournaments, can_view_leaderboard, can_view_premium_stats)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (request.form['first_name'], request.form['last_name'], full_name, request.form['email'], request.form['dob'], 
                  request.form['username'], password_hash, 'Pickleball',
                  guardian_email if guardian_email else None, account_status, 1 if requires_consent else 0, 0, 
                  f"ZIP {zip_code}" if zip_code else "Address not provided", location_description, 'Beginner',
                  latitude, longitude, 15, new_user_referral_code,
                  'premium', trial_end_date, 'trialing',
                  1, 1, 1, 1, 1, 1))
            
            player_result = cursor.fetchone()
            player_id = player_result['id']
            
            # Track referral signup if this user came through a referral link
            referrer_id=session.pop('referrer_player_id', None); code=session.pop('referral_code', None)
            if referrer_id and referrer_id!=player_id:
                cursor.execute('INSERT INTO universal_referrals (referrer_player_id, referred_player_id, referral_code) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING', (referrer_id, player_id, code))
            
            conn.commit()
            conn.close()
            
            # Send email notification to admin about new registration
            player_data = {
                'first_name': request.form['first_name'],
                'last_name': request.form['last_name'],
                'full_name': full_name,
                'email': request.form['email'],
                'username': request.form['username'],
                'dob': request.form['dob'],
                'guardian_email': guardian_email,
                'account_status': account_status,
                'skill_level': 'Beginner',
                'location1': 'Location not provided',
                'preferred_court': 'Not specified',
                'address': 'Address not provided',
                'location2': None
            }
            
            email_sent = send_new_registration_notification(player_data)
            
            if email_sent:
                logging.info(f"New registration email notification sent successfully for player {player_data.get('username', 'unknown')}")
            else:
                logging.warning(f"Failed to send email notification for new registration: {player_data['full_name']}")
            
            # Send guardian consent email if required
            if requires_consent and guardian_email:
                consent_sent = send_guardian_consent_email(guardian_email, full_name, player_id)
                if consent_sent:
                    logging.info(f"Guardian consent email sent to {guardian_email} for underage player registration")
                    flash('Registration submitted! A consent form has been sent to your guardian for approval. Your account will be activated once they complete the authorization.', 'info')
                else:
                    logging.warning(f"Failed to send guardian consent email to {guardian_email}")
                    flash('Registration successful, but we had trouble sending the guardian consent email. Please contact support.', 'warning')
                
                # Redirect to pending approval page for underage players
                return redirect(url_for('pending_guardian_approval', player_id=player_id))
            else:
                flash('Registration successful! Please review and accept our NDA and terms to continue.', 'success')
                # Set session to automatically log them in after NDA
                session['pending_player_id'] = player_id
                return redirect(url_for('nda_required'))
            
        except sqlite3.IntegrityError as e:
            error_message = str(e).lower()
            logging.error(f"Registration failed - Database constraint error: {request.form['email']} - {str(e)}")
            
            if 'unique constraint failed' in error_message and 'email' in error_message:
                flash('Email already exists. Please use a different email address.', 'danger')
            elif 'unique constraint failed' in error_message and 'username' in error_message:
                flash('Username already taken. Please choose a different username.', 'danger')
            else:
                flash('Registration failed due to a data validation error. Please check your information and try again.', 'danger')
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
        
        # Log the user in automatically
        session['current_player_id'] = int(player_id)
        session['player_id'] = int(player_id)
        session['show_profile_completion'] = True  # Flag to show completion prompt
        
        flash('Thank you for accepting our terms! Welcome to Ready 2 Dink!', 'success')
        # Try to find a match for the new player now that they've accepted terms
        find_match_for_player(int(player_id))
        return redirect(url_for('player_home', player_id=player_id))
        
    except Exception as e:
        flash(f'Error accepting disclaimers: {str(e)}', 'danger')
        return redirect(url_for('show_disclaimers', player_id=player_id))

@app.route('/guardian-consent/<int:player_id>')
def guardian_consent_form(player_id):
    """Display guardian consent form for COPPA compliance"""
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    conn.close()
    
    if not player:
        flash('Player not found', 'danger')
        return redirect(url_for('index'))
    
    if not player['guardian_consent_required']:
        flash('Guardian consent is not required for this player', 'info')
        return redirect(url_for('index'))
    
    if player['account_status'] == 'active':
        flash('This player has already been activated', 'success')
        return redirect(url_for('index'))
    
    return render_template('guardian_consent.html', player=player)

@app.route('/guardian-consent/<int:player_id>/submit', methods=['POST'])
def submit_guardian_consent(player_id):
    """Process guardian consent form submission"""
    consent_given = request.form.get('consent_given')
    guardian_name = request.form.get('guardian_name', '').strip()
    
    if not consent_given or not guardian_name:
        flash('All fields are required to provide consent', 'danger')
        return redirect(url_for('guardian_consent_form', player_id=player_id))
    
    try:
        from datetime import datetime
        consent_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
        conn.execute('''
            UPDATE players 
            SET account_status = 'active', 
                guardian_consent_date = ?,
                disclaimers_accepted = 1
            WHERE id = ?
        ''', (consent_date, player_id))
        conn.commit()
        
        # Get player details for notification
        player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
        conn.close()
        
        if player:
            # Send activation notification email to player
            activation_subject = "🎉 Ready 2 Dink Account Activated!"
            activation_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0;">Ready 2 Dink</h1>
                    <p style="color: white; margin: 5px 0;">Account Activated!</p>
                </div>
                
                <div style="padding: 30px; background: #f8f9fa;">
                    <h2 style="color: #333;">Great news, {player['full_name']}!</h2>
                    
                    <p>Your guardian has provided consent and your Ready 2 Dink account is now <strong>ACTIVE</strong>!</p>
                    
                    <div style="background: #d4edda; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #155724;">🎉 Welcome to Ready 2 Dink!</h3>
                        <p style="color: #155724; margin: 0;">
                            You can now start matching with other pickleball players, join tournaments, and enjoy all the features of our platform.
                        </p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://ready2dink.com/player_home/{player['id']}" 
                           style="background: #10B981; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold;">
                            🎾 Start Playing!
                        </a>
                    </div>
                </div>
            </div>
            """
            
            send_email_notification(player['email'], activation_subject, activation_body)
            logging.info(f"Guardian consent provided for player {player_id}. Account activated.")
        
        flash(f'Thank you for providing consent! {player["full_name"]}\'s account has been activated and they can now use Ready 2 Dink.', 'success')
        return render_template('guardian_consent_success.html', player=player, guardian_name=guardian_name)
        
    except Exception as e:
        logging.error(f"Error processing guardian consent for player {player_id}: {str(e)}")
        flash(f'Error processing consent: {str(e)}', 'danger')
        return redirect(url_for('guardian_consent_form', player_id=player_id))

@app.route('/pending-guardian-approval/<int:player_id>')
def pending_guardian_approval(player_id):
    """Show pending approval page for underage players"""
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    conn.close()
    
    if not player:
        flash('Player not found', 'danger')
        return redirect(url_for('index'))
    
    if not player['guardian_consent_required']:
        flash('Guardian consent is not required for this player', 'info')
        return redirect(url_for('show_disclaimers', player_id=player_id))
    
    if player['account_status'] == 'active':
        flash('Your account has been activated! Welcome to Ready 2 Dink!', 'success')
        return redirect(url_for('player_home', player_id=player_id))
    
    return render_template('pending_guardian_approval.html', player=player)

@app.route('/qa')
def qa():
    """Q&A help page"""
    return render_template('qa.html')

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
    
    try:
        # Start transaction for bracket generation
        conn.execute('BEGIN IMMEDIATE')
        
        # Get all players in this tournament
        players = conn.execute('''
            SELECT t.*, p.full_name, p.selfie 
            FROM tournaments t
            JOIN players p ON t.player_id = p.id
            WHERE t.tournament_instance_id = ?
            ORDER BY t.created_at
        ''', (tournament_instance_id,)).fetchall()
        
        if len(players) < 2:
            conn.rollback()
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
        matches_to_notify = []  # Store matches that need notifications
        
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
            
            match_id = cursor.lastrowid
            matches_created.append(match_id)
            
            # For matches with both players (not bye matches)
            if player2:
                # Store match for notification after successful commit
                matches_to_notify.append(match_id)
        
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
        
        # Commit the bracket creation transaction first
        conn.commit()
        logging.info(f"Tournament bracket generated for tournament {tournament_instance_id} with {len(matches_created)} matches")
        
        # Send notifications and create match schedules after successful commit
        notifications_sent = 0
        for match_id in matches_to_notify:
            try:
                # Create match schedule record with 7-day deadline
                create_match_schedule_record(match_id)
                
                # Send bracket generated notifications to both players
                send_tournament_match_notification(match_id, 'bracket_generated')
                notifications_sent += 1
            except Exception as e:
                logging.error(f"Failed to send notification for match {match_id}: {e}")
        
        conn.close()
        logging.info(f"Tournament bracket complete: {notifications_sent} matches notified out of {len(matches_to_notify)}")
        return True
        
    except Exception as e:
        logging.error(f"Error generating tournament bracket: {e}")
        conn.rollback()
        conn.close()
        return False

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
    
    # Check if current player is in this tournament - Enhanced validation
    current_player_id = session.get('current_player_id')
    player_entry = None
    if current_player_id:
        player_entry = conn.execute('''
            SELECT * FROM tournaments 
            WHERE player_id = ? AND tournament_instance_id = ?
        ''', (current_player_id, tournament_instance_id)).fetchone()
        
        # Enhanced enrollment validation
        if not player_entry:
            logging.warning(f"Player {current_player_id} attempted to access tournament bracket {tournament_instance_id} without enrollment")
            flash(f'Access denied: You are not enrolled in "{tournament["name"]}". Please join the tournament first to view its bracket.', 'warning')
            conn.close()
            return redirect(url_for('tournaments_overview'))
    
    # Get tournament matches with player details
    matches = conn.execute('''
        SELECT tm.*,
               p1.full_name as player1_name, p1.selfie as player1_selfie, p1.skill_level as player1_skill,
               p2.full_name as player2_name, p2.selfie as player2_selfie, p2.skill_level as player2_skill
        FROM tournament_matches tm
        LEFT JOIN players p1 ON tm.player1_id = p1.id
        LEFT JOIN players p2 ON tm.player2_id = p2.id
        WHERE tm.tournament_instance_id = ?
        ORDER BY tm.round_number, tm.match_number
    ''', (tournament_instance_id,)).fetchall()
    
    # Group matches by round and add enhanced context
    matches_by_round = {}
    max_rounds = 0
    player_match_context = {}
    
    for match in matches:
        round_num = match['round_number']
        if round_num not in matches_by_round:
            matches_by_round[round_num] = []
        matches_by_round[round_num].append(match)
        max_rounds = max(max_rounds, round_num)
        
        # Track player context for enhanced information
        if match['player1_id']:
            player_match_context[match['player1_id']] = {
                'current_round': round_num,
                'match_id': match['id'],
                'opponent_id': match['player2_id'],
                'opponent_name': match['player2_name'],
                'status': match['status'],
                'is_winner': match['winner_id'] == match['player1_id'] if match['winner_id'] else None
            }
        if match['player2_id']:
            player_match_context[match['player2_id']] = {
                'current_round': round_num,
                'match_id': match['id'],
                'opponent_id': match['player1_id'],
                'opponent_name': match['player1_name'],
                'status': match['status'],
                'is_winner': match['winner_id'] == match['player2_id'] if match['winner_id'] else None
            }
    
    # Enhanced player context if current player is in tournament
    current_player_context = None
    if player_entry and current_player_id:
        # Get player's previous matches in this tournament
        previous_matches = conn.execute('''
            SELECT tm.*,
                   CASE WHEN tm.player1_id = ? THEN p2.full_name ELSE p1.full_name END as opponent_name,
                   CASE WHEN tm.player1_id = ? THEN tm.player2_score ELSE tm.player1_score END as opponent_score,
                   CASE WHEN tm.player1_id = ? THEN tm.player1_score ELSE tm.player2_score END as your_score
            FROM tournament_matches tm
            LEFT JOIN players p1 ON tm.player1_id = p1.id
            LEFT JOIN players p2 ON tm.player2_id = p2.id
            WHERE tm.tournament_instance_id = ? 
            AND (tm.player1_id = ? OR tm.player2_id = ?)
            AND tm.status = 'completed'
            ORDER BY tm.round_number DESC
        ''', (current_player_id, current_player_id, current_player_id, tournament_instance_id, current_player_id, current_player_id)).fetchall()
        
        # Get player's upcoming matches with proper ordering
        upcoming_matches = conn.execute('''
            SELECT tm.*,
                   CASE WHEN tm.player1_id = ? THEN p2.full_name ELSE p1.full_name END as opponent_name,
                   CASE WHEN tm.player1_id = ? THEN p2.skill_level ELSE p1.skill_level END as opponent_skill,
                   CASE WHEN tm.player1_id = ? THEN tm.player2_id ELSE tm.player1_id END as opponent_id
            FROM tournament_matches tm
            LEFT JOIN players p1 ON tm.player1_id = p1.id
            LEFT JOIN players p2 ON tm.player2_id = p2.id
            WHERE tm.tournament_instance_id = ? 
            AND (tm.player1_id = ? OR tm.player2_id = ?)
            AND tm.status IN ('pending', 'in_progress')
            ORDER BY tm.round_number ASC, tm.match_number ASC
            LIMIT 2
        ''', (current_player_id, current_player_id, current_player_id, tournament_instance_id, current_player_id, current_player_id)).fetchall()
        
        # Get next opponent's last match for the first upcoming match
        next_opponent_last_match = None
        if upcoming_matches and upcoming_matches[0]['opponent_id']:
            next_opponent_id = upcoming_matches[0]['opponent_id']
            next_opponent_last_match = conn.execute('''
                SELECT tm.*,
                       CASE WHEN tm.player1_id = ? THEN p2.full_name ELSE p1.full_name END as opponent_opponent_name,
                       CASE WHEN tm.player1_id = ? THEN tm.player2_score ELSE tm.player1_score END as opponent_opponent_score,
                       CASE WHEN tm.player1_id = ? THEN tm.player1_score ELSE tm.player2_score END as next_opponent_score,
                       CASE WHEN tm.winner_id = ? THEN 'W' ELSE 'L' END as next_opponent_result
                FROM tournament_matches tm
                LEFT JOIN players p1 ON tm.player1_id = p1.id
                LEFT JOIN players p2 ON tm.player2_id = p2.id
                WHERE tm.tournament_instance_id = ? 
                AND (tm.player1_id = ? OR tm.player2_id = ?)
                AND tm.status = 'completed'
                ORDER BY tm.round_number DESC, tm.match_number DESC
                LIMIT 1
            ''', (next_opponent_id, next_opponent_id, next_opponent_id, next_opponent_id, tournament_instance_id, next_opponent_id, next_opponent_id)).fetchone()
        
        # Determine player status in tournament
        player_status = 'Awaiting Bracket'
        if previous_matches or upcoming_matches:
            # Check if player has been eliminated
            is_eliminated = False
            for match in previous_matches:
                if match['status'] == 'completed' and match['winner_id'] and match['winner_id'] != current_player_id:
                    is_eliminated = True
                    break
            
            if is_eliminated and not upcoming_matches:
                player_status = 'Eliminated'
            elif upcoming_matches:
                player_status = 'Active'
            elif previous_matches and not upcoming_matches and tournament['status'] == 'completed':
                # Player completed all their matches
                player_status = 'Tournament Complete'
            else:
                player_status = 'Awaiting Next Round'
        
        current_player_context = {
            'previous_matches': previous_matches if previous_matches else [],
            'upcoming_matches': upcoming_matches if upcoming_matches else [],
            'next_opponent_last_match': next_opponent_last_match,
            'player_status': player_status,
            'total_wins': len([m for m in previous_matches if m.get('winner_id') == current_player_id]) if previous_matches else 0,
            'total_matches_played': len(previous_matches) if previous_matches else 0
        }
    
    conn.close()
    
    return render_template('tournament_bracket.html',
                         tournament=tournament,
                         matches=matches,
                         matches_by_round=matches_by_round,
                         max_rounds=max_rounds,
                         player_entry=player_entry,
                         current_player_id=current_player_id,
                         player_match_context=player_match_context,
                         current_player_context=current_player_context)

@app.route('/leaderboard')
@require_permission('can_view_leaderboard')
def leaderboard():
    """Display player leaderboard by skill levels - requires premium membership"""
    beginner_leaderboard = get_leaderboard(50, 'Beginner')
    intermediate_leaderboard = get_leaderboard(50, 'Intermediate') 
    advanced_leaderboard = get_leaderboard(50, 'Advanced')
    
    return render_template('leaderboard.html', 
                         beginner_leaderboard=beginner_leaderboard,
                         intermediate_leaderboard=intermediate_leaderboard,
                         advanced_leaderboard=advanced_leaderboard)

@app.route('/subscribe-notifications', methods=['POST'])
def subscribe_notifications():
    """Handle push notification subscription"""
    try:
        logging.info(f"Notification subscription attempt - player_id: {session.get('player_id', 'not_found')}")
        
        if 'player_id' not in session:
            logging.warning("No player_id in session for notification subscription")
            return jsonify({'success': False, 'message': 'Not logged in'})
        
        data = request.get_json()
        logging.info(f"Received subscription data: {data}")
        
        subscription = data.get('subscription') if data else None
        
        if not subscription:
            logging.warning("No subscription data received")
            return jsonify({'success': False, 'message': 'No subscription data'})
        
        conn = get_db_connection()
        conn.execute('''
            UPDATE players 
            SET push_subscription = ?, notifications_enabled = 1
            WHERE id = ?
        ''', (json.dumps(subscription), session['player_id']))
        conn.commit()
        conn.close()
        
        logging.info(f"Successfully enabled notifications for player {session['player_id']}")
        return jsonify({'success': True, 'message': 'Notifications enabled successfully!'})
        
    except Exception as e:
        logging.error(f"Error in subscribe_notifications: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

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

@app.route('/sign-nda', methods=['POST'])
def sign_nda():
    """Handle NDA digital signature submission"""
    try:
        # Handle both logged-in users and pending registrations
        player_id = session.get('player_id') or session.get('pending_player_id')
        
        if not player_id:
            return jsonify({'success': False, 'message': 'Not logged in'})
        
        data = request.get_json()
        signature = data.get('signature', '').strip()
        
        if len(signature) < 3:
            return jsonify({'success': False, 'message': 'Signature must be at least 3 characters'})
        
        # Get client IP address for legal record
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # Record NDA acceptance in database
        conn = get_db_connection()
        
        # Get player details for email
        player = conn.execute('''
            SELECT * FROM players WHERE id = ?
        ''', (player_id,)).fetchone()
        
        if not player:
            conn.close()
            return jsonify({'success': False, 'message': 'Player not found'})
        
        # Update NDA status
        conn.execute('''
            UPDATE players 
            SET nda_accepted = 1,
                nda_accepted_date = datetime('now'),
                nda_signature = ?,
                nda_ip_address = ?
            WHERE id = ?
        ''', (signature, client_ip, player_id))
        conn.commit()
        conn.close()
        
        # Send email notification
        nda_date = datetime.now().strftime('%Y-%m-%d at %I:%M %p UTC')
        email_sent = send_nda_confirmation_email(
            player_data=dict(player),
            signature=signature,
            nda_date=nda_date,
            ip_address=client_ip
        )
        
        if email_sent:
            logging.info(f"NDA signed by player {player_id} with signature '{signature}' from IP {client_ip} - Email sent")
        else:
            logging.warning(f"NDA signed by player {player_id} with signature '{signature}' from IP {client_ip} - Email failed")
        
        # Set the session player_id if it was a pending registration
        if 'pending_player_id' in session:
            session['player_id'] = player_id
        
        return jsonify({'success': True, 'message': 'NDA signed successfully!'})
        
    except Exception as e:
        logging.error(f"Error in sign_nda: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/nda-required')
def nda_required():
    """Show NDA requirement page for users who haven't signed yet"""
    # Handle both logged-in users and pending registrations
    player_id = session.get('player_id') or session.get('pending_player_id')
    
    if not player_id:
        return redirect(url_for('player_login'))
    
    # Check if already signed
    conn = get_db_connection()
    player = conn.execute('''
        SELECT nda_accepted FROM players WHERE id = ?
    ''', (player_id,)).fetchone()
    conn.close()
    
    if player and player['nda_accepted']:
        # Already signed, check if this is a new registration flow
        if 'pending_player_id' in session:
            # Continue to disclaimers for new registrations
            return redirect(url_for('show_disclaimers', player_id=player_id))
        else:
            # Already established user, go to home
            return redirect(url_for('player_home', player_id=player_id))
    
    return render_template('nda_required.html')

@app.route('/toggle-notifications', methods=['POST'])
def toggle_notifications():
    """Simple toggle for notification preferences"""
    try:
        if 'player_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'})
        
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        conn = get_db_connection()
        conn.execute('''
            UPDATE players 
            SET notifications_enabled = ?
            WHERE id = ?
        ''', (1 if enabled else 0, session['player_id']))
        conn.commit()
        conn.close()
        
        status = "enabled" if enabled else "disabled"
        logging.info(f"Notifications {status} for player {session['player_id']}")
        return jsonify({'success': True, 'message': f'Notifications {status} successfully!'})
        
    except Exception as e:
        logging.error(f"Error in toggle_notifications: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

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

@app.route('/withdraw-from-tournament', methods=['POST'])
def withdraw_from_tournament():
    """Handle tournament withdrawal requests"""
    tournament_id = request.form.get('tournament_id')
    
    if not tournament_id:
        flash('Invalid tournament ID', 'danger')
        return redirect(url_for('tournaments_overview'))
    
    conn = get_db_connection()
    
    try:
        # Get tournament details first
        tournament = conn.execute('''
            SELECT * FROM tournaments WHERE id = ?
        ''', (tournament_id,)).fetchone()
        
        if not tournament:
            flash('Tournament not found', 'danger')
            return redirect(url_for('tournaments_overview'))
        
        # Check if current user owns this tournament entry
        current_player_id = session.get('current_player_id')
        if not current_player_id or tournament['player_id'] != current_player_id:
            flash('You can only withdraw from your own tournaments', 'danger')
            return redirect(url_for('tournaments_overview'))
        
        # Delete the tournament entry
        conn.execute('DELETE FROM tournaments WHERE id = ?', (tournament_id,))
        conn.commit()
        
        flash(f'Successfully withdrawn from {tournament["tournament_name"]}. Entry fees are non-refundable.', 'info')
        
    except Exception as e:
        flash(f'Error withdrawing from tournament: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('tournaments_overview'))

@app.route('/tournaments')
@require_permission('can_join_tournaments')
def tournaments_overview():
    """Tournament overview page - requires premium membership"""
    # User is already authenticated and has permission via decorator
    current_player_id = session.get('current_player_id')
    
    conn = get_db_connection()
    
    # Get current player's location data from database
    player = conn.execute('SELECT * FROM players WHERE id = ?', (current_player_id,)).fetchone()
    if not player:
        flash('Player profile not found', 'danger')
        conn.close()
        return redirect(url_for('player_login'))
    
    # Use player's stored GPS coordinates and search radius
    try:
        user_lat = player['latitude'] if player['latitude'] is not None else None
    except (KeyError, TypeError):
        user_lat = None
        
    try:
        user_lng = player['longitude'] if player['longitude'] is not None else None
    except (KeyError, TypeError):
        user_lng = None
        
    try:
        search_radius = player['travel_radius'] if player['travel_radius'] is not None else 25
    except (KeyError, TypeError):
        search_radius = 25  # Default to 25 miles
    
    # Enable location filtering if player has GPS coordinates
    location_filter_enabled = (user_lat is not None and user_lng is not None)
    
    if not location_filter_enabled:
        logging.info(f"Player {current_player_id} has no GPS coordinates - showing all tournaments")
    else:
        logging.info(f"Player {current_player_id} location filtering: {search_radius} mile travel radius from ({user_lat:.4f}, {user_lng:.4f})")
    
    tournament_levels = get_tournament_levels()
    
    # Get current tournament entries count for each level
    for level_key in tournament_levels:
        count = conn.execute('''
            SELECT COUNT(*) as count FROM tournaments 
            WHERE tournament_level = ? AND completed = 0
        ''', (level_key,)).fetchone()['count']
        tournament_levels[level_key]['current_entries'] = count
        tournament_levels[level_key]['spots_remaining'] = tournament_levels[level_key]['max_players'] - count
    
    # Get tournament instances (like upcoming championship) with location filtering
    tournament_instances_query = '''
        SELECT * FROM tournament_instances 
        WHERE status IN ('open', 'upcoming')
        ORDER BY 
            CASE 
                WHEN status = 'open' THEN 1 
                WHEN status = 'upcoming' THEN 2 
            END,
            created_at DESC
    '''
    
    all_tournament_instances = conn.execute(tournament_instances_query).fetchall()
    
    # Filter tournament instances by location if user location is provided
    tournament_instances = []
    if location_filter_enabled and user_lat is not None and user_lng is not None:
        logging.info(f"Filtering tournaments by user location: {user_lat}, {user_lng}")
        
        for instance in all_tournament_instances:
            # Skip tournaments without location data
            if instance['latitude'] is None or instance['longitude'] is None:
                logging.debug(f"Skipping tournament {instance['name']} - no GPS coordinates")
                continue
            
            # Calculate distance between user and tournament
            distance = calculate_distance_haversine(
                user_lat, user_lng, 
                instance['latitude'], instance['longitude']
            )
            
            if distance is None:
                logging.warning(f"Could not calculate distance for tournament {instance['name']}")
                continue
            
            # Check if tournament is within player's search radius
            if distance <= search_radius:
                # Convert to dict and add distance info
                instance_dict = dict(instance)
                instance_dict['distance_miles'] = round(distance, 1)
                tournament_instances.append(instance_dict)
                logging.debug(f"Including tournament {instance['name']} - {distance:.1f} miles away (within {search_radius} mi radius)")
            else:
                logging.debug(f"Excluding tournament {instance['name']} - {distance:.1f} miles away (outside {search_radius} mi radius)")
        
        # Sort by distance (closest first)
        tournament_instances.sort(key=lambda x: x.get('distance_miles', float('inf')))
        
        logging.info(f"Found {len(tournament_instances)} tournaments within range out of {len(all_tournament_instances)} total")
    else:
        # No location filtering - show all tournaments but add distance info if possible
        tournament_instances = []
        for instance in all_tournament_instances:
            instance_dict = dict(instance)
            
            # Add distance info if both user and tournament have coordinates
            if (user_lat is not None and user_lng is not None and 
                instance['latitude'] is not None and instance['longitude'] is not None):
                distance = calculate_distance_haversine(
                    user_lat, user_lng, 
                    instance['latitude'], instance['longitude']
                )
                if distance is not None:
                    instance_dict['distance_miles'] = round(distance, 1)
            
            tournament_instances.append(instance_dict)
    
    # Get custom tournaments created by users with location filtering
    custom_tournaments_query = '''
        SELECT ct.*, p.full_name as organizer_name, p.selfie as organizer_selfie
        FROM custom_tournaments ct
        JOIN players p ON ct.organizer_id = p.id
        WHERE ct.status = 'open' 
        AND datetime(ct.registration_deadline) > datetime('now')
        ORDER BY ct.created_at DESC
    '''
    
    all_custom_tournaments = conn.execute(custom_tournaments_query).fetchall()
    
    # Filter custom tournaments by location if user location is provided
    custom_tournaments = []
    if location_filter_enabled and user_lat is not None and user_lng is not None:
        for tournament in all_custom_tournaments:
            # Skip tournaments without location data
            if tournament['latitude'] is None or tournament['longitude'] is None:
                continue
            
            # Calculate distance
            distance = calculate_distance_haversine(
                user_lat, user_lng, 
                tournament['latitude'], tournament['longitude']
            )
            
            if distance is None:
                continue
            
            # Check if tournament is within user's search radius (not tournament's join radius)
            # Use the user's preferred search distance for consistency
            if distance <= search_radius:
                tournament_dict = dict(tournament)
                tournament_dict['distance_miles'] = round(distance, 1)
                custom_tournaments.append(tournament_dict)
        
        # Sort by distance
        custom_tournaments.sort(key=lambda x: x.get('distance_miles', float('inf')))
    else:
        # No location filtering - show all custom tournaments but add distance info if possible
        custom_tournaments = []
        for tournament in all_custom_tournaments:
            tournament_dict = dict(tournament)
            
            # Add distance info if both user and tournament have coordinates
            if (user_lat is not None and user_lng is not None and 
                tournament['latitude'] is not None and tournament['longitude'] is not None):
                distance = calculate_distance_haversine(
                    user_lat, user_lng, 
                    tournament['latitude'], tournament['longitude']
                )
                if distance is not None:
                    tournament_dict['distance_miles'] = round(distance, 1)
            
            custom_tournaments.append(tournament_dict)
    
    # Get recent tournament entries - FIXED TO SHOW ONLY CURRENT USER'S ENTRIES
    logging.info(f"DEBUG: Fetching recent tournament entries for current user {current_player_id}")
    recent_entries = conn.execute('''
        SELECT t.*, p.full_name, p.selfie
        FROM tournaments t
        JOIN players p ON t.player_id = p.id
        WHERE t.tournament_level IS NOT NULL 
        AND t.player_id = ?
        ORDER BY t.created_at DESC
        LIMIT 10
    ''', (current_player_id,)).fetchall()
    logging.info(f"DEBUG: Found {len(recent_entries)} recent tournament entries for current user")
    for entry in recent_entries:
        logging.debug(f"Tournament entry details - ID: {entry['id']}, Player ID: {entry['player_id']}, Tournament: {entry['tournament_name']}, Level: {entry['tournament_level']}")
    
    # Get all registered players for quick access
    players = conn.execute('SELECT id, full_name, skill_level FROM players ORDER BY full_name').fetchall()
    
    # Get tournament brackets for the current player - ADD DEBUG LOGGING
    logging.info(f"DEBUG: Fetching tournament brackets for current_player_id: {current_player_id}")
    my_tournament_brackets = conn.execute('''
        SELECT DISTINCT 
            ti.id as tournament_instance_id,
            ti.name as tournament_name,
            ti.skill_level,
            ti.status as tournament_status,
            t.tournament_type,
            t.entry_date,
            COUNT(DISTINCT tm.id) as total_matches,
            COUNT(DISTINCT CASE WHEN tm.status = 'completed' THEN tm.id END) as completed_matches,
            MAX(tm.round_number) as current_round,
            (SELECT COUNT(DISTINCT round_number) FROM tournament_matches 
             WHERE tournament_instance_id = ti.id) as total_rounds,
            CASE 
                WHEN COUNT(DISTINCT tm.id) = 0 THEN 'No Bracket Yet'
                WHEN ti.status = 'completed' THEN 'Tournament Complete'
                WHEN MAX(tm.round_number) = (SELECT MAX(round_number) FROM tournament_matches 
                                           WHERE tournament_instance_id = ti.id
                                           AND status = 'completed') THEN 'Final Round'
                ELSE 'Round ' || COALESCE(MAX(CASE WHEN tm.status IN ('pending', 'active') THEN tm.round_number END), 1)
            END as bracket_status,
            CASE 
                WHEN EXISTS (SELECT 1 FROM tournament_matches tm2 
                           WHERE tm2.tournament_instance_id = ti.id 
                           AND (tm2.player1_id = ? OR tm2.player2_id = ?)
                           AND tm2.winner_id = ?) THEN 'Advanced'
                WHEN EXISTS (SELECT 1 FROM tournament_matches tm2 
                           WHERE tm2.tournament_instance_id = ti.id 
                           AND (tm2.player1_id = ? OR tm2.player2_id = ?)
                           AND tm2.status = 'completed'
                           AND tm2.winner_id != ?) THEN 'Eliminated'
                WHEN COUNT(DISTINCT CASE WHEN tm.status IN ('pending', 'active') THEN tm.id END) > 0 THEN 'Active'
                ELSE 'Awaiting Bracket'
            END as player_status
        FROM tournaments t
        JOIN tournament_instances ti ON t.tournament_instance_id = ti.id
        LEFT JOIN tournament_matches tm ON ti.id = tm.tournament_instance_id
        WHERE t.player_id = ?
        GROUP BY ti.id, ti.name, ti.skill_level, ti.status, t.tournament_type, t.entry_date
        ORDER BY t.entry_date DESC
    ''', (current_player_id, current_player_id, current_player_id, 
          current_player_id, current_player_id, current_player_id,
          current_player_id)).fetchall()
    logging.info(f"DEBUG: Found {len(my_tournament_brackets)} tournament brackets for player {current_player_id}")
    for bracket in my_tournament_brackets:
        logging.info(f"DEBUG: Bracket - Tournament: {bracket['tournament_name']}, Status: {bracket['tournament_status']}, Player Status: {bracket['player_status']}")
        logging.info(f"DEBUG: Bracket Details - Total Matches: {bracket['total_matches']}, Bracket Status: {bracket['bracket_status']}, Current Round: {bracket['current_round']}, Total Rounds: {bracket['total_rounds']}")
    
    conn.close()
    
    # Add comprehensive location filter info to template context
    total_tournaments = len(all_tournament_instances)
    total_custom_tournaments = len(all_custom_tournaments)
    
    # Count tournaments with GPS data
    tournaments_with_gps = sum(1 for t in all_tournament_instances if t['latitude'] is not None and t['longitude'] is not None)
    custom_tournaments_with_gps = sum(1 for t in all_custom_tournaments if t['latitude'] is not None and t['longitude'] is not None)
    
    # Calculate average distance for displayed tournaments (if user location available)
    avg_distance = None
    min_distance = None
    max_distance = None
    
    if user_lat is not None and user_lng is not None:
        displayed_tournaments_with_distance = [t for t in tournament_instances if 'distance_miles' in t]
        displayed_custom_with_distance = [t for t in custom_tournaments if 'distance_miles' in t]
        all_distances = [t['distance_miles'] for t in displayed_tournaments_with_distance + displayed_custom_with_distance]
        
        if all_distances:
            avg_distance = round(sum(all_distances) / len(all_distances), 1)
            min_distance = round(min(all_distances), 1)
            max_distance = round(max(all_distances), 1)
    
    location_context = {
        'location_filter_enabled': location_filter_enabled,
        'user_latitude': user_lat,
        'user_longitude': user_lng,
        'tournaments_found': len(tournament_instances),
        'custom_tournaments_found': len(custom_tournaments),
        'total_tournaments': total_tournaments,
        'total_custom_tournaments': total_custom_tournaments,
        'tournaments_with_gps': tournaments_with_gps,
        'custom_tournaments_with_gps': custom_tournaments_with_gps,
        'tournaments_without_gps': total_tournaments - tournaments_with_gps,
        'custom_tournaments_without_gps': total_custom_tournaments - custom_tournaments_with_gps,
        'has_user_location': user_lat is not None and user_lng is not None,
        'avg_distance': avg_distance,
        'min_distance': min_distance,
        'max_distance': max_distance
    }
    
    return render_template('tournaments_overview.html', 
                         tournament_levels=tournament_levels, 
                         tournament_instances=tournament_instances,
                         custom_tournaments=custom_tournaments,
                         recent_entries=recent_entries,
                         my_tournament_brackets=my_tournament_brackets,
                         players=players,
                         location_info=location_context)

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
    
    # Check if player has accepted tournament rules (skip for test accounts)
    if not player['tournament_rules_accepted'] and not player['test_account']:
        flash('Please read and accept the tournament rules before entering tournaments', 'warning')
        return redirect(url_for('show_tournament_rules', player_id=player_id))
    
    if request.method == 'POST':
        required_fields = ['tournament_instance_id', 'tournament_type']
        tournament_type = request.form.get('tournament_type')
        payment_method = request.form.get('payment_method', 'cash')
        
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
            
            # Calculate entry fee (same price for singles and doubles)
            base_fee = tournament_instance['entry_fee']
            entry_fee = base_fee  # Same price for singles and doubles
            
            # Check if Ambassador can use free entry (excluding The Hill)
            free_entry_used = False
            is_the_hill = 'The Hill' in (tournament_instance['name'] or '') or 'Big Dink' in (tournament_instance['name'] or '')
            
            # Test accounts get free entry to all tournaments
            if player['test_account']:
                entry_fee = 0  # FREE for test accounts
                free_entry_used = True
            elif player['free_tournament_entries'] and player['free_tournament_entries'] > 0 and not is_the_hill:
                # Ambassador has free entries available and this isn't The Hill
                entry_fee = 0  # FREE for both singles and doubles with Ambassador benefits
                free_entry_used = True
            
            # Handle credit payment method
            credits_used = 0
            remaining_payment = entry_fee
            
            if payment_method == 'credits' and entry_fee > 0:
                player_credits = player['tournament_credits'] or 0
                
                if player_credits <= 0:
                    flash('You have no tournament credits available. Please choose cash payment.', 'danger')
                    return redirect(url_for('tournament_entry', player_id=player_id))
                
                # Use available credits (partial or full payment)
                credits_used = min(player_credits, entry_fee)
                remaining_payment = max(0, entry_fee - credits_used)
                
                # Update player's credit balance
                new_credit_balance = player_credits - credits_used
                conn.execute('UPDATE players SET tournament_credits = ? WHERE id = ?', (new_credit_balance, player_id))
                
                # Record credit transaction
                credit_description = f"Tournament entry payment: {tournament_instance['name']} ({tournament_type})"
                if remaining_payment > 0:
                    credit_description += f" - Partial payment (${credits_used:.2f} of ${entry_fee:.2f})"
                
                conn.execute('''
                    INSERT INTO credit_transactions (player_id, transaction_type, amount, description)
                    VALUES (?, 'credit_used', ?, ?)
                ''', (player_id, credits_used, credit_description))
                
                if remaining_payment > 0:
                    flash(f'${credits_used:.2f} in credits applied! You have a remaining balance of ${remaining_payment:.2f} to pay.', 'warning')
                    # For now, we'll proceed with the entry and mark as 'pending_payment'
                    # In a full implementation, you'd integrate with Stripe here for the remaining amount
                else:
                    flash(f'Tournament entry paid with ${credits_used:.2f} in credits! New credit balance: ${new_credit_balance:.2f}', 'success')
            
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
            match_deadline = entry_date + timedelta(days=30)  # 1 month for tournaments
            
            # Update free entries count if used
            if free_entry_used:
                conn.execute('''
                    UPDATE players SET free_tournament_entries = free_tournament_entries - 1
                    WHERE id = ?
                ''', (player_id,))
            
            # GPS Validation for Tournament Join
            user_latitude = request.form.get('user_latitude')
            user_longitude = request.form.get('user_longitude')
            
            # Convert GPS coordinates to float if provided
            try:
                if user_latitude:
                    user_latitude = float(user_latitude)
                if user_longitude:
                    user_longitude = float(user_longitude)
            except (ValueError, TypeError):
                user_latitude = None
                user_longitude = None
                logging.warning(f"Invalid GPS coordinates received for player {player_id}")
            
            # Perform GPS validation
            gps_validation = validate_tournament_join_gps(
                user_latitude, user_longitude, tournament_instance, player_id
            )
            
            if not gps_validation['allowed']:
                logging.warning(f"Tournament join BLOCKED for player {player_id}: {gps_validation['reason']}")
                flash(gps_validation['error_message'], 'danger')
                conn.close()
                return redirect(url_for('tournament_entry', player_id=player_id))
            
            # Log successful GPS validation
            if gps_validation['distance_miles'] is not None:
                logging.info(f"GPS validation PASSED for player {player_id}: {gps_validation['distance_miles']} miles from tournament")
            
            # Determine payment status based on credits used and remaining payment
            if payment_method == 'credits' and remaining_payment == 0:
                payment_status = 'completed'  # Fully paid with credits
            elif payment_method == 'credits' and remaining_payment > 0:
                payment_status = 'pending_payment'  # Partial credit payment, remaining balance due
            elif tournament_type == 'doubles' and partner_id:
                payment_status = 'pending_partner'  # Waiting for partner acceptance
            elif free_entry_used and entry_fee == 0:
                payment_status = 'completed'  # Free Ambassador entry
            else:
                payment_status = 'pending_payment'  # Requires payment processing
            
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
                  payment_status))
            
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
    conn = get_pg_connection()
    cursor = conn.cursor()
    
    # Get all tournaments with player info
    cursor.execute('''
        SELECT t.*, p.full_name, p.email
        FROM tournaments t
        JOIN players p ON t.player_id = p.id
        ORDER BY t.created_at DESC
    ''')
    tournaments = cursor.fetchall()
    
    conn.close()
    
    return render_template('manage_tournaments.html', tournaments=tournaments)

def create_tournament_payout(conn, player_id, tournament_instance_id, tournament_name, placement, prize_amount):
    """Create a payout record for tournament winnings"""
    try:
        # Get player's payout information
        player = conn.execute('''
            SELECT payout_preference, paypal_email, venmo_username, zelle_info, full_name
            FROM players WHERE id = ?
        ''', (player_id,)).fetchone()
        
        if not player:
            return False
            
        # Determine payout account based on preference
        payout_account = ""
        if player['payout_preference'] == 'PayPal' and player['paypal_email']:
            payout_account = player['paypal_email']
        elif player['payout_preference'] == 'Venmo' and player['venmo_username']:
            payout_account = player['venmo_username']
        elif player['payout_preference'] == 'Zelle' and player['zelle_info']:
            payout_account = player['zelle_info']
        
        # Create payout record
        conn.execute('''
            INSERT INTO tournament_payouts 
            (player_id, tournament_instance_id, tournament_name, placement, prize_amount, payout_method, payout_account)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (player_id, tournament_instance_id, tournament_name, placement, prize_amount, 
              player['payout_preference'], payout_account))
        
        return True
    except Exception as e:
        print(f"Error creating payout record: {e}")
        return False

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
    
    # If they won (1st place), add tournament win star and create payout record
    if 'Won - 1st Place' in result:
        conn.execute('''
            UPDATE players 
            SET tournament_wins = tournament_wins + 1
            WHERE id = ?
        ''', (tournament['player_id'],))
        
        # Calculate prize money and create payout record
        tournament_level = tournament['tournament_level']
        if tournament_level in ['Beginner', 'Intermediate', 'Advanced']:
            # Get tournament level settings
            levels = get_tournament_levels()
            if tournament_level in levels:
                entry_fee = levels[tournament_level]['entry_fee']
                max_players = levels[tournament_level]['max_players']
                prizes = levels[tournament_level]['prizes']
                
                # Create payout record for 1st place winner
                first_place_prize = prizes.get('1st', 0)
                if first_place_prize > 0:
                    create_tournament_payout(
                        conn, 
                        tournament['player_id'], 
                        tournament.get('tournament_instance_id', tournament_id),
                        tournament['tournament_name'] or f"{tournament_level} Tournament",
                        "1st Place",
                        first_place_prize
                    )
    
    # Note: Points are now awarded progressively during matches via submit_tournament_match_result
    # No need to award points here to prevent double-awarding
    logging.info(f"Tournament {tournament_id} completed with result: {result}. Points already awarded progressively.")
    
    # Send notification about tournament completion 
    completion_message = f"🏆 Tournament complete! You finished as {result.lower()}. Great job!"
    send_push_notification(tournament['player_id'], completion_message, "Tournament Results")
    
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
def find_match(player_id):
    """API endpoint to find compatible players for selection or challenge a specific player"""
    try:
        # Check if player exists and bypass disclaimers for test accounts
        conn = get_db_connection()
        player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
        
        if not player:
            conn.close()
            return jsonify({'success': False, 'message': 'Player not found'})
            
        # Skip disclaimer check for test accounts and admin
        if not player['test_account'] and player['id'] != 1 and not player['disclaimers_accepted']:
            conn.close()
            return jsonify({'success': False, 'message': 'Please accept disclaimers first', 'redirect': f'/show_disclaimers/{player_id}'})
        
        # Check for targeted challenge
        data = request.get_json() or {}
        target_player_id = data.get('target_player_id')
        
        if target_player_id:
            # Direct challenge to specific player
            # Extract proposed match details if provided
            proposed_location = data.get('proposed_location')
            proposed_date = data.get('proposed_date')  
            proposed_time = data.get('proposed_time')
            
            match_id = create_direct_challenge(
                player_id, 
                target_player_id, 
                proposed_location, 
                proposed_date, 
                proposed_time
            )
            if match_id:
                return jsonify({'success': True, 'match_id': match_id, 'message': 'Challenge sent successfully!'})
            else:
                return jsonify({'success': False, 'message': 'Unable to challenge this player. You may already have a pending match with them.'})
        else:
            # Return compatible players for selection
            compatible_players = get_compatible_players(player_id)
            
            if compatible_players:
                return jsonify({
                    'success': True, 
                    'players': compatible_players,
                    'message': f'Found {len(compatible_players)} compatible players!'
                })
            else:
                return jsonify({'success': False, 'message': 'No compatible players found at the moment. Try expanding your preferences or check back later!'})
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

@app.route('/accept_challenge', methods=['POST'])
def accept_challenge():
    """API endpoint to accept a match challenge"""
    try:
        data = request.get_json()
        challenge_id = data.get('challenge_id') or data.get('challengeId')  # Support both formats
        
        if not challenge_id:
            return jsonify({'success': False, 'message': 'Challenge ID is required'})
        
        conn = get_db_connection()
        
        # Get match details before updating
        match_details = conn.execute('''
            SELECT m.court_location, m.scheduled_time, m.sport,
                   p1.full_name as player1_name, p2.full_name as player2_name,
                   m.player1_id, m.player2_id
            FROM matches m
            JOIN players p1 ON m.player1_id = p1.id  
            JOIN players p2 ON m.player2_id = p2.id
            WHERE m.id = ?
        ''', (challenge_id,)).fetchone()
        
        if not match_details:
            conn.close()
            return jsonify({'success': False, 'message': 'Match not found'})
        
        # Update match status to confirmed
        conn.execute('UPDATE matches SET status = ? WHERE id = ?', ('confirmed', challenge_id))
        conn.commit()
        conn.close()
        
        # Format the success message with location and time
        location = match_details['court_location'] or 'TBD - coordinate with opponent'
        time = match_details['scheduled_time'] or 'Flexible timing - coordinate with opponent'
        
        message = f"Challenge accepted! 🎾 Match scheduled at {location} for {time}. Good luck!"
        
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        challenge_id_str = challenge_id if 'challenge_id' in locals() else 'unknown'
        logging.error(f"Error accepting challenge {challenge_id_str}: {str(e)}")
        return jsonify({'success': False, 'message': f'Error accepting challenge: {str(e)}'})

@app.route('/accept_counter_proposal', methods=['POST'])
def accept_counter_proposal():
    """Accept a counter-proposal and finalize the match details"""
    try:
        data = request.get_json()
        challenge_id = data.get('challenge_id') or data.get('challengeId')
        
        if not challenge_id:
            return jsonify({'success': False, 'message': 'Challenge ID is required'})
        
        conn = get_db_connection()
        
        # Get match details with the proposed changes
        match_details = conn.execute('''
            SELECT m.proposed_location, m.proposed_time, m.sport,
                   p1.full_name as player1_name, p2.full_name as player2_name,
                   m.player1_id, m.player2_id
            FROM matches m
            JOIN players p1 ON m.player1_id = p1.id  
            JOIN players p2 ON m.player2_id = p2.id
            WHERE m.id = ?
        ''', (challenge_id,)).fetchone()
        
        if not match_details:
            conn.close()
            return jsonify({'success': False, 'message': 'Match not found'})
        
        # Finalize the match with the proposed details
        final_location = match_details['proposed_location']
        final_time = match_details['proposed_time'] 
        
        conn.execute('''
            UPDATE matches 
            SET court_location = ?, scheduled_time = ?, status = 'confirmed',
                proposed_location = NULL, proposed_time = NULL, last_proposer_id = NULL
            WHERE id = ?
        ''', (final_location, final_time, challenge_id))
        
        conn.commit()
        conn.close()
        
        # Format success message
        location = final_location or 'TBD - coordinate with opponent'
        time = final_time or 'Flexible timing - coordinate with opponent'
        
        message = f"Counter-proposal accepted! 🎾 Final match: {location} at {time}. Game on!"
        
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        challenge_id_str = challenge_id if 'challenge_id' in locals() else 'unknown'
        logging.error(f"Error accepting counter-proposal {challenge_id_str}: {str(e)}")
        return jsonify({'success': False, 'message': f'Error accepting counter-proposal: {str(e)}'})

@app.route('/decline_challenge', methods=['POST'])
def decline_challenge():
    """API endpoint to decline a match challenge or propose alternatives"""
    try:
        data = request.get_json()
        challenge_id = data.get('challenge_id') or data.get('challengeId')  # Support both formats
        proposed_location = data.get('proposed_location')
        proposed_time = data.get('proposed_time')
        player_id = data.get('player_id')
        
        if not challenge_id:
            return jsonify({'success': False, 'message': 'Challenge ID is required'})
        
        conn = get_db_connection()
        
        # Check if this is a counter-proposal or outright decline
        if proposed_location or proposed_time:
            # This is a counter-proposal
            match = conn.execute('SELECT player1_id, player2_id, negotiation_round FROM matches WHERE id = ?', (challenge_id,)).fetchone()
            
            if not match:
                conn.close()
                return jsonify({'success': False, 'message': 'Match not found'})
            
            # Update match with counter-proposal
            conn.execute('''
                UPDATE matches 
                SET proposed_location = ?, proposed_time = ?, last_proposer_id = ?, 
                    negotiation_round = ?, status = 'counter_proposed'
                WHERE id = ?
            ''', (proposed_location, proposed_time, player_id, 
                  match['negotiation_round'] + 1, challenge_id))
            
            conn.commit()
            conn.close()
            
            # Format response message
            location_msg = f"Location: {proposed_location}" if proposed_location else ""
            time_msg = f"Time: {proposed_time}" if proposed_time else ""
            separator = " | " if location_msg and time_msg else ""
            
            message = f"Counter-proposal sent! {location_msg}{separator}{time_msg}. Waiting for their response."
            
            return jsonify({'success': True, 'message': message})
        
        else:
            # Outright decline - update match status to declined and allow players to find new matches
            conn.execute('UPDATE matches SET status = ? WHERE id = ?', ('declined', challenge_id))
            
            # Get the players from this match to mark them as available again
            match = conn.execute('SELECT player1_id, player2_id FROM matches WHERE id = ?', (challenge_id,)).fetchone()
            if match:
                conn.execute('UPDATE players SET is_looking_for_match = 1 WHERE id IN (?, ?)', 
                            (match['player1_id'], match['player2_id']))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Challenge declined. You can find new matches.'})
            
    except Exception as e:
        challenge_id_str = challenge_id if 'challenge_id' in locals() else 'unknown'
        logging.error(f"Error declining challenge {challenge_id_str}: {str(e)}")
        return jsonify({'success': False, 'message': f'Error declining challenge: {str(e)}'})

# Form-based challenge endpoints (non-JSON)
@app.route('/challenges/send', methods=['POST'])
def send_challenge_route():
    """Send a new challenge to another player using HTML form"""
    if 'player_id' not in session:
        flash('Please log in to send challenges', 'warning')
        return redirect(url_for('player_login'))
    
    challenger_id = session['player_id']
    opponent_id = request.form.get('opponent_id')
    court_location = request.form.get('court_location', '').strip()
    scheduled_time = request.form.get('scheduled_time', '').strip()
    
    if not opponent_id:
        flash('Please select an opponent to challenge', 'danger')
        return redirect(url_for('challenges'))
    
    try:
        opponent_id = int(opponent_id)
    except ValueError:
        flash('Invalid opponent selected', 'danger')
        return redirect(url_for('challenges'))
    
    # Prevent self-challenges
    if challenger_id == opponent_id:
        flash('You cannot challenge yourself!', 'warning')
        return redirect(url_for('challenges'))
    
    conn = get_db_connection()
    
    try:
        # Check if challenger exists and get their info
        challenger = conn.execute('SELECT * FROM players WHERE id = ?', (challenger_id,)).fetchone()
        if not challenger:
            flash('Player not found', 'danger')
            return redirect(url_for('challenges'))
        
        # Check if opponent exists
        opponent = conn.execute('SELECT * FROM players WHERE id = ?', (opponent_id,)).fetchone()
        if not opponent:
            flash('Opponent not found', 'danger')
            return redirect(url_for('challenges'))
        
        # Check for existing pending challenges between these players
        existing_challenge = conn.execute('''
            SELECT id FROM matches 
            WHERE ((player1_id = ? AND player2_id = ?) OR (player1_id = ? AND player2_id = ?))
            AND status IN ('pending', 'counter_proposed')
        ''', (challenger_id, opponent_id, opponent_id, challenger_id)).fetchone()
        
        if existing_challenge:
            flash(f'You already have a pending challenge with {opponent["full_name"]}', 'warning')
            return redirect(url_for('challenges'))
        
        # Create the challenge
        conn.execute('''
            INSERT INTO matches (player1_id, player2_id, sport, court_location, scheduled_time, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'pending', datetime('now'))
        ''', (challenger_id, opponent_id, 'Pickleball', court_location or 'TBD', scheduled_time or 'Flexible'))
        
        conn.commit()
        flash(f'Challenge sent to {opponent["full_name"]}! 🎾', 'success')
        
    except Exception as e:
        logging.error(f"Error sending challenge: {e}")
        flash('Failed to send challenge. Please try again.', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('challenges'))

@app.route('/challenges/<int:challenge_id>/accept', methods=['POST'])
def accept_challenge_route(challenge_id):
    """Accept an incoming challenge using HTML form"""
    if 'player_id' not in session:
        flash('Please log in to accept challenges', 'warning')
        return redirect(url_for('player_login'))
    
    player_id = session['player_id']
    conn = get_db_connection()
    
    try:
        # Get challenge details and verify ownership
        challenge = conn.execute('''
            SELECT m.*, p1.full_name as challenger_name
            FROM matches m
            JOIN players p1 ON m.player1_id = p1.id
            WHERE m.id = ? AND m.player2_id = ? AND m.status IN ('pending', 'counter_proposed')
        ''', (challenge_id, player_id)).fetchone()
        
        if not challenge:
            flash('Challenge not found or you are not authorized to accept it', 'danger')
            return redirect(url_for('challenges'))
        
        # Accept the challenge by updating status
        conn.execute('UPDATE matches SET status = ? WHERE id = ?', ('confirmed', challenge_id))
        conn.commit()
        
        # Format success message
        location = challenge['court_location'] or 'TBD'
        time = challenge['scheduled_time'] or 'Flexible'
        flash(f'Challenge accepted! 🎾 Match with {challenge["challenger_name"]} confirmed at {location} for {time}', 'success')
        
    except Exception as e:
        logging.error(f"Error accepting challenge {challenge_id}: {e}")
        flash('Failed to accept challenge. Please try again.', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('challenges'))

@app.route('/challenges/<int:challenge_id>/decline', methods=['POST'])
def decline_challenge_route(challenge_id):
    """Decline an incoming challenge using HTML form"""
    if 'player_id' not in session:
        flash('Please log in to decline challenges', 'warning')
        return redirect(url_for('player_login'))
    
    player_id = session['player_id']
    conn = get_db_connection()
    
    try:
        # Get challenge details and verify ownership
        challenge = conn.execute('''
            SELECT m.*, p1.full_name as challenger_name
            FROM matches m
            JOIN players p1 ON m.player1_id = p1.id
            WHERE m.id = ? AND m.player2_id = ? AND m.status IN ('pending', 'counter_proposed')
        ''', (challenge_id, player_id)).fetchone()
        
        if not challenge:
            flash('Challenge not found or you are not authorized to decline it', 'danger')
            return redirect(url_for('challenges'))
        
        # Decline the challenge
        conn.execute('UPDATE matches SET status = ? WHERE id = ?', ('declined', challenge_id))
        
        # Mark both players as available for matching again
        conn.execute('UPDATE players SET is_looking_for_match = 1 WHERE id IN (?, ?)', 
                    (challenge['player1_id'], challenge['player2_id']))
        
        conn.commit()
        flash(f'Challenge from {challenge["challenger_name"]} declined', 'info')
        
    except Exception as e:
        logging.error(f"Error declining challenge {challenge_id}: {e}")
        flash('Failed to decline challenge. Please try again.', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('challenges'))

@app.route('/players')
def players():
    """Admin view - List all registered players"""
    conn = get_db_connection()
    players = conn.execute('SELECT * FROM players ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return render_template('admin/players.html', players=players)

@app.route('/admin/check-trials')
@require_admin()
def admin_check_trials():
    """Admin route to manually check and process expired trials"""
    # Run bulk trial expiry check
    expired_count = check_bulk_trial_expiry()
    
    flash(f'Trial expiry check completed. {expired_count} users were downgraded from expired trials.', 'info')
    return redirect(url_for('players'))

@app.route('/browse-players')
def browse_players():
    """Browse compatible players page with player cards and search filters"""
    current_player_id = session.get('current_player_id')
    
    if not current_player_id:
        flash('Please log in first', 'warning')
        return redirect(url_for('player_login'))
    
    # Check and handle trial expiry for this user
    check_and_handle_trial_expiry(current_player_id)
    
    # Get filter parameters from request
    match_type = request.args.get('match_type', '')
    skill_level = request.args.get('skill_level', '')
    distance = request.args.get('distance', '')
    
    # Get filtered compatible players
    if match_type or skill_level or distance:
        compatible_players = get_filtered_compatible_players(
            current_player_id, 
            match_type=match_type, 
            skill_level=skill_level, 
            distance=int(distance) if distance else None
        )
    else:
        compatible_players = get_compatible_players(current_player_id)
    
    # Pre-calculate distances for template efficiency (avoid N+1 queries)
    for player in compatible_players:
        if isinstance(player, dict):
            # Add pre-calculated distance to each player
            player['distance_display'] = get_distance_from_current_player(player, current_player_id)
        else:
            # Convert to dict and add distance
            player_dict = dict(player)
            player_dict['distance_display'] = get_distance_from_current_player(player_dict, current_player_id)
            compatible_players[compatible_players.index(player)] = player_dict
    
    # Get current player info for display
    conn = get_db_connection()
    current_player = conn.execute('SELECT * FROM players WHERE id = ?', (current_player_id,)).fetchone()
    conn.close()
    
    if not current_player:
        flash('Player not found', 'danger')
        return redirect(url_for('player_login'))
    
    return render_template('browse_players.html', 
                         players=compatible_players, 
                         current_player=current_player,
                         current_player_id=current_player_id)

@app.route('/profile_settings')
def profile_settings():
    """Profile settings page - get current logged-in player with team information"""
    current_player_id = session.get('current_player_id')
    
    if not current_player_id:
        flash('Please log in first', 'warning')
        return redirect(url_for('player_login'))
    
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (current_player_id,)).fetchone()
    
    # Get player's team information
    current_team = get_player_team(current_player_id)
    
    # Get pending team invitations
    pending_invitations = get_player_team_invitations(current_player_id)
    
    # Get player's connections (players they've played matches with)
    connections = conn.execute('''
        SELECT DISTINCT p.id, p.full_name, p.selfie
        FROM players p
        JOIN matches m ON (p.id = m.player1_id OR p.id = m.player2_id)
        WHERE ((m.player1_id = ? AND p.id = m.player2_id) OR (m.player2_id = ? AND p.id = m.player1_id))
        AND m.status = 'completed'
        AND p.id != ?
        ORDER BY p.full_name
    ''', (current_player_id, current_player_id, current_player_id)).fetchall()
    
    conn.close()
    
    if not player:
        flash('Player not found', 'danger')
        return redirect(url_for('player_login'))
    
    return render_template('profile_settings.html', 
                         player=player,
                         current_team=current_team,
                         pending_invitations=pending_invitations,
                         connections=[dict(c) for c in connections])

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

@app.route('/api/zip-to-coordinates', methods=['POST'])
def api_zip_to_coordinates():
    """API endpoint to convert ZIP code to coordinates"""
    try:
        data = request.get_json()
        zip_code = data.get('zip_code', '').strip()
        
        if not zip_code or len(zip_code) != 5 or not zip_code.isdigit():
            return jsonify({
                'success': False,
                'message': 'Please provide a valid 5-digit ZIP code'
            })
        
        latitude, longitude = get_coordinates_from_zip_code(zip_code)
        
        if latitude is not None and longitude is not None:
            return jsonify({
                'success': True,
                'latitude': latitude,
                'longitude': longitude,
                'message': f'Successfully converted ZIP {zip_code} to coordinates'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Could not find coordinates for ZIP code {zip_code}'
            })
            
    except Exception as e:
        logging.error(f"Error in ZIP-to-coordinates API: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while converting ZIP code'
        })

@app.route('/update_profile', methods=['POST'])
def update_profile():
    """Update player profile information"""
    conn = get_db_connection()
    
    # Get current player ID from session
    current_player_id = session.get('current_player_id')
    if not current_player_id:
        flash('Please log in first', 'warning')
        return redirect(url_for('player_login'))
    
    player_id = current_player_id
    
    # Form validation
    required_fields = ['full_name', 'address', 'zip_code', 'city', 'state', 'dob', 'preferred_court_1', 'skill_level', 'email', 'player_id']
    for field in required_fields:
        if not request.form.get(field):
            flash(f'{field.replace("_", " ").title()} is required', 'danger')
            return redirect(url_for('profile_settings'))
    
    # Validate player_id format (4 digits, 1000-9999)
    player_id_input = request.form.get('player_id', '').strip()
    if not player_id_input.isdigit() or len(player_id_input) != 4:
        flash('Player ID must be exactly 4 digits', 'danger')
        return redirect(url_for('profile_settings'))
    
    player_id_num = int(player_id_input)
    if player_id_num < 1000 or player_id_num > 9999:
        flash('Player ID must be between 1000 and 9999', 'danger')
        return redirect(url_for('profile_settings'))
    
    # Check if player_id is already taken by another player
    existing_player = conn.execute('SELECT id FROM players WHERE player_id = ? AND id != ?', (player_id_input, player_id)).fetchone()
    if existing_player:
        flash('This Player ID is already taken. Please choose a different number.', 'danger')
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
    
    # Process location data updates
    user_latitude = request.form.get('latitude', '').strip() 
    user_longitude = request.form.get('longitude', '').strip()
    search_radius = request.form.get('search_radius_miles', '').strip()
    
    # Parse coordinates if provided
    latitude = None
    longitude = None
    if user_latitude and user_longitude:
        try:
            latitude = float(user_latitude)
            longitude = float(user_longitude)
            logging.info(f"Profile update: GPS coordinates updated - {latitude}, {longitude}")
        except (ValueError, TypeError):
            logging.warning(f"Profile update: Invalid GPS coordinates provided")
    
    # Parse search radius
    search_radius_miles = 15  # Default
    if search_radius:
        try:
            search_radius_miles = max(15, min(50, int(search_radius)))  # Clamp between 15-50
        except (ValueError, TypeError):
            logging.warning(f"Profile update: Invalid search radius provided, using default 15")
    
    # Validate and process gender
    gender = request.form.get('gender', 'prefer_not_to_say').strip()
    valid_genders = ['male', 'female', 'non_binary', 'prefer_not_to_say']
    if gender not in valid_genders:
        flash('Please select a valid gender option', 'danger')
        return redirect(url_for('profile_settings'))
    
    # Validate and process travel radius
    travel_radius_input = request.form.get('travel_radius', '25').strip()
    try:
        travel_radius = max(5, min(100, int(travel_radius_input)))  # Clamp between 5-100 miles
    except (ValueError, TypeError):
        flash('Travel radius must be a number between 5 and 100 miles', 'danger')
        return redirect(url_for('profile_settings'))
    
    try:
        # Update player information
        if selfie_filename:
            conn.execute('''
                UPDATE players 
                SET full_name = ?, address = ?, zip_code = ?, city = ?, state = ?, 
                    dob = ?, preferred_court_1 = ?, preferred_court_2 = ?,
                    court1_coordinates = ?, court2_coordinates = ?,
                    skill_level = ?, email = ?, selfie = ?, player_id = ?, payout_preference = ?,
                    paypal_email = ?, venmo_username = ?, zelle_info = ?,
                    latitude = ?, longitude = ?, search_radius_miles = ?, gender = ?, travel_radius = ?
                WHERE id = ?
            ''', (request.form['full_name'], request.form['address'], 
                  request.form['zip_code'], request.form['city'], request.form['state'],
                  request.form['dob'], request.form.get('preferred_court_1', ''), request.form.get('preferred_court_2', ''),
                  request.form.get('preferred_court_1_coordinates', ''), request.form.get('preferred_court_2_coordinates', ''),
                  request.form['skill_level'], request.form['email'], selfie_filename, player_id_input, 
                  request.form.get('payout_preference', ''), request.form.get('paypal_email', ''),
                  request.form.get('venmo_username', ''), request.form.get('zelle_info', ''),
                  latitude, longitude, search_radius_miles, gender, travel_radius, player_id))
        else:
            conn.execute('''
                UPDATE players 
                SET full_name = ?, address = ?, zip_code = ?, city = ?, state = ?,
                    dob = ?, preferred_court_1 = ?, preferred_court_2 = ?,
                    court1_coordinates = ?, court2_coordinates = ?,
                    skill_level = ?, email = ?, player_id = ?, payout_preference = ?,
                    paypal_email = ?, venmo_username = ?, zelle_info = ?,
                    latitude = ?, longitude = ?, search_radius_miles = ?, gender = ?, travel_radius = ?
                WHERE id = ?
            ''', (request.form['full_name'], request.form['address'], 
                  request.form['zip_code'], request.form['city'], request.form['state'],
                  request.form['dob'], request.form.get('preferred_court_1', ''), request.form.get('preferred_court_2', ''),
                  request.form.get('preferred_court_1_coordinates', ''), request.form.get('preferred_court_2_coordinates', ''),
                  request.form['skill_level'], request.form['email'], player_id_input, 
                  request.form.get('payout_preference', ''), request.form.get('paypal_email', ''),
                  request.form.get('venmo_username', ''), request.form.get('zelle_info', ''),
                  latitude, longitude, search_radius_miles, gender, travel_radius, player_id))
        
        conn.commit()
        conn.close()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        conn.close()
        flash(f'Error updating profile: {str(e)}', 'danger')
        return redirect(url_for('profile_settings'))

@app.route('/clear_profile_completion_flag', methods=['POST'])
def clear_profile_completion_flag():
    """Clear the profile completion flag from session"""
    if 'show_profile_completion' in session:
        del session['show_profile_completion']
    return jsonify({'success': True})

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
    """Submit match result with pickleball set-based scores"""
    data = request.get_json()
    match_id = data.get('match_id')
    match_score = data.get('match_score')  # Format: "11-5 6-11 11-9"
    player1_sets_won = int(data.get('player1_sets_won', 0))
    player2_sets_won = int(data.get('player2_sets_won', 0))
    
    # SECURITY FIX: Get submitter_id from server-side session, not client input
    submitter_id = session.get('current_player_id') or session.get('player_id')
    if not submitter_id:
        return jsonify({'success': False, 'message': 'Authentication required. Please login.'})
    
    # Validate input
    if not match_score or player1_sets_won == player2_sets_won:
        return jsonify({'success': False, 'message': 'Invalid match result. Sets cannot be tied.'})
    
    # Validate best of 3 format
    if (player1_sets_won + player2_sets_won) < 2 or (player1_sets_won + player2_sets_won) > 3:
        return jsonify({'success': False, 'message': 'Invalid pickleball match format.'})
    
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
    
    # Determine winner based on sets won
    winner_id = match['player1_id'] if player1_sets_won > player2_sets_won else match['player2_id']
    loser_id = match['player2_id'] if player1_sets_won > player2_sets_won else match['player1_id']
    
    # Update match with results (store sets won in score fields for backward compatibility)
    conn.execute('''
        UPDATE matches 
        SET player1_score = ?, player2_score = ?, winner_id = ?, 
            status = 'completed', match_result = ?
        WHERE id = ?
    ''', (player1_sets_won, player2_sets_won, winner_id, 
          match_score, match_id))
    
    # DOUBLES TEAM SCORING: Update win/loss records for all team members
    # Get team members for both winner and loser
    winner_team_members = get_match_team_members(match_id, winner_id)
    loser_team_members = get_match_team_members(match_id, loser_id)
    
    # Calculate points based on match type
    points_awarded = 15 if (player1_sets_won + player2_sets_won) == 3 else 10  # Bonus for 3-set matches
    points_description = 'Match victory'
    
    # Update records for all winning team members
    for player_id in winner_team_members:
        update_player_match_record(player_id, True, points_awarded, points_description, conn)
    
    # Update records for all losing team members
    for player_id in loser_team_members:
        update_player_match_record(player_id, False, 0, "", conn)
    
    logging.info(f"Regular match {match_id}: Updated {len(winner_team_members)} winning players, {len(loser_team_members)} losing players")
    
    conn.commit()
    conn.close()
    
    # Send notifications
    conn = get_db_connection()
    winner = conn.execute('SELECT full_name FROM players WHERE id = ?', (winner_id,)).fetchone()
    loser = conn.execute('SELECT full_name FROM players WHERE id = ?', (loser_id,)).fetchone()
    conn.close()
    
    if winner and loser:
        sets_result = f"{player1_sets_won}-{player2_sets_won}" if winner_id == match['player1_id'] else f"{player2_sets_won}-{player1_sets_won}"
        winner_message = f"🏆 Victory! You beat {loser['full_name']} ({sets_result}) and earned {points_awarded} ranking points!"
        loser_message = f"Good match against {winner['full_name']} ({match_score})! Keep practicing and you'll get them next time!"
        
        send_push_notification(winner_id, winner_message, "Match Result")
        send_push_notification(loser_id, loser_message, "Match Result")
    
    return jsonify({
        'success': True, 
        'message': f'Match result submitted successfully! Final score: {match_score}'
    })

@app.route('/submit_tournament_match_result', methods=['POST'])
def submit_tournament_match_result_route():
    """Submit result for a tournament match with progressive points"""
    data = request.get_json()
    tournament_match_id = data.get('tournament_match_id')
    match_score = data.get('match_score')  # Format: "11-5 6-11 11-9"
    player1_sets_won = int(data.get('player1_sets_won', 0))
    player2_sets_won = int(data.get('player2_sets_won', 0))
    
    # SECURITY FIX: Get submitter_id from server-side session, not client input
    submitter_id = session.get('current_player_id') or session.get('player_id')
    if not submitter_id:
        return jsonify({'success': False, 'message': 'Authentication required. Please login.'})
    
    # Enhanced logging for submission tracking
    logging.info(f"Tournament match submission received - Match ID: {tournament_match_id}, "
                f"Submitter: {submitter_id}, Score: {match_score}, "
                f"Sets: P1={player1_sets_won} P2={player2_sets_won}")
    
    # Validate input
    if not match_score or not tournament_match_id:
        logging.warning(f"Invalid submission attempt - missing required data. Match ID: {tournament_match_id}, Score: {match_score}")
        return jsonify({'success': False, 'message': 'Match score and tournament match ID are required.'})
    
    # Validate best of 3 format
    if (player1_sets_won + player2_sets_won) < 2 or (player1_sets_won + player2_sets_won) > 3:
        logging.warning(f"Invalid match format - total sets: {player1_sets_won + player2_sets_won} for match {tournament_match_id}")
        return jsonify({'success': False, 'message': 'Invalid pickleball match format.'})
    
    # Call the tournament match submission function
    result = submit_tournament_match_result(
        tournament_match_id, 
        player1_sets_won, 
        player2_sets_won, 
        match_score, 
        submitter_id
    )
    
    # Log the result for monitoring
    if result.get('success'):
        logging.info(f"Tournament match {tournament_match_id} submitted successfully. "
                    f"Points awarded: {result.get('points_awarded', 0)}, "
                    f"Round: {result.get('round_name', 'Unknown')}")
    else:
        logging.error(f"Tournament match {tournament_match_id} submission failed: {result.get('message', 'Unknown error')}")
    
    return jsonify(result)

@app.route('/validate_match_result', methods=['POST'])
def validate_match_result():
    """Validate match result with two-step validation process"""
    data = request.get_json()
    match_id = data.get('match_id')
    match_score = data.get('match_score')  # Format: "11-5 6-11 11-9"
    player1_sets_won = int(data.get('player1_sets_won', 0))
    player2_sets_won = int(data.get('player2_sets_won', 0))
    validator_id = data.get('validator_id')
    opponent_skill_feedback = data.get('opponent_skill_feedback')
    
    # Validate input
    if not match_score or player1_sets_won == player2_sets_won:
        return jsonify({'success': False, 'message': 'Invalid match result. Sets cannot be tied.'})
    
    conn = get_db_connection()
    
    # Get match details
    match = conn.execute('''
        SELECT * FROM matches WHERE id = ?
    ''', (match_id,)).fetchone()
    
    if not match:
        conn.close()
        return jsonify({'success': False, 'message': 'Match not found'})
    
    # Check if validator is part of this match
    if validator_id not in [match['player1_id'], match['player2_id']]:
        conn.close()
        return jsonify({'success': False, 'message': 'You are not part of this match'})
    
    # Determine which player is validating
    is_player1 = validator_id == match['player1_id']
    
    # Update validation status for the validating player
    if is_player1:
        # Check if player1 already validated
        if match['player1_validated'] == 1:
            conn.close()
            return jsonify({'success': False, 'message': 'You have already validated this match'})
        
        conn.execute('''
            UPDATE matches 
            SET player1_validated = 1, 
                player1_skill_feedback = ?,
                match_result = ?,
                player1_score = ?,
                player2_score = ?
            WHERE id = ?
        ''', (opponent_skill_feedback, match_score, player1_sets_won, player2_sets_won, match_id))
    else:
        # Check if player2 already validated
        if match['player2_validated'] == 1:
            conn.close()
            return jsonify({'success': False, 'message': 'You have already validated this match'})
        
        conn.execute('''
            UPDATE matches 
            SET player2_validated = 1,
                player2_skill_feedback = ?,
                match_result = ?,
                player1_score = ?,
                player2_score = ?
            WHERE id = ?
        ''', (opponent_skill_feedback, match_score, player1_sets_won, player2_sets_won, match_id))
    
    # Check if both players have now validated
    updated_match = conn.execute('SELECT * FROM matches WHERE id = ?', (match_id,)).fetchone()
    
    both_validated = (updated_match['player1_validated'] == 1 and 
                     updated_match['player2_validated'] == 1)
    
    if both_validated:
        # Determine winner based on sets won
        winner_id = match['player1_id'] if player1_sets_won > player2_sets_won else match['player2_id']
        loser_id = match['player2_id'] if player1_sets_won > player2_sets_won else match['player1_id']
        
        # Complete the match
        conn.execute('''
            UPDATE matches 
            SET status = 'completed', 
                winner_id = ?,
                validation_status = 'completed'
            WHERE id = ?
        ''', (winner_id, match_id))
        
        # Update player win/loss records
        conn.execute('UPDATE players SET wins = wins + 1 WHERE id = ?', (winner_id,))
        conn.execute('UPDATE players SET losses = losses + 1 WHERE id = ?', (loser_id,))
        
        conn.commit()
        conn.close()
        
        # Award points based on match type
        points_awarded = 15 if (player1_sets_won + player2_sets_won) == 3 else 10
        award_points(winner_id, points_awarded, 'Match victory')
        
        # Send notifications
        conn = get_db_connection()
        winner = conn.execute('SELECT full_name FROM players WHERE id = ?', (winner_id,)).fetchone()
        loser = conn.execute('SELECT full_name FROM players WHERE id = ?', (loser_id,)).fetchone()
        conn.close()
        
        if winner and loser:
            sets_result = f"{player1_sets_won}-{player2_sets_won}" if winner_id == match['player1_id'] else f"{player2_sets_won}-{player1_sets_won}"
            winner_message = f"🏆 Match completed! You beat {loser['full_name']} ({sets_result}) and earned {points_awarded} ranking points!"
            loser_message = f"Match completed against {winner['full_name']} ({match_score}). Keep practicing!"
            
            send_push_notification(winner_id, winner_message, "Match Completed")
            send_push_notification(loser_id, loser_message, "Match Completed")
        
        return jsonify({
            'success': True, 
            'message': f'Match completed! Both players validated. Final score: {match_score}',
            'match_completed': True
        })
    else:
        # Update validation status but don't complete match yet
        conn.execute('''
            UPDATE matches 
            SET validation_status = 'partial'
            WHERE id = ?
        ''', (match_id,))
        
        conn.commit()
        conn.close()
        
        # Notify opponent that validation is needed
        opponent_id = match['player2_id'] if is_player1 else match['player1_id']
        conn = get_db_connection()
        validator_name = conn.execute('SELECT full_name FROM players WHERE id = ?', (validator_id,)).fetchone()['full_name']
        conn.close()
        
        opponent_message = f"⚠️ {validator_name} has submitted and validated your match result. Please validate the score to complete the match."
        send_push_notification(opponent_id, opponent_message, "Score Validation Needed")
        
        return jsonify({
            'success': True, 
            'message': 'Your validation recorded! Waiting for opponent to validate the score.',
            'match_completed': False
        })
    
    conn.close()

@app.route('/get_pending_matches/<int:player_id>')
def get_pending_matches(player_id):
    """Get matches that need score submission or validation"""
    conn = get_db_connection()
    
    # Get matches that need score submission OR validation from this specific player
    # Exclude matches where this player has already validated (score should disappear from their list)
    matches = conn.execute('''
        SELECT m.*, 
               p1.full_name as player1_name,
               p2.full_name as player2_name,
               m.court_location,
               m.scheduled_time,
               CASE 
                   WHEN m.status = 'pending' THEN 'needs_score'
                   WHEN m.player1_id = ? AND COALESCE(m.player1_validated, 0) = 0 THEN 'needs_validation'
                   WHEN m.player2_id = ? AND COALESCE(m.player2_validated, 0) = 0 THEN 'needs_validation'
                   ELSE 'waiting_opponent'
               END as action_needed
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        WHERE (m.player1_id = ? OR m.player2_id = ?)
          AND (
              -- Show if match needs score submission
              m.status = 'pending' 
              OR (
                  -- Show only if this player hasn't validated yet
                  m.validation_status IN ('pending', 'partial')
                  AND (
                      (m.player1_id = ? AND COALESCE(m.player1_validated, 0) = 0)
                      OR (m.player2_id = ? AND COALESCE(m.player2_validated, 0) = 0)
                  )
              )
          )
          -- KEY FIX: Exclude matches where this player has already validated
          AND NOT (
              (m.player1_id = ? AND COALESCE(m.player1_validated, 0) = 1)
              OR (m.player2_id = ? AND COALESCE(m.player2_validated, 0) = 1)
          )
        ORDER BY m.created_at DESC
    ''', (player_id, player_id, player_id, player_id, player_id, player_id, player_id, player_id)).fetchall()
    
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
    
    # Safely parse numeric fields with error handling
    try:
        entry_fee = float(request.form.get('entry_fee', 0))
    except (ValueError, TypeError):
        flash('Invalid entry fee format. Using $0 as default.', 'warning')
        entry_fee = 0.0
    
    try:
        max_players = int(request.form.get('max_players', 32))
        if max_players < 2 or max_players > 256:
            flash('Invalid player count. Using 32 as default.', 'warning')
            max_players = 32
    except (ValueError, TypeError):
        flash('Invalid player count format. Using 32 as default.', 'warning')
        max_players = 32
    
    # Get GPS coordinates and radius with robust error handling
    latitude_str = request.form.get('latitude')
    longitude_str = request.form.get('longitude')
    join_radius_str = request.form.get('join_radius', '25')
    
    # Safely parse GPS coordinates
    latitude = None
    longitude = None
    join_radius_miles = 25
    
    # Parse latitude with validation
    if latitude_str and latitude_str.strip():
        try:
            temp_lat = float(latitude_str.strip())
            if -90 <= temp_lat <= 90:
                latitude = temp_lat
            else:
                flash('Latitude must be between -90 and 90 degrees. GPS location not set.', 'warning')
        except (ValueError, TypeError):
            flash('Invalid latitude format. GPS location not set.', 'warning')
    
    # Parse longitude with validation
    if longitude_str and longitude_str.strip():
        try:
            temp_lon = float(longitude_str.strip())
            if -180 <= temp_lon <= 180:
                longitude = temp_lon
            else:
                flash('Longitude must be between -180 and 180 degrees. GPS location not set.', 'warning')
        except (ValueError, TypeError):
            flash('Invalid longitude format. GPS location not set.', 'warning')
    
    # Parse join radius with validation
    if join_radius_str and join_radius_str.strip():
        try:
            temp_radius = int(join_radius_str.strip())
            if 1 <= temp_radius <= 100:
                join_radius_miles = temp_radius
            else:
                flash('Join radius must be between 1 and 100 miles. Using 25 miles as default.', 'warning')
                join_radius_miles = 25
        except (ValueError, TypeError):
            flash('Invalid join radius format. Using 25 miles as default.', 'warning')
            join_radius_miles = 25
    
    # Database insertion with error handling
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO tournament_instances (name, skill_level, entry_fee, max_players, latitude, longitude, join_radius_miles)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, skill_level, entry_fee, max_players, latitude, longitude, join_radius_miles))
        conn.commit()
        conn.close()
        
        # Check GPS location with proper None handling
        if latitude is not None and longitude is not None:
            flash(f'Tournament "{name}" created successfully with GPS location (lat: {latitude}, lon: {longitude})!', 'success')
        else:
            flash(f'Tournament "{name}" created successfully (no GPS location set)', 'warning')
            
    except Exception as e:
        logging.error(f"Database error creating tournament: {e}")
        flash(f'Error creating tournament: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))
    
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
        
        # Get GPS coordinates and radius if provided
        latitude_str = request.form.get('latitude')
        longitude_str = request.form.get('longitude')
        join_radius_str = request.form.get('join_radius', '25')
        
        # Convert and validate numeric fields with robust error handling
        if not max_players_str or not entry_fee_str:
            return jsonify({'success': False, 'message': 'Player count and entry fee are required'})
        
        # Safely parse max_players
        try:
            max_players = int(max_players_str)
            if max_players < 2 or max_players > 256:
                return jsonify({'success': False, 'message': 'Player count must be between 2 and 256'})
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid player count format'})
        
        # Safely parse entry_fee
        try:
            entry_fee = float(entry_fee_str)
            if entry_fee < 0 or entry_fee > 10000:
                return jsonify({'success': False, 'message': 'Entry fee must be between $0 and $10,000'})
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid entry fee format'})
        
        # Safely parse GPS coordinates with validation
        latitude = None
        longitude = None
        join_radius_miles = 25
        
        # Parse latitude with validation
        if latitude_str and latitude_str.strip():
            try:
                temp_lat = float(latitude_str.strip())
                if -90 <= temp_lat <= 90:
                    latitude = temp_lat
                else:
                    return jsonify({'success': False, 'message': 'Latitude must be between -90 and 90 degrees'})
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'Invalid latitude format'})
        
        # Parse longitude with validation
        if longitude_str and longitude_str.strip():
            try:
                temp_lon = float(longitude_str.strip())
                if -180 <= temp_lon <= 180:
                    longitude = temp_lon
                else:
                    return jsonify({'success': False, 'message': 'Longitude must be between -180 and 180 degrees'})
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'Invalid longitude format'})
        
        # Parse join radius with validation
        if join_radius_str and join_radius_str.strip():
            try:
                temp_radius = int(join_radius_str.strip())
                if 1 <= temp_radius <= 100:
                    join_radius_miles = temp_radius
                else:
                    return jsonify({'success': False, 'message': 'Join radius must be between 1 and 100 miles'})
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'Invalid join radius format'})
        
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
             registration_deadline, stripe_product_id, stripe_price_id,
             latitude, longitude, join_radius_miles)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (current_player_id, tournament_name, description, location, max_players,
              entry_fee, format_type, house_cut, prize_pool, start_date,
              registration_deadline, stripe_product.id, stripe_price.id,
              latitude, longitude, join_radius_miles))
        
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
@require_permission('can_join_tournaments')
def join_custom_tournament(tournament_id):
    """Join a custom tournament with payment and GPS validation - requires premium membership"""
    current_player_id = session.get('current_player_id')
    
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
    
    # GPS Validation for Custom Tournament Join
    user_latitude = request.args.get('lat')
    user_longitude = request.args.get('lng')
    
    # Convert GPS coordinates to float if provided
    try:
        if user_latitude:
            user_latitude = float(user_latitude)
        if user_longitude:
            user_longitude = float(user_longitude)
    except (ValueError, TypeError):
        user_latitude = None
        user_longitude = None
        logging.warning(f"Invalid GPS coordinates received for player {current_player_id}")
    
    # Perform GPS validation
    gps_validation = validate_tournament_join_gps(
        user_latitude, user_longitude, tournament, current_player_id
    )
    
    if not gps_validation['allowed']:
        logging.warning(f"Custom tournament join BLOCKED for player {current_player_id}: {gps_validation['reason']}")
        flash(gps_validation['error_message'], 'danger')
        conn.close()
        return redirect(url_for('tournaments_overview'))
    
    # Log successful GPS validation
    if gps_validation['distance_miles'] is not None:
        logging.info(f"GPS validation PASSED for custom tournament join - player {current_player_id}: {gps_validation['distance_miles']} miles from tournament")
    
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
                'tournament_type': 'custom',
                'user_latitude': str(user_latitude) if user_latitude is not None else '',
                'user_longitude': str(user_longitude) if user_longitude is not None else ''
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
    """Handle successful tournament payment with GPS validation"""
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
            
            # Get tournament details for GPS validation
            tournament = conn.execute('''
                SELECT * FROM custom_tournaments WHERE id = ?
            ''', (tournament_id,)).fetchone()
            
            if not tournament:
                flash('Tournament not found', 'danger')
                conn.close()
                return redirect(url_for('tournaments_overview'))
            
            # Extract GPS coordinates from Stripe metadata
            metadata = checkout_session.metadata or {}
            user_latitude_str = metadata.get('user_latitude', '')
            user_longitude_str = metadata.get('user_longitude', '')
            
            # Convert GPS coordinates to float if provided
            user_latitude = None
            user_longitude = None
            try:
                if user_latitude_str and user_latitude_str.strip():
                    user_latitude = float(user_latitude_str)
                if user_longitude_str and user_longitude_str.strip():
                    user_longitude = float(user_longitude_str)
            except (ValueError, TypeError):
                user_latitude = None
                user_longitude = None
                logging.warning(f"Invalid GPS coordinates in Stripe metadata for payment {checkout_session.payment_intent}")
            
            # Perform GPS validation
            gps_validation = validate_tournament_join_gps(
                user_latitude, user_longitude, tournament, current_player_id
            )
            
            if not gps_validation['allowed']:
                logging.warning(f"Tournament payment success BLOCKED for player {current_player_id}: {gps_validation['reason']}")
                # Payment was successful but GPS validation failed - this is a critical security issue
                # We need to refund the payment or handle this gracefully
                flash(f"Payment successful but tournament join blocked: {gps_validation['error_message']} Please contact support for a refund.", 'danger')
                conn.close()
                return redirect(url_for('tournaments_overview'))
            
            # Log successful GPS validation
            if gps_validation['distance_miles'] is not None:
                logging.info(f"GPS validation PASSED for tournament payment success - player {current_player_id}: {gps_validation['distance_miles']} miles from tournament")
            
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
            
            # Track referral conversion for tournament payment (counts as qualified referral)
            track_referral_conversion(current_player_id, 'tournament')
            
            flash('Successfully joined the tournament!', 'success')
            
        else:
            flash('Payment was not completed', 'warning')
            
    except Exception as e:
        logging.error(f"Error processing tournament payment success: {e}")
        flash('Error confirming payment. Please contact support.', 'danger')
    
    return redirect(url_for('tournaments_overview'))

@app.route('/admin/backfill_matches')
@admin_required
def admin_backfill_matches():
    """Admin route to backfill existing matches with team data"""
    try:
        count = backfill_existing_matches_as_singles()
        flash(f'Successfully backfilled {count} matches with team data', 'success')
    except Exception as e:
        flash(f'Error backfilling matches: {str(e)}', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/update_match_preference', methods=['POST'])
def update_match_preference():
    """Update player's match preference"""
    current_player_id = session.get('current_player_id')
    
    if not current_player_id:
        return jsonify({'success': False, 'message': 'Authentication required'})
    
    preference = request.form.get('match_preference')
    if preference not in ['singles', 'doubles_with_partner', 'doubles_need_partner']:
        return jsonify({'success': False, 'message': 'Invalid preference'})
    
    try:
        conn = get_db_connection()
        conn.execute('UPDATE players SET match_preference = ? WHERE id = ?', (preference, current_player_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Match preference updated successfully'})
    except Exception as e:
        logging.error(f"Error updating match preference: {e}")
        return jsonify({'success': False, 'message': 'Failed to update preference'})

@app.route('/send_team_invitation', methods=['POST'])
def send_team_invitation_route():
    """Send a team invitation to another player"""
    current_player_id = session.get('current_player_id')
    
    if not current_player_id:
        return jsonify({'success': False, 'message': 'Authentication required'})
    
    invitee_id = request.form.get('invitee_id')
    message = request.form.get('message', '')
    
    if not invitee_id:
        return jsonify({'success': False, 'message': 'Invitee required'})
    
    result = send_team_invitation(current_player_id, int(invitee_id), message)
    return jsonify(result)

@app.route('/accept_team_invitation/<int:invitation_id>')
def accept_team_invitation_route(invitation_id):
    """Accept a team invitation"""
    current_player_id = session.get('current_player_id')
    
    if not current_player_id:
        flash('Please log in first', 'warning')
        return redirect(url_for('player_login'))
    
    result = accept_team_invitation(invitation_id, current_player_id)
    
    if result['success']:
        flash('Team invitation accepted! You now have a doubles partner.', 'success')
    else:
        flash(f'Failed to accept invitation: {result["message"]}', 'error')
    
    return redirect(url_for('profile_settings'))

@app.route('/accept_pair_up_request/<int:invitation_id>', methods=['POST'])
def accept_pair_up_request(invitation_id):
    """Accept a pair-up request for team formation"""
    current_player_id = session.get('current_player_id') or session.get('player_id')
    
    if not current_player_id:
        flash('Please log in first', 'warning')
        return redirect(url_for('player_login'))
    
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        # Get invitation details - only actual team formation requests
        cursor.execute('''
            SELECT * FROM team_invitations 
            WHERE id = %s AND invitee_id = %s AND status = 'pending'
            AND (meta_json::jsonb->>'type' != 'singles' OR meta_json IS NULL)
        ''', (invitation_id, current_player_id))
        invitation = cursor.fetchone()
        
        if not invitation:
            flash('Invalid pair-up request', 'danger')
            return redirect(request.referrer or url_for('player_home', player_id=current_player_id))
        
        # Check if either player is already in a team
        cursor.execute('SELECT current_team_id FROM players WHERE id = %s', (invitation['inviter_id'],))
        player1_team = cursor.fetchone()
        cursor.execute('SELECT current_team_id FROM players WHERE id = %s', (current_player_id,))
        player2_team = cursor.fetchone()
        
        if (player1_team and player1_team['current_team_id']) or (player2_team and player2_team['current_team_id']):
            flash('One of you is already in a team', 'danger')
            return redirect(request.referrer or url_for('player_home', player_id=current_player_id))
        
        # Create the team
        team_result = create_team(invitation['inviter_id'], current_player_id, invitation['inviter_id'])
        
        if not team_result['success']:
            flash(f'Failed to create team: {team_result["message"]}', 'danger')
            return redirect(request.referrer or url_for('player_home', player_id=current_player_id))
        
        # Update invitation status
        cursor.execute('''
            UPDATE team_invitations 
            SET status = 'accepted', responded_at = %s
            WHERE id = %s
        ''', (datetime.now(), invitation_id))
        
        conn.commit()
        conn.close()
        
        # Show success message as requested by user
        flash('Success, go compete as a team now!', 'success')
        return redirect(request.referrer or url_for('player_home', player_id=current_player_id))
        
    except Exception as e:
        logging.error(f"Error accepting pair-up request: {e}")
        flash('Failed to accept pair-up request', 'danger')
        return redirect(request.referrer or url_for('player_home', player_id=current_player_id))

@app.route('/reject_pair_up_request/<int:invitation_id>', methods=['POST'])
def reject_pair_up_request(invitation_id):
    """Reject a pair-up request for team formation"""
    current_player_id = session.get('current_player_id') or session.get('player_id')
    
    if not current_player_id:
        flash('Please log in first', 'warning')
        return redirect(url_for('player_login'))
    
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        # Update invitation status - only actual team formation requests
        cursor.execute('''
            UPDATE team_invitations 
            SET status = 'rejected', responded_at = %s
            WHERE id = %s AND invitee_id = %s AND status = 'pending'
            AND (meta_json::jsonb->>'type' != 'singles' OR meta_json IS NULL)
        ''', (datetime.now(), invitation_id, current_player_id))
        
        if cursor.rowcount == 0:
            flash('Invalid pair-up request', 'danger')
        else:
            flash('Pair-up request declined', 'info')
        
        conn.commit()
        conn.close()
        return redirect(request.referrer or url_for('player_home', player_id=current_player_id))
        
    except Exception as e:
        logging.error(f"Error rejecting pair-up request: {e}")
        flash('Failed to reject pair-up request', 'danger')
        return redirect(request.referrer or url_for('player_home', player_id=current_player_id))

@app.route('/accept_match_challenge/<int:challenge_id>', methods=['POST'])
def accept_match_challenge(challenge_id):
    """Accept a singles match challenge"""
    current_player_id = session.get('current_player_id') or session.get('player_id')
    
    if not current_player_id:
        flash('Please log in first', 'warning')
        return redirect(url_for('player_login'))
    
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        # Get challenge details - only singles challenges
        cursor.execute('''
            SELECT * FROM team_invitations 
            WHERE id = %s AND invitee_id = %s AND status = 'pending'
            AND meta_json::jsonb->>'type' = 'singles'
        ''', (challenge_id, current_player_id))
        challenge = cursor.fetchone()
        
        if not challenge:
            flash('Invalid match challenge', 'danger')
            return redirect(request.referrer or url_for('player_home', player_id=current_player_id))
        
        # Handle the random match acceptance
        result = handle_random_match_acceptance(challenge, current_player_id, conn)
        
        if result['success']:
            flash('Match challenge accepted! Get ready to play.', 'success')
        else:
            flash(f'Failed to accept challenge: {result["message"]}', 'danger')
        
        conn.close()
        return redirect(request.referrer or url_for('player_home', player_id=current_player_id))
        
    except Exception as e:
        logging.error(f"Error accepting match challenge: {e}")
        flash('Failed to accept match challenge', 'danger')
        return redirect(request.referrer or url_for('player_home', player_id=current_player_id))

@app.route('/reject_match_challenge/<int:challenge_id>', methods=['POST'])
def reject_match_challenge(challenge_id):
    """Reject a singles match challenge"""
    current_player_id = session.get('current_player_id') or session.get('player_id')
    
    if not current_player_id:
        flash('Please log in first', 'warning')
        return redirect(url_for('player_login'))
    
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        # Update challenge status - only singles challenges
        cursor.execute('''
            UPDATE team_invitations 
            SET status = 'rejected', responded_at = %s
            WHERE id = %s AND invitee_id = %s AND status = 'pending'
            AND meta_json::jsonb->>'type' = 'singles'
        ''', (datetime.now(), challenge_id, current_player_id))
        
        if cursor.rowcount == 0:
            flash('Invalid match challenge', 'danger')
        else:
            flash('Match challenge declined', 'info')
        
        conn.commit()
        conn.close()
        return redirect(request.referrer or url_for('player_home', player_id=current_player_id))
        
    except Exception as e:
        logging.error(f"Error rejecting match challenge: {e}")
        flash('Failed to reject match challenge', 'danger')
        return redirect(request.referrer or url_for('player_home', player_id=current_player_id))

@app.route('/reject_team_invitation/<int:invitation_id>')
def reject_team_invitation_route(invitation_id):
    """Reject a team invitation or match challenge"""
    current_player_id = session.get('current_player_id') or session.get('player_id')
    
    logging.info(f"🚫 DECLINE DEBUG: invitation_id={invitation_id}, current_player_id={current_player_id}")
    
    if not current_player_id:
        flash('Please log in first', 'warning')
        return redirect(url_for('player_login'))
    
    # First check if this is a match challenge (singles/doubles match) instead of a team invitation
    try:
        conn = get_db_connection()
        invitation = conn.execute('''
            SELECT * FROM team_invitations WHERE id = ? AND invitee_id = ? AND status = 'pending'
        ''', (invitation_id, current_player_id)).fetchone()
        
        logging.info(f"🚫 INVITATION FOUND: {invitation}")
        
        if invitation:
            # Check if this has meta_json indicating it's a match challenge
            if invitation.get('meta_json'):
                import json
                try:
                    meta = json.loads(invitation['meta_json'])
                    logging.info(f"🚫 META JSON: {meta}")
                    if meta.get('type') in ['singles', 'doubles']:
                        # This is a match challenge, not a team invitation
                        logging.info("🚫 Detected as match challenge - declining directly")
                        conn.execute('''
                            UPDATE team_invitations 
                            SET status = 'rejected', responded_at = datetime('now')
                            WHERE id = ? AND invitee_id = ? AND status = 'pending'
                        ''', (invitation_id, current_player_id))
                        conn.commit()
                        conn.close()
                        
                        flash('Match challenge declined.', 'info')
                        return redirect(url_for('player_home'))
                except json.JSONDecodeError:
                    logging.error(f"Invalid JSON in meta_json: {invitation.get('meta_json')}")
        
        conn.close()
    except Exception as e:
        logging.error(f"Error checking invitation type: {e}")
    
    # Regular team invitation decline
    result = reject_team_invitation(invitation_id, current_player_id)
    
    logging.info(f"🚫 DECLINE RESULT: {result}")
    
    if result['success']:
        flash('Team invitation declined.', 'info')
    else:
        flash(f'Failed to decline invitation: {result["message"]}', 'error')
    
    return redirect(url_for('profile_settings'))

@app.route('/leave_team')
def leave_team():
    """Leave/dissolve current team"""
    current_player_id = session.get('current_player_id')
    
    if not current_player_id:
        flash('Please log in first', 'warning')
        return redirect(url_for('player_login'))
    
    try:
        conn = get_db_connection()
        
        # Get player's current team
        player = conn.execute('SELECT current_team_id FROM players WHERE id = ?', (current_player_id,)).fetchone()
        
        if not player or not player['current_team_id']:
            flash('You are not currently in a team', 'info')
            return redirect(url_for('profile_settings'))
        
        team_id = player['current_team_id']
        
        # Get team details for notification
        team = conn.execute('''
            SELECT player1_id, player2_id FROM teams WHERE id = ? AND status = 'active'
        ''', (team_id,)).fetchone()
        
        if not team:
            flash('Team not found', 'error')
            return redirect(url_for('profile_settings'))
        
        # Dissolve the team
        conn.execute('UPDATE teams SET status = "dissolved" WHERE id = ?', (team_id,))
        
        # Clear current_team_id for both players
        conn.execute('UPDATE players SET current_team_id = NULL WHERE id IN (?, ?)', 
                    (team['player1_id'], team['player2_id']))
        
        # Update match preferences back to singles for both players
        conn.execute('UPDATE players SET match_preference = "singles" WHERE id IN (?, ?)', 
                    (team['player1_id'], team['player2_id']))
        
        conn.commit()
        conn.close()
        
        flash('You have successfully switched partners. You can now form a new partnership.', 'success')
        
    except Exception as e:
        logging.error(f"Error leaving team: {e}")
        flash('Error leaving team. Please try again.', 'error')
    
    return redirect(url_for('profile_settings'))

@app.route('/team_search')
def team_search():
    """Search for potential team partners"""
    current_player_id = session.get('current_player_id')
    
    logging.info(f"🎯 TEAM SEARCH DEBUG: current_player_id = {current_player_id}")
    
    if not current_player_id:
        flash('Please log in first', 'warning')
        return redirect(url_for('player_login'))
    
    # Check if player needs a partner
    conn = get_db_connection()
    player = conn.execute('SELECT match_preference FROM players WHERE id = ?', (current_player_id,)).fetchone()
    
    logging.info(f"🎯 PLAYER DEBUG: player found = {player}")
    if player:
        logging.info(f"🎯 PREFERENCE DEBUG: match_preference = '{player['match_preference']}'")
    
    if not player or player['match_preference'] != 'doubles_need_partner':
        logging.error(f"🎯 ACCESS DENIED: player={player}, preference={player['match_preference'] if player else 'None'}")
        flash('Team search is only available if you need a doubles partner', 'warning')
        return redirect(url_for('profile_settings'))
    
    # Get potential partners (players who also need partners)
    potential_partners = conn.execute('''
        SELECT p.id, p.full_name, p.selfie, p.skill_level, p.location1, p.wins, p.losses, p.ranking_points
        FROM players p
        WHERE p.id != ? 
        AND p.match_preference = 'doubles_need_partner'
        AND p.current_team_id IS NULL
        AND p.is_looking_for_match = 1
        AND (p.discoverability_preference = 'doubles' OR p.discoverability_preference = 'both' OR p.discoverability_preference IS NULL)
        ORDER BY p.ranking_points DESC, p.wins DESC
    ''', (current_player_id,)).fetchall()
    
    logging.info(f"🎯 PARTNERS DEBUG: Found {len(potential_partners)} potential partners")
    for partner in potential_partners:
        logging.info(f"🎯 PARTNER: {partner['full_name']} - {partner['location1']} - Preference: Need Partner")
    
    conn.close()
    
    return render_template('team_search.html', 
                         potential_partners=[dict(p) for p in potential_partners],
                         current_player_id=current_player_id)

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard with platform overview"""
    conn = get_pg_connection()
    cursor = conn.cursor()
    
    # Get existing tournament instances for management
    cursor.execute('''
        SELECT * FROM tournament_instances 
        ORDER BY skill_level, created_at
    ''')
    existing_tournaments = cursor.fetchall()
    
    # Get key metrics
    cursor.execute('SELECT COUNT(*) as count FROM players')
    total_players = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM matches')
    total_matches = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM tournaments')
    total_tournaments = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM tournaments WHERE completed = FALSE')
    active_tournaments = cursor.fetchone()['count']
    
    # Get detailed player metrics by skill level
    cursor.execute('SELECT COUNT(*) as count FROM players WHERE skill_level = %s', ('Beginner',))
    beginner_players = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM players WHERE skill_level = %s', ('Intermediate',))
    intermediate_players = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM players WHERE skill_level = %s', ('Advanced',))
    advanced_players = cursor.fetchone()['count']
    
    # Get tournament financial metrics
    tournament_levels = get_tournament_levels()
    total_revenue = 0
    total_payouts = 0
    
    for level_key, level_info in tournament_levels.items():
        entry_fee = level_info['entry_fee']
        
        # Count entries for this level
        cursor.execute('''
            SELECT COUNT(*) as count FROM tournaments 
            WHERE tournament_level = %s
        ''', (level_key,))
        level_entries = cursor.fetchone()['count']
        
        # Calculate revenue for this level
        level_revenue = level_entries * entry_fee
        total_revenue += level_revenue
        
        # Calculate payouts (70% of revenue goes to winners, 30% platform revenue)
        level_payouts = level_revenue * 0.7
        total_payouts += level_payouts
    
    # Recent activity
    cursor.execute('''
        SELECT * FROM players ORDER BY created_at DESC LIMIT 5
    ''')
    recent_players = cursor.fetchall()
    
    cursor.execute('''
        SELECT m.*, p1.full_name as player1_name, p2.full_name as player2_name
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        ORDER BY m.created_at DESC LIMIT 10
    ''')
    recent_matches = cursor.fetchall()
    
    cursor.execute('''
        SELECT t.*, p.full_name FROM tournaments t
        JOIN players p ON t.player_id = p.id
        ORDER BY t.created_at DESC LIMIT 10
    ''')
    recent_tournaments = cursor.fetchall()
    
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

@app.route('/admin/players/<int:player_id>/edit')
@admin_required
def admin_edit_player(player_id):
    """Admin edit specific player profile"""
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    conn.close()
    
    if not player:
        flash('Player not found', 'danger')
        return redirect(url_for('admin_players'))
    
    return render_template('admin/edit_player.html', player=player)

@app.route('/admin/players/<int:player_id>/edit', methods=['POST'])
@admin_required
def admin_update_player(player_id):
    """Handle admin player profile update"""
    from werkzeug.security import generate_password_hash
    
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    
    if not player:
        flash('Player not found', 'danger')
        return redirect(url_for('admin_players'))
    
    # Form validation
    required_fields = ['full_name', 'email', 'skill_level']
    for field in required_fields:
        if not request.form.get(field):
            flash(f'{field.replace("_", " ").title()} is required', 'danger')
            return redirect(url_for('admin_edit_player', player_id=player_id))
    
    # Handle file upload
    selfie_filename = player['selfie']  # Keep existing if no new upload
    if 'selfie' in request.files:
        file = request.files['selfie']
        if file and file.filename and file.filename != '':
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                selfie_filename = timestamp + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], selfie_filename))
    
    try:
        # Update player information
        update_data = {
            'full_name': request.form['full_name'],
            'email': request.form['email'],
            'skill_level': request.form['skill_level'],
            'address': request.form.get('address', ''),
            'zip_code': request.form.get('zip_code', ''),
            'city': request.form.get('city', ''),
            'state': request.form.get('state', ''),
            'dob': request.form.get('dob', ''),
            'location1': request.form.get('location1', ''),
            'location2': request.form.get('location2', ''),
            'preferred_court_1': request.form.get('preferred_court_1', ''),
            'preferred_court_2': request.form.get('preferred_court_2', ''),
            'selfie': selfie_filename
        }
        
        # Handle username and password updates
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username:
            # Check if username is already taken by another player
            existing = conn.execute('SELECT id FROM players WHERE username = ? AND id != ?', 
                                  (username, player_id)).fetchone()
            if existing:
                flash('Username already taken by another player', 'danger')
                return redirect(url_for('admin_edit_player', player_id=player_id))
            update_data['username'] = username
        
        if password:
            update_data['password_hash'] = generate_password_hash(password)
        
        # Build dynamic update query
        set_clause = ', '.join([f"{key} = ?" for key in update_data.keys()])
        values = list(update_data.values()) + [player_id]
        
        conn.execute(f'UPDATE players SET {set_clause} WHERE id = ?', values)
        conn.commit()
        conn.close()
        
        flash(f'Player {request.form["full_name"]} updated successfully!', 'success')
        return redirect(url_for('admin_players'))
        
    except Exception as e:
        logging.error(f"Error updating player {player_id}: {str(e)}")
        flash(f'Error updating player: {str(e)}', 'danger')
        return redirect(url_for('admin_edit_player', player_id=player_id))

@app.route('/admin/players/<int:player_id>/delete', methods=['POST'])
@admin_required
def admin_delete_player(player_id):
    """Delete a test player (except ID 1)"""
    # Prevent deletion of the main admin account (ID 1)
    if player_id == 1:
        flash('Cannot delete the main admin account', 'danger')
        return redirect(url_for('admin_players'))
    
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    
    if not player:
        flash('Player not found', 'danger')
        conn.close()
        return redirect(url_for('admin_players'))
    
    try:
        # Delete the player
        conn.execute('DELETE FROM players WHERE id = ?', (player_id,))
        conn.commit()
        flash(f'Player "{player["full_name"]}" deleted successfully', 'success')
        logging.info(f"Player {player_id} deleted by admin")
    except Exception as e:
        logging.error(f"Error deleting player {player_id}: {str(e)}")
        flash(f'Error deleting player: {str(e)}', 'danger')
    
    conn.close()
    return redirect(url_for('admin_players'))

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

@app.route('/admin/ambassadors')
@admin_required
def admin_ambassadors():
    """Admin ambassador management with state tracking"""
    conn = get_db_connection()
    
    # Get ambassador statistics by state
    state_stats = conn.execute('''
        SELECT 
            state_territory,
            COUNT(*) as ambassador_count,
            AVG(qualified_referrals) as avg_referrals,
            MAX(qualified_referrals) as top_referrals,
            COUNT(CASE WHEN lifetime_membership_granted = 1 THEN 1 END) as lifetime_members
        FROM ambassadors 
        WHERE status = 'active'
        GROUP BY state_territory
        ORDER BY ambassador_count DESC, state_territory
    ''').fetchall()
    
    # Get all ambassadors with their details
    ambassadors = conn.execute('''
        SELECT 
            a.*, 
            p.full_name, 
            p.email,
            COUNT(ar.id) as total_referrals,
            COUNT(CASE WHEN ar.qualified = 1 THEN 1 END) as qualified_referrals_actual
        FROM ambassadors a
        JOIN players p ON a.player_id = p.id
        LEFT JOIN ambassador_referrals ar ON a.id = ar.ambassador_id
        WHERE a.status = 'active'
        GROUP BY a.id
        ORDER BY a.state_territory, a.qualified_referrals DESC
    ''').fetchall()
    
    # Get total counts for overview
    total_ambassadors = conn.execute('SELECT COUNT(*) as count FROM ambassadors WHERE status = "active"').fetchone()['count']
    total_states = conn.execute('SELECT COUNT(DISTINCT state_territory) as count FROM ambassadors WHERE status = "active"').fetchone()['count']
    total_referrals = conn.execute('SELECT COUNT(*) as count FROM ambassador_referrals WHERE qualified = 1').fetchone()['count']
    
    conn.close()
    
    return render_template('admin/ambassadors.html', 
                         state_stats=state_stats,
                         ambassadors=ambassadors,
                         total_ambassadors=total_ambassadors,
                         total_states=total_states,
                         total_referrals=total_referrals)

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
    flash('Switched to player session for testing', 'info')
    return redirect(url_for('player_home', player_id=player_id))

@app.route('/admin/create_test_player', methods=['POST'])
@admin_required
def create_test_player():
    """Create a test player for admin testing purposes"""
    import secrets
    from datetime import datetime
    
    # Get form data
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    skill_level = request.form.get('skill_level')
    membership_type = request.form.get('membership_type') or None
    location1 = request.form.get('location1')
    dob = request.form.get('dob')
    address = request.form.get('address')
    username = request.form.get('username')
    password = request.form.get('password')
    switch_immediately = request.form.get('switch_immediately')
    
    # Auto-generate email if not provided
    if not email or email.strip() == '':
        import time
        timestamp = int(time.time())
        email = f"{username}_{timestamp}@ready2dink.test"
    
    # Validate required fields (email is now optional and auto-generated)
    if not all([full_name, skill_level, location1, dob, address, username, password]):
        flash('All fields except email are required', 'danger')
        return redirect(url_for('admin_players'))
    
    conn = get_db_connection()
    
    try:
        from werkzeug.security import generate_password_hash
        
        # Check if email already exists
        existing = conn.execute('SELECT id FROM players WHERE email = ?', (email,)).fetchone()
        if existing:
            flash('Email already exists', 'danger')
            return redirect(url_for('admin_players'))
        
        # Check if username already exists
        existing_username = conn.execute('SELECT id FROM players WHERE username = ?', (username,)).fetchone()
        if existing_username:
            flash('Username already exists', 'danger')
            return redirect(url_for('admin_players'))
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Create test player with default values
        conn.execute('''
            INSERT INTO players (
                full_name, email, skill_level, location1, dob, address,
                membership_type, subscription_status, tournament_credits,
                wins, losses, is_admin, username, password_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            full_name, email, skill_level, location1, dob, address,
            membership_type, 'active' if membership_type else None, 
            5 if membership_type == 'tournament' else 0,  # Give tournament credits if tournament member
            0, 0, False, username, password_hash, datetime.now().isoformat()
        ))
        
        conn.commit()
        
        # Get the new player ID and full data
        new_player = conn.execute('SELECT * FROM players WHERE email = ?', (email,)).fetchone()
        
        # Send email notification to admin about new test player registration
        player_data = {
            'full_name': full_name,
            'email': email,
            'skill_level': skill_level,
            'location1': location1,
            'location2': '',
            'preferred_court': address,  # Use address as preferred court for test players
            'address': address,
            'dob': dob
        }
        
        email_sent = send_new_registration_notification(player_data)
        
        if email_sent:
            logging.info(f"New test player registration email notification sent successfully")
        else:
            logging.warning(f"Failed to send email notification for new test player: {full_name}")
        
        if switch_immediately:
            session['current_player_id'] = new_player['id']
            flash(f'Test player "{full_name}" created and logged in!', 'success')
            return redirect(url_for('player_home', player_id=new_player['id']))
        else:
            flash(f'Test player "{full_name}" created successfully!', 'success')
            return redirect(url_for('admin_players'))
            
    except Exception as e:
        conn.rollback()
        flash(f'Error creating test player: {str(e)}', 'danger')
        return redirect(url_for('admin_players'))
    finally:
        conn.close()

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

@app.route('/admin/payouts')
@admin_required
def admin_payouts():
    """Admin payout management interface"""
    conn = get_db_connection()
    
    # Get all pending payouts
    pending_payouts = conn.execute('''
        SELECT tp.*, p.full_name, p.email, p.player_id
        FROM tournament_payouts tp
        JOIN players p ON tp.player_id = p.id
        WHERE tp.status = 'pending'
        ORDER BY tp.created_at ASC
    ''').fetchall()
    
    # Get processing payouts
    processing_payouts = conn.execute('''
        SELECT tp.*, p.full_name, p.email, p.player_id
        FROM tournament_payouts tp
        JOIN players p ON tp.player_id = p.id
        WHERE tp.status = 'processing'
        ORDER BY tp.created_at ASC
    ''').fetchall()
    
    # Get recent completed payouts
    completed_payouts = conn.execute('''
        SELECT tp.*, p.full_name, p.email, p.player_id, admin.full_name as paid_by_name
        FROM tournament_payouts tp
        JOIN players p ON tp.player_id = p.id
        LEFT JOIN players admin ON tp.paid_by = admin.id
        WHERE tp.status = 'paid'
        ORDER BY tp.paid_at DESC
        LIMIT 20
    ''').fetchall()
    
    # Calculate totals
    total_pending = sum(float(payout['prize_amount']) for payout in pending_payouts)
    total_processing = sum(float(payout['prize_amount']) for payout in processing_payouts)
    total_paid_this_month = conn.execute('''
        SELECT COALESCE(SUM(prize_amount), 0) as total
        FROM tournament_payouts 
        WHERE status = 'paid' 
        AND date(paid_at) >= date('now', 'start of month')
    ''').fetchone()['total']
    
    conn.close()
    
    return render_template('admin/payouts.html', 
                         pending_payouts=pending_payouts,
                         processing_payouts=processing_payouts,
                         completed_payouts=completed_payouts,
                         total_pending=total_pending,
                         total_processing=total_processing,
                         total_paid_this_month=total_paid_this_month)

@app.route('/admin/update_payout_status/<int:payout_id>', methods=['POST'])
@admin_required
def update_payout_status(payout_id):
    """Update payout status"""
    new_status = request.form.get('status')
    admin_notes = request.form.get('admin_notes', '')
    admin_id = session.get('current_player_id')
    
    if new_status not in ['pending', 'processing', 'paid', 'failed']:
        flash('Invalid status', 'danger')
        return redirect(url_for('admin_payouts'))
    
    conn = get_db_connection()
    
    try:
        # Update payout status
        if new_status == 'paid':
            conn.execute('''
                UPDATE tournament_payouts 
                SET status = ?, admin_notes = ?, paid_by = ?, paid_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_status, admin_notes, admin_id, payout_id))
        else:
            conn.execute('''
                UPDATE tournament_payouts 
                SET status = ?, admin_notes = ?
                WHERE id = ?
            ''', (new_status, admin_notes, payout_id))
        
        conn.commit()
        
        # Get payout info for flash message
        payout = conn.execute('''
            SELECT tp.*, p.full_name 
            FROM tournament_payouts tp
            JOIN players p ON tp.player_id = p.id
            WHERE tp.id = ?
        ''', (payout_id,)).fetchone()
        
        if payout:
            flash(f'Payout status updated to "{new_status}" for {payout["full_name"]} - ${payout["prize_amount"]:.2f}', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error updating payout: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('admin_payouts'))

@app.route('/admin/bank_settings')
@admin_required
def admin_bank_settings():
    """Display bank account settings page"""
    conn = get_db_connection()
    
    # Get current bank settings (there should only be one record)
    bank_settings = conn.execute('SELECT * FROM bank_settings ORDER BY updated_at DESC LIMIT 1').fetchone()
    
    conn.close()
    
    return render_template('admin/bank_settings.html', bank_settings=bank_settings)

@app.route('/admin/save_bank_settings', methods=['POST'])
@admin_required
def save_bank_settings():
    """Save or update bank account settings"""
    admin_id = session.get('current_player_id')
    
    # Get form data
    bank_name = request.form.get('bank_name')
    account_holder_name = request.form.get('account_holder_name')
    account_type = request.form.get('account_type')
    routing_number = request.form.get('routing_number')
    account_number = request.form.get('account_number')
    business_name = request.form.get('business_name')
    business_address = request.form.get('business_address')
    business_phone = request.form.get('business_phone')
    business_email = request.form.get('business_email')
    stripe_account_id = request.form.get('stripe_account_id')
    payout_method = request.form.get('payout_method', 'manual')
    auto_payout_enabled = 1 if request.form.get('auto_payout_enabled') else 0
    
    # Validate required fields
    if not account_holder_name or not account_type:
        flash('Account holder name and account type are required', 'danger')
        return redirect(url_for('admin_bank_settings'))
    
    conn = get_db_connection()
    
    try:
        # Check if bank settings already exist
        existing = conn.execute('SELECT id FROM bank_settings LIMIT 1').fetchone()
        
        if existing:
            # Update existing settings
            conn.execute('''
                UPDATE bank_settings SET
                    bank_name = ?, account_holder_name = ?, account_type = ?,
                    routing_number = ?, account_number = ?, business_name = ?,
                    business_address = ?, business_phone = ?, business_email = ?,
                    stripe_account_id = ?, payout_method = ?, auto_payout_enabled = ?,
                    updated_at = CURRENT_TIMESTAMP, updated_by = ?
                WHERE id = ?
            ''', (bank_name, account_holder_name, account_type, routing_number, 
                  account_number, business_name, business_address, business_phone,
                  business_email, stripe_account_id, payout_method, auto_payout_enabled,
                  admin_id, existing['id']))
            
            flash('Bank settings updated successfully!', 'success')
        else:
            # Insert new settings
            conn.execute('''
                INSERT INTO bank_settings (
                    bank_name, account_holder_name, account_type, routing_number,
                    account_number, business_name, business_address, business_phone,
                    business_email, stripe_account_id, payout_method, auto_payout_enabled,
                    updated_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (bank_name, account_holder_name, account_type, routing_number,
                  account_number, business_name, business_address, business_phone,
                  business_email, stripe_account_id, payout_method, auto_payout_enabled,
                  admin_id))
            
            flash('Bank settings saved successfully!', 'success')
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        flash(f'Error saving bank settings: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('admin_bank_settings'))

@app.route('/admin/staff')
@admin_required
def admin_staff():
    """Display admin staff management page"""
    conn = get_db_connection()
    
    # Get all admin users
    admin_staff = conn.execute('''
        SELECT * FROM players 
        WHERE is_admin = 1 
        ORDER BY created_at DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin/staff.html', admin_staff=admin_staff)

@app.route('/admin/create_admin_staff', methods=['POST'])
@admin_required
def create_admin_staff():
    """Create a new admin staff member"""
    from datetime import datetime
    import secrets
    import string
    from werkzeug.security import generate_password_hash
    
    # Get form data
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    job_title = request.form.get('job_title')
    location1 = request.form.get('location1')
    dob = request.form.get('dob')
    admin_level = request.form.get('admin_level', 'staff')
    address = request.form.get('address')
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Validate required fields
    if not all([full_name, email, location1, dob, address, username]):
        flash('All required fields must be filled', 'danger')
        return redirect(url_for('admin_staff'))
    
    # Generate password if not provided
    if not password:
        password = ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(12))
    
    conn = get_db_connection()
    
    try:
        # Check if email or username already exists
        existing_email = conn.execute('SELECT id FROM players WHERE email = ?', (email,)).fetchone()
        existing_username = conn.execute('SELECT id FROM players WHERE username = ?', (username,)).fetchone()
        
        if existing_email:
            flash('Email already exists in the system', 'danger')
            return redirect(url_for('admin_staff'))
            
        if existing_username:
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect(url_for('admin_staff'))
        
        # Hash the password
        password_hash = generate_password_hash(password)
        
        # Create admin staff account
        conn.execute('''
            INSERT INTO players (
                full_name, email, location1, dob, address, job_title,
                admin_level, is_admin, skill_level, membership_type,
                subscription_status, tournament_credits, wins, losses, 
                username, password_hash, must_change_password, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            full_name, email, location1, dob, address, job_title,
            admin_level, True, 'Admin', 'tournament',
            'active', 10, 0, 0, username, password_hash, 1, datetime.now().isoformat()
        ))
        
        conn.commit()
        
        # Send email with credentials
        login_url = f"{request.host_url}admin/login"
        email_sent = send_admin_credentials_email(full_name, email, username, password, login_url)
        
        # Show the login credentials to the admin
        flash(f'Admin staff member "{full_name}" created successfully!', 'success')
        
        if email_sent:
            flash(f'Login credentials have been sent to {email}', 'success')
        else:
            flash(f'Email failed to send. Manual credentials - Username: {username} | Password: {password}', 'warning')
            flash('Please share these credentials securely with the staff member.', 'warning')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error creating admin staff: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('admin_staff'))

@app.route('/admin/remove_admin_staff/<int:player_id>', methods=['POST'])
@admin_required
def remove_admin_staff(player_id):
    """Remove admin access from a staff member"""
    conn = get_db_connection()
    
    try:
        # Get player info before removing admin access
        player = conn.execute('SELECT full_name FROM players WHERE id = ?', (player_id,)).fetchone()
        
        if not player:
            flash('Staff member not found', 'danger')
            return redirect(url_for('admin_staff'))
        
        # Remove admin access
        conn.execute('UPDATE players SET is_admin = 0 WHERE id = ?', (player_id,))
        conn.commit()
        
        flash(f'Admin access removed from {player["full_name"]}', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error removing admin access: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('admin_staff'))

@app.route('/admin/login')
def admin_login():
    """Display admin login page"""
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    """Handle admin login form submission"""
    from werkzeug.security import check_password_hash
    
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Username and password are required', 'danger')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    
    try:
        # Find admin user by username
        admin = conn.execute('''
            SELECT id, full_name, username, password_hash, is_admin, must_change_password
            FROM players 
            WHERE username = ? AND is_admin = 1
        ''', (username,)).fetchone()
        
        if not admin:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('admin_login'))
        
        # Check password
        if not admin['password_hash'] or not check_password_hash(admin['password_hash'], password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('admin_login'))
        
        # Login successful - set session
        session['current_player_id'] = admin['id']
        
        # Check if password change is required
        if admin['must_change_password']:
            flash('You must change your password before accessing the admin panel', 'warning')
            return redirect(url_for('admin_change_password'))
        
        flash(f'Welcome back, {admin["full_name"]}!', 'success')
        return redirect(url_for('admin_dashboard'))
        
    except Exception as e:
        flash(f'Login error: {str(e)}', 'danger')
        return redirect(url_for('admin_login'))
    finally:
        conn.close()

@app.route('/admin/change_password')
def admin_change_password():
    """Display password change form for first-time login"""
    # Check if user is logged in
    if 'current_player_id' not in session:
        flash('Please log in first', 'warning')
        return redirect(url_for('admin_login'))
    
    return render_template('admin_change_password.html')

@app.route('/admin/change_password', methods=['POST'])
def admin_change_password_post():
    """Handle password change form submission"""
    from werkzeug.security import check_password_hash, generate_password_hash
    import re
    
    # Check if user is logged in
    if 'current_player_id' not in session:
        flash('Please log in first', 'warning')
        return redirect(url_for('admin_login'))
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        flash('All fields are required', 'danger')
        return redirect(url_for('admin_change_password'))
    
    # Validate password requirements
    if len(new_password) < 8:
        flash('Password must be at least 8 characters long', 'danger')
        return redirect(url_for('admin_change_password'))
    
    if not re.search(r'[A-Za-z]', new_password) or not re.search(r'[0-9]', new_password):
        flash('Password must contain both letters and numbers', 'danger')
        return redirect(url_for('admin_change_password'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('admin_change_password'))
    
    conn = get_db_connection()
    
    try:
        # Get current user
        admin = conn.execute('''
            SELECT id, full_name, password_hash
            FROM players 
            WHERE id = ? AND is_admin = 1
        ''', (session['current_player_id'],)).fetchone()
        
        if not admin:
            flash('Admin user not found', 'danger')
            return redirect(url_for('admin_login'))
        
        # Verify current password
        if not check_password_hash(admin['password_hash'], current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('admin_change_password'))
        
        # Hash new password
        new_password_hash = generate_password_hash(new_password)
        
        # Update password and clear must_change_password flag
        conn.execute('''
            UPDATE players 
            SET password_hash = ?, must_change_password = 0
            WHERE id = ?
        ''', (new_password_hash, admin['id']))
        
        conn.commit()
        
        flash(f'Password updated successfully! Welcome to the admin panel, {admin["full_name"]}!', 'success')
        return redirect(url_for('admin_dashboard'))
        
    except Exception as e:
        conn.rollback()
        flash(f'Error updating password: {str(e)}', 'danger')
        return redirect(url_for('admin_change_password'))
    finally:
        conn.close()

@app.route('/issue_tournament_credit', methods=['POST'])
@admin_required
def issue_tournament_credit():
    """Issue tournament credit to a player"""
    player_id = request.form.get('player_id')
    amount_str = request.form.get('amount')
    reason = request.form.get('reason')
    description = request.form.get('description', '')
    
    # Get current admin ID
    admin_id = session.get('current_player_id')
    
    # Validate required fields
    if not player_id or not amount_str or not reason:
        flash('All fields are required', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        amount = float(amount_str)
        if amount <= 0:
            flash('Credit amount must be greater than 0', 'danger')
            return redirect(url_for('admin_dashboard'))
    except (ValueError, TypeError):
        flash('Invalid credit amount', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    conn = get_db_connection()
    
    try:
        # Verify player exists
        player = conn.execute('SELECT full_name, tournament_credits FROM players WHERE id = ?', (player_id,)).fetchone()
        if not player:
            flash('Player not found', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        # Update player's credit balance
        new_balance = (player['tournament_credits'] or 0) + amount
        conn.execute('UPDATE players SET tournament_credits = ? WHERE id = ?', (new_balance, player_id))
        
        # Record the transaction
        full_description = f"{reason.replace('_', ' ').title()}: {description}" if description else reason.replace('_', ' ').title()
        conn.execute('''
            INSERT INTO credit_transactions (player_id, transaction_type, amount, description, admin_id)
            VALUES (?, 'credit_issued', ?, ?, ?)
        ''', (player_id, amount, full_description, admin_id))
        
        conn.commit()
        
        flash(f'Successfully issued ${amount:.2f} credit to {player["full_name"]}. New balance: ${new_balance:.2f}', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error issuing credit: {str(e)}', 'danger')
        
    finally:
        conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/api/search_players')
def api_search_players():
    """API endpoint to search for players"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify({'players': []})
    
    conn = get_db_connection()
    
    # Search by name, email, or player ID
    players = conn.execute('''
        SELECT id, full_name, email, player_id, tournament_credits
        FROM players 
        WHERE full_name LIKE ? OR email LIKE ? OR player_id LIKE ?
        ORDER BY full_name
        LIMIT 10
    ''', (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    
    conn.close()
    
    players_list = []
    for player in players:
        players_list.append({
            'id': player['id'],
            'full_name': player['full_name'],
            'email': player['email'],
            'player_id': player['player_id'],
            'tournament_credits': float(player['tournament_credits'] or 0)
        })
    
    return jsonify({'players': players_list})

@app.route('/api/recent_credit_transactions')
def api_recent_credit_transactions():
    """API endpoint to get recent credit transactions"""
    conn = get_db_connection()
    
    transactions = conn.execute('''
        SELECT ct.*, p.full_name as player_name, p.player_id, a.full_name as admin_name
        FROM credit_transactions ct
        JOIN players p ON ct.player_id = p.id
        LEFT JOIN players a ON ct.admin_id = a.id
        ORDER BY ct.created_at DESC
        LIMIT 20
    ''').fetchall()
    
    conn.close()
    
    transactions_list = []
    for tx in transactions:
        transactions_list.append({
            'id': tx['id'],
            'player_name': tx['player_name'],
            'player_id': tx['player_id'],
            'transaction_type': tx['transaction_type'],
            'amount': float(tx['amount']),
            'description': tx['description'],
            'admin_name': tx['admin_name'],
            'created_at': tx['created_at']
        })
    
    return jsonify({'transactions': transactions_list})

@app.route('/api/player_stats/<int:player_id>')
def api_player_stats(player_id):
    """API endpoint to get player statistics"""
    try:
        conn = get_db_connection()
        
        player = conn.execute('''
            SELECT id, full_name, skill_level, wins, losses, ranking_points, location
            FROM players 
            WHERE id = ?
        ''', (player_id,)).fetchone()
        
        conn.close()
        
        if not player:
            return jsonify({'success': False, 'message': 'Player not found'})
        
        return jsonify({
            'success': True,
            'player': {
                'id': player['id'],
                'full_name': player['full_name'],
                'skill_level': player['skill_level'],
                'wins': player['wins'] or 0,
                'losses': player['losses'] or 0,
                'ranking_points': player['ranking_points'] or 0,
                'location': player['location']
            }
        })
        
    except Exception as e:
        logging.error(f"Error fetching player stats for player {player_id}: {e}")
        return jsonify({'success': False, 'message': 'Error loading player stats'})

@app.route('/credit_transaction_history/<int:player_id>')
def credit_transaction_history(player_id):
    """Display credit transaction history for a player"""
    current_player_id = session.get('current_player_id')
    
    # Verify the player can view this history (must be their own or admin)
    if current_player_id != player_id:
        conn = get_db_connection()
        current_player = conn.execute('SELECT is_admin FROM players WHERE id = ?', (current_player_id,)).fetchone()
        if not current_player or not current_player['is_admin']:
            flash('You can only view your own credit history', 'danger')
            return redirect(url_for('dashboard', player_id=current_player_id))
        conn.close()
    
    conn = get_db_connection()
    
    # Get player information
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    if not player:
        flash('Player not found', 'danger')
        return redirect(url_for('index'))
    
    # Get all credit transactions for this player
    transactions = conn.execute('''
        SELECT ct.*, a.full_name as admin_name
        FROM credit_transactions ct
        LEFT JOIN players a ON ct.admin_id = a.id
        WHERE ct.player_id = ?
        ORDER BY ct.created_at DESC
    ''', (player_id,)).fetchall()
    
    conn.close()
    
    return render_template('credit_history.html', player=player, transactions=transactions)

@app.route('/quick_join_tournament/<int:player_id>')
@require_permission('can_join_tournaments')
def quick_join_tournament(player_id):
    """Quick tournament join - show format selection page first - requires premium membership"""
    level = request.args.get('level')
    
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    
    if not player:
        flash('Player not found', 'danger')
        conn.close()
        return redirect(url_for('index'))
    
    # Check if player has accepted tournament rules
    if not player['tournament_rules_accepted']:
        flash('Please read and accept the tournament rules before entering tournaments', 'warning')
        conn.close()
        return redirect(url_for('show_tournament_rules', player_id=player_id))
    
    try:
        # Get available tournament instance for the specified level
        if level:
            tournament_instance = conn.execute('''
                SELECT * FROM tournament_instances 
                WHERE status = 'open' AND skill_level = ? AND current_players < max_players
                ORDER BY created_at ASC
                LIMIT 1
            ''', (level,)).fetchone()
        else:
            # Get any available tournament matching player skill level
            tournament_instance = conn.execute('''
                SELECT * FROM tournament_instances 
                WHERE status = 'open' AND skill_level = ? AND current_players < max_players
                ORDER BY created_at ASC
                LIMIT 1
            ''', (player['skill_level'],)).fetchone()
        
        if not tournament_instance:
            flash(f'No available tournaments found for {level or player["skill_level"]} level', 'warning')
            conn.close()
            return redirect(url_for('tournaments_overview'))
        
        # Get player connections (people they've played matches with)
        player_connections = conn.execute('''
            SELECT DISTINCT p.id, p.full_name, p.skill_level, p.player_id
            FROM players p
            INNER JOIN matches m ON (
                (m.player1_id = ? AND m.player2_id = p.id) OR
                (m.player2_id = ? AND m.player1_id = p.id)
            )
            WHERE p.id != ?
            ORDER BY p.full_name
            LIMIT 20
        ''', (player_id, player_id, player_id)).fetchall()
        
        conn.close()
        return render_template('tournament_format_selection.html', 
                             tournament_instance=tournament_instance, 
                             player=player,
                             player_connections=player_connections)
        
    except Exception as e:
        conn.close()
        flash(f'Error loading tournament: {str(e)}', 'danger')
        return redirect(url_for('tournaments_overview'))

@app.route('/process_format_selection', methods=['POST'])
def process_format_selection():
    """Process tournament format selection and proceed to payment"""
    tournament_instance_id = request.form.get('tournament_instance_id')
    player_id = request.form.get('player_id')
    tournament_format = request.form.get('tournament_format', 'singles')
    partner_id = request.form.get('partner_id') if tournament_format == 'doubles' else None
    
    conn = get_db_connection()
    
    try:
        player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
        tournament_instance = conn.execute('SELECT * FROM tournament_instances WHERE id = ?', (tournament_instance_id,)).fetchone()
        
        if not player or not tournament_instance:
            flash('Invalid player or tournament', 'danger')
            conn.close()
            return redirect(url_for('tournaments_overview'))
        
        # Validate partner selection for doubles
        if tournament_format == 'doubles':
            if not partner_id:
                flash('Please select a partner for doubles play.', 'danger')
                conn.close()
                return redirect(url_for('quick_join_tournament', player_id=player_id))
            
            # Verify partner exists and has played with this player
            partner = conn.execute('SELECT * FROM players WHERE id = ?', (partner_id,)).fetchone()
            if not partner:
                flash('Selected partner not found.', 'danger')
                conn.close()
                return redirect(url_for('quick_join_tournament', player_id=player_id))
            
            # Check if they've played together
            connection = conn.execute('''
                SELECT 1 FROM matches 
                WHERE (player1_id = ? AND player2_id = ?) 
                   OR (player1_id = ? AND player2_id = ?)
                LIMIT 1
            ''', (player_id, partner_id, partner_id, player_id)).fetchone()
            
            if not connection:
                flash('You can only invite players you have played with before.', 'danger')
                conn.close()
                return redirect(url_for('quick_join_tournament', player_id=player_id))
        
        # Calculate entry fee (NO EXTRA FEE FOR DOUBLES!)
        base_fee = tournament_instance['entry_fee']
        entry_fee = base_fee  # Same price for singles and doubles
        
        # Check for free Ambassador entries (5 total)
        free_entry_used = False
        is_the_hill = 'The Hill' in (tournament_instance['name'] or '') or 'Big Dink' in (tournament_instance['name'] or '')
        
        # Ambassador gets 5 free entries (excluding The Hill/Big Dink championships)
        if player['free_tournament_entries'] and player['free_tournament_entries'] > 0 and not is_the_hill:
            entry_fee = 0  # FREE for both singles and doubles with Ambassador benefits
            free_entry_used = True
        
        # Store tournament joining data in session
        session['quick_join_data'] = {
            'player_id': int(player_id),
            'tournament_instance_id': int(tournament_instance_id),
            'tournament_type': tournament_format,
            'entry_fee': entry_fee,
            'free_entry_used': free_entry_used,
            'partner_id': int(partner_id) if partner_id else None
        }
        
        # Store player ID in session
        session['player_id'] = int(player_id)
        
        conn.close()
        return redirect(url_for('quick_tournament_payment', player_id=player_id))
        
    except Exception as e:
        conn.close()
        flash(f'Error processing tournament selection: {str(e)}', 'danger')
        return redirect(url_for('tournaments_overview'))

@app.route('/quick_tournament_payment/<int:player_id>')
def quick_tournament_payment(player_id):
    """Quick payment page for tournament entry"""
    quick_join_data = session.get('quick_join_data')
    
    if not quick_join_data or quick_join_data['player_id'] != player_id:
        flash('Tournament selection expired. Please try again.', 'warning')
        return redirect(url_for('tournaments_overview'))
    
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    tournament_instance = conn.execute('SELECT * FROM tournament_instances WHERE id = ?', (quick_join_data['tournament_instance_id'],)).fetchone()
    
    if not player or not tournament_instance:
        flash('Invalid tournament or player', 'danger')
        conn.close()
        return redirect(url_for('tournaments_overview'))
    
    conn.close()
    
    return render_template('quick_tournament_payment.html', 
                         player=player, 
                         tournament_instance=tournament_instance,
                         quick_join_data=quick_join_data)

@app.route('/process_quick_tournament_payment', methods=['POST'])
def process_quick_tournament_payment():
    """Process quick tournament payment"""
    quick_join_data = session.get('quick_join_data')
    payment_method = request.form.get('payment_method', 'cash')
    
    if not quick_join_data:
        flash('Tournament selection expired. Please try again.', 'warning')
        return redirect(url_for('tournaments_overview'))
    
    player_id = quick_join_data['player_id']
    conn = get_db_connection()
    
    try:
        player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
        tournament_instance = conn.execute('SELECT * FROM tournament_instances WHERE id = ?', (quick_join_data['tournament_instance_id'],)).fetchone()
        
        entry_fee = quick_join_data['entry_fee']
        credits_used = 0
        remaining_payment = entry_fee
        new_credit_balance = player['tournament_credits'] or 0
        
        # Handle credit payment
        if payment_method == 'credits' and entry_fee > 0:
            player_credits = player['tournament_credits'] or 0
            
            if player_credits <= 0:
                flash('You have no tournament credits available. Please choose cash payment.', 'danger')
                return redirect(url_for('quick_tournament_payment', player_id=player_id))
            
            credits_used = min(player_credits, entry_fee)
            remaining_payment = max(0, entry_fee - credits_used)
            
            # Update player's credit balance
            new_credit_balance = player_credits - credits_used
            conn.execute('UPDATE players SET tournament_credits = ? WHERE id = ?', (new_credit_balance, player_id))
            
            # Record credit transaction
            credit_description = f"Tournament entry payment: {tournament_instance['name']} ({quick_join_data['tournament_type']})"
            if remaining_payment > 0:
                credit_description += f" - Partial payment (${credits_used:.2f} of ${entry_fee:.2f})"
            
            conn.execute('''
                INSERT INTO credit_transactions (player_id, transaction_type, amount, description)
                VALUES (?, 'credit_used', ?, ?)
            ''', (player_id, credits_used, credit_description))
        
        # GPS Validation for Tournament Join
        user_latitude = request.form.get('user_latitude')
        user_longitude = request.form.get('user_longitude')
        
        # Convert GPS coordinates to float if provided
        try:
            if user_latitude:
                user_latitude = float(user_latitude)
            if user_longitude:
                user_longitude = float(user_longitude)
        except (ValueError, TypeError):
            user_latitude = None
            user_longitude = None
            logging.warning(f"Invalid GPS coordinates received for player {player_id}")
        
        # Perform GPS validation
        gps_validation = validate_tournament_join_gps(
            user_latitude, user_longitude, tournament_instance, player_id
        )
        
        if not gps_validation['allowed']:
            logging.warning(f"Tournament join BLOCKED for player {player_id}: {gps_validation['reason']}")
            flash(gps_validation['error_message'], 'danger')
            conn.close()
            return redirect(url_for('quick_tournament_payment', player_id=player_id))
        
        # Log successful GPS validation
        if gps_validation['distance_miles'] is not None:
            logging.info(f"GPS validation PASSED for player {player_id}: {gps_validation['distance_miles']} miles from tournament")
        
        # Process tournament entry
        entry_date = datetime.now()
        match_deadline = entry_date + timedelta(days=14)
        
        # Update free entries if used
        if quick_join_data['free_entry_used']:
            conn.execute('UPDATE players SET free_tournament_entries = free_tournament_entries - 1 WHERE id = ?', (player_id,))
        
        # Determine payment status - for doubles, inviter pays immediately, partner pays on acceptance
        partner_id = quick_join_data.get('partner_id')
        if payment_method == 'credits' and remaining_payment == 0:
            payment_status = 'completed'
        elif payment_method == 'credits' and remaining_payment > 0:
            payment_status = 'pending_payment'
        elif quick_join_data['free_entry_used'] and entry_fee == 0:
            payment_status = 'completed'  # Free Ambassador entry
        elif quick_join_data['tournament_type'] == 'doubles' and partner_id:
            payment_status = 'completed'  # Inviter pays upfront, waiting for partner acceptance
        else:
            payment_status = 'pending_payment'  # Requires actual payment processing
        
        # Insert tournament entry
        conn.execute('''
            INSERT INTO tournaments (player_id, tournament_instance_id, tournament_name, tournament_level, tournament_type, entry_fee, sport, entry_date, match_deadline, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (player_id, quick_join_data['tournament_instance_id'], tournament_instance['name'], tournament_instance['skill_level'], quick_join_data['tournament_type'], entry_fee, 'Pickleball', entry_date.strftime('%Y-%m-%d'), match_deadline.strftime('%Y-%m-%d'), payment_status))
        
        # Get the tournament entry ID for partner invitation
        tournament_entry_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Handle doubles partner invitation
        if quick_join_data['tournament_type'] == 'doubles' and partner_id:
            # Create partner invitation record
            conn.execute('''
                INSERT INTO partner_invitations 
                (tournament_entry_id, inviter_id, invitee_id, tournament_name, entry_fee, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'pending', datetime('now'))
            ''', (tournament_entry_id, player_id, partner_id, tournament_instance['name'], entry_fee))
            
            # Send notification to partner
            partner = conn.execute('SELECT * FROM players WHERE id = ?', (partner_id,)).fetchone()
            message = f"{player['full_name']} has invited you to play doubles in {tournament_instance['name']}! Entry fee: ${entry_fee}. Check your invitations to accept."
            
            # Create notification record
            conn.execute('''
                INSERT INTO notifications (player_id, type, title, message, data)
                VALUES (?, 'partner_invitation', 'Doubles Tournament Invitation', ?, ?)
            ''', (partner_id, message, str({'tournament_entry_id': tournament_entry_id, 'inviter_id': player_id})))
            
            # Send push notification
            send_push_notification(partner_id, message, "Doubles Tournament Invitation")
        
        conn.commit()
        
        # Clear session data
        session.pop('quick_join_data', None)
        
        # Show success message and redirect based on payment status
        if quick_join_data['tournament_type'] == 'doubles' and partner_id:
            # Doubles tournament with partner invitation - inviter pays upfront
            partner = conn.execute('SELECT * FROM players WHERE id = ?', (partner_id,)).fetchone()
            if quick_join_data['free_entry_used']:
                flash(f'FREE Ambassador entry used! Partner invitation sent to {partner["full_name"]}.', 'success')
            elif payment_method == 'credits' and remaining_payment == 0:
                flash(f'Tournament entry paid with ${credits_used:.2f} in credits! Partner invitation sent to {partner["full_name"]}. New credit balance: ${new_credit_balance:.2f}', 'success')
            else:
                flash(f'Tournament entry complete! Partner invitation sent to {partner["full_name"]}.', 'success')
            conn.close()
            return redirect(url_for('dashboard', player_id=player_id))
        elif payment_method == 'credits' and remaining_payment == 0:
            flash(f'Tournament entry paid with ${credits_used:.2f} in credits! New credit balance: ${new_credit_balance:.2f}', 'success')
            conn.close()
            return redirect(url_for('dashboard', player_id=player_id))
        elif payment_method == 'credits' and remaining_payment > 0:
            flash(f'${credits_used:.2f} in credits applied! You have a remaining balance of ${remaining_payment:.2f} to pay.', 'warning')
            conn.close()
            return redirect(url_for('dashboard', player_id=player_id))
        elif quick_join_data['free_entry_used'] and entry_fee == 0:
            flash('FREE Ambassador entry used! Successfully entered tournament! Good luck!', 'success')
            conn.close()
            return redirect(url_for('dashboard', player_id=player_id))
        else:
            # Payment required - redirect to actual payment processing
            flash(f'Tournament reserved! Payment of ${entry_fee:.2f} is required to complete your entry.', 'warning')
            conn.close()
            
            # Get payment type from form
            payment_type = request.form.get('payment_type', 'stripe')
            
            # Store payment info in session for Stripe checkout
            session['payment_data'] = {
                'amount': int(entry_fee * 100),  # Stripe uses cents
                'description': f'Tournament Entry: {tournament_instance["name"]} ({quick_join_data["tournament_type"]})',
                'success_url': url_for('payment_success', _external=True),
                'cancel_url': url_for('payment_cancel', _external=True),
                'tournament_instance_id': quick_join_data['tournament_instance_id'],
                'player_id': player_id,
                'payment_type': payment_type
            }
            
            # Redirect to payment page
            return redirect(url_for('payment_page'))
        
    except Exception as e:
        conn.rollback()
        conn.close()
        flash(f'Error processing tournament entry: {str(e)}', 'danger')
        return redirect(url_for('tournaments_overview'))

@app.route('/partner_invitations/<int:player_id>')
def partner_invitations(player_id):
    """View partner invitations for a player"""
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    
    if not player:
        flash('Player not found', 'danger')
        conn.close()
        return redirect(url_for('index'))
    
    # Get pending invitations for this player
    invitations = conn.execute('''
        SELECT pi.*, 
               p.full_name as inviter_name, 
               p.player_id as inviter_player_id,
               p.skill_level as inviter_skill_level
        FROM partner_invitations pi
        JOIN players p ON pi.inviter_id = p.id
        WHERE pi.invitee_id = ? AND pi.status = 'pending'
        ORDER BY pi.created_at DESC
    ''', (player_id,)).fetchall()
    
    conn.close()
    return render_template('partner_invitations.html', 
                         player=player, 
                         invitations=invitations)

@app.route('/accept_partner_invitation/<int:invitation_id>')
def accept_partner_invitation(invitation_id):
    """Accept a partner invitation with GPS validation"""
    # GPS Validation - Get coordinates from request parameters
    user_latitude = request.args.get('lat')
    user_longitude = request.args.get('lng')
    
    # Convert GPS coordinates to float if provided
    try:
        if user_latitude:
            user_latitude = float(user_latitude)
        if user_longitude:
            user_longitude = float(user_longitude)
    except (ValueError, TypeError):
        user_latitude = None
        user_longitude = None
        logging.warning(f"Invalid GPS coordinates received for partner invitation {invitation_id}")
    
    conn = get_db_connection()
    
    try:
        # Get invitation details
        invitation = conn.execute('''
            SELECT pi.*, t.tournament_instance_id, t.tournament_name, t.entry_fee
            FROM partner_invitations pi
            JOIN tournaments t ON pi.tournament_entry_id = t.id
            WHERE pi.id = ? AND pi.status = 'pending'
        ''', (invitation_id,)).fetchone()
        
        if not invitation:
            flash('Invitation not found or already processed.', 'danger')
            conn.close()
            return redirect(url_for('index'))
        
        # Get tournament instance for GPS validation
        tournament_instance = conn.execute('''
            SELECT * FROM tournament_instances 
            WHERE id = ?
        ''', (invitation['tournament_instance_id'],)).fetchone()
        
        if not tournament_instance:
            flash('Tournament not found.', 'danger')
            conn.close()
            return redirect(url_for('index'))
        
        # Perform GPS validation before accepting invitation
        gps_validation = validate_tournament_join_gps(
            user_latitude, user_longitude, tournament_instance, invitation['invitee_id']
        )
        
        if not gps_validation['allowed']:
            logging.warning(f"Partner invitation acceptance BLOCKED for player {invitation['invitee_id']}: {gps_validation['reason']}")
            flash(gps_validation['error_message'], 'danger')
            conn.close()
            return redirect(url_for('partner_invitations', player_id=invitation['invitee_id']))
        
        # Log successful GPS validation
        if gps_validation['distance_miles'] is not None:
            logging.info(f"GPS validation PASSED for partner invitation acceptance - player {invitation['invitee_id']}: {gps_validation['distance_miles']} miles from tournament")
        
        # Update invitation status
        conn.execute('''
            UPDATE partner_invitations 
            SET status = 'accepted', responded_at = datetime('now')
            WHERE id = ?
        ''', (invitation_id,))
        
        # Get player info
        invitee = conn.execute('SELECT * FROM players WHERE id = ?', (invitation['invitee_id'],)).fetchone()
        inviter = conn.execute('SELECT * FROM players WHERE id = ?', (invitation['inviter_id'],)).fetchone()
        
        # Create tournament entry for the accepting player
        entry_date = datetime.now()
        match_deadline = entry_date + timedelta(days=14)
        
        conn.execute('''
            INSERT INTO tournaments (player_id, tournament_instance_id, tournament_name, tournament_level, tournament_type, entry_fee, sport, entry_date, match_deadline, payment_status)
            VALUES (?, ?, ?, 'Intermediate', 'doubles', ?, 'Pickleball', ?, ?, 'pending_payment')
        ''', (invitation['invitee_id'], invitation['tournament_instance_id'], invitation['tournament_name'], invitation['entry_fee'], entry_date.strftime('%Y-%m-%d'), match_deadline.strftime('%Y-%m-%d')))
        
        # Original tournament entry stays completed since inviter already paid
        # No need to update the inviter's payment status
        
        # Send notification to inviter
        message = f"{invitee['full_name']} accepted your doubles invitation for {invitation['tournament_name']}! Your team is confirmed."
        
        conn.execute('''
            INSERT INTO notifications (player_id, type, title, message, data)
            VALUES (?, 'invitation_accepted', 'Partner Accepted!', ?, ?)
        ''', (invitation['inviter_id'], message, str({'invitation_id': invitation_id})))
        
        send_push_notification(invitation['inviter_id'], message, "Partner Accepted!")
        
        conn.commit()
        flash(f'Partner invitation accepted! You are now teamed up with {inviter["full_name"]} for {invitation["tournament_name"]}.', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error accepting invitation: {str(e)}', 'danger')
    
    conn.close()
    return redirect(url_for('dashboard', player_id=invitation['invitee_id']))

@app.route('/decline_partner_invitation/<int:invitation_id>')
def decline_partner_invitation(invitation_id):
    """Decline a partner invitation"""
    conn = get_db_connection()
    
    try:
        # Get invitation details
        invitation = conn.execute('''
            SELECT pi.*
            FROM partner_invitations pi
            WHERE pi.id = ? AND pi.status = 'pending'
        ''', (invitation_id,)).fetchone()
        
        if not invitation:
            flash('Invitation not found or already processed.', 'danger')
            conn.close()
            return redirect(url_for('index'))
        
        # Update invitation status
        conn.execute('''
            UPDATE partner_invitations 
            SET status = 'declined', responded_at = datetime('now')
            WHERE id = ?
        ''', (invitation_id,))
        
        # Original tournament entry stays completed since inviter already paid
        # No need to update the inviter's payment status when declined
        
        # Get player info
        invitee = conn.execute('SELECT * FROM players WHERE id = ?', (invitation['invitee_id'],)).fetchone()
        inviter = conn.execute('SELECT * FROM players WHERE id = ?', (invitation['inviter_id'],)).fetchone()
        
        # Send notification to inviter
        message = f"{invitee['full_name']} declined your doubles invitation for {invitation['tournament_name']}. You can select a different partner or continue as singles."
        
        conn.execute('''
            INSERT INTO notifications (player_id, type, title, message, data)
            VALUES (?, 'invitation_declined', 'Partner Declined', ?, ?)
        ''', (invitation['inviter_id'], message, str({'invitation_id': invitation_id})))
        
        send_push_notification(invitation['inviter_id'], message, "Partner Declined")
        
        conn.commit()
        flash(f'Partner invitation declined. {inviter["full_name"]} has been notified.', 'info')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error declining invitation: {str(e)}', 'danger')
    
    conn.close()
    return redirect(url_for('dashboard', player_id=invitation['invitee_id']))

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

# Tournament Payment Processing Routes
@app.route('/payment_page')
def payment_page():
    """Display payment page with Stripe checkout link"""
    payment_data = session.get('payment_data')
    if not payment_data:
        flash('Payment session expired. Please try again.', 'warning')
        return redirect(url_for('tournaments_overview'))
    
    # Create Stripe checkout URL
    stripe_checkout_url = url_for('create_stripe_checkout')
    
    return render_template('payment_page.html', 
                         payment_data=payment_data, 
                         stripe_checkout_url=stripe_checkout_url)

@app.route('/create_stripe_checkout')
def create_stripe_checkout():
    """Create Stripe checkout session for tournament payment"""
    import stripe
    
    payment_data = session.get('payment_data')
    if not payment_data:
        flash('Payment session expired. Please try again.', 'warning')
        return redirect(url_for('tournaments_overview'))
    
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    
    try:
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Tournament Entry',
                        'description': payment_data['description'],
                    },
                    'unit_amount': payment_data['amount'],
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=payment_data['success_url'],
            cancel_url=payment_data['cancel_url'],
            metadata={
                'player_id': payment_data['player_id'],
                'tournament_instance_id': payment_data['tournament_instance_id'],
                'payment_type': payment_data['payment_type']
            }
        )
        
        if checkout_session.url:
            return redirect(checkout_session.url, code=303)
        else:
            flash('Error creating checkout session. Please try again.', 'danger')
            return redirect(url_for('tournaments_overview'))
        
    except Exception as e:
        flash(f'Error creating payment session: {str(e)}', 'danger')
        return redirect(url_for('tournaments_overview'))

@app.route('/payment_success')
def payment_success():
    """Handle successful payment"""
    payment_data = session.get('payment_data')
    if payment_data:
        # Update tournament payment status to completed
        conn = get_db_connection()
        try:
            # Find the pending tournament entry
            tournament_entry = conn.execute('''
                SELECT * FROM tournaments 
                WHERE player_id = ? AND tournament_instance_id = ? AND payment_status = 'pending_payment'
                ORDER BY entry_date DESC LIMIT 1
            ''', (payment_data['player_id'], payment_data['tournament_instance_id'])).fetchone()
            
            if tournament_entry:
                # Update payment status to completed
                conn.execute('''
                    UPDATE tournaments SET payment_status = 'completed'
                    WHERE id = ?
                ''', (tournament_entry['id'],))
                conn.commit()
                
                flash('🎉 Payment successful! You are now entered in the tournament. Good luck!', 'success')
            else:
                flash('Tournament entry not found. Please contact support.', 'warning')
                
        except Exception as e:
            flash(f'Error updating payment status: {str(e)}', 'danger')
        finally:
            conn.close()
        
        # Clear payment session data
        session.pop('payment_data', None)
        
        return redirect(url_for('dashboard', player_id=payment_data['player_id']))
    else:
        flash('Payment session not found.', 'warning')
        return redirect(url_for('tournaments_overview'))

@app.route('/payment_cancel')
def payment_cancel():
    """Handle cancelled payment"""
    payment_data = session.get('payment_data')
    if payment_data:
        # Optionally remove the pending tournament entry or leave it for retry
        flash('Payment cancelled. Your tournament spot is still reserved. You can complete payment anytime.', 'info')
        session.pop('payment_data', None)
        return redirect(url_for('dashboard', player_id=payment_data['player_id']))
    else:
        flash('Payment session not found.', 'warning')
        return redirect(url_for('tournaments_overview'))

@app.route('/withdraw_tournament/<int:tournament_id>')
def withdraw_tournament(tournament_id):
    """Allow player to withdraw from tournament and get refund"""
    if 'player_id' not in session:
        flash('Please log in to withdraw from tournaments.', 'warning')
        return redirect(url_for('player_login'))
    
    player_id = session['player_id']
    conn = get_db_connection()
    
    try:
        # Get tournament entry details
        tournament_entry = conn.execute('''
            SELECT t.*, ti.name as tournament_name, ti.current_players, ti.max_players, ti.status
            FROM tournaments t 
            JOIN tournament_instances ti ON t.tournament_instance_id = ti.id
            WHERE t.id = ? AND t.player_id = ?
        ''', (tournament_id, player_id)).fetchone()
        
        if not tournament_entry:
            flash('Tournament entry not found or you are not registered for this tournament.', 'danger')
            conn.close()
            return redirect(url_for('dashboard', player_id=player_id))
        
        # Check if tournament is still accepting withdrawals (not full yet)
        if tournament_entry['current_players'] >= tournament_entry['max_players']:
            flash('Cannot withdraw from full tournaments. Contact support for assistance.', 'warning')
            conn.close()
            return redirect(url_for('dashboard', player_id=player_id))
        
        # Check if tournament has started
        if tournament_entry['status'] != 'open':
            flash('Cannot withdraw from tournaments that have already started.', 'warning')
            conn.close()
            return redirect(url_for('dashboard', player_id=player_id))
        
        # Process withdrawal
        if tournament_entry['payment_status'] == 'completed' and tournament_entry['entry_fee'] > 0:
            # Paid entry - process refund
            refund_amount = tournament_entry['entry_fee']
            
            # Remove tournament entry
            conn.execute('DELETE FROM tournaments WHERE id = ?', (tournament_id,))
            
            # Update tournament player count
            conn.execute('UPDATE tournament_instances SET current_players = current_players - 1 WHERE id = ?', 
                        (tournament_entry['tournament_instance_id'],))
            
            # Add refund as tournament credits (easier than Stripe refund processing)
            player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
            current_credits = player['tournament_credits'] or 0
            new_credits = current_credits + refund_amount
            
            conn.execute('UPDATE players SET tournament_credits = ? WHERE id = ?', (new_credits, player_id))
            
            # Record credit transaction
            conn.execute('''
                INSERT INTO credit_transactions (player_id, transaction_type, amount, description)
                VALUES (?, 'refund', ?, ?)
            ''', (player_id, refund_amount, f'Tournament withdrawal refund: {tournament_entry["tournament_name"]} ({tournament_entry["tournament_type"]})'))
            
            conn.commit()
            flash(f'Successfully withdrawn from {tournament_entry["tournament_name"]}! ${refund_amount:.2f} added to your tournament credits.', 'success')
            
        elif tournament_entry['payment_status'] == 'pending_payment':
            # Pending payment - just remove entry
            conn.execute('DELETE FROM tournaments WHERE id = ?', (tournament_id,))
            conn.execute('UPDATE tournament_instances SET current_players = current_players - 1 WHERE id = ?', 
                        (tournament_entry['tournament_instance_id'],))
            conn.commit()
            flash(f'Successfully withdrawn from {tournament_entry["tournament_name"]}!', 'success')
            
        else:
            # Free entry - just remove
            conn.execute('DELETE FROM tournaments WHERE id = ?', (tournament_id,))
            conn.execute('UPDATE tournament_instances SET current_players = current_players - 1 WHERE id = ?', 
                        (tournament_entry['tournament_instance_id'],))
            
            # Restore free entry if it was used
            if tournament_entry['entry_fee'] == 0:
                conn.execute('UPDATE players SET free_tournament_entries = free_tournament_entries + 1 WHERE id = ?', (player_id,))
            
            conn.commit()
            flash(f'Successfully withdrawn from {tournament_entry["tournament_name"]}!', 'success')
        
        conn.close()
        return redirect(url_for('dashboard', player_id=player_id))
        
    except Exception as e:
        conn.rollback()
        conn.close()
        flash(f'Error withdrawing from tournament: {str(e)}', 'danger')
        return redirect(url_for('dashboard', player_id=player_id))

# Stripe Subscription Routes
def create_membership_prices():
    """Create or retrieve Stripe prices for membership subscriptions"""
    import stripe
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    
    # Define membership plans - Updated pricing structure
    membership_plans = {
        'premium': {
            'name': 'Premium Membership', 
            'amount': 999,  # $9.99
            'description': 'Full access including tournaments, leaderboard, and all competitive features'
        }
    }
    
    price_ids = {}
    
    for plan_type, plan_info in membership_plans.items():
        try:
            # Try to find existing price by looking for products with matching names
            products = stripe.Product.list(limit=100)
            existing_product = None
            
            for product in products.data:
                if product.name == plan_info['name']:
                    existing_product = product
                    break
            
            if existing_product:
                # Get the price for this product
                prices = stripe.Price.list(product=existing_product.id, limit=1)
                if prices.data:
                    price_ids[plan_type] = prices.data[0].id
                    continue
            
            # Create new product and price if not found
            product = stripe.Product.create(
                name=plan_info['name'],
                description=plan_info['description']
            )
            
            price = stripe.Price.create(
                unit_amount=plan_info['amount'],
                currency='usd',
                recurring={'interval': 'month'},
                product=product.id,
                nickname=f"{plan_type}_monthly"
            )
            
            price_ids[plan_type] = price.id
            
        except Exception as e:
            # Fallback to creating new ones
            logging.error(f"Error creating/finding price for {plan_type}: {e}")
            try:
                product = stripe.Product.create(
                    name=f"{plan_info['name']} - {plan_type}",
                    description=plan_info['description']
                )
                
                price = stripe.Price.create(
                    unit_amount=plan_info['amount'],
                    currency='usd',
                    recurring={'interval': 'month'},
                    product=product.id,
                    nickname=f"{plan_type}_monthly_fallback"
                )
                
                price_ids[plan_type] = price.id
                
            except Exception as fallback_error:
                logging.error(f"Fallback price creation failed for {plan_type}: {fallback_error}")
                # Use a hardcoded fallback (this should be replaced with actual price IDs)
                price_ids[plan_type] = 'price_fallback_' + plan_type
    
    return price_ids

@app.route('/membership_payment/<membership_type>')
def membership_payment_page(membership_type):
    """Display membership payment page"""
    if 'player_id' not in session:
        flash('Please log in to access memberships.', 'warning')
        return redirect(url_for('player_login'))
    
    if membership_type not in ['premium']:
        flash('Invalid membership type.', 'warning')
        return redirect(url_for('dashboard', player_id=session['player_id']))
    
    # Check if this is a test account - bypass payment and grant membership directly
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (session['player_id'],)).fetchone()
    
    if player and player['test_account']:
        # Grant test accounts immediate access without payment
        conn.execute('''
            UPDATE players 
            SET membership_type = ?, 
                subscription_status = 'active'
            WHERE id = ?
        ''', (membership_type, session['player_id']))
        conn.commit()
        conn.close()
        
        membership_display = membership_type.replace("_", " ").title()
        flash(f'Test account granted {membership_display} membership access!', 'success')
        return redirect(url_for('player_home', player_id=session['player_id']))
        
    # TEMPORARY: Make admin user (id=1) act like test account for testing
    if player and player['id'] == 1:
        conn.execute('''
            UPDATE players 
            SET membership_type = ?, 
                subscription_status = 'active',
                test_account = 1
            WHERE id = ?
        ''', (membership_type, session['player_id']))
        conn.commit()
        conn.close()
        
        membership_display = membership_type.replace("_", " ").title()
        flash(f'Admin account granted {membership_display} membership access for testing!', 'success')
        return redirect(url_for('player_home', player_id=session['player_id']))
    
    conn.close()
    
    # Store membership data in session
    session['membership_data'] = {
        'membership_type': membership_type,
        'player_id': session['player_id']
    }
    
    # Create Stripe checkout URL
    stripe_checkout_url = url_for('create_subscription_checkout')
    
    return render_template('membership_payment_page.html', 
                         membership_type=membership_type,
                         stripe_checkout_url=stripe_checkout_url)

@app.route('/create_subscription_checkout')
def create_subscription_checkout():
    """Create Stripe subscription checkout session"""
    if 'player_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    # Check for test account and bypass payment
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (session['player_id'],)).fetchone()
    
    if player and player['test_account']:
        # Test accounts should have already been handled in membership_payment_page
        # But if they somehow get here, redirect them back to dashboard
        conn.close()
        flash('Test account access already granted!', 'info')
        return redirect(url_for('player_home', player_id=session['player_id']))
    
    conn.close()
    
    membership_data = session.get('membership_data')
    if not membership_data:
        flash('Membership session expired. Please try again.', 'warning')
        return redirect(url_for('dashboard', player_id=session['player_id']))
    
    membership_type = membership_data['membership_type']
    player_id = membership_data['player_id']
    
    if membership_type not in ['premium']:
        return jsonify({'error': 'Invalid membership type'}), 400
    
    import stripe
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    
    if not player:
        conn.close()
        flash('Player not found.', 'danger')
        return redirect(url_for('dashboard', player_id=player_id))
    
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
        
        # Create or get Stripe prices for memberships
        price_ids = create_membership_prices()
        
        # Get domain for success/cancel URLs
        domain = request.headers.get('Host', 'localhost:5000')
        protocol = 'https' if 'replit' in domain else 'http'
        
        # Create Stripe Checkout Session with free trial (removed automatic_tax)
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
        )
        
        conn.close()
        
        if checkout_session.url:
            return redirect(checkout_session.url, code=303)
        else:
            flash('Error creating subscription. Please try again.', 'danger')
            return redirect(url_for('dashboard', player_id=player_id))
        
    except Exception as e:
        conn.close()
        flash(f'Error creating subscription: {str(e)}', 'danger')
        return redirect(url_for('dashboard', player_id=player_id))

@app.route('/subscription_success')
def subscription_success():
    """Handle successful subscription"""
    import stripe
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    
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
        
        # Add player_id to session for login
        session['player_id'] = player_id
        
        # Create a celebratory success message
        success_message = f'🎉 Payment processed, let\'s play! Welcome to {membership_display} membership! Your 30-day free trial has started - enjoy full access!'
        flash(success_message, 'success')
        
        logging.info(f"Subscription successful for player {player_id}: {membership_type}")
        return redirect(url_for('player_home', player_id=player_id))
        
    except Exception as e:
        logging.error(f"Subscription processing error: {str(e)}")
        flash(f'Error processing subscription: {str(e)}. Please contact support if this continues.', 'danger')
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
        
        # Check ambassador limit for this state (10 max per state)
        state_count = conn.execute('''
            SELECT COUNT(*) as count FROM ambassadors 
            WHERE state_territory = ? AND status = 'active'
        ''', (state_territory,)).fetchone()['count']
        
        if state_count >= 10:
            flash(f'Sorry, {state_territory} already has the maximum of 10 ambassadors. Please choose a different state or territory.', 'warning')
            conn.close()
            return render_template('become_ambassador.html', error_state=state_territory)
        
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

@app.route('/referral_dashboard')
def universal_referral_dashboard():
    """Universal referral dashboard for all users"""
    if 'player_id' not in session:
        flash('Please log in to access your referral dashboard.', 'warning')
        return redirect(url_for('player_login'))
    
    player_id = session['player_id']
    conn = get_db_connection()
    
    # Get player information and referral code
    player = conn.execute('''
        SELECT id, full_name, email, referral_code, membership_type, subscription_status 
        FROM players WHERE id = ?
    ''', (player_id,)).fetchone()
    
    if not player:
        flash('Player not found.', 'danger')
        return redirect(url_for('player_login'))
    
    # Get referral statistics
    total_referrals = conn.execute('''
        SELECT COUNT(*) as count FROM universal_referrals 
        WHERE referrer_player_id = ?
    ''', (player_id,)).fetchone()['count']
    
    qualified_referrals = conn.execute('''
        SELECT COUNT(*) as count FROM universal_referrals 
        WHERE referrer_player_id = ? AND qualified = 1
    ''', (player_id,)).fetchone()['count']
    
    # Get detailed referral list
    referrals = conn.execute('''
        SELECT ur.*, p.full_name as referred_name, p.email as referred_email, 
               p.membership_type as referred_membership
        FROM universal_referrals ur
        JOIN players p ON ur.referred_player_id = p.id
        WHERE ur.referrer_player_id = ?
        ORDER BY ur.created_at DESC
    ''', (player_id,)).fetchall()
    
    # Check if 12-month reward has been granted
    reward_granted = conn.execute('''
        SELECT COUNT(*) as count FROM universal_referrals 
        WHERE referrer_player_id = ? AND reward_granted = 1
    ''', (player_id,)).fetchone()['count'] > 0
    
    # Calculate progress percentage
    progress_percentage = min((qualified_referrals / 20) * 100, 100)
    
    # Get referral link
    domain = request.headers.get('Host', 'localhost:5000')
    protocol = 'https' if 'replit' in domain else 'http'
    referral_link = f"{protocol}://{domain}/r/{player['referral_code']}"
    
    conn.close()
    
    return render_template('universal_referral_dashboard.html',
                         player=player,
                         total_referrals=total_referrals,
                         qualified_referrals=qualified_referrals,
                         referrals=referrals,
                         reward_granted=reward_granted,
                         progress_percentage=progress_percentage,
                         referral_link=referral_link)

@app.route('/r/<code>')
def intake_referral(code):
    conn = get_db_connection()
    row = conn.execute('SELECT id FROM players WHERE referral_code=?', (code,)).fetchone()
    conn.close()
    
    if not row:
        flash('Invalid referral link', 'warning')
        return redirect(url_for('register'))
    
    session['referrer_player_id'] = row['id']
    session['referral_code'] = code
    return redirect(url_for('register'))

@app.route('/referrals')
def referral_dashboard():
    pid = session.get('player_id')
    if not pid: 
        return redirect(url_for('player_login'))
    
    conn = get_db_connection()
    player = conn.execute('SELECT full_name, email, referral_code FROM players WHERE id=?', (pid,)).fetchone()
    
    # Get referral statistics
    total_referrals = conn.execute('SELECT COUNT(*) as count FROM universal_referrals WHERE referrer_player_id=?', (pid,)).fetchone()['count']
    qualified_referrals = conn.execute('SELECT COUNT(*) as count FROM universal_referrals WHERE referrer_player_id=? AND qualified=1', (pid,)).fetchone()['count']
    
    # Check if reward has been granted
    reward_granted = conn.execute('SELECT reward_granted FROM universal_referrals WHERE referrer_player_id=? AND reward_granted IS NOT NULL LIMIT 1', (pid,)).fetchone()
    reward_granted = reward_granted is not None
    
    # Get detailed referral list
    referrals = conn.execute('''
        SELECT ur.*, p.full_name, p.email, ur.qualified_at, ur.created_at
        FROM universal_referrals ur
        JOIN players p ON ur.referred_player_id = p.id
        WHERE ur.referrer_player_id = ?
        ORDER BY ur.created_at DESC
    ''', (pid,)).fetchall()
    
    conn.close()
    
    # Calculate progress percentage (out of 20 referrals needed)
    progress_percentage = min((qualified_referrals / 20) * 100, 100)
    
    # Generate referral link
    referral_link = url_for('intake_referral', code=player['referral_code'], _external=True)
    
    return render_template('universal_referral_dashboard.html',
                         player=player,
                         total_referrals=total_referrals,
                         qualified_referrals=qualified_referrals,
                         referrals=referrals,
                         reward_granted=reward_granted,
                         progress_percentage=progress_percentage,
                         referral_link=referral_link)

@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig = request.headers.get('Stripe-Signature')
    secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    if not secret:
        logging.error("STRIPE_WEBHOOK_SECRET not configured - webhook security compromised!")
        return Response(status=500)
    
    try:
        # CRITICAL SECURITY: Verify Stripe webhook signature
        event = stripe.Webhook.construct_event(payload, sig, secret)
        logging.info(f"Stripe webhook verified successfully: {event['type']}")
    except ValueError as e:
        logging.error(f"Invalid payload in Stripe webhook: {e}")
        return Response(status=400)
    except stripe.error.SignatureVerificationError as e:
        logging.error(f"Invalid signature in Stripe webhook: {e}")
        return Response(status=400)
    except Exception as e:
        logging.error(f"Unexpected error verifying Stripe webhook: {e}")
        return Response(status=400)
    
    # Process payment success events for referral conversions
    if event['type'] in ('checkout.session.completed', 'invoice.payment_succeeded'):
        customer_id = event['data']['object'].get('customer')
        if customer_id:
            conn = get_db_connection()
            row = conn.execute('SELECT id, membership_type FROM players WHERE stripe_customer_id=?', (customer_id,)).fetchone()
            conn.close()
            if row:
                logging.info(f"Processing referral conversion for player {row['id']} with membership {row['membership_type']}")
                track_referral_conversion(row['id'], row['membership_type'] or 'membership')
    
    return Response(status=200)

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

def track_referral_conversion(referred_player_id, membership_type):
    conn = get_db_connection()
    conn.execute('UPDATE universal_referrals SET qualified=1, qualified_at=CURRENT_TIMESTAMP WHERE referred_player_id=? AND qualified=0', (referred_player_id,))
    conn.commit()
    conn.close()
    check_and_grant_ambassador_reward(referrer_id_of(referred_player_id))

def check_and_grant_ambassador_reward(referrer_id):
    if not referrer_id:
        return
    
    conn = get_db_connection()
    
    # CRITICAL FIX: Check if reward already granted to prevent duplicates
    already_granted = conn.execute('''
        SELECT COUNT(*) c FROM universal_referrals 
        WHERE referrer_player_id=? AND reward_granted=1
    ''', (referrer_id,)).fetchone()['c']
    
    if already_granted > 0:
        logging.info(f"Referral reward already granted for referrer {referrer_id}")
        conn.close()
        return
    
    # Count qualified referrals
    q = conn.execute('SELECT COUNT(*) c FROM universal_referrals WHERE referrer_player_id=? AND qualified=1', (referrer_id,)).fetchone()['c']
    
    if q >= 20:
        # Grant 12-month membership reward
        row = conn.execute('SELECT subscription_end_date FROM players WHERE id=?', (referrer_id,)).fetchone()
        start = max(datetime.utcnow(), datetime.strptime(row['subscription_end_date'], '%Y-%m-%d') if row and row['subscription_end_date'] else datetime.utcnow())
        new_end = (start + timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Update player membership
        conn.execute('UPDATE players SET membership_type="tournament", subscription_status="complimentary", subscription_end_date=? WHERE id=?', (new_end, referrer_id))
        
        # Mark rewards as granted to prevent duplicates
        conn.execute('''
            UPDATE universal_referrals 
            SET reward_granted=1, reward_granted_at=CURRENT_TIMESTAMP 
            WHERE referrer_player_id=? AND qualified=1 AND reward_granted=0
        ''', (referrer_id,))
        
        conn.commit()
        conn.close()
        
        logging.info(f"Granted 12-month membership reward to referrer {referrer_id} for 20 qualified referrals")
        send_referral_reward_email(referrer_id, new_end)
    else:
        conn.close()

def referrer_id_of(referred_player_id):
    conn = get_db_connection()
    row = conn.execute('SELECT referrer_player_id FROM universal_referrals WHERE referred_player_id=?', (referred_player_id,)).fetchone()
    conn.close()
    return row['referrer_player_id'] if row else None

def send_referral_reward_email(referrer_id, end_date):
    """Send email notification for 12-month membership reward using SendGrid"""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_key:
            logging.error("SendGrid API key not found")
            return False
        
        # Get player information
        conn = get_db_connection()
        player = conn.execute('SELECT full_name, email FROM players WHERE id = ?', (referrer_id,)).fetchone()
        conn.close()
        
        if not player:
            logging.error(f"Player not found for reward email: {referrer_id}")
            return False
        
        subject = f"🎉 Referral Achievement Unlocked - 12 Months FREE! - Ready 2 Dink"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f8f9fa;">
            <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 32px;">🎉 CONGRATULATIONS! 🎉</h1>
                <p style="color: white; margin: 10px 0; font-size: 18px; font-weight: bold;">Referral Achievement Unlocked</p>
            </div>
            
            <div style="padding: 40px; background: white;">
                <h2 style="color: #28a745; text-align: center; margin-bottom: 20px;">You've Earned 12 Months FREE!</h2>
                
                <div style="background: linear-gradient(135deg, #fff3cd, #d1ecf1); padding: 25px; border-radius: 12px; margin: 25px 0; text-align: center;">
                    <h3 style="color: #155724; margin-top: 0;">🏆 Outstanding Achievement!</h3>
                    <p style="color: #155724; font-size: 18px; margin: 0;">
                        You've successfully referred <strong>20 players</strong> who joined Ready 2 Dink with paid memberships!
                    </p>
                </div>
                
                <h3 style="color: #333; border-bottom: 2px solid #28a745; padding-bottom: 10px;">Your Reward Package:</h3>
                <ul style="color: #333; font-size: 16px; line-height: 1.8;">
                    <li>✅ <strong>12 Months FREE Tournament Membership</strong></li>
                    <li>🎫 <strong>5 FREE Tournament Entries</strong></li>
                    <li>🏓 <strong>Full Access to All Features</strong></li>
                    <li>🏆 <strong>Priority Support</strong></li>
                </ul>
                
                <div style="background: #e8f5e8; border-left: 4px solid #28a745; padding: 20px; margin: 25px 0;">
                    <h4 style="color: #155724; margin-top: 0;">🚀 Your Membership is Now Active!</h4>
                    <p style="color: #155724; margin: 0;">
                        Your 12-month free tournament membership has been automatically activated until {end_date}. 
                        Log in to Ready 2 Dink to start enjoying all premium features!
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="color: #333; font-size: 16px;">Thank you for being an amazing part of the Ready 2 Dink community!</p>
                    <p style="color: #666; font-size: 14px;">Keep sharing your referral link to help grow our pickleball family!</p>
                </div>
            </div>
            
            <div style="background: #343a40; padding: 20px; text-align: center;">
                <p style="color: #adb5bd; margin: 0; font-size: 12px;">
                    Ready 2 Dink - Premium Pickleball Experience | Generated on {datetime.now().strftime('%Y-%m-%d at %I:%M %p')}
                </p>
            </div>
        </div>
        """
        
        message = Mail(
            from_email='admin@ready2dink.com',
            to_emails=player['email'],
            subject=subject,
            html_content=html_content
        )
        
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        
        if response.status_code == 202:
            logging.info(f"Referral reward email sent successfully to player {player['id']}")
            return True
        else:
            logging.error(f"Failed to send referral reward email. Status: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"Error sending referral reward email: {e}")
        return False

def track_referral_conversion(player_id, membership_type):
    """Track when a referral gets paid membership (universal system for all users)"""
    referral_code = session.get('referral_code', '')
    ambassador_id = session.get('ambassador_id', None)
    referrer_player_id = session.get('referrer_player_id', None)
    
    # Check if this is a referral (either ambassador or regular user)
    if not referral_code and not ambassador_id and not referrer_player_id:
        return
    
    # Only count paid memberships as qualified referrals (premium only)
    if membership_type not in ['premium']:
        return
    
    conn = get_db_connection()
    
    # Determine referrer information
    if ambassador_id:
        # Ambassador referral - maintain existing ambassador system
        ambassador = conn.execute('SELECT player_id FROM ambassadors WHERE id = ?', (ambassador_id,)).fetchone()
        referrer_id = ambassador['player_id'] if ambassador else None
        referrer_type = 'ambassador'
    else:
        # Regular user referral through universal system
        referrer_id = referrer_player_id
        referrer_type = 'regular'
    
    if not referrer_id:
        conn.close()
        return
    
    # Record referral in universal tracking table
    conn.execute('''
        INSERT INTO universal_referrals 
        (referrer_player_id, referred_player_id, referral_code, referrer_type, membership_type, qualified, qualified_at)
        VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
    ''', (referrer_id, player_id, referral_code, referrer_type, membership_type))
    
    # Also maintain ambassador tracking for backwards compatibility
    if ambassador_id:
        conn.execute('''
            INSERT INTO ambassador_referrals 
            (ambassador_id, referred_player_id, referral_code, membership_type, qualified, qualified_at)
            VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        ''', (ambassador_id, player_id, referral_code, membership_type))
        
        conn.execute('''
            UPDATE ambassadors 
            SET qualified_referrals = qualified_referrals + 1,
                referrals_count = referrals_count + 1
            WHERE id = ?
        ''', (ambassador_id,))
    
    # Check if referrer reached 20 qualified referrals (universal system)
    qualified_count = conn.execute('''
        SELECT COUNT(*) as count FROM universal_referrals 
        WHERE referrer_player_id = ? AND qualified = 1
    ''', (referrer_id,)).fetchone()['count']
    
    if qualified_count >= 20:
        # Check if reward already granted
        reward_granted = conn.execute('''
            SELECT COUNT(*) as count FROM universal_referrals 
            WHERE referrer_player_id = ? AND reward_granted = 1
        ''', (referrer_id,)).fetchone()['count']
        
        if reward_granted == 0:
            # Grant 12-month free tournament membership
            from datetime import datetime, timedelta
            end_date = datetime.now() + timedelta(days=365)
            
            # Handle existing Stripe subscription if user has one
            player_info = conn.execute('''
                SELECT stripe_customer_id, subscription_status, subscription_end_date 
                FROM players WHERE id = ?
            ''', (referrer_id,)).fetchone()
            
            existing_stripe_subscription_id = None
            
            if player_info and player_info['stripe_customer_id']:
                try:
                    import stripe
                    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
                    
                    # Get active subscriptions for this customer
                    subscriptions = stripe.Subscription.list(
                        customer=player_info['stripe_customer_id'],
                        status='active',
                        limit=10
                    )
                    
                    # Cancel active subscriptions (they get 12 months free instead)
                    for subscription in subscriptions.data:
                        # Store the subscription ID for potential future reference
                        existing_stripe_subscription_id = subscription.id
                        
                        # Cancel the subscription at period end (so they don't get charged again)
                        stripe.Subscription.modify(
                            subscription.id,
                            cancel_at_period_end=True,
                            metadata={
                                'cancelled_for': 'referral_reward_12month',
                                'referrer_player_id': str(referrer_id),
                                'reward_date': datetime.now().isoformat()
                            }
                        )
                        
                        logging.info(f"Cancelled Stripe subscription {subscription.id} for player {referrer_id} due to referral reward")
                        
                except Exception as e:
                    logging.error(f"Error handling Stripe subscription for referral reward (player {referrer_id}): {e}")
                    # Continue with the reward even if Stripe handling fails
            
            conn.execute('''
                UPDATE players 
                SET membership_type = 'tournament', 
                    subscription_status = 'referral_reward_12month',
                    subscription_end_date = ?,
                    free_tournament_entries = free_tournament_entries + 5
                WHERE id = ?
            ''', (end_date.isoformat(), referrer_id))
            
            # Mark all referrals as reward granted
            conn.execute('''
                UPDATE universal_referrals 
                SET reward_granted = 1, reward_granted_at = CURRENT_TIMESTAMP
                WHERE referrer_player_id = ?
            ''', (referrer_id,))
            
            # Send email notification using SendGrid
            send_referral_reward_email(referrer_id, referrer_type)
            
            logging.info(f"Granted 12-month free membership to player {referrer_id} for 20 referrals")
    
    conn.commit()
    conn.close()
    
    # Clear session referral data
    session.pop('ambassador_id', None)
    session.pop('referral_code', None)
    session.pop('referrer_player_id', None)

@app.route('/admin/create-bulk-test-accounts', methods=['POST'])
@admin_required
def create_bulk_test_accounts():
    """Create multiple test accounts for testing purposes"""
    import secrets
    from datetime import datetime
    from werkzeug.security import generate_password_hash
    
    # Get the number of accounts to create
    count = int(request.form.get('count', 30))
    
    if count > 50:  # Safety limit
        flash('Cannot create more than 50 test accounts at once', 'danger')
        return redirect(url_for('admin_players'))
    
    conn = get_db_connection()
    created_accounts = []
    
    try:
        for i in range(1, count + 1):
            # Generate test user data
            username = f"testuser{i:03d}"
            email = f"testuser{i:03d}@ready2dink.test"
            full_name = f"Test User {i:03d}"
            password = "testpass123"  # Standard password for all test accounts
            
            # Check if account already exists
            existing = conn.execute('SELECT id FROM players WHERE email = ? OR username = ?', (email, username)).fetchone()
            if existing:
                continue  # Skip if already exists
                
            # Hash password  
            password_hash = generate_password_hash(password)
            
            # Create test account with premium benefits
            conn.execute('''
                INSERT INTO players (
                    full_name, email, username, password_hash, skill_level, 
                    location1, location2, dob, address, zip_code,
                    membership_type, subscription_status, tournament_credits,
                    free_tournament_entries, disclaimers_accepted, tournament_rules_accepted,
                    test_account, is_looking_for_match, ranking_points, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                full_name, email, username, password_hash, 
                ['Beginner', 'Intermediate', 'Advanced'][i % 3],  # Rotate skill levels
                f"Test City {i % 10}", f"Test State {i % 5}", '1990-01-01', 
                f"{i} Test Street", f"1234{i % 10}",
                'tournament', 'active', 50,  # Premium membership with credits
                10, 1, 1,  # Free entries, disclaimers and rules accepted
                1, 1, 100,  # Test account, looking for match, starting points
                datetime.now().isoformat()
            ))
            
            player_id = conn.lastrowid
            created_accounts.append({
                'id': player_id,
                'username': username, 
                'email': email,
                'full_name': full_name,
                'password': password
            })
        
        conn.commit()
        flash(f'Successfully created {len(created_accounts)} test accounts with full access!', 'success')
        logging.info(f"Created {len(created_accounts)} bulk test accounts")
        
        # Display account details for the admin
        account_details = []
        for account in created_accounts[:10]:  # Show first 10 for reference
            account_details.append(f"Username: {account['username']}, Password: testpass123")
        
        if account_details:
            flash(f"Sample logins - {', '.join(account_details[:3])} (All use password: testpass123)", 'info')
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Error creating bulk test accounts: {str(e)}")
        flash(f'Error creating test accounts: {str(e)}', 'danger')
    
    conn.close()
    return redirect(url_for('admin_players'))

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

# ========== TEAM MANAGEMENT ROUTES ==========

@app.route('/teams')
def teams():
    """Teams dashboard showing user's teams, invitations, and team search"""
    if 'player_id' not in session:
        return redirect(url_for('login'))
    
    player_id = session['player_id']
    conn = get_db_connection()
    
    # Get user's current teams
    user_teams = conn.execute('''
        SELECT t.*, p1.full_name as player1_name, p2.full_name as player2_name
        FROM teams t
        JOIN players p1 ON t.player1_id = p1.id
        JOIN players p2 ON t.player2_id = p2.id
        WHERE t.player1_id = ? OR t.player2_id = ?
        ORDER BY t.created_at DESC
    ''', (player_id, player_id)).fetchall()
    
    # Get pending invitations sent to this player
    pending_invitations = conn.execute('''
        SELECT ti.*, p.full_name as inviter_name
        FROM team_invitations ti
        JOIN players p ON ti.inviter_id = p.id
        WHERE ti.invitee_id = ? AND ti.status = 'pending'
        ORDER BY ti.created_at DESC
    ''', (player_id,)).fetchall()
    
    # Get invitations sent by this player
    sent_invitations = conn.execute('''
        SELECT ti.*, p.full_name as invitee_name
        FROM team_invitations ti
        JOIN players p ON ti.invitee_id = p.id
        WHERE ti.inviter_id = ? AND ti.status = 'pending'
        ORDER BY ti.created_at DESC
    ''', (player_id,)).fetchall()
    
    conn.close()
    
    return render_template('teams.html', 
                         user_teams=user_teams,
                         pending_invitations=pending_invitations,
                         sent_invitations=sent_invitations)

@app.route('/send_team_invitation', methods=['POST'])
def send_team_invitation():
    """Send a team invitation to another player"""
    if 'player_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})
    
    data = request.get_json()
    inviter_id = session['player_id']
    invitee_id = data.get('invitee_id')
    team_name = data.get('team_name', '').strip()
    location = data.get('location', '').strip()
    travel_radius = int(data.get('travel_radius', 10))
    
    if not invitee_id:
        return jsonify({'success': False, 'message': 'Please select a player to invite'})
    
    if inviter_id == invitee_id:
        return jsonify({'success': False, 'message': 'You cannot invite yourself'})
    
    conn = get_db_connection()
    
    # Check if players already have a team together
    existing_team = conn.execute('''
        SELECT id FROM teams 
        WHERE (player1_id = ? AND player2_id = ?) OR (player1_id = ? AND player2_id = ?)
    ''', (inviter_id, invitee_id, invitee_id, inviter_id)).fetchone()
    
    if existing_team:
        conn.close()
        return jsonify({'success': False, 'message': 'You already have a team with this player'})
    
    # Check if there's already a pending invitation between these players
    existing_invitation = conn.execute('''
        SELECT id FROM team_invitations 
        WHERE ((inviter_id = ? AND invitee_id = ?) OR (inviter_id = ? AND invitee_id = ?))
        AND status = 'pending'
    ''', (inviter_id, invitee_id, invitee_id, inviter_id)).fetchone()
    
    if existing_invitation:
        conn.close()
        return jsonify({'success': False, 'message': 'There is already a pending team invitation between you two'})
    
    # Create the invitation
    conn.execute('''
        INSERT INTO team_invitations (inviter_id, invitee_id, team_name, location, travel_radius)
        VALUES (?, ?, ?, ?, ?)
    ''', (inviter_id, invitee_id, team_name, location, travel_radius))
    
    conn.commit()
    
    # Get player names for notification
    inviter = conn.execute('SELECT full_name FROM players WHERE id = ?', (inviter_id,)).fetchone()
    invitee = conn.execute('SELECT full_name FROM players WHERE id = ?', (invitee_id,)).fetchone()
    
    conn.close()
    
    # Send notification to invitee
    if inviter and invitee:
        message = f"🤝 {inviter['full_name']} wants to form a doubles team with you!"
        send_push_notification(invitee_id, message, "Team Invitation")
    
    return jsonify({'success': True, 'message': f'Team invitation sent to {invitee["full_name"] if invitee else "player"}!'})

@app.route('/respond_team_invitation', methods=['POST'])
def respond_team_invitation():
    """Accept or decline a team invitation"""
    if 'player_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})
    
    data = request.get_json()
    invitation_id = data.get('invitation_id')
    response = data.get('response')  # 'accept' or 'decline'
    
    if response not in ['accept', 'decline']:
        return jsonify({'success': False, 'message': 'Invalid response'})
    
    conn = get_db_connection()
    
    # Get the invitation
    invitation = conn.execute('''
        SELECT * FROM team_invitations 
        WHERE id = ? AND invitee_id = ? AND status = 'pending'
    ''', (invitation_id, session['player_id'])).fetchone()
    
    if not invitation:
        conn.close()
        return jsonify({'success': False, 'message': 'Invitation not found or already processed'})
    
    if response == 'accept':
        # Create the team
        conn.execute('''
            INSERT INTO teams (player1_id, player2_id, team_name, location, travel_radius)
            VALUES (?, ?, ?, ?, ?)
        ''', (invitation['inviter_id'], invitation['invitee_id'], 
              invitation['team_name'], invitation['location'], invitation['travel_radius']))
        
        # Update invitation status
        conn.execute('''
            UPDATE team_invitations 
            SET status = 'accepted', responded_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (invitation_id,))
        
        conn.commit()
        
        # Get player names for notifications
        inviter = conn.execute('SELECT full_name FROM players WHERE id = ?', (invitation['inviter_id'],)).fetchone()
        invitee = conn.execute('SELECT full_name FROM players WHERE id = ?', (invitation['invitee_id'],)).fetchone()
        
        conn.close()
        
        # Send notification to inviter
        if inviter and invitee:
            message = f"🎉 {invitee['full_name']} accepted your team invitation! Your doubles team is now formed."
            send_push_notification(invitation['inviter_id'], message, "Team Formed")
        
        return jsonify({'success': True, 'message': 'Team invitation accepted! Your doubles team has been formed.'})
    
    else:  # decline
        # Update invitation status
        conn.execute('''
            UPDATE team_invitations 
            SET status = 'declined', responded_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (invitation_id,))
        
        conn.commit()
        
        # Get player names for notification
        inviter = conn.execute('SELECT full_name FROM players WHERE id = ?', (invitation['inviter_id'],)).fetchone()
        invitee = conn.execute('SELECT full_name FROM players WHERE id = ?', (invitation['invitee_id'],)).fetchone()
        
        conn.close()
        
        # Send notification to inviter
        if inviter and invitee:
            message = f"{invitee['full_name']} declined your team invitation."
            send_push_notification(invitation['inviter_id'], message, "Team Invitation")
        
        return jsonify({'success': True, 'message': 'Team invitation declined.'})

@app.route('/find_teams')
def find_teams():
    """Find other teams to challenge based on location and travel radius"""
    if 'player_id' not in session:
        return redirect(url_for('login'))
    
    player_id = session['player_id']
    conn = get_db_connection()
    
    # Get user's teams
    user_teams = conn.execute('''
        SELECT t.*, p1.full_name as player1_name, p2.full_name as player2_name
        FROM teams t
        JOIN players p1 ON t.player1_id = p1.id
        JOIN players p2 ON t.player2_id = p2.id
        WHERE t.player1_id = ? OR t.player2_id = ?
    ''', (player_id, player_id)).fetchall()
    
    # Get all other teams that could be challenged
    available_teams = conn.execute('''
        SELECT t.*, p1.full_name as player1_name, p2.full_name as player2_name
        FROM teams t
        JOIN players p1 ON t.player1_id = p1.id
        JOIN players p2 ON t.player2_id = p2.id
        WHERE t.player1_id != ? AND t.player2_id != ?
        ORDER BY t.ranking_points DESC, t.wins DESC
    ''', (player_id, player_id)).fetchall()
    
    conn.close()
    
    return render_template('find_teams.html', 
                         user_teams=user_teams,
                         available_teams=available_teams)

@app.route('/challenge_team', methods=['POST'])
def challenge_team():
    """Challenge another team to a doubles match"""
    if 'player_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})
    
    data = request.get_json()
    challenger_team_id = data.get('challenger_team_id')
    challenged_team_id = data.get('challenged_team_id')
    court_location = data.get('court_location', '').strip()
    scheduled_time = data.get('scheduled_time', '').strip()
    
    if not all([challenger_team_id, challenged_team_id, court_location, scheduled_time]):
        return jsonify({'success': False, 'message': 'Please fill in all fields'})
    
    player_id = session['player_id']
    conn = get_db_connection()
    
    # Verify the challenger is part of the challenging team
    challenger_team = conn.execute('''
        SELECT * FROM teams 
        WHERE id = ? AND (player1_id = ? OR player2_id = ?)
    ''', (challenger_team_id, player_id, player_id)).fetchone()
    
    if not challenger_team:
        conn.close()
        return jsonify({'success': False, 'message': 'You are not part of this team'})
    
    # Create the team match
    conn.execute('''
        INSERT INTO team_matches (team1_id, team2_id, court_location, scheduled_time)
        VALUES (?, ?, ?, ?)
    ''', (challenger_team_id, challenged_team_id, court_location, scheduled_time))
    
    conn.commit()
    
    # Get team names for notifications
    challenged_team = conn.execute('''
        SELECT t.*, p1.full_name as player1_name, p2.full_name as player2_name
        FROM teams t
        JOIN players p1 ON t.player1_id = p1.id
        JOIN players p2 ON t.player2_id = p2.id
        WHERE t.id = ?
    ''', (challenged_team_id,)).fetchone()
    
    conn.close()
    
    # Send notifications to challenged team members
    if challenged_team:
        team_name = challenged_team['team_name'] or f"{challenged_team['player1_name']} & {challenged_team['player2_name']}"
        challenge_message = f"🎾 Team challenge! Another doubles team wants to play you at {court_location} on {scheduled_time}"
        
        send_push_notification(challenged_team['player1_id'], challenge_message, "Team Challenge")
        send_push_notification(challenged_team['player2_id'], challenge_message, "Team Challenge")
    
    return jsonify({'success': True, 'message': 'Team challenge sent successfully!'})

@app.route('/api/available_players')
def api_available_players():
    """Get list of players available for team invitations"""
    if 'player_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})
    
    player_id = session['player_id']
    conn = get_db_connection()
    
    # Get all players except current user and those already on teams with current user
    players = conn.execute('''
        SELECT DISTINCT p.id, p.full_name, p.location1
        FROM players p
        WHERE p.id != ? 
        AND p.id NOT IN (
            SELECT CASE 
                WHEN t.player1_id = ? THEN t.player2_id 
                ELSE t.player1_id 
            END
            FROM teams t 
            WHERE t.player1_id = ? OR t.player2_id = ?
        )
        AND p.id NOT IN (
            SELECT CASE 
                WHEN ti.inviter_id = ? THEN ti.invitee_id 
                ELSE ti.inviter_id 
            END
            FROM team_invitations ti 
            WHERE (ti.inviter_id = ? OR ti.invitee_id = ?) 
            AND ti.status = 'pending'
        )
        ORDER BY p.full_name
    ''', (player_id, player_id, player_id, player_id, player_id, player_id, player_id)).fetchall()
    
    conn.close()
    
    players_list = [{'id': p['id'], 'full_name': p['full_name'], 'location1': p['location1']} for p in players]
    
    return jsonify({'success': True, 'players': players_list})

@app.route('/submit_team_match_result', methods=['POST'])
def submit_team_match_result():
    """Submit result for a team doubles match"""
    if 'player_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})
    
    data = request.get_json()
    match_id = data.get('match_id')
    match_score = data.get('match_score')  # Format: "11-5 6-11 11-9"
    team1_sets_won = int(data.get('team1_sets_won', 0))
    team2_sets_won = int(data.get('team2_sets_won', 0))
    
    player_id = session['player_id']
    conn = get_db_connection()
    
    # Get the match and verify player is part of one of the teams
    match = conn.execute('''
        SELECT tm.*, 
               t1.player1_id as team1_player1, t1.player2_id as team1_player2,
               t2.player1_id as team2_player1, t2.player2_id as team2_player2
        FROM team_matches tm
        JOIN teams t1 ON tm.team1_id = t1.id
        JOIN teams t2 ON tm.team2_id = t2.id
        WHERE tm.id = ? AND tm.status = 'confirmed'
    ''', (match_id,)).fetchone()
    
    if not match:
        conn.close()
        return jsonify({'success': False, 'message': 'Match not found or not confirmed'})
    
    # Verify player is part of one of the teams
    if player_id not in [match['team1_player1'], match['team1_player2'], 
                        match['team2_player1'], match['team2_player2']]:
        conn.close()
        return jsonify({'success': False, 'message': 'You are not part of this match'})
    
    # Determine winner team
    winner_team_id = match['team1_id'] if team1_sets_won > team2_sets_won else match['team2_id']
    loser_team_id = match['team2_id'] if team1_sets_won > team2_sets_won else match['team1_id']
    
    # Update match with results
    conn.execute('''
        UPDATE team_matches 
        SET team1_score = ?, team2_score = ?, winner_team_id = ?, 
            status = 'completed', match_result = ?
        WHERE id = ?
    ''', (team1_sets_won, team2_sets_won, winner_team_id, match_score, match_id))
    
    # Update team win/loss records and ranking points
    points_awarded = 15 if (team1_sets_won + team2_sets_won) == 3 else 10  # Bonus for 3-set matches
    
    # Update winner team
    conn.execute('''
        UPDATE teams 
        SET wins = wins + 1, ranking_points = ranking_points + ?
        WHERE id = ?
    ''', (points_awarded, winner_team_id))
    
    # Update loser team  
    conn.execute('''
        UPDATE teams 
        SET losses = losses + 1
        WHERE id = ?
    ''', (loser_team_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True, 
        'message': f'Team match result submitted successfully! Final score: {match_score}'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

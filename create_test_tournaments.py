#!/usr/bin/env python3
"""
Quick script to create test tournament instances with GPS coordinates
for testing location-based filtering functionality.
"""

import sqlite3
from datetime import datetime, timedelta

def create_test_tournaments():
    """Create test tournament instances with GPS coordinates in different cities"""
    
    try:
        # Connect to the app database
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Test tournament data with GPS coordinates from different cities
        test_tournaments = [
            {
                'name': 'Manhattan Open',
                'skill_level': 'Intermediate',
                'entry_fee': 25.0,
                'max_players': 32,
                'current_players': 8,
                'status': 'open',
                'latitude': 40.7831, # Central Park, NYC
                'longitude': -73.9712,
                'join_radius_miles': 15,
                'start_date': (datetime.now() + timedelta(days=7)).isoformat(),
                'end_date': (datetime.now() + timedelta(days=8)).isoformat()
            },
            {
                'name': 'Golden Gate Tournament',
                'skill_level': 'Advanced',
                'entry_fee': 30.0,
                'max_players': 16,
                'current_players': 4,
                'status': 'open',
                'latitude': 37.7749, # San Francisco, CA
                'longitude': -122.4194,
                'join_radius_miles': 25,
                'start_date': (datetime.now() + timedelta(days=10)).isoformat(),
                'end_date': (datetime.now() + timedelta(days=11)).isoformat()
            },
            {
                'name': 'Windy City Championship',
                'skill_level': 'Beginner',
                'entry_fee': 20.0,
                'max_players': 24,
                'current_players': 12,
                'status': 'open',
                'latitude': 41.8781, # Chicago, IL
                'longitude': -87.6298,
                'join_radius_miles': 20,
                'start_date': (datetime.now() + timedelta(days=5)).isoformat(),
                'end_date': (datetime.now() + timedelta(days=6)).isoformat()
            },
            {
                'name': 'Brooklyn Pickleball Classic',
                'skill_level': 'Advanced',
                'entry_fee': 35.0,
                'max_players': 20,
                'current_players': 6,
                'status': 'open',
                'latitude': 40.6782, # Brooklyn, NY
                'longitude': -73.9442,
                'join_radius_miles': 10,
                'start_date': (datetime.now() + timedelta(days=14)).isoformat(),
                'end_date': (datetime.now() + timedelta(days=15)).isoformat()
            },
            {
                'name': 'Miami Beach Open',
                'skill_level': 'Intermediate',
                'entry_fee': 28.0,
                'max_players': 28,
                'current_players': 3,
                'status': 'open',
                'latitude': 25.7617, # Miami Beach, FL
                'longitude': -80.1918,
                'join_radius_miles': 30,
                'start_date': (datetime.now() + timedelta(days=12)).isoformat(),
                'end_date': (datetime.now() + timedelta(days=13)).isoformat()
            }
        ]
        
        # Insert test tournaments
        for tournament in test_tournaments:
            cursor.execute('''
                INSERT INTO tournament_instances 
                (name, skill_level, entry_fee, max_players, current_players, status, 
                 latitude, longitude, join_radius_miles, start_date, end_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tournament['name'],
                tournament['skill_level'],
                tournament['entry_fee'],
                tournament['max_players'],
                tournament['current_players'],
                tournament['status'],
                tournament['latitude'],
                tournament['longitude'],
                tournament['join_radius_miles'],
                tournament['start_date'],
                tournament['end_date'],
                datetime.now().isoformat()
            ))
        
        conn.commit()
        print(f"✅ Successfully created {len(test_tournaments)} test tournaments with GPS coordinates!")
        
        # Display the created tournaments
        cursor.execute('''
            SELECT name, latitude, longitude, join_radius_miles, current_players, max_players
            FROM tournament_instances 
            WHERE name IN ('Manhattan Open', 'Golden Gate Tournament', 'Windy City Championship', 
                          'Brooklyn Pickleball Classic', 'Miami Beach Open')
        ''')
        
        tournaments = cursor.fetchall()
        print("\n📍 Test Tournaments Created:")
        print("-" * 80)
        for t in tournaments:
            print(f"🏆 {t[0]:<25} | GPS: ({t[1]:.4f}, {t[2]:.4f}) | Radius: {t[3]}mi | Players: {t[4]}/{t[5]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating test tournaments: {e}")
        return False

if __name__ == "__main__":
    success = create_test_tournaments()
    if success:
        print("\n🎯 You can now test location-based filtering by:")
        print("1. Visit the tournaments page in your browser")
        print("2. Allow GPS location access when prompted")
        print("3. Check if tournaments are filtered by your location")
        print("4. Test with different simulated GPS coordinates")
    else:
        print("\n❌ Failed to create test tournaments. Check the database connection.")
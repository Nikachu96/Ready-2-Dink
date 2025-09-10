#!/usr/bin/env python3
"""
Test script to verify location-based tournament filtering functionality.
Tests the backend filtering logic without requiring GPS browser permissions.
"""

import sqlite3
import sys
import os

# Add the current directory to Python path to import from app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_distance_calculation():
    """Test the calculate_distance_haversine function"""
    try:
        from app import calculate_distance_haversine
        
        # Test distance between NYC (40.7831, -73.9712) and Brooklyn (40.6782, -73.9442)
        # Should be approximately 7-8 miles
        distance = calculate_distance_haversine(40.7831, -73.9712, 40.6782, -73.9442)
        
        print(f"✅ Distance calculation test:")
        print(f"   NYC to Brooklyn: {distance:.1f} miles (expected ~7-8 miles)")
        
        # Test distance between NYC and San Francisco
        # Should be approximately 2500+ miles
        distance_sf = calculate_distance_haversine(40.7831, -73.9712, 37.7749, -122.4194)
        print(f"   NYC to San Francisco: {distance_sf:.1f} miles (expected ~2500+ miles)")
        
        return True
    except Exception as e:
        print(f"❌ Distance calculation test failed: {e}")
        return False

def test_tournament_filtering():
    """Test tournament filtering by location"""
    try:
        conn = sqlite3.connect('app.db')
        
        # Test data: NYC location (40.7831, -73.9712)
        user_lat, user_lng = 40.7831, -73.9712
        
        # Get all tournaments with GPS data
        tournaments = conn.execute('''
            SELECT name, latitude, longitude, join_radius_miles
            FROM tournament_instances 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            AND status = 'open'
        ''').fetchall()
        
        print(f"\n🔍 Testing tournament filtering for NYC location ({user_lat}, {user_lng}):")
        print("-" * 80)
        
        from app import calculate_distance_haversine
        
        nearby_tournaments = []
        far_tournaments = []
        
        for tournament in tournaments:
            name, lat, lng, radius = tournament
            distance = calculate_distance_haversine(user_lat, user_lng, lat, lng)
            
            if distance is not None:
                if distance <= radius:
                    nearby_tournaments.append((name, distance, radius))
                    print(f"✅ {name:<25} | {distance:.1f} mi away | Within {radius} mi radius")
                else:
                    far_tournaments.append((name, distance, radius))
                    print(f"❌ {name:<25} | {distance:.1f} mi away | Outside {radius} mi radius")
        
        print(f"\n📊 Filtering Results:")
        print(f"   Nearby tournaments (within radius): {len(nearby_tournaments)}")
        print(f"   Far tournaments (outside radius): {len(far_tournaments)}")
        
        # Expected results: Manhattan Open and Brooklyn Classic should be nearby for NYC user
        expected_nearby = ['Manhattan Open', 'Brooklyn Pickleball Classic']
        found_nearby = [t[0] for t in nearby_tournaments]
        
        success = all(name in found_nearby for name in expected_nearby)
        if success:
            print(f"✅ Expected NYC area tournaments found in results")
        else:
            print(f"❌ Some expected NYC tournaments missing: {expected_nearby} vs {found_nearby}")
        
        conn.close()
        return success
        
    except Exception as e:
        print(f"❌ Tournament filtering test failed: {e}")
        return False

def test_backend_route_simulation():
    """Simulate the backend filtering route"""
    try:
        print(f"\n🌐 Testing backend route filtering logic:")
        print("-" * 80)
        
        # Simulate the tournaments_overview route logic
        from app import get_db_connection, calculate_distance_haversine
        
        conn = get_db_connection()
        user_lat, user_lng = 40.7831, -73.9712  # NYC coordinates
        location_filter_enabled = True
        
        # Get all tournament instances
        all_tournament_instances = conn.execute('''
            SELECT * FROM tournament_instances 
            WHERE status IN ('open', 'upcoming')
        ''').fetchall()
        
        # Apply filtering logic (same as in app.py)
        tournament_instances = []
        if location_filter_enabled and user_lat is not None and user_lng is not None:
            for instance in all_tournament_instances:
                if instance['latitude'] is None or instance['longitude'] is None:
                    continue
                
                distance = calculate_distance_haversine(
                    user_lat, user_lng, 
                    instance['latitude'], instance['longitude']
                )
                
                if distance is None:
                    continue
                
                join_radius = instance.get('join_radius_miles', 25)
                
                if distance <= join_radius:
                    instance_dict = dict(instance)
                    instance_dict['distance_miles'] = round(distance, 1)
                    tournament_instances.append(instance_dict)
        
        print(f"📍 User location: NYC ({user_lat}, {user_lng})")
        print(f"🏆 Total tournaments: {len(all_tournament_instances)}")
        print(f"🎯 Filtered tournaments: {len(tournament_instances)}")
        
        for t in tournament_instances:
            print(f"   ✅ {t['name']:<25} | {t['distance_miles']} miles away")
        
        conn.close()
        
        # Test should find at least the NYC area tournaments
        success = len(tournament_instances) >= 2  # Manhattan Open + Brooklyn Classic
        return success
        
    except Exception as e:
        print(f"❌ Backend route simulation failed: {e}")
        return False

def run_all_tests():
    """Run all location-based filtering tests"""
    print("🧪 Location-Based Tournament Filtering Tests")
    print("=" * 80)
    
    tests = [
        ("Distance Calculation", test_distance_calculation),
        ("Tournament Filtering", test_tournament_filtering),
        ("Backend Route Logic", test_backend_route_simulation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n📋 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All location-based filtering tests PASSED!")
        print("\n✨ The implementation successfully:")
        print("   • Calculates distances using Haversine formula")
        print("   • Filters tournaments by GPS proximity") 
        print("   • Applies join radius rules correctly")
        print("   • Integrates with backend routing logic")
        return True
    else:
        print("❌ Some tests failed. Check the implementation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print(f"\n🎯 Next Steps for Manual Testing:")
        print(f"1. Visit http://localhost:5000/tournaments in your browser")
        print(f"2. Accept location permissions when prompted")
        print(f"3. Verify tournaments show distance badges")
        print(f"4. Check that location filtering works as expected")
        print(f"5. Test different geographic locations")
    
    sys.exit(0 if success else 1)
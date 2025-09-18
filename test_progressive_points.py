#!/usr/bin/env python3
"""
Test script for progressive tournament point system
"""

import sqlite3
import sys
import math
from datetime import datetime

def get_db_connection():
    """Get database connection with dict cursor"""
    conn = sqlite3.connect('app.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

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
    print(f"Round {round_number}/{total_rounds} ({stage}): {points} points")
    return points

def create_test_tournament():
    """Create a test tournament with 8 players"""
    conn = get_db_connection()
    
    # Create a test tournament instance
    cursor = conn.execute('''
        INSERT INTO tournament_instances (name, skill_level, entry_fee, max_players, status)
        VALUES ('Progressive Points Test Tournament', 'Intermediate', 25, 8, 'active')
    ''')
    tournament_instance_id = cursor.lastrowid
    
    # Create 8 test players
    test_players = []
    for i in range(1, 9):
        cursor = conn.execute('''
            INSERT INTO players (full_name, email, skill_level, ranking_points, address, dob, location1)
            VALUES (?, ?, 'Intermediate', 0, ?, ?, ?)
        ''', (f'Test Player {i}', f'testplayer{i}@test.com', f'123 Test St {i}', '1990-01-01', 'Test Location'))
        test_players.append(cursor.lastrowid)
    
    # Register players in tournament
    for player_id in test_players:
        conn.execute('''
            INSERT INTO tournaments (player_id, tournament_instance_id, tournament_level, tournament_name, completed, entry_date, match_deadline)
            VALUES (?, ?, 'Intermediate', 'Progressive Points Test Tournament', 0, datetime('now'), datetime('now', '+7 days'))
        ''', (player_id, tournament_instance_id))
    
    # Generate tournament bracket (3 rounds for 8 players)
    # Round 1: 4 matches (8 players -> 4 winners)
    # Round 2: 2 matches (4 players -> 2 winners) - Semi-finals
    # Round 3: 1 match (2 players -> 1 winner) - Final
    
    total_rounds = math.ceil(math.log2(len(test_players)))
    print(f"Creating tournament with {len(test_players)} players requiring {total_rounds} rounds")
    
    # Create Round 1 matches (4 matches)
    round1_matches = []
    for i in range(0, len(test_players), 2):
        cursor = conn.execute('''
            INSERT INTO tournament_matches 
            (tournament_instance_id, round_number, match_number, player1_id, player2_id, status)
            VALUES (?, 1, ?, ?, ?, 'pending')
        ''', (tournament_instance_id, (i // 2) + 1, test_players[i], test_players[i + 1]))
        round1_matches.append(cursor.lastrowid)
    
    # Create Round 2 matches (2 matches) - Semi-finals
    round2_matches = []
    for i in range(2):
        cursor = conn.execute('''
            INSERT INTO tournament_matches 
            (tournament_instance_id, round_number, match_number, status)
            VALUES (?, 2, ?, 'pending')
        ''', (tournament_instance_id, i + 1))
        round2_matches.append(cursor.lastrowid)
    
    # Create Round 3 match (1 match) - Final
    cursor = conn.execute('''
        INSERT INTO tournament_matches 
        (tournament_instance_id, round_number, match_number, status)
        VALUES (?, 3, 1, 'pending')
    ''', (tournament_instance_id,))
    final_match_id = cursor.lastrowid
    
    conn.commit()
    
    print(f"Created tournament instance {tournament_instance_id}")
    print(f"Test players: {test_players}")
    print(f"Round 1 matches: {round1_matches}")
    print(f"Round 2 matches: {round2_matches}")
    print(f"Final match: {final_match_id}")
    
    return {
        'tournament_instance_id': tournament_instance_id,
        'players': test_players,
        'total_rounds': total_rounds,
        'round1_matches': round1_matches,
        'round2_matches': round2_matches,
        'final_match': final_match_id
    }

def simulate_tournament_match(match_id, winner_player_id):
    """Simulate completing a tournament match"""
    conn = get_db_connection()
    
    # Get match details
    match = conn.execute('''
        SELECT tm.*, ti.name as tournament_name
        FROM tournament_matches tm
        JOIN tournament_instances ti ON tm.tournament_instance_id = ti.id
        WHERE tm.id = ?
    ''', (match_id,)).fetchone()
    
    if not match:
        print(f"Match {match_id} not found")
        return
    
    player1_id, player2_id = match['player1_id'], match['player2_id']
    
    # Determine scores based on winner
    if winner_player_id == player1_id:
        player1_sets_won, player2_sets_won = 2, 1
        match_score = "11-9 6-11 11-7"
        loser_id = player2_id
    else:
        player1_sets_won, player2_sets_won = 1, 2
        match_score = "11-9 6-11 7-11"
        loser_id = player1_id
    
    # Get total rounds for this tournament
    max_round = conn.execute('''
        SELECT MAX(round_number) as max_round
        FROM tournament_matches 
        WHERE tournament_instance_id = ?
    ''', (match['tournament_instance_id'],)).fetchone()
    
    total_rounds = max_round['max_round'] if max_round else 1
    
    # Get player names for display
    winner_name = conn.execute('SELECT full_name FROM players WHERE id = ?', (winner_player_id,)).fetchone()['full_name']
    loser_name = conn.execute('SELECT full_name FROM players WHERE id = ?', (loser_id,)).fetchone()['full_name']
    
    print(f"\n--- Completing Match {match_id} ---")
    print(f"{winner_name} beats {loser_name} ({match_score})")
    
    # Update tournament match with results
    conn.execute('''
        UPDATE tournament_matches 
        SET player1_score = ?, player2_score = ?, winner_id = ?, 
            status = 'completed', completed_date = datetime('now')
        WHERE id = ?
    ''', (f"{player1_sets_won} sets", f"{player2_sets_won} sets", winner_player_id, match_id))
    
    # Update player win/loss records
    conn.execute('UPDATE players SET wins = wins + 1 WHERE id = ?', (winner_player_id,))
    conn.execute('UPDATE players SET losses = losses + 1 WHERE id = ?', (loser_id,))
    
    # Award progressive tournament points for this round win
    points_awarded = get_progressive_tournament_points(match['round_number'], total_rounds, include_first_round=False)
    
    if points_awarded > 0:
        round_name = get_tournament_round_name(match['round_number'], total_rounds)
        conn.execute('''
            UPDATE players 
            SET ranking_points = ranking_points + ?
            WHERE id = ?
        ''', (points_awarded, winner_player_id))
        print(f"Awarded {points_awarded} points to {winner_name} for {round_name} win")
    else:
        round_name = get_tournament_round_name(match['round_number'], total_rounds)
        print(f"No points awarded for {round_name} win (first round)")
    
    # Advance winner to next round if not final
    if match['round_number'] < total_rounds:
        # Calculate next round and match position
        next_round = match['round_number'] + 1
        next_match_number = (match['match_number'] + 1) // 2
        
        # Find next round match
        next_match = conn.execute('''
            SELECT * FROM tournament_matches 
            WHERE tournament_instance_id = ? AND round_number = ? AND match_number = ?
        ''', (match['tournament_instance_id'], next_round, next_match_number)).fetchone()
        
        if next_match:
            # Determine if winner goes to player1 or player2 slot
            if match['match_number'] % 2 == 1:  # Odd match numbers go to player1
                conn.execute('''
                    UPDATE tournament_matches 
                    SET player1_id = ? 
                    WHERE id = ?
                ''', (winner_player_id, next_match['id']))
                print(f"Advanced {winner_name} to Round {next_round} Match {next_match_number} as Player 1")
            else:  # Even match numbers go to player2
                conn.execute('''
                    UPDATE tournament_matches 
                    SET player2_id = ? 
                    WHERE id = ?
                ''', (winner_player_id, next_match['id']))
                print(f"Advanced {winner_name} to Round {next_round} Match {next_match_number} as Player 2")
    else:
        print(f"🏆 {winner_name} wins the tournament!")
    
    conn.commit()
    conn.close()

def simulate_complete_tournament():
    """Simulate a complete tournament to test progressive points"""
    print("=== Creating Test Tournament ===")
    
    # Create test tournament
    tournament_data = create_test_tournament()
    
    print(f"\n=== Simulating Tournament Progression ===")
    print(f"Tournament will have {tournament_data['total_rounds']} rounds")
    
    # Simulate Round 1 (First round - no points awarded)
    print(f"\n--- ROUND 1 (First round) ---")
    round1_winners = []
    for i, match_id in enumerate(tournament_data['round1_matches']):
        # Let lower-numbered players win (players 1, 3, 5, 7)
        winner_idx = i * 2  # 0, 2, 4, 6 -> players 1, 3, 5, 7
        winner_player_id = tournament_data['players'][winner_idx]
        round1_winners.append(winner_player_id)
        simulate_tournament_match(match_id, winner_player_id)
    
    # Simulate Round 2 (Semi-finals - 100 points each)
    print(f"\n--- ROUND 2 (Semi-finals) ---")
    round2_winners = []
    for i, match_id in enumerate(tournament_data['round2_matches']):
        # Let first and third players from round 1 win (players 1 and 5)
        winner_player_id = round1_winners[i * 2]  # players 1 and 5
        round2_winners.append(winner_player_id)
        simulate_tournament_match(match_id, winner_player_id)
    
    # Simulate Round 3 (Final - 400 points)
    print(f"\n--- ROUND 3 (Final) ---")
    final_winner = round2_winners[0]  # Player 1 wins
    simulate_tournament_match(tournament_data['final_match'], final_winner)
    
    # Check final point totals
    print(f"\n=== Final Point Verification ===")
    conn = get_db_connection()
    
    for player_id in tournament_data['players']:
        player = conn.execute('''
            SELECT full_name, ranking_points, wins, losses
            FROM players 
            WHERE id = ?
        ''', (player_id,)).fetchone()
        
        print(f"{player['full_name']}: {player['ranking_points']} points "
              f"({player['wins']} wins, {player['losses']} losses)")
    
    # Verify champion got correct total points
    champion = conn.execute('''
        SELECT full_name, ranking_points
        FROM players 
        WHERE id = ?
    ''', (final_winner,)).fetchone()
    
    expected_champion_points = 40 + 100 + 400  # Quarter-final + Semi-final + Final = 540 points
    print(f"\n🏆 Champion: {champion['full_name']}")
    print(f"Expected points: {expected_champion_points} (Quarter-final: 40 + Semi-final: 100 + Final: 400)")
    print(f"Actual points: {champion['ranking_points']}")
    
    if champion['ranking_points'] == expected_champion_points:
        print("✅ Progressive point system working correctly!")
        print("🎯 Champion earned points for all rounds: Quarter-final (40) + Semi-final (100) + Final (400)")
    else:
        print("❌ Progressive point system has issues!")
    
    conn.close()
    
    return tournament_data['tournament_instance_id']

def cleanup_test_data(tournament_instance_id):
    """Clean up test data"""
    print(f"\n=== Cleaning up test data ===")
    conn = get_db_connection()
    
    # Get test player IDs
    test_players = conn.execute('''
        SELECT player_id FROM tournaments 
        WHERE tournament_instance_id = ?
    ''', (tournament_instance_id,)).fetchall()
    
    # Delete tournament matches
    conn.execute('DELETE FROM tournament_matches WHERE tournament_instance_id = ?', (tournament_instance_id,))
    
    # Delete tournament entries
    conn.execute('DELETE FROM tournaments WHERE tournament_instance_id = ?', (tournament_instance_id,))
    
    # Delete tournament instance
    conn.execute('DELETE FROM tournament_instances WHERE id = ?', (tournament_instance_id,))
    
    # Delete test players
    for player_row in test_players:
        player_id = player_row['player_id']
        conn.execute('DELETE FROM players WHERE id = ?', (player_id,))
    
    conn.commit()
    conn.close()
    print("Test data cleaned up")

if __name__ == "__main__":
    try:
        tournament_id = simulate_complete_tournament()
        
        # Ask user if they want to keep test data
        if len(sys.argv) > 1 and sys.argv[1] == "--keep":
            print(f"\nTest data kept. Tournament instance ID: {tournament_id}")
        else:
            cleanup_test_data(tournament_id)
            
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
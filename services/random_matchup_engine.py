#!/usr/bin/env python3
"""
Random Matchup Engine for Ready 2 Dink

Automatically creates random matchups between players based on:
- Discoverability preferences (singles/doubles/both)
- Skill level compatibility (±1 level)
- Rate limiting (1 random challenge per player per day)
- Background processing with leader election
"""

import sqlite3
import json
import random
import logging
import os
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RandomMatchupEngine:
    """Handles automatic random matchup generation between players"""
    
    def __init__(self):
        self.lock_file = "/tmp/random_matchup.lock"
        self.job_name = "random_matchup_engine"
        self.enabled = os.environ.get("RANDOM_MATCHUP_ENABLED", "1") == "1"
        
    def acquire_leader_lock(self) -> bool:
        """Acquire filesystem lock to ensure single leader"""
        try:
            # Check if lock file exists and is recent
            if os.path.exists(self.lock_file):
                stat = os.stat(self.lock_file)
                if time.time() - stat.st_mtime < 3600:  # 1 hour timeout
                    return False
                else:
                    os.remove(self.lock_file)  # Remove stale lock
            
            # Create lock file with PID
            with open(self.lock_file, 'w') as f:
                f.write(str(os.getpid()))
            
            # Update database heartbeat
            self.update_heartbeat()
            return True
            
        except Exception as e:
            logger.error(f"Failed to acquire leader lock: {e}")
            return False
    
    def update_heartbeat(self):
        """Update database heartbeat to indicate active leader"""
        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT OR REPLACE INTO system_jobs (job_name, last_run_at, owner_pid, heartbeat_at)
                VALUES (?, ?, ?, ?)
            ''', (self.job_name, datetime.now(), str(os.getpid()), datetime.now()))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to update heartbeat: {e}")
    
    def release_lock(self):
        """Release filesystem lock"""
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
        except Exception as e:
            logger.error(f"Failed to release lock: {e}")
    
    def get_eligible_players(self, match_type: str) -> List[Dict]:
        """Get players eligible for random matchups"""
        try:
            conn = get_db_connection()
            
            # Base eligibility criteria
            query = '''
                SELECT id, full_name, skill_level, discoverability_preference, 
                       current_team_id, last_random_challenge_at, wins, losses, ranking_points
                FROM players 
                WHERE is_looking_for_match = 1
                AND account_status != 'suspended'
                AND (last_random_challenge_at IS NULL OR last_random_challenge_at < ?)
                AND (discoverability_preference = ? OR discoverability_preference = 'both' OR discoverability_preference IS NULL)
            '''
            
            # 24 hours ago
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            params = [cutoff_time, match_type]
            
            # Additional filters for doubles - no locked teams
            if match_type == 'doubles':
                query += ' AND (current_team_id IS NULL OR current_team_id = "")'
            
            players = conn.execute(query, params).fetchall()
            
            # Filter out players with pending invitations
            eligible_players = []
            for player in players:
                # Check for pending outgoing invitations
                pending_out = conn.execute('''
                    SELECT COUNT(*) as count FROM team_invitations 
                    WHERE inviter_id = ? AND status = 'pending'
                ''', (player['id'],)).fetchone()
                
                # Check for pending incoming invitations
                pending_in = conn.execute('''
                    SELECT COUNT(*) as count FROM team_invitations 
                    WHERE invitee_id = ? AND status = 'pending'
                ''', (player['id'],)).fetchone()
                
                if pending_out['count'] == 0 and pending_in['count'] == 0:
                    eligible_players.append(dict(player))
            
            conn.close()
            logger.info(f"Found {len(eligible_players)} eligible players for {match_type} matchups")
            return eligible_players
            
        except Exception as e:
            logger.error(f"Error getting eligible players: {e}")
            return []
    
    def group_by_skill_level(self, players: List[Dict]) -> Dict[str, List[Dict]]:
        """Group players by skill level"""
        skill_groups = {}
        for player in players:
            skill = player['skill_level']
            if skill not in skill_groups:
                skill_groups[skill] = []
            skill_groups[skill].append(player)
        return skill_groups
    
    def create_singles_matchups(self, eligible_players: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """Create random singles matchups between players of similar skill"""
        skill_groups = self.group_by_skill_level(eligible_players)
        matchups = []
        
        skill_levels = ['Beginner', 'Intermediate', 'Advanced']
        
        for i, skill in enumerate(skill_levels):
            if skill not in skill_groups:
                continue
                
            players_pool = skill_groups[skill].copy()
            
            # Add adjacent skill levels for more variety
            if i > 0 and skill_levels[i-1] in skill_groups:
                players_pool.extend(skill_groups[skill_levels[i-1]])
            if i < len(skill_levels)-1 and skill_levels[i+1] in skill_groups:
                players_pool.extend(skill_groups[skill_levels[i+1]])
            
            # Shuffle for randomness
            random.shuffle(players_pool)
            
            # Create pairs from pool
            while len(players_pool) >= 2:
                player1 = players_pool.pop()
                player2 = players_pool.pop()
                matchups.append((player1, player2))
        
        logger.info(f"Created {len(matchups)} singles matchups")
        return matchups
    
    def create_doubles_matchups(self, eligible_players: List[Dict]) -> List[Tuple[Tuple[Dict, Dict], Tuple[Dict, Dict]]]:
        """Create random doubles matchups (team vs team)"""
        if len(eligible_players) < 4:
            return []
            
        skill_groups = self.group_by_skill_level(eligible_players)
        matchups = []
        
        # Create teams first, then match teams against each other
        teams = []
        
        for skill, players in skill_groups.items():
            players_copy = players.copy()
            random.shuffle(players_copy)
            
            # Create teams from same skill level
            while len(players_copy) >= 2:
                team = (players_copy.pop(), players_copy.pop())
                teams.append(team)
        
        # Match teams against each other
        random.shuffle(teams)
        while len(teams) >= 2:
            team1 = teams.pop()
            team2 = teams.pop()
            matchups.append((team1, team2))
        
        logger.info(f"Created {len(matchups)} doubles matchups")
        return matchups
    
    def send_singles_invitation(self, player1: Dict, player2: Dict) -> bool:
        """Send a singles match invitation"""
        try:
            conn = get_db_connection()
            
            # Randomly choose who sends the invitation
            inviter = random.choice([player1, player2])
            invitee = player2 if inviter == player1 else player1
            
            # Create invitation record
            conn.execute('''
                INSERT INTO team_invitations (inviter_id, invitee_id, invitation_message, status, source, meta_json, created_at)
                VALUES (?, ?, ?, 'pending', 'random', ?, ?)
            ''', (
                inviter['id'], 
                invitee['id'],
                "Hey! Want to play a singles match?",
                json.dumps({"type": "singles", "players": [player1['id'], player2['id']]}),
                datetime.now()
            ))
            
            # Update last random challenge time
            conn.execute('''
                UPDATE players SET last_random_challenge_at = ? WHERE id IN (?, ?)
            ''', (datetime.now(), player1['id'], player2['id']))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created singles invitation: {inviter['full_name']} -> {invitee['full_name']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending singles invitation: {e}")
            return False
    
    def send_doubles_invitation(self, team1: Tuple[Dict, Dict], team2: Tuple[Dict, Dict]) -> bool:
        """Send a doubles match invitation"""
        try:
            conn = get_db_connection()
            
            # Choose one player from team1 to send invitation to one player from team2
            inviter = random.choice(team1)
            invitee = random.choice(team2)
            
            all_player_ids = [team1[0]['id'], team1[1]['id'], team2[0]['id'], team2[1]['id']]
            
            # Create invitation record
            conn.execute('''
                INSERT INTO team_invitations (inviter_id, invitee_id, invitation_message, status, source, meta_json, created_at)
                VALUES (?, ?, ?, 'pending', 'random', ?, ?)
            ''', (
                inviter['id'], 
                invitee['id'],
                "Hey! Want to play a doubles match?",
                json.dumps({
                    "type": "doubles", 
                    "team1": [team1[0]['id'], team1[1]['id']], 
                    "team2": [team2[0]['id'], team2[1]['id']],
                    "all_players": all_player_ids
                }),
                datetime.now()
            ))
            
            # Update last random challenge time for all players
            conn.execute('''
                UPDATE players SET last_random_challenge_at = ? WHERE id IN (?, ?, ?, ?)
            ''', (datetime.now(), *all_player_ids))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created doubles invitation: {inviter['full_name']} -> {invitee['full_name']} (4 players total)")
            return True
            
        except Exception as e:
            logger.error(f"Error sending doubles invitation: {e}")
            return False
    
    def run_matchup_cycle(self):
        """Run one cycle of random matchup generation"""
        if not self.enabled:
            logger.info("Random Matchup Engine is disabled")
            return
            
        logger.info("Starting Random Matchup Engine cycle")
        
        try:
            # Get eligible players for singles and doubles
            singles_players = self.get_eligible_players('singles')
            doubles_players = self.get_eligible_players('doubles')
            
            # Create matchups
            singles_matchups = self.create_singles_matchups(singles_players)
            doubles_matchups = self.create_doubles_matchups(doubles_players)
            
            # Send invitations (limit to prevent spam)
            max_singles = min(len(singles_matchups), 5)  # Max 5 singles per cycle
            max_doubles = min(len(doubles_matchups), 3)  # Max 3 doubles per cycle
            
            singles_sent = 0
            for i, (player1, player2) in enumerate(singles_matchups[:max_singles]):
                if self.send_singles_invitation(player1, player2):
                    singles_sent += 1
            
            doubles_sent = 0
            for i, (team1, team2) in enumerate(doubles_matchups[:max_doubles]):
                if self.send_doubles_invitation(team1, team2):
                    doubles_sent += 1
            
            logger.info(f"Random Matchup Engine cycle complete: {singles_sent} singles, {doubles_sent} doubles invitations sent")
            
        except Exception as e:
            logger.error(f"Error in matchup cycle: {e}")
    
    def start_background_scheduler(self):
        """Start the background scheduler thread"""
        if not self.enabled:
            logger.info("Random Matchup Engine is disabled via RANDOM_MATCHUP_ENABLED=0")
            return
            
        def scheduler_loop():
            logger.info("Random Matchup Engine background scheduler started")
            
            while True:
                try:
                    if self.acquire_leader_lock():
                        logger.info("Acquired leader lock, running matchup cycle")
                        self.run_matchup_cycle()
                        self.update_heartbeat()
                    else:
                        logger.debug("Failed to acquire leader lock, skipping cycle")
                    
                    # Sleep for 6-12 hours with jitter
                    base_sleep = 6 * 3600  # 6 hours
                    jitter = random.randint(0, 6 * 3600)  # 0-6 hours
                    total_sleep = base_sleep + jitter
                    
                    logger.info(f"Sleeping for {total_sleep/3600:.1f} hours until next cycle")
                    time.sleep(total_sleep)
                    
                except Exception as e:
                    logger.error(f"Error in scheduler loop: {e}")
                    time.sleep(3600)  # Sleep 1 hour on error
                finally:
                    self.release_lock()
        
        # Start scheduler thread
        scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        scheduler_thread.start()
        logger.info("Background scheduler thread started")


def start_random_matchup_engine():
    """Start the Random Matchup Engine background service"""
    engine = RandomMatchupEngine()
    engine.start_background_scheduler()
    return engine


if __name__ == "__main__":
    # For testing - run one cycle
    engine = RandomMatchupEngine()
    if engine.acquire_leader_lock():
        engine.run_matchup_cycle()
        engine.release_lock()
    else:
        print("Failed to acquire lock - another instance may be running")
-- schema.sql
-- Full Postgres schema converted from your SQLite init_db()

-- players table (all original columns + ALTER additions)
CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    address TEXT NOT NULL,
    dob TEXT,
    location1 TEXT NOT NULL,
    location2 TEXT,
    preferred_sport TEXT,
    preferred_court TEXT,
    skill_level TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    selfie TEXT,
    is_looking_for_match INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- ALTER/added columns
    gender TEXT,
    player_id TEXT UNIQUE,             -- unique 4-digit player id, kept as TEXT unique
    travel_radius TEXT,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    tournament_wins INTEGER DEFAULT 0,
    is_admin INTEGER DEFAULT 0,
    membership_type TEXT,
    stripe_customer_id TEXT,
    subscription_status TEXT,
    first_name TEXT,
    last_name TEXT,
    ranking_points INTEGER DEFAULT 0,
    guardian_email TEXT,
    account_status TEXT DEFAULT 'active',
    guardian_consent_required INTEGER DEFAULT 0,
    guardian_consent_date TEXT,
    subscription_end_date TEXT,
    trial_end_date TEXT,
    can_search_players INTEGER DEFAULT 1,
    can_send_challenges INTEGER DEFAULT 1,
    can_receive_challenges INTEGER DEFAULT 1,
    can_join_tournaments INTEGER DEFAULT 0,
    can_view_leaderboard INTEGER DEFAULT 0,
    can_view_premium_stats INTEGER DEFAULT 0,
    test_account INTEGER DEFAULT 0,
    disclaimers_accepted INTEGER DEFAULT 0,
    tournament_rules_accepted INTEGER DEFAULT 0,
    push_subscription TEXT,
    notifications_enabled INTEGER DEFAULT 1,
    free_tournament_entries INTEGER DEFAULT 0,
    job_title TEXT,
    admin_level TEXT DEFAULT 'staff',
    username TEXT,
    password_hash TEXT,
    must_change_password INTEGER DEFAULT 0,
    availability_schedule TEXT,
    time_preference TEXT DEFAULT 'Flexible',
    preferred_court_1 TEXT,
    preferred_court_2 TEXT,
    court1_coordinates TEXT,
    court2_coordinates TEXT,
    tournament_credits NUMERIC(10,2) DEFAULT 0.00,
    payout_preference TEXT,
    paypal_email TEXT,
    venmo_username TEXT,
    zelle_info TEXT,
    nda_accepted INTEGER DEFAULT 0,
    nda_accepted_date TEXT,
    nda_signature TEXT,
    nda_ip_address TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    search_radius_miles INTEGER DEFAULT 15,
    zip_code TEXT,
    city TEXT,
    state TEXT,
    referral_code TEXT,
    phone_number TEXT,
    match_preference TEXT DEFAULT 'singles',
    current_team_id INTEGER
);

-- settings
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- bank_settings
CREATE TABLE IF NOT EXISTS bank_settings (
    id SERIAL PRIMARY KEY,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES players(id)
);

-- credit_transactions
CREATE TABLE IF NOT EXISTS credit_transactions (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('credit_issued', 'credit_used')),
    amount NUMERIC(10,2) NOT NULL,
    description TEXT NOT NULL,
    tournament_id INTEGER REFERENCES tournaments(id),
    admin_id INTEGER REFERENCES players(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- tournament_payouts
CREATE TABLE IF NOT EXISTS tournament_payouts (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    tournament_instance_id INTEGER NOT NULL REFERENCES tournament_instances(id),
    tournament_name TEXT NOT NULL,
    placement TEXT NOT NULL,
    prize_amount NUMERIC(10,2) NOT NULL,
    payout_method TEXT,
    payout_account TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'paid', 'failed')),
    admin_notes TEXT,
    paid_by INTEGER REFERENCES players(id),
    paid_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- matches (main)
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    player1_id INTEGER NOT NULL REFERENCES players(id),
    tournament_id INTEGER,
    player2_id INTEGER NOT NULL REFERENCES players(id),
    sport TEXT NOT NULL,
    team1_id INTEGER,
    team2_id INTEGER,
    winner_team_id INTEGER,
    round INTEGER DEFAULT 1,
    court_location TEXT NOT NULL,
    match_date TEXT,
    status TEXT DEFAULT 'pending',
    player1_confirmed INTEGER DEFAULT 0,
    player2_confirmed INTEGER DEFAULT 0,
    winner_id INTEGER REFERENCES players(id),
    player1_score INTEGER DEFAULT 0,
    player2_score INTEGER DEFAULT 0,
    match_result TEXT,
    result_submitted_by INTEGER REFERENCES players(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- additional/altered columns
    player1_validated INTEGER DEFAULT 0,
    player2_validated INTEGER DEFAULT 0,
    loser_id INTEGER,
    completed_at TEXT,
    player1_skill_feedback TEXT,
    player2_skill_feedback TEXT,
    validation_status TEXT DEFAULT 'pending',
    match_type TEXT DEFAULT 'singles',
    scheduled_time TEXT,
    notification_sent INTEGER DEFAULT 0
);

-- match_teams
CREATE TABLE IF NOT EXISTS match_teams (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id),
    team_number INTEGER NOT NULL,
    player_id INTEGER NOT NULL REFERENCES players(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (match_id, player_id)
);

-- teams
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    player1_id INTEGER REFERENCES players(id),
    home_court TEXT,
    player2_id INTEGER REFERENCES players(id),
    team_name TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES players(id),
    UNIQUE (player1_id, player2_id)
);

-- team_invitations
CREATE TABLE IF NOT EXISTS team_invitations (
    id SERIAL PRIMARY KEY,
    inviter_id INTEGER NOT NULL REFERENCES players(id),
    invitee_id INTEGER NOT NULL REFERENCES players(id),
    invitation_message TEXT,
    team_id INTEGER REFERENCES teams(id),
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TEXT,
    expires_at TEXT
);

-- tournament_instances
CREATE TABLE IF NOT EXISTS tournament_instances (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    skill_level TEXT NOT NULL,
    entry_fee NUMERIC NOT NULL,
    max_players INTEGER DEFAULT 32,
    current_players INTEGER DEFAULT 0,
    status TEXT DEFAULT 'open',
    start_date TEXT,
    end_date TEXT,
    winner_id INTEGER REFERENCES players(id),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    join_radius_miles INTEGER DEFAULT 25,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tournament_notification_sent INTEGER DEFAULT 0
);

-- tournaments
CREATE TABLE IF NOT EXISTS tournaments (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    tournament_instance_id INTEGER NOT NULL REFERENCES tournament_instances(id),
    tournament_name TEXT NOT NULL,
    tournament_level TEXT,
    tournament_type TEXT DEFAULT 'singles',
    entry_fee NUMERIC,
    sport TEXT,
    entry_date TEXT NOT NULL,
    match_deadline TEXT NOT NULL,
    completed INTEGER DEFAULT 0,
    match_result TEXT,
    payment_status TEXT DEFAULT 'pending',
    bracket_position INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tournament_notification_sent INTEGER DEFAULT 0
);

-- messages
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL REFERENCES players(id),
    receiver_id INTEGER NOT NULL REFERENCES players(id),
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_status INTEGER DEFAULT 0
);

-- tournament_matches
CREATE TABLE IF NOT EXISTS tournament_matches (
    id SERIAL PRIMARY KEY,
    tournament_instance_id INTEGER NOT NULL REFERENCES tournament_instances(id),
    round_number INTEGER NOT NULL,
    match_number INTEGER NOT NULL,
    player1_id INTEGER REFERENCES players(id),
    player2_id INTEGER REFERENCES players(id),
    winner_id INTEGER REFERENCES players(id),
    player1_score TEXT,
    player2_score TEXT,
    status TEXT DEFAULT 'pending',
    scheduled_date TEXT,
    completed_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ambassadors
CREATE TABLE IF NOT EXISTS ambassadors (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL UNIQUE REFERENCES players(id),
    referral_code TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'active',
    referrals_count INTEGER DEFAULT 0,
    qualified_referrals INTEGER DEFAULT 0,
    lifetime_membership_granted INTEGER DEFAULT 0,
    state_territory TEXT,
    application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    qualification_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ambassador_referrals
CREATE TABLE IF NOT EXISTS ambassador_referrals (
    id SERIAL PRIMARY KEY,
    ambassador_id INTEGER NOT NULL REFERENCES ambassadors(id),
    referred_player_id INTEGER NOT NULL REFERENCES players(id),
    referral_code TEXT NOT NULL,
    membership_type TEXT,
    qualified INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    qualified_at TEXT
);

-- universal_referrals
CREATE TABLE IF NOT EXISTS universal_referrals (
    id SERIAL PRIMARY KEY,
    referrer_player_id INTEGER NOT NULL REFERENCES players(id),
    referred_player_id INTEGER NOT NULL REFERENCES players(id),
    referral_code TEXT NOT NULL,
    referrer_type TEXT DEFAULT 'regular' CHECK (referrer_type IN ('regular', 'ambassador')),
    membership_type TEXT,
    qualified INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    qualified_at TEXT,
    reward_granted INTEGER DEFAULT 0,
    reward_granted_at TEXT
);

-- partner_invitations
CREATE TABLE IF NOT EXISTS partner_invitations (
    id SERIAL PRIMARY KEY,
    tournament_entry_id INTEGER NOT NULL REFERENCES tournaments(id),
    inviter_id INTEGER NOT NULL REFERENCES players(id),
    invitee_id INTEGER NOT NULL REFERENCES players(id),
    tournament_name TEXT NOT NULL,
    entry_fee NUMERIC NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TEXT
);

-- notifications
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    data TEXT,
    read_status INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- match_schedules
CREATE TABLE IF NOT EXISTS match_schedules (
    id SERIAL PRIMARY KEY,
    tournament_match_id INTEGER NOT NULL REFERENCES tournament_matches(id),
    proposer_id INTEGER NOT NULL REFERENCES players(id),
    proposed_location TEXT,
    proposed_at TEXT NOT NULL,
    confirmation_status TEXT DEFAULT 'pending',
    confirmed_by INTEGER REFERENCES players(id),
    confirmed_at TEXT,
    counter_proposal_id INTEGER REFERENCES match_schedules(id),
    deadline_at TEXT NOT NULL,
    forfeit_status TEXT,
    forfeit_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- partial/unique indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_match_schedules_confirmed
ON match_schedules (tournament_match_id)
WHERE confirmation_status = 'confirmed';

CREATE INDEX IF NOT EXISTS idx_match_schedules_tournament_match ON match_schedules(tournament_match_id);
CREATE INDEX IF NOT EXISTS idx_match_schedules_proposer ON match_schedules(proposer_id);

-- custom_tournaments and entries
CREATE TABLE IF NOT EXISTS custom_tournaments (
    id SERIAL PRIMARY KEY,
    organizer_id INTEGER REFERENCES players(id),
    tournament_name TEXT,
    description TEXT,
    location TEXT,
    max_players INTEGER,
    entry_fee NUMERIC,
    format TEXT,
    winner_id TEXT,
    prize_pool NUMERIC DEFAULT 0,
    current_entries INTEGER DEFAULT 0,
    join_radius_miles INTEGER DEFAULT 25,
    start_date TEXT,
    registration_deadline TEXT,
    status TEXT DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS custom_tournament_entries (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER NOT NULL REFERENCES custom_tournaments(id),
    player_id INTEGER NOT NULL REFERENCES players(id),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tournament_id, player_id)
);

-- score_submissions
CREATE TABLE IF NOT EXISTS score_submissions (
    id SERIAL PRIMARY KEY,
    tournament_match_id INTEGER NOT NULL REFERENCES tournament_matches(id),
    submitter_id INTEGER NOT NULL REFERENCES players(id),
    opponent_id INTEGER NOT NULL REFERENCES players(id),
    submitted_score TEXT NOT NULL,
    winner_id INTEGER NOT NULL REFERENCES players(id),
    approval_status TEXT DEFAULT 'pending',
    approved_by INTEGER REFERENCES players(id),
    approved_at TEXT,
    dispute_reason TEXT,
    auto_approval_deadline_at TEXT,
    admin_resolution TEXT,
    resolved_by INTEGER REFERENCES players(id),
    resolved_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_score_submissions_pending
ON score_submissions (tournament_match_id)
WHERE approval_status IN ('pending', 'disputed');

CREATE INDEX IF NOT EXISTS idx_score_submissions_tournament_match ON score_submissions(tournament_match_id);
CREATE INDEX IF NOT EXISTS idx_score_submissions_submitter ON score_submissions(submitter_id);
CREATE INDEX IF NOT EXISTS idx_score_submissions_status ON score_submissions(approval_status);

-- match_reminders
CREATE TABLE IF NOT EXISTS match_reminders (
    id SERIAL PRIMARY KEY,
    tournament_match_id INTEGER NOT NULL REFERENCES tournament_matches(id),
    player_id INTEGER NOT NULL REFERENCES players(id),
    reminder_type TEXT NOT NULL,
    notification_method TEXT DEFAULT 'in_app',
    sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
    delivery_status TEXT DEFAULT 'pending',
    external_id TEXT,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_match_reminders_composite ON match_reminders(tournament_match_id, player_id, reminder_type);
CREATE INDEX IF NOT EXISTS idx_match_reminders_status ON match_reminders(delivery_status);

-- indexes referenced in init_db()
CREATE UNIQUE INDEX IF NOT EXISTS idx_players_referral_code_unique ON players (referral_code) WHERE referral_code IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_universal_referrals_pair_unique ON universal_referrals (referrer_player_id, referred_player_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_universal_referrals_referred_unique ON universal_referrals (referred_player_id);
CREATE INDEX IF NOT EXISTS idx_universal_referrals_code ON universal_referrals (referral_code);
CREATE INDEX IF NOT EXISTS idx_universal_referrals_qualified ON universal_referrals (qualified);
CREATE INDEX IF NOT EXISTS idx_universal_referrals_referrer_id ON universal_referrals (referrer_player_id);

-- seed default settings (idempotent)
INSERT INTO settings (key, value, description)
VALUES
('beginner_price','10','Beginner tournament entry fee'),
('intermediate_price','20','Intermediate tournament entry fee'),
('advanced_price','40','Advanced tournament entry fee'),
('match_deadline_days','7','Days to complete a match before it expires'),
('platform_name','Ready 2 Dink','Platform display name'),
('registration_enabled','1','Allow new player registrations')
ON CONFLICT (key) DO NOTHING;

-- seed default tournament instances (only if none exist)
DO $$
BEGIN
    IF (SELECT COUNT(*) FROM tournament_instances) = 0 THEN
        INSERT INTO tournament_instances (name, skill_level, entry_fee, max_players, status)
        VALUES
        ('The B League Weekly','Beginner',20,32,'open'),
        ('Rookie Rumble','Beginner',20,32,'open'),
        ('Intermediate Challenge','Intermediate',25,32,'open'),
        ('Mid-Level Mashup','Intermediate',25,32,'open'),
        ('Advanced Showdown','Advanced',30,32,'open'),
        ('Elite Competition','Advanced',30,32,'open'),
        ('Big Dink Championship','Championship',30,128,'open'),
        ('The Hill Premium','Championship',50,64,'open');
    END IF;
END$$;

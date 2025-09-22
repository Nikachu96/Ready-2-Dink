--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (63f4182)
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ambassador_referrals; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.ambassador_referrals (
    id integer NOT NULL,
    ambassador_id integer NOT NULL,
    referred_player_id integer NOT NULL,
    referral_code text NOT NULL,
    membership_type text,
    qualified integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    qualified_at text
);


ALTER TABLE public.ambassador_referrals OWNER TO neondb_owner;

--
-- Name: ambassador_referrals_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.ambassador_referrals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ambassador_referrals_id_seq OWNER TO neondb_owner;

--
-- Name: ambassador_referrals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.ambassador_referrals_id_seq OWNED BY public.ambassador_referrals.id;


--
-- Name: ambassadors; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.ambassadors (
    id integer NOT NULL,
    player_id integer NOT NULL,
    referral_code text NOT NULL,
    status text DEFAULT 'active'::text,
    referrals_count integer DEFAULT 0,
    qualified_referrals integer DEFAULT 0,
    lifetime_membership_granted integer DEFAULT 0,
    state_territory text,
    application_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    qualification_date text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.ambassadors OWNER TO neondb_owner;

--
-- Name: ambassadors_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.ambassadors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ambassadors_id_seq OWNER TO neondb_owner;

--
-- Name: ambassadors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.ambassadors_id_seq OWNED BY public.ambassadors.id;


--
-- Name: bank_settings; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.bank_settings (
    id integer NOT NULL,
    bank_name text,
    account_holder_name text,
    account_type text,
    routing_number text,
    account_number text,
    business_name text,
    business_address text,
    business_phone text,
    business_email text,
    stripe_account_id text,
    payout_method text DEFAULT 'manual'::text,
    auto_payout_enabled integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by integer,
    CONSTRAINT bank_settings_account_type_check CHECK ((account_type = ANY (ARRAY['checking'::text, 'savings'::text, 'business'::text]))),
    CONSTRAINT bank_settings_payout_method_check CHECK ((payout_method = ANY (ARRAY['manual'::text, 'stripe_connect'::text, 'ach'::text])))
);


ALTER TABLE public.bank_settings OWNER TO neondb_owner;

--
-- Name: bank_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.bank_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bank_settings_id_seq OWNER TO neondb_owner;

--
-- Name: bank_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.bank_settings_id_seq OWNED BY public.bank_settings.id;


--
-- Name: credit_transactions; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.credit_transactions (
    id integer NOT NULL,
    player_id integer NOT NULL,
    transaction_type text NOT NULL,
    amount numeric(10,2) NOT NULL,
    description text NOT NULL,
    tournament_id integer,
    admin_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT credit_transactions_transaction_type_check CHECK ((transaction_type = ANY (ARRAY['credit_issued'::text, 'credit_used'::text])))
);


ALTER TABLE public.credit_transactions OWNER TO neondb_owner;

--
-- Name: credit_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.credit_transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.credit_transactions_id_seq OWNER TO neondb_owner;

--
-- Name: credit_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.credit_transactions_id_seq OWNED BY public.credit_transactions.id;


--
-- Name: matches; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.matches (
    id integer NOT NULL,
    player1_id integer NOT NULL,
    player2_id integer NOT NULL,
    sport text NOT NULL,
    court_location text NOT NULL,
    match_date text,
    status text DEFAULT 'pending'::text,
    player1_confirmed integer DEFAULT 0,
    player2_confirmed integer DEFAULT 0,
    winner_id integer,
    player1_score integer DEFAULT 0,
    player2_score integer DEFAULT 0,
    match_result text,
    result_submitted_by integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    player1_validated integer DEFAULT 0,
    player2_validated integer DEFAULT 0,
    player1_skill_feedback text,
    player2_skill_feedback text,
    validation_status text DEFAULT 'pending'::text,
    notification_sent integer DEFAULT 0
);


ALTER TABLE public.matches OWNER TO neondb_owner;

--
-- Name: matches_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.matches_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.matches_id_seq OWNER TO neondb_owner;

--
-- Name: matches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.matches_id_seq OWNED BY public.matches.id;


--
-- Name: messages; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.messages (
    id integer NOT NULL,
    sender_id integer NOT NULL,
    receiver_id integer NOT NULL,
    message text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    read_status integer DEFAULT 0
);


ALTER TABLE public.messages OWNER TO neondb_owner;

--
-- Name: messages_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.messages_id_seq OWNER TO neondb_owner;

--
-- Name: messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.messages_id_seq OWNED BY public.messages.id;


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.notifications (
    id integer NOT NULL,
    player_id integer NOT NULL,
    type text NOT NULL,
    title text NOT NULL,
    message text NOT NULL,
    data text,
    read_status integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.notifications OWNER TO neondb_owner;

--
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notifications_id_seq OWNER TO neondb_owner;

--
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- Name: partner_invitations; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.partner_invitations (
    id integer NOT NULL,
    tournament_entry_id integer NOT NULL,
    inviter_id integer NOT NULL,
    invitee_id integer NOT NULL,
    tournament_name text NOT NULL,
    entry_fee real NOT NULL,
    status text DEFAULT 'pending'::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    responded_at text
);


ALTER TABLE public.partner_invitations OWNER TO neondb_owner;

--
-- Name: partner_invitations_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.partner_invitations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.partner_invitations_id_seq OWNER TO neondb_owner;

--
-- Name: partner_invitations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.partner_invitations_id_seq OWNED BY public.partner_invitations.id;


--
-- Name: players; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.players (
    id integer NOT NULL,
    full_name text NOT NULL,
    address text NOT NULL,
    dob text NOT NULL,
    location1 text NOT NULL,
    location2 text,
    preferred_sport text,
    preferred_court text,
    skill_level text NOT NULL,
    email text NOT NULL,
    selfie text,
    is_looking_for_match integer DEFAULT 1,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    wins integer DEFAULT 0,
    losses integer DEFAULT 0,
    tournament_wins integer DEFAULT 0,
    is_admin integer DEFAULT 0,
    membership_type text,
    stripe_customer_id text,
    subscription_status text,
    first_name text,
    last_name text,
    ranking_points integer DEFAULT 0,
    guardian_email text,
    account_status text DEFAULT 'active'::text,
    guardian_consent_required integer DEFAULT 0,
    guardian_consent_date text,
    subscription_end_date text,
    trial_end_date text,
    test_account integer DEFAULT 0,
    disclaimers_accepted integer DEFAULT 0,
    tournament_rules_accepted integer DEFAULT 0,
    push_subscription text,
    notifications_enabled integer DEFAULT 1,
    free_tournament_entries integer DEFAULT 0,
    job_title text,
    admin_level text DEFAULT 'staff'::text,
    username text,
    password_hash text,
    must_change_password integer DEFAULT 0,
    availability_schedule text,
    time_preference text DEFAULT 'Flexible'::text,
    preferred_court_1 text,
    preferred_court_2 text,
    court1_coordinates text,
    court2_coordinates text,
    player_id text,
    tournament_credits numeric(10,2) DEFAULT 0.00,
    payout_preference text,
    paypal_email text,
    venmo_username text,
    zelle_info text,
    nda_accepted integer DEFAULT 0,
    nda_accepted_date text,
    nda_signature text,
    nda_ip_address text,
    latitude real,
    longitude real,
    search_radius_miles integer DEFAULT 15,
    referral_code text,
    match_preference text DEFAULT 'singles'::text,
    current_team_id integer,
    discoverability_preference text DEFAULT 'both'::text,
    last_random_challenge_at timestamp without time zone,
    CONSTRAINT players_search_radius_miles_check CHECK (((search_radius_miles >= 15) AND (search_radius_miles <= 50)))
);


ALTER TABLE public.players OWNER TO neondb_owner;

--
-- Name: players_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.players_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.players_id_seq OWNER TO neondb_owner;

--
-- Name: players_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.players_id_seq OWNED BY public.players.id;


--
-- Name: settings; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.settings (
    key text NOT NULL,
    value text NOT NULL,
    description text,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.settings OWNER TO neondb_owner;

--
-- Name: system_jobs; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.system_jobs (
    job_name text NOT NULL,
    last_run_at timestamp without time zone,
    owner_pid text,
    heartbeat_at timestamp without time zone
);


ALTER TABLE public.system_jobs OWNER TO neondb_owner;

--
-- Name: team_invitations; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.team_invitations (
    id integer NOT NULL,
    inviter_id integer NOT NULL,
    invitee_id integer NOT NULL,
    invitation_message text,
    status text DEFAULT 'pending'::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    responded_at timestamp without time zone,
    expires_at timestamp without time zone,
    source text DEFAULT 'user'::text,
    meta_json text DEFAULT '{}'::text
);


ALTER TABLE public.team_invitations OWNER TO neondb_owner;

--
-- Name: team_invitations_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.team_invitations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.team_invitations_id_seq OWNER TO neondb_owner;

--
-- Name: team_invitations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.team_invitations_id_seq OWNED BY public.team_invitations.id;


--
-- Name: teams; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.teams (
    id integer NOT NULL,
    player1_id integer NOT NULL,
    player2_id integer NOT NULL,
    team_name text,
    status text DEFAULT 'active'::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer NOT NULL
);


ALTER TABLE public.teams OWNER TO neondb_owner;

--
-- Name: teams_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.teams_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.teams_id_seq OWNER TO neondb_owner;

--
-- Name: teams_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.teams_id_seq OWNED BY public.teams.id;


--
-- Name: tournament_instances; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.tournament_instances (
    id integer NOT NULL,
    name text NOT NULL,
    skill_level text NOT NULL,
    entry_fee real NOT NULL,
    max_players integer DEFAULT 32,
    current_players integer DEFAULT 0,
    status text DEFAULT 'open'::text,
    start_date text,
    end_date text,
    winner_id integer,
    latitude real,
    longitude real,
    join_radius_miles integer DEFAULT 25,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.tournament_instances OWNER TO neondb_owner;

--
-- Name: tournament_instances_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.tournament_instances_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tournament_instances_id_seq OWNER TO neondb_owner;

--
-- Name: tournament_instances_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.tournament_instances_id_seq OWNED BY public.tournament_instances.id;


--
-- Name: tournament_matches; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.tournament_matches (
    id integer NOT NULL,
    tournament_instance_id integer NOT NULL,
    round_number integer NOT NULL,
    match_number integer NOT NULL,
    player1_id integer,
    player2_id integer,
    winner_id integer,
    player1_score text,
    player2_score text,
    status text DEFAULT 'pending'::text,
    scheduled_date text,
    completed_date text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.tournament_matches OWNER TO neondb_owner;

--
-- Name: tournament_matches_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.tournament_matches_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tournament_matches_id_seq OWNER TO neondb_owner;

--
-- Name: tournament_matches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.tournament_matches_id_seq OWNED BY public.tournament_matches.id;


--
-- Name: tournament_payouts; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.tournament_payouts (
    id integer NOT NULL,
    player_id integer NOT NULL,
    tournament_instance_id integer NOT NULL,
    tournament_name text NOT NULL,
    placement text NOT NULL,
    prize_amount numeric(10,2) NOT NULL,
    payout_method text,
    payout_account text,
    status text DEFAULT 'pending'::text,
    admin_notes text,
    paid_by integer,
    paid_at text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tournament_payouts_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'processing'::text, 'paid'::text, 'failed'::text])))
);


ALTER TABLE public.tournament_payouts OWNER TO neondb_owner;

--
-- Name: tournament_payouts_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.tournament_payouts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tournament_payouts_id_seq OWNER TO neondb_owner;

--
-- Name: tournament_payouts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.tournament_payouts_id_seq OWNED BY public.tournament_payouts.id;


--
-- Name: tournaments; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.tournaments (
    id integer NOT NULL,
    player_id integer NOT NULL,
    tournament_instance_id integer NOT NULL,
    tournament_name text NOT NULL,
    tournament_level text,
    tournament_type text DEFAULT 'singles'::text,
    entry_fee real,
    sport text,
    entry_date text NOT NULL,
    match_deadline text NOT NULL,
    completed integer DEFAULT 0,
    match_result text,
    payment_status text DEFAULT 'pending'::text,
    bracket_position integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.tournaments OWNER TO neondb_owner;

--
-- Name: tournaments_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.tournaments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tournaments_id_seq OWNER TO neondb_owner;

--
-- Name: tournaments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.tournaments_id_seq OWNED BY public.tournaments.id;


--
-- Name: universal_referrals; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.universal_referrals (
    id integer NOT NULL,
    referrer_player_id integer NOT NULL,
    referred_player_id integer NOT NULL,
    referral_code text NOT NULL,
    referrer_type text DEFAULT 'regular'::text,
    membership_type text,
    qualified integer DEFAULT 0,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    qualified_at text,
    reward_granted integer DEFAULT 0,
    reward_granted_at text,
    CONSTRAINT universal_referrals_referrer_type_check CHECK ((referrer_type = ANY (ARRAY['regular'::text, 'ambassador'::text])))
);


ALTER TABLE public.universal_referrals OWNER TO neondb_owner;

--
-- Name: ambassador_referrals id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ambassador_referrals ALTER COLUMN id SET DEFAULT nextval('public.ambassador_referrals_id_seq'::regclass);


--
-- Name: ambassadors id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ambassadors ALTER COLUMN id SET DEFAULT nextval('public.ambassadors_id_seq'::regclass);


--
-- Name: bank_settings id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bank_settings ALTER COLUMN id SET DEFAULT nextval('public.bank_settings_id_seq'::regclass);


--
-- Name: credit_transactions id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.credit_transactions ALTER COLUMN id SET DEFAULT nextval('public.credit_transactions_id_seq'::regclass);


--
-- Name: matches id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.matches ALTER COLUMN id SET DEFAULT nextval('public.matches_id_seq'::regclass);


--
-- Name: messages id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.messages ALTER COLUMN id SET DEFAULT nextval('public.messages_id_seq'::regclass);


--
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- Name: partner_invitations id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_invitations ALTER COLUMN id SET DEFAULT nextval('public.partner_invitations_id_seq'::regclass);


--
-- Name: players id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.players ALTER COLUMN id SET DEFAULT nextval('public.players_id_seq'::regclass);


--
-- Name: team_invitations id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.team_invitations ALTER COLUMN id SET DEFAULT nextval('public.team_invitations_id_seq'::regclass);


--
-- Name: teams id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.teams ALTER COLUMN id SET DEFAULT nextval('public.teams_id_seq'::regclass);


--
-- Name: tournament_instances id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournament_instances ALTER COLUMN id SET DEFAULT nextval('public.tournament_instances_id_seq'::regclass);


--
-- Name: tournament_matches id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournament_matches ALTER COLUMN id SET DEFAULT nextval('public.tournament_matches_id_seq'::regclass);


--
-- Name: tournament_payouts id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournament_payouts ALTER COLUMN id SET DEFAULT nextval('public.tournament_payouts_id_seq'::regclass);


--
-- Name: tournaments id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournaments ALTER COLUMN id SET DEFAULT nextval('public.tournaments_id_seq'::regclass);


--
-- Data for Name: ambassador_referrals; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.ambassador_referrals (id, ambassador_id, referred_player_id, referral_code, membership_type, qualified, created_at, qualified_at) FROM stdin;
\.


--
-- Data for Name: ambassadors; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.ambassadors (id, player_id, referral_code, status, referrals_count, qualified_referrals, lifetime_membership_granted, state_territory, application_date, qualification_date, created_at) FROM stdin;
\.


--
-- Data for Name: bank_settings; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.bank_settings (id, bank_name, account_holder_name, account_type, routing_number, account_number, business_name, business_address, business_phone, business_email, stripe_account_id, payout_method, auto_payout_enabled, created_at, updated_at, updated_by) FROM stdin;
\.


--
-- Data for Name: credit_transactions; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.credit_transactions (id, player_id, transaction_type, amount, description, tournament_id, admin_id, created_at) FROM stdin;
\.


--
-- Data for Name: matches; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.matches (id, player1_id, player2_id, sport, court_location, match_date, status, player1_confirmed, player2_confirmed, winner_id, player1_score, player2_score, match_result, result_submitted_by, created_at, player1_validated, player2_validated, player1_skill_feedback, player2_skill_feedback, validation_status, notification_sent) FROM stdin;
12	1	2	Pickleball	Ready 2 Dink Courts	2024-09-18	completed	1	1	1	11	7	completed	1	2025-09-18 21:14:31.660488	1	1	\N	\N	validated	1
13	3	5	Pickleball	Ready 2 Dink Courts	2024-09-18	completed	1	1	5	9	11	completed	3	2025-09-18 21:14:31.660488	1	1	\N	\N	validated	1
14	6	7	Pickleball	Ready 2 Dink Courts	2024-09-18	completed	1	1	6	11	5	completed	6	2025-09-18 21:14:31.660488	1	1	\N	\N	validated	1
15	8	9	Pickleball	Ready 2 Dink Courts	2024-09-18	completed	1	1	9	8	11	completed	8	2025-09-18 21:14:31.660488	1	1	\N	\N	validated	1
16	1	5	Pickleball	Ready 2 Dink Courts	2024-09-18	completed	1	1	1	11	5	completed	1	2025-09-18 21:14:58.715895	1	1	\N	\N	validated	1
17	6	9	Pickleball	Ready 2 Dink Courts	2024-09-18	completed	1	1	6	11	9	completed	6	2025-09-18 21:14:58.715895	1	1	\N	\N	validated	1
18	1	6	Pickleball	Ready 2 Dink Championship Court	2024-09-18	completed	1	1	1	11	9	completed	1	2025-09-18 21:15:16.428282	1	1	\N	\N	validated	1
19	1	8	pickleball	TBD	\N	scheduled	0	0	\N	0	0	\N	\N	2025-09-21 16:15:46.721334	0	0	\N	\N	pending	0
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.messages (id, sender_id, receiver_id, message, created_at, read_status) FROM stdin;
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.notifications (id, player_id, type, title, message, data, read_status, created_at) FROM stdin;
\.


--
-- Data for Name: partner_invitations; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.partner_invitations (id, tournament_entry_id, inviter_id, invitee_id, tournament_name, entry_fee, status, created_at, responded_at) FROM stdin;
\.


--
-- Data for Name: players; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.players (id, full_name, address, dob, location1, location2, preferred_sport, preferred_court, skill_level, email, selfie, is_looking_for_match, created_at, wins, losses, tournament_wins, is_admin, membership_type, stripe_customer_id, subscription_status, first_name, last_name, ranking_points, guardian_email, account_status, guardian_consent_required, guardian_consent_date, subscription_end_date, trial_end_date, test_account, disclaimers_accepted, tournament_rules_accepted, push_subscription, notifications_enabled, free_tournament_entries, job_title, admin_level, username, password_hash, must_change_password, availability_schedule, time_preference, preferred_court_1, preferred_court_2, court1_coordinates, court2_coordinates, player_id, tournament_credits, payout_preference, paypal_email, venmo_username, zelle_info, nda_accepted, nda_accepted_date, nda_signature, nda_ip_address, latitude, longitude, search_radius_miles, referral_code, match_preference, current_team_id, discoverability_preference, last_random_challenge_at) FROM stdin;
6	Mike Johnson	456 Oak Ave	1985-05-15	Manhattan, NY	\N	\N	\N	Intermediate	mike@test.com	\N	1	2025-09-17 16:14:11.729611	2	1	0	0	\N	\N	\N	Mike	Johnson	100	\N	active	0	\N	\N	\N	0	0	0	\N	1	0	\N	staff	\N	test_hash	0	\N	Flexible	\N	\N	\N	\N	\N	0.00	\N	\N	\N	\N	0	\N	\N	\N	\N	\N	15	\N	singles	\N	doubles	2025-09-20 18:47:42.672222
9	Lisa Garcia	654 Maple Dr	1991-11-25	Queens, NY	\N	\N	\N	Advanced	lisa@test.com	\N	1	2025-09-17 16:14:11.729611	1	1	0	0	\N	\N	\N	Lisa	Garcia	50	\N	active	0	\N	\N	\N	0	0	0	\N	1	0	\N	staff	\N	test_hash	0	\N	Flexible	\N	\N	\N	\N	\N	0.00	\N	\N	\N	\N	0	\N	\N	\N	\N	\N	15	\N	singles	\N	both	2025-09-22 01:54:38.817085
1	Lucien Flahaut	123 Main St	1990-01-01	New York, NY	\N	\N	\N	Intermediate	lucien@ready2dink.com	\N	1	2025-09-17 14:37:01.82039	6	0	1	1	\N	\N	\N	\N	\N	350	\N	active	0	\N	\N	\N	0	1	0	\N	1	0	\N	staff	lucien08	scrypt:32768:8:1$LXS7SoowozpbQrow$38c48c43326062c048c777be55c43eacb356b9d7f7b724ef3db0741442da5d4c1684e3d6cede3e9c3fcb4007a3c804b203e416ab5c38f23375c1c004e24d2fe9	0	\N	Flexible	\N	\N	\N	\N	\N	0.00	\N	\N	\N	\N	1	\N	\N	\N	40.7128	-74.006	15	R2DTEST01	doubles_need_partner	\N	singles	2025-09-22 01:54:38.817085
7	Emma Brown	789 Pine Rd	1992-03-20	Brooklyn, NY	\N	\N	\N	Intermediate	emma@test.com	\N	1	2025-09-17 16:14:11.729611	0	1	0	0	\N	\N	\N	Emma	Brown	0	\N	active	0	\N	\N	\N	0	0	0	\N	1	0	\N	staff	\N	test_hash	0	\N	Flexible	\N	\N	\N	\N	\N	0.00	\N	\N	\N	\N	0	\N	\N	\N	\N	\N	15	\N	singles	\N	both	2025-09-20 18:47:42.29796
2	Bob Tester	456 Oak Ave	1992-02-02	Los Angeles, CA	\N	\N	\N	Beginner	bob@example.com	\N	1	2025-09-17 14:37:01.82039	1	2	0	0	\N	\N	\N	\N	\N	50	\N	active	0	\N	\N	\N	0	0	0	\N	1	0	\N	staff	bob_test	hash2	0	\N	Flexible	\N	\N	\N	\N	\N	0.00	\N	\N	\N	\N	0	\N	\N	\N	34.0522	-118.2437	15	R2DTEST02	singles	\N	doubles	2025-09-20 18:47:43.411967
3	Charlie Friend	789 Pine St	1988-03-03	Chicago, IL	\N	\N	\N	Advanced	charlie@example.com	\N	1	2025-09-17 14:37:01.82039	0	3	0	0	\N	\N	\N	\N	\N	0	\N	active	0	\N	\N	\N	0	0	0	\N	1	0	\N	staff	charlie_f	hash3	0	\N	Flexible	\N	\N	\N	\N	\N	0.00	\N	\N	\N	\N	0	\N	\N	\N	41.8781	-87.6298	15	R2DTEST03	singles	\N	singles	2025-09-20 18:47:43.776005
5	Sarah Wilson	123 Main St	1990-01-01	New York, NY	\N	\N	\N	Intermediate	sarah@test.com	\N	1	2025-09-17 16:14:11.729611	1	2	0	0	\N	\N	\N	Sarah	Wilson	50	\N	active	0	\N	\N	\N	0	0	0	\N	1	0	\N	staff	\N	test_hash	0	\N	Flexible	\N	\N	\N	\N	\N	0.00	\N	\N	\N	\N	0	\N	\N	\N	\N	\N	15	\N	singles	\N	both	2025-09-20 18:47:43.411967
15	Jessica Chen	123 Salem St, Apex, NC 27502	1993-09-25	Apex, NC	Apex, North Carolina	\N	\N	Advanced	jessica.chen@test.com	default-avatar.png	1	2025-09-20 17:02:31.899919	22	4	0	0	\N	\N	\N	Jessica	Chen	1150	\N	active	0	\N	\N	\N	1	1	1	\N	1	0	\N	staff	\N	\N	0	\N	Flexible	\N	\N	\N	\N	\N	0.00	\N	\N	\N	\N	0	\N	\N	\N	35.7323	-78.8503	15	\N	doubles_need_partner	\N	both	2025-09-20 18:47:43.776005
8	David Lee	321 Elm St	1988-07-10	New York, NY	\N	\N	\N	Beginner	david@test.com	\N	1	2025-09-17 16:14:11.729611	0	1	0	0	\N	\N	\N	David	Lee	0	\N	active	0	\N	\N	\N	0	0	0	\N	1	0	\N	staff	\N	test_hash	0	\N	Flexible	\N	\N	\N	\N	\N	0.00	\N	\N	\N	\N	0	\N	\N	\N	\N	\N	15	\N	singles	\N	both	2025-09-22 01:54:37.789989
\.


--
-- Data for Name: settings; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.settings (key, value, description, updated_at) FROM stdin;
beginner_price	10	Beginner tournament entry fee	2025-09-12 17:39:24.663311
intermediate_price	20	Intermediate tournament entry fee	2025-09-12 17:39:24.663311
advanced_price	40	Advanced tournament entry fee	2025-09-12 17:39:24.663311
match_deadline_days	7	Days to complete a match before it expires	2025-09-12 17:39:24.663311
platform_name	Ready 2 Dink	Platform display name	2025-09-12 17:39:24.663311
registration_enabled	1	Allow new player registrations	2025-09-12 17:39:24.663311
\.


--
-- Data for Name: system_jobs; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.system_jobs (job_name, last_run_at, owner_pid, heartbeat_at) FROM stdin;
random_matchup_engine	2025-09-22 12:49:45.324786	8923	2025-09-22 12:49:45.324795
\.


--
-- Data for Name: team_invitations; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.team_invitations (id, inviter_id, invitee_id, invitation_message, status, created_at, responded_at, expires_at, source, meta_json) FROM stdin;
1	5	7	Hey! Want to play a singles match?	pending	2025-09-20 18:47:42.213864	\N	\N	random	{"type": "singles", "players": [7, 5]}
2	2	6	Hey! Want to play a singles match?	pending	2025-09-20 18:47:42.595626	\N	\N	random	{"type": "singles", "players": [2, 6]}
4	5	2	Hey! Want to play a singles match?	pending	2025-09-20 18:47:43.333728	\N	\N	random	{"type": "singles", "players": [2, 5]}
5	15	3	Hey! Want to play a singles match?	pending	2025-09-20 18:47:43.700822	\N	\N	random	{"type": "singles", "players": [3, 15]}
3	8	1	Hey! Want to play a singles match?	accepted	2025-09-20 18:47:42.964579	2025-09-21 16:15:46.782823	\N	random	{"type": "singles", "players": [1, 8]}
6	1	8	Hey! Want to play a singles match?	pending	2025-09-22 01:54:36.462014	\N	\N	random	{"type": "singles", "players": [1, 8]}
7	1	8	Hey! Want to play a singles match?	pending	2025-09-22 01:54:37.662111	\N	\N	random	{"type": "singles", "players": [1, 8]}
8	1	9	Hey! Want to play a singles match?	pending	2025-09-22 01:54:38.762126	\N	\N	random	{"type": "singles", "players": [1, 9]}
\.


--
-- Data for Name: teams; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.teams (id, player1_id, player2_id, team_name, status, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: tournament_instances; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.tournament_instances (id, name, skill_level, entry_fee, max_players, current_players, status, start_date, end_date, winner_id, latitude, longitude, join_radius_miles, created_at) FROM stdin;
1	Ready 2 Dink Championship 2024	Mixed	25	8	8	completed	2024-09-18	2024-09-18	1	40.7128	-74.006	50	2025-09-18 21:13:09.864714
2	Test Intermediate Tournament	Intermediate	25	8	1	open	2025-09-20 00:00:00	2025-09-27 00:00:00	\N	\N	\N	25	2025-09-19 01:14:56.939763
\.


--
-- Data for Name: tournament_matches; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.tournament_matches (id, tournament_instance_id, round_number, match_number, player1_id, player2_id, winner_id, player1_score, player2_score, status, scheduled_date, completed_date, created_at) FROM stdin;
1	1	1	1	1	2	\N	\N	\N	pending	\N	\N	2025-09-19 14:00:52.161498
2	1	1	2	3	5	\N	\N	\N	pending	\N	\N	2025-09-19 14:00:52.161498
3	1	1	3	6	7	\N	\N	\N	pending	\N	\N	2025-09-19 14:00:52.161498
4	1	1	4	8	9	\N	\N	\N	pending	\N	\N	2025-09-19 14:00:52.161498
5	1	2	1	\N	\N	\N	\N	\N	pending	\N	\N	2025-09-19 14:00:52.161498
6	1	2	2	\N	\N	\N	\N	\N	pending	\N	\N	2025-09-19 14:00:52.161498
7	1	3	1	\N	\N	\N	\N	\N	pending	\N	\N	2025-09-19 14:00:52.161498
\.


--
-- Data for Name: tournament_payouts; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.tournament_payouts (id, player_id, tournament_instance_id, tournament_name, placement, prize_amount, payout_method, payout_account, status, admin_notes, paid_by, paid_at, created_at) FROM stdin;
\.


--
-- Data for Name: tournaments; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.tournaments (id, player_id, tournament_instance_id, tournament_name, tournament_level, tournament_type, entry_fee, sport, entry_date, match_deadline, completed, match_result, payment_status, bracket_position, created_at) FROM stdin;
1	1	1	Ready 2 Dink Championship 2024	Mixed	Single Elimination	25	Pickleball	2024-09-18	2024-09-18	1	pending	paid	1	2025-09-18 21:13:23.365367
2	2	1	Ready 2 Dink Championship 2024	Mixed	Single Elimination	25	Pickleball	2024-09-18	2024-09-18	1	pending	paid	2	2025-09-18 21:13:23.365367
3	3	1	Ready 2 Dink Championship 2024	Mixed	Single Elimination	25	Pickleball	2024-09-18	2024-09-18	1	pending	paid	3	2025-09-18 21:13:23.365367
4	5	1	Ready 2 Dink Championship 2024	Mixed	Single Elimination	25	Pickleball	2024-09-18	2024-09-18	1	pending	paid	4	2025-09-18 21:13:23.365367
5	6	1	Ready 2 Dink Championship 2024	Mixed	Single Elimination	25	Pickleball	2024-09-18	2024-09-18	1	pending	paid	5	2025-09-18 21:13:23.365367
6	7	1	Ready 2 Dink Championship 2024	Mixed	Single Elimination	25	Pickleball	2024-09-18	2024-09-18	1	pending	paid	6	2025-09-18 21:13:23.365367
7	8	1	Ready 2 Dink Championship 2024	Mixed	Single Elimination	25	Pickleball	2024-09-18	2024-09-18	1	pending	paid	7	2025-09-18 21:13:23.365367
8	9	1	Ready 2 Dink Championship 2024	Mixed	Single Elimination	25	Pickleball	2024-09-18	2024-09-18	1	pending	paid	8	2025-09-18 21:13:23.365367
11	1	2	Test Intermediate Tournament	Intermediate	singles	25	Pickleball	2025-09-19	2025-09-26 00:00:00	0	\N	pending	\N	2025-09-19 01:15:13.191649
\.


--
-- Data for Name: universal_referrals; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.universal_referrals (id, referrer_player_id, referred_player_id, referral_code, referrer_type, membership_type, qualified, created_at, qualified_at, reward_granted, reward_granted_at) FROM stdin;
\.


--
-- Name: ambassador_referrals_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.ambassador_referrals_id_seq', 1, false);


--
-- Name: ambassadors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.ambassadors_id_seq', 1, false);


--
-- Name: bank_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.bank_settings_id_seq', 1, false);


--
-- Name: credit_transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.credit_transactions_id_seq', 1, false);


--
-- Name: matches_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.matches_id_seq', 19, true);


--
-- Name: messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.messages_id_seq', 1, false);


--
-- Name: notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.notifications_id_seq', 1, false);


--
-- Name: partner_invitations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.partner_invitations_id_seq', 1, false);


--
-- Name: players_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.players_id_seq', 15, true);


--
-- Name: team_invitations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.team_invitations_id_seq', 8, true);


--
-- Name: teams_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.teams_id_seq', 1, false);


--
-- Name: tournament_instances_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.tournament_instances_id_seq', 2, true);


--
-- Name: tournament_matches_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.tournament_matches_id_seq', 7, true);


--
-- Name: tournament_payouts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.tournament_payouts_id_seq', 1, false);


--
-- Name: tournaments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.tournaments_id_seq', 11, true);


--
-- Name: ambassador_referrals ambassador_referrals_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ambassador_referrals
    ADD CONSTRAINT ambassador_referrals_pkey PRIMARY KEY (id);


--
-- Name: ambassadors ambassadors_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ambassadors
    ADD CONSTRAINT ambassadors_pkey PRIMARY KEY (id);


--
-- Name: ambassadors ambassadors_player_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ambassadors
    ADD CONSTRAINT ambassadors_player_id_key UNIQUE (player_id);


--
-- Name: ambassadors ambassadors_referral_code_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ambassadors
    ADD CONSTRAINT ambassadors_referral_code_key UNIQUE (referral_code);


--
-- Name: bank_settings bank_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bank_settings
    ADD CONSTRAINT bank_settings_pkey PRIMARY KEY (id);


--
-- Name: credit_transactions credit_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.credit_transactions
    ADD CONSTRAINT credit_transactions_pkey PRIMARY KEY (id);


--
-- Name: matches matches_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.matches
    ADD CONSTRAINT matches_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: partner_invitations partner_invitations_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_invitations
    ADD CONSTRAINT partner_invitations_pkey PRIMARY KEY (id);


--
-- Name: players players_email_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_email_key UNIQUE (email);


--
-- Name: players players_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_pkey PRIMARY KEY (id);


--
-- Name: players players_player_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_player_id_key UNIQUE (player_id);


--
-- Name: players players_referral_code_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_referral_code_key UNIQUE (referral_code);


--
-- Name: settings settings_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_pkey PRIMARY KEY (key);


--
-- Name: system_jobs system_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.system_jobs
    ADD CONSTRAINT system_jobs_pkey PRIMARY KEY (job_name);


--
-- Name: team_invitations team_invitations_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.team_invitations
    ADD CONSTRAINT team_invitations_pkey PRIMARY KEY (id);


--
-- Name: teams teams_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_pkey PRIMARY KEY (id);


--
-- Name: teams teams_player1_id_player2_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_player1_id_player2_id_key UNIQUE (player1_id, player2_id);


--
-- Name: tournament_instances tournament_instances_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournament_instances
    ADD CONSTRAINT tournament_instances_pkey PRIMARY KEY (id);


--
-- Name: tournament_matches tournament_matches_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournament_matches
    ADD CONSTRAINT tournament_matches_pkey PRIMARY KEY (id);


--
-- Name: tournament_payouts tournament_payouts_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournament_payouts
    ADD CONSTRAINT tournament_payouts_pkey PRIMARY KEY (id);


--
-- Name: tournaments tournaments_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournaments
    ADD CONSTRAINT tournaments_pkey PRIMARY KEY (id);


--
-- Name: universal_referrals universal_referrals_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.universal_referrals
    ADD CONSTRAINT universal_referrals_pkey PRIMARY KEY (id);


--
-- Name: universal_referrals uq_universal_referrals_referrer_referred; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.universal_referrals
    ADD CONSTRAINT uq_universal_referrals_referrer_referred UNIQUE (referrer_player_id, referred_player_id);


--
-- Name: idx_players_referral_code; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE UNIQUE INDEX idx_players_referral_code ON public.players USING btree (referral_code) WHERE (referral_code IS NOT NULL);


--
-- Name: idx_universal_referrals_referral_code; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_universal_referrals_referral_code ON public.universal_referrals USING btree (referral_code);


--
-- Name: ambassador_referrals ambassador_referrals_ambassador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ambassador_referrals
    ADD CONSTRAINT ambassador_referrals_ambassador_id_fkey FOREIGN KEY (ambassador_id) REFERENCES public.ambassadors(id);


--
-- Name: ambassador_referrals ambassador_referrals_referred_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ambassador_referrals
    ADD CONSTRAINT ambassador_referrals_referred_player_id_fkey FOREIGN KEY (referred_player_id) REFERENCES public.players(id);


--
-- Name: ambassadors ambassadors_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ambassadors
    ADD CONSTRAINT ambassadors_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(id);


--
-- Name: bank_settings bank_settings_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bank_settings
    ADD CONSTRAINT bank_settings_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.players(id);


--
-- Name: credit_transactions credit_transactions_admin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.credit_transactions
    ADD CONSTRAINT credit_transactions_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES public.players(id);


--
-- Name: credit_transactions credit_transactions_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.credit_transactions
    ADD CONSTRAINT credit_transactions_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(id);


--
-- Name: matches matches_player1_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.matches
    ADD CONSTRAINT matches_player1_id_fkey FOREIGN KEY (player1_id) REFERENCES public.players(id);


--
-- Name: matches matches_player2_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.matches
    ADD CONSTRAINT matches_player2_id_fkey FOREIGN KEY (player2_id) REFERENCES public.players(id);


--
-- Name: matches matches_result_submitted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.matches
    ADD CONSTRAINT matches_result_submitted_by_fkey FOREIGN KEY (result_submitted_by) REFERENCES public.players(id);


--
-- Name: matches matches_winner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.matches
    ADD CONSTRAINT matches_winner_id_fkey FOREIGN KEY (winner_id) REFERENCES public.players(id);


--
-- Name: messages messages_receiver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_receiver_id_fkey FOREIGN KEY (receiver_id) REFERENCES public.players(id);


--
-- Name: messages messages_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.players(id);


--
-- Name: notifications notifications_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(id);


--
-- Name: partner_invitations partner_invitations_invitee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_invitations
    ADD CONSTRAINT partner_invitations_invitee_id_fkey FOREIGN KEY (invitee_id) REFERENCES public.players(id);


--
-- Name: partner_invitations partner_invitations_inviter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_invitations
    ADD CONSTRAINT partner_invitations_inviter_id_fkey FOREIGN KEY (inviter_id) REFERENCES public.players(id);


--
-- Name: partner_invitations partner_invitations_tournament_entry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_invitations
    ADD CONSTRAINT partner_invitations_tournament_entry_id_fkey FOREIGN KEY (tournament_entry_id) REFERENCES public.tournaments(id);


--
-- Name: team_invitations team_invitations_invitee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.team_invitations
    ADD CONSTRAINT team_invitations_invitee_id_fkey FOREIGN KEY (invitee_id) REFERENCES public.players(id);


--
-- Name: team_invitations team_invitations_inviter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.team_invitations
    ADD CONSTRAINT team_invitations_inviter_id_fkey FOREIGN KEY (inviter_id) REFERENCES public.players(id);


--
-- Name: teams teams_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.players(id);


--
-- Name: teams teams_player1_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_player1_id_fkey FOREIGN KEY (player1_id) REFERENCES public.players(id);


--
-- Name: teams teams_player2_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_player2_id_fkey FOREIGN KEY (player2_id) REFERENCES public.players(id);


--
-- Name: tournament_instances tournament_instances_winner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournament_instances
    ADD CONSTRAINT tournament_instances_winner_id_fkey FOREIGN KEY (winner_id) REFERENCES public.players(id);


--
-- Name: tournament_matches tournament_matches_player1_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournament_matches
    ADD CONSTRAINT tournament_matches_player1_id_fkey FOREIGN KEY (player1_id) REFERENCES public.players(id);


--
-- Name: tournament_matches tournament_matches_player2_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournament_matches
    ADD CONSTRAINT tournament_matches_player2_id_fkey FOREIGN KEY (player2_id) REFERENCES public.players(id);


--
-- Name: tournament_matches tournament_matches_tournament_instance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournament_matches
    ADD CONSTRAINT tournament_matches_tournament_instance_id_fkey FOREIGN KEY (tournament_instance_id) REFERENCES public.tournament_instances(id);


--
-- Name: tournament_matches tournament_matches_winner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournament_matches
    ADD CONSTRAINT tournament_matches_winner_id_fkey FOREIGN KEY (winner_id) REFERENCES public.players(id);


--
-- Name: tournament_payouts tournament_payouts_paid_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournament_payouts
    ADD CONSTRAINT tournament_payouts_paid_by_fkey FOREIGN KEY (paid_by) REFERENCES public.players(id);


--
-- Name: tournament_payouts tournament_payouts_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournament_payouts
    ADD CONSTRAINT tournament_payouts_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(id);


--
-- Name: tournament_payouts tournament_payouts_tournament_instance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournament_payouts
    ADD CONSTRAINT tournament_payouts_tournament_instance_id_fkey FOREIGN KEY (tournament_instance_id) REFERENCES public.tournament_instances(id);


--
-- Name: tournaments tournaments_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournaments
    ADD CONSTRAINT tournaments_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(id);


--
-- Name: tournaments tournaments_tournament_instance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tournaments
    ADD CONSTRAINT tournaments_tournament_instance_id_fkey FOREIGN KEY (tournament_instance_id) REFERENCES public.tournament_instances(id);


--
-- Name: universal_referrals universal_referrals_referred_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.universal_referrals
    ADD CONSTRAINT universal_referrals_referred_player_id_fkey FOREIGN KEY (referred_player_id) REFERENCES public.players(id);


--
-- Name: universal_referrals universal_referrals_referrer_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.universal_referrals
    ADD CONSTRAINT universal_referrals_referrer_player_id_fkey FOREIGN KEY (referrer_player_id) REFERENCES public.players(id);


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO neon_superuser WITH GRANT OPTION;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLES TO neon_superuser WITH GRANT OPTION;


--
-- PostgreSQL database dump complete
--


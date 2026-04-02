-- V2 Meta Automation Stack: Supabase Schema
-- Kopieer en plak dit in de Supabase SQL Editor (Dashboard > SQL Editor)
-- Voer alle queries 1 voor 1 uit om de tabellen in te richten.

-- Table 1: Daily Instagram metrics
CREATE TABLE IF NOT EXISTS instagram_daily (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  handle TEXT NOT NULL,
  followers INT,
  followers_change INT DEFAULT 0,
  engagement_rate DECIMAL(5,2),
  posts_count INT,
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_instagram_daily_date ON instagram_daily(date);

-- Table 2: Meta campaigns
CREATE TABLE IF NOT EXISTS meta_campaigns_daily (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  campaign_name TEXT,
  meta_id TEXT,
  impressions INT,
  clicks INT,
  spend DECIMAL(10,2),
  leads INT,
  cpl DECIMAL(10,2),
  status TEXT CHECK (status IN ('green', 'yellow', 'red')),
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_meta_date_cpl ON meta_campaigns_daily(date, cpl);

-- Table 3: Competitor intelligence
CREATE TABLE IF NOT EXISTS competitor_intelligence (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  week_of DATE NOT NULL,
  competitor_handle TEXT,
  followers INT,
  follower_growth_percent DECIMAL(5,2),
  engagement_rate DECIMAL(5,2),
  posts_this_week INT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Table 4: Alerts
CREATE TABLE IF NOT EXISTS alerts (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  alert_type TEXT,
  campaign_id TEXT,
  value DECIMAL(10,2),
  threshold DECIMAL(10,2),
  severity TEXT CHECK (severity IN ('critical', 'high', 'medium')),
  resolved BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Table 5: CPL → Recruitment mapping
CREATE TABLE IF NOT EXISTS cpl_recruitment_mapping (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  campaign_id TEXT,
  cpl_eur DECIMAL(10,2),
  job_title TEXT,
  target_audience TEXT,
  jobdigger_conversion_rate DECIMAL(5,2),
  recruitment_roi DECIMAL(5,2),
  recommended_action TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

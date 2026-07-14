CREATE DATABASE IF NOT EXISTS weibo_system DEFAULT CHARSET utf8mb4;
USE weibo_system;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(64) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'analyst',
  is_active TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_config (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  config_key VARCHAR(64) UNIQUE NOT NULL,
  config_value JSON NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  event_name VARCHAR(255) NOT NULL,
  summary TEXT NULL,
  risk_level VARCHAR(10) NULL,
  start_time DATETIME NULL,
  end_time DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weibos (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  weibo_id VARCHAR(64) NOT NULL,
  event_id BIGINT NULL,
  content TEXT NOT NULL,
  url VARCHAR(512) NULL,
  user_name VARCHAR(128) NULL,
  published_at DATETIME NULL,
  collected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  sentiment_label VARCHAR(20) NULL,
  sentiment_score DECIMAL(6,4) NULL,
  UNIQUE KEY uk_weibo_id(weibo_id),
  INDEX idx_event_id(event_id),
  FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS crawl_tasks (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  task_name VARCHAR(128) NOT NULL,
  keywords VARCHAR(512) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  collector_name VARCHAR(64) NOT NULL,
  started_at DATETIME NULL,
  finished_at DATETIME NULL,
  created_by BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS analysis_history (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  event_id BIGINT NOT NULL,
  snapshot_json JSON NOT NULL,
  exported_count INT NOT NULL DEFAULT 0,
  created_by BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (event_id) REFERENCES events(id),
  FOREIGN KEY (created_by) REFERENCES users(id)
);

-- admin / admin123 (pbkdf2_sha256)
INSERT INTO users(username, password_hash, role, is_active)
SELECT
  'admin',
  '$pbkdf2-sha256$29000$L6V0LoVw7r1Xas05xzhHaA$P2J5.PnEIu5tbsOgR6KYf.zpu7mbcS9dOcIAdgXraMA',
  'admin',
  1
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username='admin');

INSERT INTO system_config(config_key, config_value)
SELECT 'collector_active', JSON_OBJECT('name','real_collector','endpoint','http://127.0.0.1:9001','enabled',true)
WHERE NOT EXISTS (SELECT 1 FROM system_config WHERE config_key='collector_active');

INSERT INTO system_config(config_key, config_value)
SELECT 'model_active', JSON_OBJECT('name','real_sentiment_model','version','v1.0.0','enabled',true)
WHERE NOT EXISTS (SELECT 1 FROM system_config WHERE config_key='model_active');
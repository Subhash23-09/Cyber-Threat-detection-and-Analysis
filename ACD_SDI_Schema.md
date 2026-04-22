# MySQL Database Schema: ACD-SDI Platform
This document outlines the table structures for the Autonomous Cyber Defense & Security Decision Intelligence (ACD-SDI) platform.

## 1. Core Tables
### security_signals
Stores the output of the Signal Engine (Step 2 and Agents).
*   **id**: INT (Primary Key)
*   **attack_type**: VARCHAR(255)
*   **anomaly_score**: ENUM('HIGH','MEDIUM','LOW','INFO')
*   **confidence**: DECIMAL(5,2)
*   **risk_level**: ENUM('CRITICAL','HIGH','MEDIUM','LOW')
*   **mitre_id**: VARCHAR(50) (e.g., T1110)
*   **source_ip**: VARCHAR(50)
*   **target_user**: VARCHAR(255)
*   **event_count**: INT
*   **reasoning**: TEXT
*   **context_json**: JSON
*   **timestamp**: TIMESTAMP

### incident_memory
Stores the long-term memory of confirmed incidents (Step 10).
*   **id**: INT (Primary Key)
*   **entity_type**: ENUM('ACTOR', 'TARGET', 'ACTION')
*   **entity_value**: VARCHAR(255) (e.g., IP address or Attack Name)
*   **incident_data**: JSON (Full snapshot of the confirmed case)
*   **feedback_score**: INT
*   **analyst_notes**: TEXT
*   **last_seen**: TIMESTAMP

### attack_storylines
Stores the generated narrative reports (Step 6).
*   **id**: INT (Primary Key)
*   **title**: VARCHAR(255)
*   **description**: TEXT
*   **mitre_techniques**: JSON
*   **involved_ips**: JSON
*   **involved_users**: JSON
*   **severity**: ENUM('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')
*   **storyline_markdown**: TEXT
*   **created_at**: TIMESTAMP

## 2. Ingestion & Pre-processing
### raw_logs
Archives raw log entries.
*   **id**: INT (Primary Key)
*   **timestamp**: DATETIME
*   **source_system**: VARCHAR(100)
*   **raw_message**: TEXT
*   **ingested_at**: TIMESTAMP

### parsed_templates
Stores log patterns identified by Drain3.
*   **id**: INT (Primary Key)
*   **template_id**: INT
*   **template_string**: TEXT
*   **source_system**: VARCHAR(100)
*   **last_seen**: TIMESTAMP

## 3. Assets & Identity
### users
System administrators and analysts.
*   **id**: INT (Primary Key)
*   **username**: VARCHAR(80)
*   **email**: VARCHAR(120)
*   **password_hash**: VARCHAR(128)
*   **created_at**: DATETIME

### assets
Enrichment data for scoring logic.
*   **username**: VARCHAR(255) (Primary Key)
*   **criticality**: ENUM('CRITICAL','HIGH','MEDIUM','LOW')
*   **mfa_status**: TINYINT(1)
*   **privilege_level**: VARCHAR(50)
*   **department**: VARCHAR(100)

## 4. Statistical Anomaly Detection (New)
### daily_stats
Tracks daily usage stats per user/IP for learning normal behavior.
*   **id**: INT (Primary Key)
*   **date**: DATE
*   **entity_type**: ENUM('USER', 'IP')
*   **entity_val**: VARCHAR(255)
*   **event_count**: INT
*   **created_at**: TIMESTAMP

### user_baselines
Stores calculated statistical profiles (Mean & Std Dev) for users/IPs.
*   **id**: INT (Primary Key)
*   **entity_type**: ENUM('USER', 'IP')
*   **entity_val**: VARCHAR(255)
*   **avg_events_per_day**: FLOAT
*   **std_dev_events**: FLOAT
*   **last_updated**: TIMESTAMP

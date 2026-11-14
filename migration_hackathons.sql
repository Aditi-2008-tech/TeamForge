-- TeamForge: university profile + admin-managed hackathon catalogue
-- BACK UP your database before running this migration.
-- Run once against the existing teamforge database.

ALTER TABLE profiles
    ADD COLUMN university VARCHAR(150) NULL AFTER user_id;

CREATE TABLE hackathons (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    organizer VARCHAR(150) NULL,
    description TEXT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    registration_url VARCHAR(500) NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_hackathons_start_date (start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

ALTER TABLE projects
    ADD COLUMN hackathon_id INT NULL AFTER project_type,
    ADD KEY idx_projects_hackathon_id (hackathon_id),
    ADD CONSTRAINT fk_projects_hackathons
        FOREIGN KEY (hackathon_id) REFERENCES hackathons(id)
        ON DELETE SET NULL;

-- Existing users remain valid. They can fill in university in Edit Profile.
-- Existing projects remain independent because hackathon_id defaults to NULL.

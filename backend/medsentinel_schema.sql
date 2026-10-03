-- ==============================================================================
-- MedSentinel Healthcare Intelligence Platform - MySQL Database Schema & Seed Data
-- Target Database: MySQL 8.0+
-- Engine: InnoDB
-- Character Set: utf8mb4
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS `medsentinel` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `medsentinel`;

SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------------------------
-- 1. Table: hospitals
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `hospitals`;
CREATE TABLE `hospitals` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(200) NOT NULL,
  `location` VARCHAR(200) DEFAULT NULL,
  `specialization` VARCHAR(200) DEFAULT NULL,
  `rating` FLOAT DEFAULT 0.0,
  `distance` FLOAT DEFAULT 0.0,
  `cost_range` VARCHAR(100) DEFAULT NULL,
  `schemes` TEXT DEFAULT NULL,
  `insurance_accepted` TEXT DEFAULT NULL,
  `is_available` TINYINT(1) NOT NULL DEFAULT 1,
  `image_url` VARCHAR(255) DEFAULT NULL,
  `facilities` TEXT DEFAULT NULL,
  `description` TEXT DEFAULT NULL,
  `phone` VARCHAR(50) DEFAULT NULL,
  `email` VARCHAR(100) DEFAULT NULL,
  INDEX `ix_hospitals_name` (`name`),
  INDEX `ix_hospitals_location` (`location`),
  INDEX `ix_hospitals_specialization` (`specialization`),
  INDEX `ix_hospitals_rating` (`rating`),
  INDEX `ix_hospitals_distance` (`distance`),
  INDEX `ix_hospitals_loc_spec` (`location`, `specialization`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 2. Table: insurances
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `insurances`;
CREATE TABLE `insurances` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(200) NOT NULL UNIQUE,
  `provider` VARCHAR(100) NOT NULL,
  `coverage_amount` FLOAT NOT NULL,
  `premium_monthly` FLOAT NOT NULL,
  `premium_annual` FLOAT NOT NULL,
  `cashless_network` INT DEFAULT 0,
  `claim_settlement_days` INT DEFAULT 3,
  `rating` FLOAT DEFAULT 0.0,
  `features` TEXT DEFAULT NULL,
  `inclusions` TEXT DEFAULT NULL,
  `exclusions` TEXT DEFAULT NULL,
  `coverage_type` VARCHAR(50) DEFAULT NULL,
  `waiting_period_days` INT DEFAULT 30,
  `eligibility_age_min` INT DEFAULT 18,
  `eligibility_age_max` INT DEFAULT 65,
  INDEX `ix_insurances_name` (`name`),
  INDEX `ix_insurances_provider` (`provider`),
  INDEX `ix_insurances_provider_type` (`provider`, `coverage_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 3. Table: users
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(150) NOT NULL UNIQUE,
  `phone` VARCHAR(20) DEFAULT NULL,
  `hashed_password` VARCHAR(255) NOT NULL,
  `role` VARCHAR(50) NOT NULL DEFAULT 'USER',
  `hospital_id` INT DEFAULT NULL,
  `insurance_id` INT DEFAULT NULL,
  `blood_group` VARCHAR(20) DEFAULT NULL,
  `allergies` TEXT DEFAULT NULL,
  `emergency_contact` VARCHAR(50) DEFAULT NULL,
  `schemes` TEXT DEFAULT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `ix_users_email` (`email`),
  INDEX `ix_users_role` (`role`),
  INDEX `ix_users_email_role` (`email`, `role`),
  CONSTRAINT `fk_users_hospital` FOREIGN KEY (`hospital_id`) REFERENCES `hospitals` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_users_insurance` FOREIGN KEY (`insurance_id`) REFERENCES `insurances` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 4. Table: schemes
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `schemes`;
CREATE TABLE `schemes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(200) NOT NULL UNIQUE,
  `description` TEXT DEFAULT NULL,
  `coverage` VARCHAR(100) DEFAULT NULL,
  `eligibility` TEXT DEFAULT NULL,
  `benefits` TEXT DEFAULT NULL,
  `category` VARCHAR(100) DEFAULT NULL,
  `max_income` VARCHAR(100) DEFAULT NULL,
  `type` VARCHAR(50) DEFAULT NULL,
  INDEX `ix_schemes_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 5. Table: user_insurances
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `user_insurances`;
CREATE TABLE `user_insurances` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `insurance_id` INT NOT NULL,
  `policy_number` VARCHAR(100) NOT NULL UNIQUE,
  `start_date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `end_date` DATETIME DEFAULT NULL,
  `status` VARCHAR(50) DEFAULT 'active',
  `sum_insured` FLOAT NOT NULL,
  `dependents` VARCHAR(255) DEFAULT NULL,
  INDEX `ix_user_insurances_user_id` (`user_id`),
  INDEX `ix_user_insurances_insurance_id` (`insurance_id`),
  INDEX `ix_user_insurances_policy_number` (`policy_number`),
  INDEX `ix_user_insurances_user_status` (`user_id`, `status`),
  CONSTRAINT `fk_user_insurances_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_user_insurances_insurance` FOREIGN KEY (`insurance_id`) REFERENCES `insurances` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 6. Table: insurance_claims
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `insurance_claims`;
CREATE TABLE `insurance_claims` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `insurance_id` INT DEFAULT NULL,
  `hospital_id` INT DEFAULT NULL,
  `claim_amount` FLOAT NOT NULL,
  `claim_date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `claim_status` VARCHAR(50) NOT NULL DEFAULT 'SUBMITTED',
  `claim_description` TEXT DEFAULT NULL,
  `documents` TEXT DEFAULT NULL,
  INDEX `ix_insurance_claims_user_id` (`user_id`),
  INDEX `ix_insurance_claims_insurance_id` (`insurance_id`),
  INDEX `ix_insurance_claims_hospital_id` (`hospital_id`),
  INDEX `ix_insurance_claims_claim_status` (`claim_status`),
  INDEX `ix_insurance_claims_claim_date` (`claim_date`),
  INDEX `ix_insurance_claims_user_status` (`user_id`, `claim_status`),
  INDEX `ix_insurance_claims_status_date` (`claim_status`, `claim_date`),
  CONSTRAINT `fk_insurance_claims_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_insurance_claims_insurance` FOREIGN KEY (`insurance_id`) REFERENCES `insurances` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_insurance_claims_hospital` FOREIGN KEY (`hospital_id`) REFERENCES `hospitals` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 7. Table: claim_status_history
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `claim_status_history`;
CREATE TABLE `claim_status_history` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `claim_id` INT NOT NULL,
  `previous_status` VARCHAR(50) DEFAULT NULL,
  `new_status` VARCHAR(50) NOT NULL,
  `updated_by_id` INT DEFAULT NULL,
  `comment` TEXT DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `ix_claim_status_history_claim_id` (`claim_id`),
  INDEX `ix_claim_status_history_created_at` (`created_at`),
  INDEX `ix_claim_status_history_claim_date` (`claim_id`, `created_at`),
  CONSTRAINT `fk_claim_status_history_claim` FOREIGN KEY (`claim_id`) REFERENCES `insurance_claims` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_claim_status_history_user` FOREIGN KEY (`updated_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 8. Table: appointments
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `appointments`;
CREATE TABLE `appointments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT DEFAULT NULL,
  `hospital_id` INT DEFAULT NULL,
  `name` VARCHAR(100) NOT NULL,
  `phone` VARCHAR(20) NOT NULL,
  `email` VARCHAR(150) NOT NULL,
  `preferred_date` VARCHAR(50) NOT NULL,
  `preferred_time` VARCHAR(50) NOT NULL,
  `department` VARCHAR(100) NOT NULL,
  `reason` TEXT DEFAULT NULL,
  `status` VARCHAR(50) NOT NULL DEFAULT 'CONFIRMED',
  `notes` TEXT DEFAULT NULL,
  `cancelled_at` DATETIME DEFAULT NULL,
  `cancellation_reason` VARCHAR(255) DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `ix_appointments_user_id` (`user_id`),
  INDEX `ix_appointments_hospital_id` (`hospital_id`),
  INDEX `ix_appointments_status` (`status`),
  INDEX `ix_appointments_preferred_date` (`preferred_date`),
  INDEX `ix_appointments_department` (`department`),
  INDEX `ix_appointments_user_status` (`user_id`, `status`),
  INDEX `ix_appointments_hospital_status` (`hospital_id`, `status`),
  INDEX `ix_appointments_date_dept` (`preferred_date`, `department`),
  CONSTRAINT `fk_appointments_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_appointments_hospital` FOREIGN KEY (`hospital_id`) REFERENCES `hospitals` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 9. Table: user_documents
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `user_documents`;
CREATE TABLE `user_documents` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `doc_type` VARCHAR(100) DEFAULT 'Other',
  `filename` VARCHAR(255) NOT NULL,
  `original_name` VARCHAR(255) NOT NULL,
  `file_path` VARCHAR(500) NOT NULL,
  `file_type` VARCHAR(100) NOT NULL,
  `file_size` INT DEFAULT 0,
  `upload_date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `status` VARCHAR(50) NOT NULL DEFAULT 'PENDING',
  `verified_by_id` INT DEFAULT NULL,
  `verified_at` DATETIME DEFAULT NULL,
  `rejection_reason` TEXT DEFAULT NULL,
  INDEX `ix_user_documents_user_id` (`user_id`),
  INDEX `ix_user_documents_doc_type` (`doc_type`),
  INDEX `ix_user_documents_status` (`status`),
  INDEX `ix_user_documents_upload_date` (`upload_date`),
  INDEX `ix_user_documents_user_status` (`user_id`, `status`),
  INDEX `ix_user_documents_user_type` (`user_id`, `doc_type`),
  CONSTRAINT `fk_user_documents_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_user_documents_verifier` FOREIGN KEY (`verified_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 10. Table: notifications
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `notifications`;
CREATE TABLE `notifications` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `title` VARCHAR(200) NOT NULL,
  `message` TEXT NOT NULL,
  `type` VARCHAR(50) DEFAULT 'info',
  `is_read` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `ix_notifications_user_id` (`user_id`),
  INDEX `ix_notifications_is_read` (`is_read`),
  INDEX `ix_notifications_created_at` (`created_at`),
  INDEX `ix_notifications_user_read` (`user_id`, `is_read`),
  INDEX `ix_notifications_user_created` (`user_id`, `created_at`),
  CONSTRAINT `fk_notifications_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 11. Table: saved_items
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `saved_items`;
CREATE TABLE `saved_items` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `hospital_id` INT NOT NULL,
  `saved_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `ix_saved_items_user_id` (`user_id`),
  INDEX `ix_saved_items_hospital_id` (`hospital_id`),
  INDEX `ix_saved_items_user_hospital` (`user_id`, `hospital_id`),
  CONSTRAINT `fk_saved_items_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_saved_items_hospital` FOREIGN KEY (`hospital_id`) REFERENCES `hospitals` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 12. Table: refresh_tokens
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `refresh_tokens`;
CREATE TABLE `refresh_tokens` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `token` VARCHAR(500) NOT NULL UNIQUE,
  `expires_at` DATETIME NOT NULL,
  `revoked` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX `ix_refresh_tokens_user_id` (`user_id`),
  INDEX `ix_refresh_tokens_token` (`token`),
  INDEX `ix_refresh_tokens_user_token` (`user_id`, `token`),
  CONSTRAINT `fk_refresh_tokens_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 13. Table: otp_codes
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `otp_codes`;
CREATE TABLE `otp_codes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `phone` VARCHAR(20) NOT NULL,
  `code` VARCHAR(6) NOT NULL,
  `expires_at` DATETIME NOT NULL,
  `attempts` INT NOT NULL DEFAULT 0,
  `is_verified` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX `ix_otp_codes_phone` (`phone`),
  INDEX `ix_otp_codes_phone_verified` (`phone`, `is_verified`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 14. Table: ai_conversations
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `ai_conversations`;
CREATE TABLE `ai_conversations` (
  `id` VARCHAR(36) PRIMARY KEY,
  `user_id` INT NOT NULL,
  `title` VARCHAR(200) DEFAULT 'New Medical Consultation',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `ix_ai_conversations_user_id` (`user_id`),
  INDEX `ix_ai_conversations_created_at` (`created_at`),
  INDEX `ix_ai_conversations_user_created` (`user_id`, `created_at`),
  CONSTRAINT `fk_ai_conversations_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 15. Table: ai_messages
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `ai_messages`;
CREATE TABLE `ai_messages` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `conversation_id` VARCHAR(36) NOT NULL,
  `sender` VARCHAR(20) NOT NULL,
  `content` TEXT NOT NULL,
  `tools_used` TEXT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX `ix_ai_messages_conversation_id` (`conversation_id`),
  INDEX `ix_ai_messages_created_at` (`created_at`),
  INDEX `ix_ai_messages_conv_created` (`conversation_id`, `created_at`),
  CONSTRAINT `fk_ai_messages_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `ai_conversations` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 16. Table: admin_audit_logs
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `admin_audit_logs`;
CREATE TABLE `admin_audit_logs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `admin_user_id` INT DEFAULT NULL,
  `action` VARCHAR(100) NOT NULL,
  `resource_type` VARCHAR(50) NOT NULL,
  `resource_id` VARCHAR(50) DEFAULT NULL,
  `old_value` TEXT DEFAULT NULL,
  `new_value` TEXT DEFAULT NULL,
  `ip_address` VARCHAR(50) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX `ix_admin_audit_logs_admin_user_id` (`admin_user_id`),
  INDEX `ix_admin_audit_logs_action` (`action`),
  INDEX `ix_admin_audit_logs_resource_type` (`resource_type`),
  INDEX `ix_admin_audit_logs_created_at` (`created_at`),
  INDEX `ix_admin_audit_logs_action_resource` (`action`, `resource_type`),
  INDEX `ix_admin_audit_logs_admin_created` (`admin_user_id`, `created_at`),
  CONSTRAINT `fk_admin_audit_logs_admin` FOREIGN KEY (`admin_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- ==============================================================================
-- INITIAL SEED DATA
-- ==============================================================================

-- 1. Insert Hospitals
INSERT INTO `hospitals` (`id`, `name`, `location`, `specialization`, `rating`, `distance`, `cost_range`, `schemes`, `insurance_accepted`, `is_available`, `facilities`, `description`, `phone`, `email`) VALUES
(1, 'City General Hospital', 'Bengaluru Central, Karnataka', 'Multispeciality, Emergency Care, Cardiology', 4.8, 2.4, '₹45,000 - ₹85,000', 'Ayushman Bharat, MJPJAY, State Health Card', 'Care Supreme, Star Health, Optima Secure', 1, '24/7 Trauma Care, 32-Bed ICU, Cath Lab, MRI & CT Diagnostics, Blood Bank', 'Premier multispeciality center offering tertiary healthcare and high-volume emergency trauma response.', '+91-80-2222-1111', 'contact@citygeneral.org'),
(2, 'Apollo Multispeciality Hospital', 'Bannerghatta Road, Bengaluru', 'Cardiology, Oncology, Organ Transplants', 4.9, 4.1, '₹90,000 - ₹1,80,000', 'Ayushman Bharat, CGHS, ESIC', 'Care Supreme, Optima Secure, Star Health', 1, 'Robotic Surgery Suites, Comprehensive Cancer Center, 64-Slice Cardiac CT, Advanced Neonatal ICU', 'Internationally accredited hospital with world-renowned cardiology and organ transplant surgeons.', '+91-80-2630-4050', 'info@apollomulti.in'),
(3, 'St. Jude Medical Research Institute', 'Indiranagar, Bengaluru', 'Neurology, Neurosurgery, Orthopedics', 4.7, 5.8, '₹60,000 - ₹1,10,000', 'Ayushman Bharat, MJPJAY', 'Optima Secure, Star Health', 1, 'Neuro Navigation System, High-Field 3T MRI, Joint Replacement Center, Dedicated Stroke Unit', 'Leading center of excellence in complex neurosurgical procedures and joint replacement surgeries.', '+91-80-4100-7890', 'care@stjudemedical.org'),
(4, 'Fortis HealthCare Super Speciality', 'Cunningham Road, Bengaluru', 'Cardiology, Nephrology, Urology', 4.6, 3.2, '₹80,000 - ₹1,50,000', 'Ayushman Bharat, CGHS', 'Care Supreme, Optima Secure', 1, 'Hemodialysis Wing, Renal Transplant Unit, Digital Cath Lab, 24/7 Pharmacy', 'Advanced renal care and cardiovascular treatment facility with rapid diagnosis support.', '+91-80-4011-1222', 'support@fortisblr.com'),
(5, 'Manipal Comprehensive Hospital', 'Old Airport Road, Bengaluru', 'Pediatrics, Oncology, Gastrointestinal Surgery', 4.8, 6.5, '₹70,000 - ₹1,35,000', 'Ayushman Bharat, MJPJAY, ESIC', 'Care Supreme, Star Health, Optima Secure', 1, 'Pediatric ICU, Bone Marrow Transplant Unit, Endoscopy Suites, Genetic Testing Lab', 'Distinguished hospital group delivering patient-centric cancer care and pediatric super-specialties.', '+91-80-2502-4444', 'info@manipalhospitals.com');

-- 2. Insert Insurances
INSERT INTO `insurances` (`id`, `name`, `provider`, `coverage_amount`, `premium_monthly`, `premium_annual`, `cashless_network`, `claim_settlement_days`, `rating`, `features`, `inclusions`, `exclusions`, `coverage_type`, `waiting_period_days`, `eligibility_age_min`, `eligibility_age_max`) VALUES
(1, 'Care Supreme Comprehensive Plan', 'Care Health Insurance', 1000000.0, 850.0, 9800.0, 21000, 2, 4.9, 'Unlimited Automatic Recharge, 500% No Claim Bonus, OPD Consultations, AYUSH Cover, No Room Rent Capping', 'In-patient hospitalization, Day care treatments, Pre & Post hospitalization (60/180 days), Ambulance charges', 'Cosmetic surgeries, Self-inflicted injuries, Drug abuse treatments', 'Comprehensive', 30, 18, 75),
(2, 'Optima Secure Smart Health', 'HDFC ERGO', 1500000.0, 1250.0, 14200.0, 14000, 1, 4.8, '2X Coverage from Day 1, Plus Benefit (100% bonus in 2 yrs), Global Emergency Cover, Zero Deductibles', 'All day-care surgeries, Robotic surgery, Organ donor expenses, Home healthcare', 'Unproven treatments, Rest cure and rehabilitation admissions', 'Family Floater', 30, 18, 65),
(3, 'Star Comprehensive Health Plan', 'Star Health Insurance', 750000.0, 680.0, 7800.0, 13000, 3, 4.6, 'Maternity cover for up to 2 deliveries, New-born baby cover, Free annual health check-ups, Air ambulance cover', 'Hospital room rent up to single private room, ICU charges, Surgeon & anesthetist fees', 'Dental cosmetic procedures, Weight control treatments', 'Individual', 30, 18, 65);

-- 3. Insert Government Schemes
INSERT INTO `schemes` (`id`, `name`, `description`, `coverage`, `eligibility`, `benefits`, `category`, `max_income`, `type`) VALUES
(1, 'Ayushman Bharat (PM-JAY)', 'World''s largest government-funded health assurance scheme providing secondary and tertiary care hospitalization across empanelled public and private hospitals.', '₹5,00,000 / family / year', 'Low-income households, BPL card holders, SECC identified families with no earning adult member.', '100% cashless hospitalization, covers 3 days pre-hospitalization and 15 days post-hospitalization medications.', 'National Government', '₹2,50,000 / year', 'government'),
(2, 'Mahatma Jyotirao Phule Jan Arogya Yojana (MJPJAY)', 'Flagship health scheme of the Government of Maharashtra offering comprehensive financial cover for serious illnesses requiring surgery and hospitalization.', '₹1,50,000 - ₹5,00,000 / family', 'Families holding Yellow or Orange Ration Cards, Antyodaya Anna Yojana (AAY) beneficiaries.', '996 recognized surgical procedures, renal transplants, cardiology surgeries, oncology cycles.', 'State Government', '₹1,00,000 / year', 'state'),
(3, 'Employees'' State Insurance (ESIC)', 'Self-financing social security and health insurance scheme for Indian workers earning monthly wages up to ₹21,000.', 'Full Comprehensive Medical Benefit', 'Organized workforce employees with ESIC registration and monthly statutory contributions.', 'Unlimited medical coverage for worker and dependents from day one of insurable employment, plus sickness cash benefits.', 'Social Security', '₹2,52,000 / year', 'social_security'),
(4, 'Central Government Health Scheme (CGHS)', 'Healthcare facility for Central Government employees, pensioners, and their dependents across allopathic and AYUSH systems.', 'Comprehensive Medical Care & Hospitalization', 'Central government employees, retired defense personnel, members of parliament.', 'Dispensary services, cashless indoor treatment at CGHS empanelled hospitals, cancer & cardiac care.', 'Central Government', 'N/A', 'central');

-- 4. Insert RBAC Users (Bcrypt hashed passwords)
INSERT INTO `users` (`id`, `name`, `email`, `phone`, `hashed_password`, `role`, `hospital_id`, `insurance_id`, `blood_group`, `allergies`, `emergency_contact`, `schemes`, `is_active`) VALUES
(1, 'Alex Demo Patient', 'demo@medsentinel.com', '+91 98765 43210', '$2b$12$0t1aL5aDqfH2/n2yv9uIHeh9o1lF3v8uY4Q6F9n9H3f1l7uF3v8uY', 'USER', NULL, NULL, 'O+', 'Penicillin, Peanuts', '+91 91234 56789', 'Ayushman Bharat, MJPJAY', 1),
(2, 'Dr. Sarah Hospital Director', 'hospitaladmin@medsentinel.com', '+91 98765 11111', '$2b$12$0t1aL5aDqfH2/n2yv9uIHeh9o1lF3v8uY4Q6F9n9H3f1l7uF3v8uY', 'HOSPITAL_ADMIN', 1, NULL, NULL, NULL, NULL, NULL, 1),
(3, 'Marcus Claim Underwriter', 'insuranceadmin@medsentinel.com', '+91 98765 22222', '$2b$12$0t1aL5aDqfH2/n2yv9uIHeh9o1lF3v8uY4Q6F9n9H3f1l7uF3v8uY', 'INSURANCE_ADMIN', NULL, 1, NULL, NULL, NULL, NULL, 1),
(4, 'Chief Platform Admin', 'superadmin@medsentinel.com', '+91 98765 99999', '$2b$12$0t1aL5aDqfH2/n2yv9uIHeh9o1lF3v8uY4Q6F9n9H3f1l7uF3v8uY', 'SUPER_ADMIN', NULL, NULL, NULL, NULL, NULL, NULL, 1);

-- 5. Insert Sample User Insurance Enrollment
INSERT INTO `user_insurances` (`id`, `user_id`, `insurance_id`, `policy_number`, `start_date`, `status`, `sum_insured`, `dependents`) VALUES
(1, 1, 1, 'MS-POL-2026-0091', CURRENT_TIMESTAMP, 'active', 1000000.0, 'Self + Spouse');

-- 6. Insert Sample Insurance Claim
INSERT INTO `insurance_claims` (`id`, `user_id`, `insurance_id`, `hospital_id`, `claim_amount`, `claim_date`, `claim_status`, `claim_description`) VALUES
(1, 1, 1, 1, 65000.0, CURRENT_TIMESTAMP, 'UNDER_REVIEW', 'Inpatient hospitalization for laparoscopic appendectomy surgery.');

-- 7. Insert Claim Status Timeline History
INSERT INTO `claim_status_history` (`id`, `claim_id`, `previous_status`, `new_status`, `updated_by_id`, `comment`, `created_at`) VALUES
(1, 1, NULL, 'SUBMITTED', 1, 'Claim submitted by patient with hospital discharge slip.', DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 2 DAY)),
(2, 1, 'SUBMITTED', 'UNDER_REVIEW', 3, 'Medical bills and surgical records verified by insurance underwriter.', CURRENT_TIMESTAMP);

-- 8. Insert Sample Notification
INSERT INTO `notifications` (`id`, `user_id`, `title`, `message`, `type`, `is_read`, `created_at`) VALUES
(1, 1, 'Welcome to MedSentinel 2.2', 'Your MySQL-powered health intelligence dashboard with AI Assistant is ready.', 'info', 0, CURRENT_TIMESTAMP);

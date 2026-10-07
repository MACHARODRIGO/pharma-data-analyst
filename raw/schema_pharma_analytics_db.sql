-- ============================================================
-- PHARMA ANALYTICS DB — Schema Reference Script
-- Compatible with MySQL 8.0+ / MySQL Workbench
-- Portfolio database for the Pastela Pharmaceuticals
-- pharmacovigilance analytics project.
--
-- Tables: Doctors, Medications, Patients,
--         Treatments, Adverse_Events
--
-- Adapted (and translated to English) from the reference
-- farmacovigilancia_db schema. This script defines the DDL
-- only -- the ~84,000 rows of synthetic data live as CSV
-- files in this same folder (doctors.csv, medications.csv,
-- patients.csv, treatments.csv, adverse_events.csv) and are
-- meant to be loaded either:
--   (a) into a local SQLite DB on the fly, from the project
--       notebooks, via pandas + SQLAlchemy (no server needed), or
--   (b) into a real MySQL instance with LOAD DATA INFILE, using
--       the table definitions below.
-- ============================================================

DROP DATABASE IF EXISTS pharma_analytics_db;

CREATE DATABASE pharma_analytics_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE pharma_analytics_db;

-- ============================================================
-- DDL — Table creation (parents before children)
-- ============================================================

CREATE TABLE Doctors (
    doctor_id      INT          NOT NULL AUTO_INCREMENT,
    first_name     VARCHAR(100) NOT NULL,
    last_name      VARCHAR(100) NOT NULL,
    specialty      VARCHAR(100) NOT NULL,
    license_number VARCHAR(20)  NOT NULL,
    hospital       VARCHAR(150) NOT NULL,
    PRIMARY KEY (doctor_id),
    CONSTRAINT uq_license_number UNIQUE (license_number)
);

CREATE TABLE Medications (
    medication_id        INT           NOT NULL AUTO_INCREMENT,
    brand_name           VARCHAR(150)  NOT NULL,
    active_ingredient    VARCHAR(150)  NOT NULL,
    manufacturer         VARCHAR(100)  NOT NULL,
    pharmaceutical_form  VARCHAR(50)   NOT NULL,
    concentration_mg     DECIMAL(10,4) NOT NULL,
    who_atc_category     VARCHAR(150)  NOT NULL,
    requires_prescription TINYINT(1)   NOT NULL DEFAULT 1,
    PRIMARY KEY (medication_id),
    CONSTRAINT chk_concentration CHECK (concentration_mg > 0)
);

CREATE TABLE Patients (
    patient_id        INT          NOT NULL AUTO_INCREMENT,
    first_name        VARCHAR(100) NOT NULL,
    last_name         VARCHAR(100) NOT NULL,
    birth_date        DATE         NOT NULL,
    sex               CHAR(1)      NOT NULL,
    weight_kg         DECIMAL(5,2) NOT NULL,
    height_cm         INT          NOT NULL,
    blood_type        VARCHAR(5)   NOT NULL,
    registration_date DATE         NOT NULL DEFAULT (CURRENT_DATE),
    PRIMARY KEY (patient_id),
    CONSTRAINT chk_sex    CHECK (sex IN ('M', 'F')),
    CONSTRAINT chk_weight CHECK (weight_kg > 0),
    CONSTRAINT chk_height CHECK (height_cm > 0)
);

CREATE TABLE Treatments (
    treatment_id   INT          NOT NULL AUTO_INCREMENT,
    patient_id     INT          NOT NULL,
    doctor_id      INT          NOT NULL,
    medication_id  INT          NOT NULL,
    start_date     DATE         NOT NULL,
    end_date       DATE,
    dose_mg        DECIMAL(10,4) NOT NULL,
    frequency      VARCHAR(50)  NOT NULL,
    route          VARCHAR(50)  NOT NULL DEFAULT 'Oral',
    indication     VARCHAR(200) NOT NULL,
    status         VARCHAR(20)  NOT NULL DEFAULT 'Active',
    PRIMARY KEY (treatment_id),
    CONSTRAINT chk_dose   CHECK (dose_mg > 0),
    CONSTRAINT chk_status CHECK (status IN ('Active', 'Completed', 'Suspended')),
    CONSTRAINT fk_trt_patient    FOREIGN KEY (patient_id)    REFERENCES Patients(patient_id),
    CONSTRAINT fk_trt_doctor     FOREIGN KEY (doctor_id)     REFERENCES Doctors(doctor_id),
    CONSTRAINT fk_trt_medication FOREIGN KEY (medication_id) REFERENCES Medications(medication_id)
);

CREATE TABLE Adverse_Events (
    event_id                 INT          NOT NULL AUTO_INCREMENT,
    treatment_id              INT          NOT NULL,
    patient_id                INT          NOT NULL,
    event_date                DATE         NOT NULL,
    description                TEXT         NOT NULL,
    severity                   VARCHAR(20)  NOT NULL,
    reaction_type              VARCHAR(100) NOT NULL,
    required_hospitalization  TINYINT(1)   NOT NULL DEFAULT 0,
    report_date                DATE         NOT NULL,
    resolution                 VARCHAR(30)  NOT NULL DEFAULT 'Under evaluation',
    PRIMARY KEY (event_id),
    CONSTRAINT chk_severity   CHECK (severity   IN ('Mild', 'Moderate', 'Severe', 'Fatal')),
    CONSTRAINT chk_resolution CHECK (resolution IN ('Recovered', 'Ongoing', 'Sequelae', 'Fatal', 'Under evaluation')),
    CONSTRAINT fk_ae_treatment FOREIGN KEY (treatment_id) REFERENCES Treatments(treatment_id),
    CONSTRAINT fk_ae_patient   FOREIGN KEY (patient_id)   REFERENCES Patients(patient_id)
);

-- ============================================================
-- DML — Loading the CSV files (run from MySQL Workbench with
-- local_infile enabled, adjusting the path to this folder)
-- ============================================================

-- LOAD DATA LOCAL INFILE 'raw/doctors.csv'
-- INTO TABLE Doctors
-- FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS
-- (doctor_id, first_name, last_name, specialty, license_number, hospital);

-- LOAD DATA LOCAL INFILE 'raw/medications.csv'
-- INTO TABLE Medications
-- FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS
-- (medication_id, brand_name, active_ingredient, manufacturer, pharmaceutical_form,
--  concentration_mg, who_atc_category, requires_prescription);

-- LOAD DATA LOCAL INFILE 'raw/patients.csv'
-- INTO TABLE Patients
-- FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS
-- (patient_id, first_name, last_name, birth_date, sex, weight_kg, height_cm,
--  blood_type, registration_date);

-- LOAD DATA LOCAL INFILE 'raw/treatments.csv'
-- INTO TABLE Treatments
-- FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS
-- (treatment_id, patient_id, doctor_id, medication_id, start_date, @end_date,
--  dose_mg, frequency, route, indication, status)
-- SET end_date = NULLIF(@end_date, '');

-- LOAD DATA LOCAL INFILE 'raw/adverse_events.csv'
-- INTO TABLE Adverse_Events
-- FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS
-- (event_id, treatment_id, patient_id, event_date, description, severity,
--  reaction_type, required_hospitalization, report_date, resolution);

-- ============================================================
-- Verification
-- ============================================================

-- SELECT 'Doctors'         AS table_name, COUNT(*) AS rows_count FROM Doctors
-- UNION ALL SELECT 'Medications',    COUNT(*) FROM Medications
-- UNION ALL SELECT 'Patients',       COUNT(*) FROM Patients
-- UNION ALL SELECT 'Treatments',     COUNT(*) FROM Treatments
-- UNION ALL SELECT 'Adverse_Events', COUNT(*) FROM Adverse_Events;

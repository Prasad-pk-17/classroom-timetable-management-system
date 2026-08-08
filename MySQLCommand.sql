------------0.Database name
Create database classroom_db;


------------1.Admin Table

CREATE TABLE admin (
    id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE,
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255),
    PRIMARY KEY (id)
);


------------2.Classrooms Table

CREATE TABLE classrooms (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    capacity INT NOT NULL,
    department VARCHAR(150) NOT NULL,
    PRIMARY KEY (id)
);


------------3.Subjects Table

CREATE TABLE subjects (
    id INT NOT NULL AUTO_INCREMENT,
    department VARCHAR(150) NOT NULL,
    name VARCHAR(150) NOT NULL,
    subject_code VARCHAR(50) NOT NULL,
    teacher VARCHAR(150) NOT NULL,
    num_students INT NOT NULL,
    semester VARCHAR(10) NOT NULL,
    lectures_per_week INT DEFAULT 3,
    type VARCHAR(20),
    year VARCHAR(10),
    PRIMARY KEY (id)
);


------------4.Timeslots Table

CREATE TABLE timeslots (
    id INT NOT NULL AUTO_INCREMENT,
    day VARCHAR(20) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    PRIMARY KEY (id)
);

------------5.Timetable Table

CREATE TABLE timetable (
    id INT NOT NULL AUTO_INCREMENT,
    day VARCHAR(20),
    classroom_id INT,
    subject_id INT,
    timeslot_id INT,
    PRIMARY KEY (id),
    INDEX (classroom_id),
    INDEX (subject_id),
    INDEX (timeslot_id)
);
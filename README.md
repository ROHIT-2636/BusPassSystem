# 🚌 Maharashtra Bus Pass System
> A complete web-based Student Bus Pass Management System for Maharashtra State Road Transport Corporation (MSRTC)

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Login Credentials](#login-credentials)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Tech Stack](#tech-stack)
---
## 📌 Project Overview

This system allows students to apply for bus passes online, upload documents, make payments, and download digital passes with QR codes. 
Administrators can approve/reject applications, and bus conductors can validate passes by scanning QR codes.

### Key Features
- ✅ Student Registration & Login
- ✅ Online Bus Pass Application
- ✅ Document Upload (Photo, Bonafide, Address Proof, College ID)
- ✅ Digital Pass with QR Code
- ✅ Admin Dashboard for Approval/Rejection
- ✅ Payment Status Tracking
- ✅ Application Status Tracking
- ✅ Profile Management

---

## 💻 Prerequisites

Before running this project, make sure you have the following installed:

| Software | Version | Download Link |
|----------|---------|---------------|
| Python | 3.8 or higher | [python.org](https://www.python.org/downloads/) |
| MySQL | 5.7 or higher | [mysql.com](https://dev.mysql.com/downloads/mysql/) |
| pip | Latest version | Comes with Python |
| Git | (Optional) | [git-scm.com](https://git-scm.com/) |

---

### Step 1: Clone or Download the Project

1. Click on Code button (green color)
2. Select Download ZIP
3. Extract the ZIP file
4. Open  terminal/cmd in the extracted folder or open folder in VS Code (Safe) & right click on app.py file then select 'Open in integrated terminal'.

### Step 2: Create Virtual Environment 
Windows:

python -m venv venv
venv\Scripts\activate


Mac: 
python3 -m venv venv
source venv/bin/activate


After activation, you will see (venv) at the beginning of your terminal line.

### Step 3: Install Required Packages
pip install -r requirements.txt

If requirements.txt file is not available, manually install these packages:

pip install flask==2.3.0
pip install pymysql==1.0.2
pip install werkzeug==2.3.0
pip install Pillow==9.5.0
pip install qrcode==7.4.2

To verify installation:

pip list

### Step 4: Setup MySQL Database

4.1 Start MySQL Server
    Windows:
      Open XAMPP → Start MySQL OR
      Open MySQL Workbench → Connect to local instance

   Mac/Linux:
    sudo service mysql start

4.2 Open MySQL Command Line
Using Command Line:

mysql -u root -p

(Enter your MySQL password when prompted)
Using XAMPP:

Open phpMyAdmin at http://localhost/phpmyadmin

Click on SQL tab


4.3 Create Database

CREATE DATABASE bus_pass_system;
USE bus_pass_system;

4.4 Create Tables
Run the following SQL queries:
-- Students Table
CREATE TABLE students (
    id INT PRIMARY KEY AUTO_INCREMENT,
    register_no VARCHAR(50) UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    dob DATE,
    password VARCHAR(255) NOT NULL,
    college VARCHAR(200),
    course VARCHAR(100),
    year VARCHAR(20),
    student_photo_file VARCHAR(255),
    phone VARCHAR(15),
    address TEXT,
    photo_url VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active TINYINT DEFAULT 1
);

-- Pass Applications Table
CREATE TABLE pass_applications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    student_dob DATE,
    unique_pass_id VARCHAR(50) UNIQUE,
    travel_from VARCHAR(100),
    travel_to VARCHAR(100),
    pass_type VARCHAR(50),
    duration VARCHAR(20),
    id_proof_url VARCHAR(255),
    address_proof_url VARCHAR(255),
    college_id_url VARCHAR(255),
    fees DECIMAL(10,2),
    payment_status VARCHAR(20) DEFAULT 'pending',
    application_status VARCHAR(20) DEFAULT 'pending',
    applied_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    approved_date DATETIME,
    college_id_file VARCHAR(255),
    student_photo_file VARCHAR(255),
    address_proof_file VARCHAR(255),
    bonafide_file VARCHAR(255),
    previous_pass_file VARCHAR(255),
    address_proof_type VARCHAR(50),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Settings Table
CREATE TABLE settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    setting_key VARCHAR(100) UNIQUE,
    setting_value TEXT,
    setting_type VARCHAR(50),
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert default settings
INSERT INTO settings (setting_key, setting_value, setting_type) VALUES
('system_name', 'Bus Pass Management System', 'text'),
('processing_fee', '50', 'number'),
('pass_regular_1month', '500', 'number'),
('pass_regular_3months', '1500', 'number'),
('pass_regular_6months', '3000', 'number');

### Step 5: Configure Database Connection
Open app.py file and update the database configuration:

db_config = {
    'host': 'localhost',
    'user': 'root',           # Your MySQL username
    'password': 'yourpassword',  # Your MySQL password
    'database': 'bus_pass_system',
    'cursorclass': pymysql.cursors.DictCursor
}

Note: If you are using XAMPP with default settings:

Username: root
Password: '' (blank / empty)

### Step 6: Create Upload Folder
The application needs a folder to store uploaded documents. Run this command in your project directory:
Windows:

mkdir static\uploads

Mac/Linux:
mkdir -p static/uploads

### Step 7: Start the Flask Application
python app.py

You will see output similar to:
* Running on http://127.0.0.1:5000
 * Running on http://localhost:5000

### Step 8: Access the Application
http://localhost:5000  --- Home Page (Student Portal)


Admin Login: 
Username	admin
Password	admin123

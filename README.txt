HALAXY CLINIC — SQLITE WEBSITE (NO PHP / NO WAMP)
=================================================

WHAT YOU NEED
- Windows 10/11
- Python 3.9 or newer (free)
- A modern browser such as Chrome or Edge

This app uses Python's built-in web server and SQLite database. It does not need PHP,
WAMP, XAMPP, MySQL, Node.js, Flask or any third-party Python packages.

INSTALL PYTHON
1. If Python is not installed, download it from https://www.python.org/downloads/
2. During installation, tick "Add Python to PATH".
3. Finish installation.

START THE WEBSITE
1. Extract this ZIP to a folder (for example Desktop\halaxy-sqlite-website).
2. Double-click START-HALAXY.bat.
3. A command window will open. Keep it open while using the website.
4. Open your browser and go to http://127.0.0.1:8000
5. To stop the website, close the command window or press Ctrl+C.

DEMO ACCOUNTS
Doctor:  doctor@halaxy.com  / password
Patient: patient@halaxy.com / password

DATABASE LOCATION
Your records are stored in:
  clinic_data\halaxy.db

This is a real SQLite database file. The app creates the folder and database
automatically the first time it runs. Do not delete this file if you want to keep
your records. Back it up regularly by copying the clinic_data folder while the
server is stopped. You can also use the Export data backup button in the website
to download a JSON export.

FEATURES
- Public clinic landing page
- Patient and doctor account registration/login
- Passwords hashed using PBKDF2 (not stored as plain text)
- Patient and doctor dashboards
- Book appointments
- Doctor approve/complete/cancel appointment workflow
- Patients can cancel pending requests
- Patient directory for doctors
- Payment history display
- Clinic settings
- JSON data export
- SQLite persistence across browser restarts

IMPORTANT LIMITATIONS / PRODUCTION
This is a small local demonstration app. It is configured to listen only on this
computer (127.0.0.1), so other computers cannot connect to it by default.
It does not provide production-grade healthcare security, audit logs, encrypted
database storage, advanced role administration, automated backups or compliance
controls. Do not use it for real patient medical records until it has been
professionally secured, reviewed and deployed with appropriate privacy safeguards.

If you need multiple computers to share the same database, the app must be deployed
on a trusted clinic network/server with secure authentication, HTTPS, backups and
appropriate access controls. Do not simply expose this development server to the
internet.

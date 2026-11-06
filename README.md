# Ashoka Online Examination Portal

A starter browser-based multi-student MCQ examination portal built with Python Flask and SQLite.

## Features
- Student login using name and roll number
- 20 Python MCQs based on the supplied question bank
- One-question-at-a-time interface with Previous/Next and question navigation
- Countdown timer and automatic submission when time expires
- Server-side answer checking (correct answers are not sent to the browser)
- One attempt per roll number
- Faculty password-protected dashboard
- Results, class average, pass percentage and CSV export
- SQLite database stores attempts

## Requirements
- Python 3.9+
- Flask

## Run on Windows
1. Extract the ZIP file.
2. Open Command Prompt in the extracted folder.
3. Create a virtual environment (recommended):
   `python -m venv venv`
4. Activate it:
   `venv\Scripts\activate`
5. Install dependencies:
   `pip install -r requirements.txt`
6. Set a faculty password and secret key (recommended):
   `set ADMIN_PASSWORD=YourStrongFacultyPassword`
   `set SECRET_KEY=UseALongRandomSecretString`
7. Start the portal:
   `python app.py`
8. Open `http://127.0.0.1:5000`

## Access for students on the same Wi-Fi/LAN
- Find the host computer's local IPv4 address using `ipconfig`.
- Students open `http://HOST-IP:5000` in their browser.
- Allow Python through the computer firewall on a trusted private network.
- Keep the host computer running throughout the examination.

## Faculty
- Open `/admin/login`
- Use the password configured in `ADMIN_PASSWORD`.
- Default for local testing only: `change-this-password`
- Download results using the CSV button.

## Important deployment and examination notes
- This is a starter application, not a hardened institutional examination platform.
- Change the default admin password and SECRET_KEY before use.
- For internet access, deploy behind HTTPS on a properly managed server; do not expose the Flask development server directly to the public internet.
- Student login uses roll number as an identifier, not identity verification. For a formal exam, add college SSO or individual credentials.
- One attempt per roll number is enforced in the database. An administrator must manage/reset attempts if a student needs a retake.
- Browser timers are for user display; the server deadline is authoritative.
- The portal does not provide full proctoring, webcam monitoring, tab-switch detection, or guaranteed prevention of collaboration.
- Back up `exam_portal.db` before and after each examination.
- The included questions and answers should be reviewed by the faculty before a live assessment.

## Configuration
Optional environment variables:
- `PORT` (default 5000)
- `EXAM_DURATION_MINUTES` (default 30)
- `ADMIN_PASSWORD`
- `SECRET_KEY`

The database file `exam_portal.db` is created automatically on first run.

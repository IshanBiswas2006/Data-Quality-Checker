# Data Quality Checker

A beginner-to-intermediate Python and Flask web application that enables users to upload CSV datasets, automatically inspect them for common data quality issues (missing values, duplicate rows, data type anomalies, validation rule failures), apply controlled, non-destructive cleaning operations on a working copy, compare before-and-after metrics, and export cleaned CSV files.

---

## Key Features

1. **Robust CSV Upload & Validation**
   - File extension and size validation (configurable up to 16 MB).
   - Multi-encoding fallback (`utf-8`, `utf-8-sig`, `latin-1`, `cp1252`) and delimiter auto-detection (comma, semicolon, tab, pipe).
   - Protection against malformed, unreadable, and empty files.
   - Built-in rate limiting to prevent upload denial-of-service abuse.

2. **Instant Dataset Preview**
   - Immediate inspection of dataset dimensions (total rows, columns, and cells).
   - Display of column names, inferred data types, and capped sample records without overloading the browser.

3. **Comprehensive Data Quality Analysis**
   - **Missing Value Detection:** Counts, percentages per column, overall dataset null rates, and sample row numbers.
   - **Duplicate Detection:** Automatic identification of exact matching rows, sample duplicated row previews, and clear rule explanation.
   - **Data Type Profiling:** Semantic type inference (Integer, Decimal, Datetime, Boolean, Text) and detection of non-conforming values (e.g. text in numeric fields).

4. **Extensible Validation Rules**
   - Configurable rules including numeric ranges (`Age >= 0`, `Price > 0`), required fields, email format checks, and date format checks.
   - Transparent reporting showing exact row numbers, failed values, and clear failure rationales.

5. **Controlled, Non-Destructive Data Cleaning**
   - Cleaning operations apply strictly to a separate working copy, ensuring the original upload is never mutated.
   - Supported operations:
     - Duplicate removal
     - Missing row deletion (any or all columns)
     - Missing value imputation (constant, mean, median, mode)
     - Column data type conversion (integer, decimal, datetime, boolean, string)
     - Whitespace trimming
     - Column dropping
   - Confirmation dialogs before destructive operations and one-click reset back to the original dataset.

6. **Before-and-After Comparison & Export**
   - Side-by-side metric comparison tracking rows removed, missing values resolved, and duplicates dropped.
   - Complete audit trail of all applied operations.
   - Safe CSV download with formula injection protection (DDE sanitization).

7. **User Authentication & Profile Management**
   - Secure account registration and login powered by salted PBKDF2/scrypt password hashing via `werkzeug.security`.
   - Dynamic profile navigation: guests see "Log In" and "Sign Up", while authenticated users see their personalized avatar badge and quick profile menu.
   - User Profile Studio: edit name, bio, email, customize avatar theme colors, update password, and maintain a saved history of inspected datasets.
   - Non-intrusive access: public browsing, CSV inspection, and cleaning remain open to all users without forced authentication.

8. **Production & Security Hardened**
   - Security headers: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy`.
   - Comprehensive pages: Home, Results, Interactive FAQ, About, Privacy Policy, Terms of Service, Robots.txt, Sitemap.xml, and dedicated 404 handler.
   - Dark and light theme switcher using minimalist design tokens.

---

## Architecture & Folder Structure

```text
data-quality-checker/
|-- app.py                      # Development server entry point
|-- wsgi.py                     # Production WSGI entry point
|-- Procfile                    # Deployment process configuration
|-- config.py                   # Environment profiles (Dev, Test, Prod)
|-- requirements.txt            # Python dependencies
|-- .env.example                # Example environment variables
|-- .gitignore                  # Git ignore rules
|-- LICENSE                     # MIT License
|-- README.md                   # Documentation
|-- MEMORY.md                   # Project status and implementation memory
|
|-- app/
|   |-- __init__.py             # Flask app factory, security headers & error handlers
|   |-- routes/
|   |   |-- __init__.py         # Blueprints initialization
|   |   |-- main.py             # Home, About, FAQ, privacy, terms, health, robots, sitemap
|   |   |-- auth.py             # Sign up, login, logout, profile & password management
|   |   |-- upload.py           # CSV file upload, validation & rate limiting
|   |   |-- analysis.py         # Results dashboard and rules validation
|   |   |-- cleaning.py         # Controlled cleaning operations and reset
|   |   |-- download.py         # Cleaned CSV file export
|   |
|   |-- services/
|   |   |-- __init__.py         # Services package
|   |   |-- user_service.py     # User model, authentication, profile & database operations
|   |   |-- file_validator.py   # Safe file size and format validation
|   |   |-- csv_reader.py       # Multi-encoding, delimiter-aware CSV reader
|   |   |-- quality_analyzer.py # Missing, duplicate, and type analysis
|   |   |-- validation_rules.py # Extensible validation rule engine
|   |   |-- cleaning_service.py # Non-destructive data cleaning service
|   |   |-- report_service.py   # Comparison metrics and Matplotlib charts
|   |   |-- export_service.py   # Safe CSV export and sanitization
|   |   |-- session_store.py    # Temporary in-memory analysis sessions
|   |   |-- rate_limiter.py     # IP-based sliding window rate limiter
|   |
|   |-- templates/
|   |   |-- base.html           # Master layout with theme switcher & metadata
|   |   |-- index.html          # Drag-and-drop upload page
|   |   |-- results.html        # Comprehensive analysis & cleaning dashboard
|   |   |-- about.html          # About page documenting mission and tech stack
|   |   |-- faq.html            # Frequently Asked Questions with accordion
|   |   |-- privacy.html        # Privacy policy (data handling & retention)
|   |   |-- terms.html          # Terms of service
|   |   |-- auth/
|   |   |   |-- login.html      # User login page
|   |   |   |-- signup.html     # User registration page
|   |   |   |-- profile.html    # Profile studio & dataset history
|   |   |-- errors/
|   |       |-- 400.html        # Bad request error template
|   |       |-- 404.html        # Page not found error template
|   |       |-- 413.html        # File too large error template
|   |       |-- 500.html        # Internal server error template
|   |
|   |-- static/
|       |-- css/
|       |   |-- style.css       # Token-based styles (dark & light theme)
|       |-- js/
|           |-- main.js         # Theme toggle and notification toasts
|           |-- upload.js       # Drag-and-drop & sample data handler
|           |-- results.js      # Tab switching, cleaning modal, and AJAX updates
|
|-- tests/
|   |-- __init__.py             # Tests package
|   |-- test_auth.py            # Unit & integration tests for authentication and profile
|   |-- test_file_validator.py  # Unit tests for upload validation
|   |-- test_quality_analyzer.py# Unit tests for metrics and analysis
|   |-- test_validation_rules.py# Unit tests for validation engine
|   |-- test_cleaning_service.py# Unit tests for non-destructive cleaning
|   |-- test_export_service.py  # Unit tests for export and formula sanitization
|   |-- test_routes.py          # Integration tests for web routes & FAQ
|   |-- test_security.py        # Security headers, rate limit & 404 tests
|   |-- fixtures/               # Test CSV fixture files
|
|-- examples/
|   |-- sample_sales.csv        # Realistic demonstration dataset
```

---

## Installation & Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Git

### 1. Clone or Open the Repository
```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Application

### Development Server
```bash
python app.py
```
Open your browser at `http://127.0.0.1:5000`.

### Production WSGI Server

#### On Linux / Docker / Cloud (Gunicorn)
```bash
gunicorn wsgi:app
```

#### On Windows (Waitress)
```bash
waitress-serve --port=5000 wsgi:app
```

#### Cloud PaaS (Render, Railway, Fly.io, Heroku)
The included `Procfile` (`web: gunicorn wsgi:app`) allows automatic detection and deployment.

---

## Running the Automated Test Suite

Run the full pytest suite:
```bash
pytest -v
```
All 55 unit, integration, and security tests will execute and confirm file validation, quality analysis, cleaning operations, route behavior, authentication, and security protections.

---

## License

This project is licensed under the [MIT License](LICENSE).

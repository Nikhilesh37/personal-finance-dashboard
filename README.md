# Personal Finance Dashboard

A comprehensive, beautifully designed web application built with Django to help you track your income, expenses, set monthly budgets, and visualize your financial trends.

## Features
- **User Authentication:** Secure registration and login.
- **Transaction Tracking:** Add, edit, and view income and expenses.
- **Budgeting:** Set monthly budgets for different categories and track your spending against them.
- **Data Visualization:** Interactive charts (using Chart.js) showing your monthly income vs. expense trends.
- **Reporting:** Export your monthly transactions to a downloadable PDF report (powered by `xhtml2pdf`).
- **CSV Import:** Bulk upload transactions via CSV.

## Tech Stack
- **Backend:** Python 3, Django 5
- **Database:** SQLite (Development) / PostgreSQL (Production)
- **Frontend:** HTML5, Vanilla CSS, Bootstrap 5 (via crispy-forms), Chart.js
- **PDF Generation:** xhtml2pdf

## Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd Personal_finance_dashboard
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database and environment variables:**
   - Create a `.env` file in the root directory:
     ```env
     SECRET_KEY=your-secret-key-here
     DEBUG=True
     # DB_ENGINE=django.db.backends.postgresql  # Uncomment for PostgreSQL
     ```
   - Run migrations:
     ```bash
     python manage.py migrate
     ```

5. **(Optional) Seed the database with demo data:**
   ```bash
   python seed_data.py
   ```

6. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server:**
   ```bash
   python manage.py runserver
   ```
   Visit `http://127.0.0.1:8000/` in your browser.

## Deployment on Railway

This project is configured to be deployed easily on [Railway](https://railway.app/).

1. Create a GitHub repository and push your code.
2. Log in to Railway and click **New Project** -> **Deploy from GitHub repo**.
3. Select your repository.
4. Add a **PostgreSQL** database service to your Railway project.
5. In your Django app's **Variables** tab on Railway, ensure the following are set:
   - `SECRET_KEY`: A secure random string.
   - `DEBUG`: `False`
   - `DATABASE_URL`: (Railway should inject this automatically when you link the PostgreSQL service).
6. Railway will automatically detect the `Procfile` and install dependencies from `requirements.txt`.
7. Once deployed, run `python manage.py createsuperuser` via the Railway CLI or the dashboard's command interface.

## License
MIT

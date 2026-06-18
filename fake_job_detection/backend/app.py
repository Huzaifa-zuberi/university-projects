# ============================================================
# app.py
# The main Flask application.
# Handles: pages, registration, login, logout, sessions,
#          prediction, saving, and prediction history.
# ------------------------------------------------------------
# Run with:  python app.py
# Then open: http://127.0.0.1:5000
# ============================================================

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, jsonify
)
import os
import json

import config
import auth
import database
import model_utils


# ---- Create the Flask app ----
app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)
app.secret_key = config.SECRET_KEY


# ------------------------------------------------------------
# SMALL HELPER: check if a user is logged in
# ------------------------------------------------------------
def is_logged_in():
    return "user_id" in session


def load_model_results():
    """Read the model comparison file saved by the training notebook.
    Returns the data, or None if the file does not exist yet.
    """
    path = os.path.join(os.path.dirname(__file__), "..", "model", "model_results.json")
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


# ------------------------------------------------------------
# HOME PAGE  (public)
# ------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html", logged_in=is_logged_in())


# ------------------------------------------------------------
# ABOUT PAGE  (public)
# ------------------------------------------------------------
@app.route("/about")
def about():
    return render_template("about.html", logged_in=is_logged_in())


# ------------------------------------------------------------
# REGISTRATION
# ------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")

        success, message = auth.register_user(full_name, email, password)
        flash(message)
        if success:
            return redirect(url_for("login"))

    return render_template("register.html")


# ------------------------------------------------------------
# LOGIN  (starts the session)
# ------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        success, message, user = auth.login_user(email, password)
        if success:
            session["user_id"] = user["id"]
            session["user_name"] = user["full_name"]
            return redirect(url_for("dashboard"))
        else:
            flash(message)

    return render_template("login.html")


# ------------------------------------------------------------
# LOGOUT  (ends the session)
# ------------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


# ------------------------------------------------------------
# DASHBOARD  (statistics + history + model performance)
# ------------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))

    records = database.get_user_predictions(session["user_id"])

    total = len(records)
    fake_count = sum(1 for r in records if r["predicted_result"] == "Fake")
    real_count = total - fake_count
    stats = {"total": total, "fake": fake_count, "real": real_count}

    # The 5 most recent checks (for the "Recent Predictions" section).
    recent = records[:5]

    # Model comparison numbers (may be None if not trained yet).
    model_data = load_model_results()

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name"),
        stats=stats,
        records=records,
        recent=recent,
        model_data=model_data,
    )


# ------------------------------------------------------------
# JOB FORM PAGE  (the posting form)
# ------------------------------------------------------------
@app.route("/job_form")
def job_form():
    if not is_logged_in():
        return redirect(url_for("login"))
    return render_template("job_form.html", user_name=session.get("user_name"))


# ------------------------------------------------------------
# PREDICTION RESULT PAGE  (JavaScript fills it in)
# ------------------------------------------------------------
@app.route("/prediction")
def prediction():
    if not is_logged_in():
        return redirect(url_for("login"))
    return render_template("prediction.html", user_name=session.get("user_name"))


# ------------------------------------------------------------
# PREDICT  (receives the posting, runs model, saves result)
# Returns the result as JSON for the frontend to display.
# ------------------------------------------------------------
@app.route("/predict", methods=["POST"])
def predict():
    if not is_logged_in():
        return jsonify({"error": "Please log in first."}), 401

    form = request.get_json()

    data = {
        "job_title":       form.get("job_title", "").strip(),
        "company_name":    form.get("company_name", "").strip(),
        "salary":          form.get("salary", "").strip(),
        "location":        form.get("location", "").strip(),
        "employment_type": form.get("employment_type", "").strip(),
        "posting_platform": form.get("posting_platform", "").strip(),
        "industry":        form.get("industry", "").strip(),
        "job_category":    form.get("job_category", "").strip(),
        "experience":      form.get("experience", "").strip(),
        "education":       form.get("education", "").strip(),
        "description":     form.get("description", "").strip(),
    }

    # The title and description are the most important fields.
    if data["job_title"] == "" or data["description"] == "":
        return jsonify({"error": "Please enter at least the job title and description."}), 400

    result_data = model_utils.predict(data)

    database.save_prediction(session["user_id"], data, result_data)

    return jsonify(result_data)


# ------------------------------------------------------------
# MODEL COMPARISON PAGE
# ------------------------------------------------------------
@app.route("/comparison")
def comparison():
    if not is_logged_in():
        return redirect(url_for("login"))
    # Numbers come from model/model_results.json (auto-loaded).
    model_data = load_model_results()
    return render_template("model_comparison.html", model_data=model_data)


# ------------------------------------------------------------
# START THE APP
# ------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)

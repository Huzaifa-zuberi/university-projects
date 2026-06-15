# ============================================================
# app.py (FIXED FOR RENDER DEPLOYMENT)
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


# ------------------------------------------------------------
# Flask App
# ------------------------------------------------------------
app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)

app.secret_key = config.SECRET_KEY


# ------------------------------------------------------------
# Helper
# ------------------------------------------------------------
def is_logged_in():
    return "user_id" in session


def load_model_results():
    path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "model",
        "model_results.json"
    )
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


# ------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html", logged_in=is_logged_in())


@app.route("/about")
def about():
    return render_template("about.html", logged_in=is_logged_in())


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


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))

    records = database.get_user_predictions(session["user_id"])

    total = len(records)
    fake_count = sum(1 for r in records if r["predicted_result"] == "Fake")
    real_count = total - fake_count

    stats = {"total": total, "fake": fake_count, "real": real_count}

    recent = records[:5]
    model_data = load_model_results()

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name"),
        stats=stats,
        records=records,
        recent=recent,
        model_data=model_data,
    )


@app.route("/job_form")
def job_form():
    if not is_logged_in():
        return redirect(url_for("login"))

    return render_template("job_form.html", user_name=session.get("user_name"))


@app.route("/prediction")
def prediction():
    if not is_logged_in():
        return redirect(url_for("login"))

    return render_template("prediction.html", user_name=session.get("user_name"))


@app.route("/predict", methods=["POST"])
def predict():
    if not is_logged_in():
        return jsonify({"error": "Please log in first."}), 401

    form = request.get_json()

    data = {
        "job_title": form.get("job_title", "").strip(),
        "company_name": form.get("company_name", "").strip(),
        "salary": form.get("salary", "").strip(),
        "location": form.get("location", "").strip(),
        "employment_type": form.get("employment_type", "").strip(),
        "posting_platform": form.get("posting_platform", "").strip(),
        "industry": form.get("industry", "").strip(),
        "job_category": form.get("job_category", "").strip(),
        "experience": form.get("experience", "").strip(),
        "education": form.get("education", "").strip(),
        "description": form.get("description", "").strip(),
    }

    if data["job_title"] == "" or data["description"] == "":
        return jsonify({"error": "Job title and description required"}), 400

    result_data = model_utils.predict(data)

    database.save_prediction(session["user_id"], data, result_data)

    return jsonify(result_data)


@app.route("/comparison")
def comparison():
    if not is_logged_in():
        return redirect(url_for("login"))

    model_data = load_model_results()

    return render_template("model_comparison.html", model_data=model_data)


# ------------------------------------------------------------
# RENDER ENTRY POINT (IMPORTANT FIX)
# ------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)

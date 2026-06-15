# ============================================================
# model_utils.py
# Loads the trained model bundle and turns a job posting into a
# result: Real/Fake, confidence %, fake probability %, risk level,
# reasons, warning indicators, and safety suggestions.
# ------------------------------------------------------------
# best_model.pkl is a dictionary that holds 4 things saved during
# training:  model, scaler, label_encoders, feature_names.
# The model is a tabular classifier that expects 17 numeric
# features, so we build those features from the job posting.
# ============================================================

import re
import joblib

import config


# ---- Load the model bundle only once, when first needed ----
_bundle = None

def get_bundle():
    """Load and cache the saved model bundle."""
    global _bundle
    if _bundle is None:
        _bundle = joblib.load(config.MODEL_PATH)
    return _bundle


# ------------------------------------------------------------
# Helpers to safely turn user input into the numbers the model wants
# ------------------------------------------------------------
def safe_encode(label_encoder, value, default):
    """Turn a category (text) into the number the model learned.
    If the value was never seen in training, return a neutral default.
    """
    classes = list(label_encoder.classes_)
    if value in classes:
        return int(label_encoder.transform([value])[0])
    return default


def get_number(text):
    """Pull the first number out of a string like '90,000 PKR'. """
    digits = re.sub(r"[^0-9]", "", str(text))
    return int(digits) if digits else None


# Simple ordinal maps for the dropdowns (used as the model's numeric codes)
EXPERIENCE_MAP = {"No Experience": 0, "Entry Level": 1, "1-3 Years": 2, "3-5 Years": 3, "5+ Years": 4}
EDUCATION_MAP  = {"Matric": 0, "Intermediate": 1, "Bachelor's": 2, "Master's": 3, "Any": 1}


def build_features(data):
    """Build the 17-feature row the model expects, in the correct order.
    For anything we cannot work out, we use the training average
    (scaler.mean_) so that feature stays neutral.
    """
    bundle = get_bundle()
    feats = bundle["feature_names"]
    encs = bundle["label_encoders"]
    means = bundle["scaler"].mean_   # average of each feature during training

    # All the text together (used for the yes/no flag features)
    text = " ".join([
        str(data.get("job_title", "")), str(data.get("company_name", "")),
        str(data.get("description", "")), str(data.get("location", "")),
    ]).lower()

    desc = str(data.get("description", ""))
    salary_num = get_number(data.get("salary", ""))

    # Work out each feature value (None means "use training average")
    values = {
        "job_title":             safe_encode(encs["job_title"], data.get("job_title", ""), round(means[feats.index("job_title")])),
        "location":              safe_encode(encs["location"], data.get("location", ""), round(means[feats.index("location")])),
        "salary":                salary_num,
        "employment_type":       safe_encode(encs["employment_type"], data.get("employment_type", ""), round(means[feats.index("employment_type")])),
        "required_experience":   EXPERIENCE_MAP.get(data.get("experience", ""), None),
        "required_education":    EDUCATION_MAP.get(data.get("education", ""), None),
        "job_description_length": len(desc),
        "has_company_website":   1 if ("http" in text or "www." in text or ".com" in text) else 0,
        "has_contact_number":    1 if re.search(r"\d{7,}", re.sub(r"[^0-9]", "", text)) else 0,
        "remote_job":            1 if ("remote" in text or "work from home" in text or data.get("employment_type", "") == "Freelance") else 0,
        "posting_platform":      safe_encode(encs["posting_platform"], data.get("posting_platform", ""), round(means[feats.index("posting_platform")])),
        "industry":              safe_encode(encs["industry"], data.get("industry", ""), round(means[feats.index("industry")])),
        "job_category":          safe_encode(encs["job_category"], data.get("job_category", ""), round(means[feats.index("job_category")])),
        "suspicious_email":      1 if re.search(r"(gmail|yahoo|hotmail|outlook)\.com", text) else 0,
        "salary_band":           None,   # binning unknown -> stay neutral
        "no_info_flag":          1 if len(str(data.get("company_name", "")).strip()) < 3 else 0,
        "short_description":     1 if len(desc) < 200 else 0,
    }

    # Build the row in the exact order the model was trained on.
    row = []
    for i, name in enumerate(feats):
        v = values.get(name, None)
        row.append(float(means[i]) if v is None else float(v))
    return [row]


def predict(data):
    """Run the model and build the full result dictionary."""
    bundle = get_bundle()
    model = bundle["model"]
    scaler = bundle["scaler"]

    # 1. Build features and scale them the same way as training.
    features = build_features(data)
    features_scaled = scaler.transform(features)

    # 2. Predict.  The model uses 1 = Fake, 0 = Real.
    pred = int(model.predict(features_scaled)[0])
    predicted_result = "Fake" if pred == 1 else "Real"

    # 3. Probabilities.
    proba = model.predict_proba(features_scaled)[0]
    classes = list(model.classes_)
    confidence_percentage = round(max(proba) * 100, 2)
    if 1 in classes:
        fake_probability = round(proba[classes.index(1)] * 100, 2)
    else:
        fake_probability = 0.0

    # 4. Extra report parts (simple rules).
    risk_level = get_risk_level(fake_probability)
    warning_signs = find_warnings(data)
    reasons = build_reasons(predicted_result, fake_probability, warning_signs)
    safety_suggestions = build_safety_tips()

    return {
        "predicted_result": predicted_result,
        "confidence_percentage": confidence_percentage,
        "fake_probability": fake_probability,
        "risk_level": risk_level,
        "warning_signs": warning_signs,
        "reasons": reasons,
        "safety_suggestions": safety_suggestions,
    }


# ------------------------------------------------------------
# SIMPLE RULE-BASED HELPERS (easy to read and explain)
# ------------------------------------------------------------
def get_risk_level(fake_probability):
    if fake_probability >= 70:
        return "High"
    elif fake_probability >= 40:
        return "Medium"
    else:
        return "Low"


def find_warnings(data):
    text = " ".join(str(data.get(f, "")) for f in
                     ["job_title", "company_name", "description", "location"]).lower()
    warnings = []
    if any(w in text for w in ["fee", "registration charge", "deposit", "payment",
                               "send money", "easypaisa", "jazzcash", "western union"]):
        warnings.append("Mentions money, fees, or payment.")
    if any(w in text for w in ["cnic", "bank account", "passport", "atm pin", "account number"]):
        warnings.append("Asks for sensitive personal or bank details.")
    if any(w in text for w in ["no experience", "earn fast", "quick money", "guaranteed",
                               "urgent", "immediate joining", "work from home and earn"]):
        warnings.append("Uses urgent or 'too good to be true' wording.")
    if re.search(r"(gmail|yahoo|hotmail|outlook)\.com", text):
        warnings.append("Uses a personal email address, not a company one.")
    if len(str(data.get("company_name", "")).strip()) < 3:
        warnings.append("Little or no company information provided.")
    if not warnings:
        warnings.append("No obvious warning signs detected.")
    return warnings


def build_reasons(predicted_result, fake_probability, warnings):
    reasons = []
    if predicted_result == "Fake":
        reasons.append("The model matched this posting to patterns seen in fake jobs.")
    else:
        reasons.append("The posting looks similar to genuine jobs the model learned.")
    reasons.append("Estimated fake probability is " + str(fake_probability) + "%.")
    real = [w for w in warnings if "No obvious" not in w]
    reasons.append("Found " + str(len(real)) + " warning sign(s) in the text." if real
                   else "No rule-based warning signs were triggered.")
    return reasons


def build_safety_tips():
    return [
        "Never pay any fee or deposit to get a job.",
        "Verify the company on its official website or LinkedIn.",
        "Do not share your CNIC, bank, or password details.",
        "Be careful with 'work from home, earn fast' offers.",
        "Interview only through official company channels.",
    ]

/* ============================================================
   script.js  -  JobShield (Fake Job Detection)
   Simple, beginner-friendly JavaScript.
   Handles: mobile menu, job form submit, showing the result.
   ============================================================ */


/* ---- 1. Mobile menu toggle ---- */
function toggleMenu() {
    var links = document.getElementById("navLinks");
    if (links) {
        links.classList.toggle("open");
    }
}


/* ============================================================
   2. JOB FORM
   Read the values, send them to /predict, save the result,
   then go to the result page.
   ============================================================ */
var form = document.getElementById("jobForm");

if (form) {
    form.addEventListener("submit", function (event) {
        event.preventDefault();   // stop the normal page reload

        var errorBox = document.getElementById("formError");
        var button = document.getElementById("submitBtn");

        // Collect all the form values into one object.
        var data = {
            job_title:       getValue("job_title"),
            company_name:    getValue("company_name"),
            salary:          getValue("salary"),
            location:        getValue("location"),
            employment_type: getValue("employment_type"),
            experience:      getValue("experience"),
            education:       getValue("education"),
            description:     getValue("description")
        };

        button.innerText = "Checking...";
        button.disabled = true;

        fetch("/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        })
        .then(function (response) { return response.json(); })
        .then(function (result) {
            if (result.error) {
                errorBox.innerText = result.error;
                errorBox.style.display = "block";
                button.innerText = "Check This Job";
                button.disabled = false;
                return;
            }
            // Save the input and the result for the result page.
            sessionStorage.setItem("jobInput", JSON.stringify(data));
            sessionStorage.setItem("jobResult", JSON.stringify(result));
            window.location.href = "/prediction";
        })
        .catch(function () {
            errorBox.innerText = "Something went wrong. Please try again.";
            errorBox.style.display = "block";
            button.innerText = "Check This Job";
            button.disabled = false;
        });
    });
}

/* Helper: read the value of an input by its id. */
function getValue(id) {
    var el = document.getElementById(id);
    return el ? el.value : "";
}


/* ============================================================
   3. RESULT PAGE
   Read the saved result and fill in the report.
   ============================================================ */
var statusBanner = document.getElementById("statusBanner");

if (statusBanner) {
    var result = JSON.parse(sessionStorage.getItem("jobResult") || "null");
    var input  = JSON.parse(sessionStorage.getItem("jobInput")  || "null");

    if (!result) {
        // No saved result -> go back to the form.
        window.location.href = "/job_form";
    } else {
        showResult(result, input);
    }
}

function showResult(result, input) {

    /* ---- Result banner (green for Real, red for Fake) ---- */
    document.getElementById("statusText").innerText = result.predicted_result + " Job";
    if (result.predicted_result === "Fake") {
        statusBanner.classList.add("status-fake");
    } else {
        statusBanner.classList.add("status-real");
    }

    /* ---- Risk level badge ---- */
    var riskBadge = document.getElementById("riskBadge");
    riskBadge.innerText = "Risk Level: " + result.risk_level;

    /* ---- Fake probability bar ---- */
    document.getElementById("fakeValue").innerText = result.fake_probability + "%";
    setTimeout(function () {
        document.getElementById("fakeBar").style.width = result.fake_probability + "%";
    }, 100);

    /* ---- Confidence bar ---- */
    document.getElementById("confValue").innerText = result.confidence_percentage + "%";
    setTimeout(function () {
        document.getElementById("confBar").style.width = result.confidence_percentage + "%";
    }, 100);

    /* ---- Reasons / Warnings / Suggestions ---- */
    fillList("reasonsList", result.reasons, "No reasons available.");
    fillList("warningsList", result.warning_signs, "No warning signs found.");
    fillList("suggestionsList", result.safety_suggestions, "No suggestions available.");

    /* ---- Detailed report table ---- */
    if (input) {
        var rows = [
            ["Job Title", input.job_title || "—"],
            ["Company Name", input.company_name || "—"],
            ["Salary", input.salary || "—"],
            ["Location", input.location || "—"],
            ["Employment Type", input.employment_type || "—"],
            ["Experience", input.experience || "—"],
            ["Education", input.education || "—"],
            ["Prediction", result.predicted_result],
            ["Fake Probability", result.fake_probability + "%"],
            ["Confidence", result.confidence_percentage + "%"],
            ["Risk Level", result.risk_level]
        ];
        var tbody = document.querySelector("#reportTable tbody");
        rows.forEach(function (row) {
            var tr = document.createElement("tr");
            tr.innerHTML = "<td style='font-weight:600;width:40%'>" + row[0] +
                           "</td><td>" + row[1] + "</td>";
            tbody.appendChild(tr);
        });
    }
}

/* Helper: fill a <ul> with list items, or a default message. */
function fillList(listId, items, emptyMessage) {
    var list = document.getElementById(listId);
    if (!list) { return; }
    if (!items || items.length === 0) {
        var li = document.createElement("li");
        li.innerText = emptyMessage;
        list.appendChild(li);
        return;
    }
    items.forEach(function (text) {
        var li = document.createElement("li");
        li.innerText = text;
        list.appendChild(li);
    });
}

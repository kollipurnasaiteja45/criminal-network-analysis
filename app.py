from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    jsonify
)

import pandas as pd
import os
import re

from pypdf import PdfReader

from analysis import (
    get_graph_data,
    get_person_network,
    get_network_score,
    get_crime_patterns,
    get_case_connections
)

from ai import answer_question


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

app.secret_key = "criminal-analysis-authorized-login-key"


# ============================================================
# FILE PATHS
# ============================================================

CASE_FILE = "data/cases.csv"
UPLOAD_FOLDER = "uploads"

os.makedirs("data", exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============================================================
# AUTHORIZED USERS
# ============================================================

AUTHORIZED_USERS = {

    "admin": {
        "password": "Admin@123",
        "role": "Administrator"
    },

    "officer": {
        "password": "Officer@123",
        "role": "Investigator"
    }

}


# ============================================================
# LOGIN HELPER
# ============================================================

def login_required():

    return session.get("logged_in") is True


# ============================================================
# LOAD CASE DATA
# ============================================================

def load_case_data():

    if not os.path.exists(CASE_FILE):

        return pd.DataFrame(
            columns=[
                "fir_id",
                "police_station",
                "offence_gravity",
                "crime_category",
                "crime_major_head",
                "act_sections",
                "incident_date",
                "registration_date",
                "district",
                "location",
                "person",
                "phone",
                "vehicle",
                "description"
            ]
        )

    data = pd.read_csv(CASE_FILE)

    # --------------------------------------------------------
    # LOCATION COMPATIBILITY
    # --------------------------------------------------------

    if "location" not in data.columns:

        if "incident_location" in data.columns:

            data["location"] = data["incident_location"]

        else:

            data["location"] = ""


    # --------------------------------------------------------
    # REQUIRED COLUMNS
    # --------------------------------------------------------

    required_columns = [
        "fir_id",
        "person",
        "phone",
        "vehicle",
        "location"
    ]

    for column in required_columns:

        if column not in data.columns:

            data[column] = ""


    return data


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    if login_required():

        return redirect("/dashboard")

    return render_template("login.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if login_required():

        return redirect("/dashboard")


    if request.method == "GET":

        return render_template("login.html")


    username = request.form.get(
        "username",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )


    user = AUTHORIZED_USERS.get(username)


    if user and user["password"] == password:

        session["logged_in"] = True

        session["username"] = username

        session["role"] = user["role"]

        return redirect("/dashboard")


    return render_template(
        "login.html",
        error=(
            "Invalid username or password. "
            "Only authorized personnel can access the system."
        )
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    if not login_required():

        return redirect("/")


    data = load_case_data()


    total_firs = data["fir_id"].nunique()

    total_persons = data["person"].nunique()

    total_locations = data["location"].nunique()

    total_vehicles = data["vehicle"].nunique()


    return render_template(
        "dashboard.html",

        total_firs=total_firs,

        total_persons=total_persons,

        total_locations=total_locations,

        total_vehicles=total_vehicles,

        username=session.get("username"),

        role=session.get("role")
    )


# ============================================================
# ADD FIR
# ============================================================

@app.route("/add-fir", methods=["GET", "POST"])
def add_fir():

    if not login_required():

        return redirect("/")


    data = load_case_data()


    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        numbers = []


        for fir in data["fir_id"].astype(str):

            match = re.match(
                r"^FIR(\d+)$",
                fir.upper()
            )


            if match:

                numbers.append(
                    int(match.group(1))
                )


        if numbers:

            next_number = max(numbers) + 1

        else:

            next_number = 1


        next_fir = f"FIR{next_number:03d}"


        return render_template(
            "add_fir.html",

            next_fir=next_fir,

            username=session.get("username"),

            role=session.get("role")
        )


    # ========================================================
    # FORM DATA
    # ========================================================

    fir_id = request.form.get(
        "fir_id",
        ""
    ).strip().upper()


    police_station = request.form.get(
        "police_station",
        ""
    ).strip()


    offence_gravity = request.form.get(
        "offence_gravity",
        ""
    ).strip()


    crime_category = request.form.get(
        "crime_category",
        ""
    ).strip()


    crime_major_head = request.form.get(
        "crime_major_head",
        ""
    ).strip()


    act_sections = request.form.get(
        "act_sections",
        ""
    ).strip()


    incident_date = request.form.get(
        "incident_date",
        ""
    ).strip()


    registration_date = request.form.get(
        "registration_date",
        ""
    ).strip()


    district = request.form.get(
        "district",
        ""
    ).strip()


    incident_location = request.form.get(
        "incident_location",
        ""
    ).strip()


    person = request.form.get(
        "person",
        ""
    ).strip()


    phone = request.form.get(
        "phone",
        ""
    ).strip()


    vehicle = request.form.get(
        "vehicle",
        ""
    ).strip().upper()


    description = request.form.get(
        "description",
        ""
    ).strip()


    errors = []


    # ========================================================
    # VALIDATION
    # ========================================================

    if not fir_id:

        errors.append(
            "FIR number is required."
        )

    elif not re.match(
        r"^FIR\d+$",
        fir_id
    ):

        errors.append(
            "FIR number must be in format FIR001, FIR002, etc."
        )


    if not police_station:

        errors.append(
            "Police station is required."
        )


    if not offence_gravity:

        errors.append(
            "Offence gravity is required."
        )


    if not crime_category:

        errors.append(
            "Crime category is required."
        )


    if not crime_major_head:

        errors.append(
            "Crime major head is required."
        )


    if not act_sections:

        errors.append(
            "Applicable Act / Sections are required."
        )


    if not incident_date:

        errors.append(
            "Incident date is required."
        )


    if not registration_date:

        errors.append(
            "Registration date is required."
        )


    if not district:

        errors.append(
            "District / jurisdiction is required."
        )


    if not incident_location:

        errors.append(
            "Incident location is required."
        )


    if not person:

        errors.append(
            "Person name is required."
        )

    elif not re.match(
        r"^[A-Za-z .'-]+$",
        person
    ):

        errors.append(
            "Person name contains invalid characters."
        )


    if not phone:

        errors.append(
            "Phone number is required."
        )

    elif not re.match(
        r"^[6-9]\d{9}$",
        phone
    ):

        errors.append(
            "Phone number must contain 10 digits "
            "and start with 6-9."
        )


    if not vehicle:

        errors.append(
            "Vehicle number is required."
        )


    # ========================================================
    # DUPLICATE FIR
    # ========================================================

    existing_firs = (

        data["fir_id"]
        .astype(str)
        .str.upper()
        .tolist()

    )


    if fir_id in existing_firs:

        errors.append(
            f"{fir_id} already exists."
        )


    # ========================================================
    # SHOW ERRORS
    # ========================================================

    if errors:

        return render_template(
            "add_fir.html",

            error="\n".join(errors),

            fir_id=fir_id,

            police_station=police_station,

            offence_gravity=offence_gravity,

            crime_category=crime_category,

            crime_major_head=crime_major_head,

            act_sections=act_sections,

            incident_date=incident_date,

            registration_date=registration_date,

            district=district,

            incident_location=incident_location,

            person=person,

            phone=phone,

            vehicle=vehicle,

            description=description,

            username=session.get("username"),

            role=session.get("role")
        )


    # ========================================================
    # CREATE NEW RECORD
    # ========================================================

    new_record = pd.DataFrame([
        {

            "fir_id": fir_id,

            "police_station": police_station,

            "offence_gravity": offence_gravity,

            "crime_category": crime_category,

            "crime_major_head": crime_major_head,

            "act_sections": act_sections,

            "incident_date": incident_date,

            "registration_date": registration_date,

            "district": district,

            # IMPORTANT:
            # Save incident location as "location"
            # for compatibility with analysis.py

            "location": incident_location,

            "person": person,

            "phone": phone,

            "vehicle": vehicle,

            "description": description

        }
    ])


    # ========================================================
    # SAVE
    # ========================================================

    data = pd.concat(
        [data, new_record],
        ignore_index=True
    )


    data.to_csv(
        CASE_FILE,
        index=False
    )


    # ========================================================
    # SUCCESS
    # ========================================================

    return render_template(
        "add_fir.html",

        success=f"{fir_id} was successfully registered.",

        saved_fir={

            "fir_id": fir_id,

            "police_station": police_station,

            "offence_gravity": offence_gravity,

            "crime_category": crime_category,

            "crime_major_head": crime_major_head,

            "act_sections": act_sections,

            "incident_date": incident_date,

            "registration_date": registration_date,

            "district": district,

            "location": incident_location,

            "person": person,

            "phone": phone,

            "vehicle": vehicle,

            "description": description

        },

        username=session.get("username"),

        role=session.get("role")
    )


# ============================================================
# CASES
# ============================================================

@app.route("/cases")
def cases():

    if not login_required():

        return redirect("/")


    data = load_case_data()


    records = data.to_dict(
        orient="records"
    )


    return render_template(
        "cases.html",

        cases=records,

        username=session.get("username"),

        role=session.get("role")
    )


# ============================================================
# SINGLE CASE
# ============================================================

@app.route("/case/<fir_id>")
def case_details(fir_id):

    if not login_required():

        return redirect("/")


    data = load_case_data()


    matches = data[
        data["fir_id"]
        .astype(str)
        .str.upper()
        ==
        fir_id.upper()
    ]


    if matches.empty:

        return "FIR not found", 404


    case = matches.iloc[0].to_dict()


    return render_template(
        "case.html",

        case=case,

        username=session.get("username"),

        role=session.get("role")
    )


# ============================================================
# NETWORK ANALYSIS
# ============================================================

@app.route("/network")
def network():

    if not login_required():

        return redirect("/")


    graph_data = get_graph_data()


    return render_template(
        "network.html",

        graph_data=graph_data,

        username=session.get("username"),

        role=session.get("role")
    )


# ============================================================
# PERSON NETWORK
# ============================================================

@app.route("/person/<person_name>")
def person_network(person_name):

    if not login_required():

        return redirect("/")


    person, relationships = get_person_network(
        person_name
    )


    score = get_network_score(
        person_name
    )


    return render_template(
        "person.html",

        person=person,

        relationships=relationships,

        score=score,

        username=session.get("username"),

        role=session.get("role")
    )


# ============================================================
# CRIME PATTERNS
# ============================================================

@app.route("/patterns")
def patterns():

    if not login_required():

        return redirect("/")


    pattern_data = get_crime_patterns()


    return render_template(
        "patterns.html",

        patterns=pattern_data,

        username=session.get("username"),

        role=session.get("role")
    )


# ============================================================
# CASE CONNECTIONS
# ============================================================

@app.route("/connections")
def connections():

    if not login_required():

        return redirect("/")


    connection_data = get_case_connections()


    return render_template(
        "connections.html",

        connections=connection_data,

        username=session.get("username"),

        role=session.get("role")
    )


# ============================================================
# AI AGENT PAGE
# ============================================================

@app.route("/ai-agent")
def ai_agent_page():

    if not login_required():

        return redirect("/")


    return render_template(
        "ai_agent.html",

        username=session.get("username"),

        role=session.get("role")
    )


# ============================================================
# AI AGENT API
# ============================================================

@app.route(
    "/ai-agent/ask",
    methods=["POST"]
)
def ai_agent_ask():

    if not login_required():

        return jsonify({
            "answer": "Unauthorized access."
        }), 401


    data = request.get_json()


    if not data:

        return jsonify({
            "answer": "Invalid request."
        }), 400


    question = data.get(
        "question",
        ""
    ).strip()


    if not question:

        return jsonify({
            "answer": "Please enter an investigation question."
        }), 400


    try:

        answer = answer_question(
            question
        )


        return jsonify({
            "answer": answer
        })


    except Exception as e:

        print(
            "AI Agent Error:",
            e
        )


        return jsonify({
            "answer": (
                "The investigation agent encountered "
                "an error while analyzing the data."
            )
        }), 500


# ============================================================
# DOCUMENT TEXT EXTRACTION
# ============================================================

def extract_text_from_file(file_path):

    extension = os.path.splitext(
        file_path
    )[1].lower()


    # ========================================================
    # TXT
    # ========================================================

    if extension == ".txt":

        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:

            return file.read()


    # ========================================================
    # PDF
    # ========================================================

    if extension == ".pdf":

        reader = PdfReader(
            file_path
        )


        text = ""


        for page in reader.pages:

            page_text = page.extract_text()


            if page_text:

                text += page_text + "\n"


        return text


    return ""


# ============================================================
# DOCUMENT INFORMATION EXTRACTION
# ============================================================

def extract_document_information(text):
    information = {
        "fir_id": "",
        "police_station": "",
        "offence_gravity": "",
        "crime_category": "",
        "crime_major_head": "",
        "act_sections": "",
        "incident_date": "",
        "registration_date": "",
        "district": "",
        "location": "",
        "person": "",
        "phone": "",
        "vehicle": "",
        "description": ""
    }

    # FIR ID
    fir_match = re.search(
        r"\\bFIR\\s*(?:ID|NO|NUMBER)?\\s*[:\\-]?\\s*(\\d+)\\b",
        text, re.IGNORECASE
    )
    if fir_match:
        information["fir_id"] = ("FIR" + fir_match.group(1)).upper()

    # Person
    person_match = re.search(
        r"(?:Person|Name|Accused)\\s*:\\s*([A-Za-z .'-]+)",
        text, re.IGNORECASE
    )
    if person_match:
        information["person"] = person_match.group(1).strip()

    # Phone
    phone_match = re.search(r"\\b[6-9]\\d{9}\\b", text)
    if phone_match:
        information["phone"] = phone_match.group(0)

    # Vehicle
    vehicle_match = re.search(
        r"\\b[A-Z]{2}\\d{1,2}[A-Z]{1,3}\\d{1,4}\\b",
        text.upper()
    )
    if vehicle_match:
        information["vehicle"] = vehicle_match.group(0)

    def extract_labeled(pattern):
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else ""

    information["location"] = extract_labeled(
        r"^(?:Location|Place|Incident Location|Address)\\s*:\\s*(.+)$"
    )
    information["police_station"] = extract_labeled(
        r"^Police Station\\s*:\\s*(.+)$"
    )
    information["crime_category"] = extract_labeled(
        r"^Crime Category\\s*:\\s*(.+)$"
    )
    information["crime_major_head"] = extract_labeled(
        r"^Crime Major Head\\s*:\\s*(.+)$"
    )
    information["offence_gravity"] = extract_labeled(
        r"^Offence Gravity\\s*:\\s*(.+)$"
    )
    information["district"] = extract_labeled(
        r"^District\\s*(?:/\\s*Jurisdiction)?\\s*:\\s*(.+)$"
    )

    information["act_sections"] = extract_labeled(
        r"^(?:Applicable IPC / Act Sections|Applicable Sections|Act Sections)\\s*:\\s*(.+)$"
    )

    information["incident_date"] = extract_labeled(
        r"^Incident Date\\s*:\\s*(.+)$"
    )
    information["registration_date"] = extract_labeled(
        r"^Registration Date\\s*:\\s*(.+)$"
    )
    information["description"] = extract_labeled(
        r"^(?:Case Description|Description)\\s*:\\s*(.+)$"
    )

    return information


# ============================================================
# ADD FIR FILE EXTRACTION
# ============================================================

@app.route("/add-fir/extract", methods=["POST"])
def add_fir_extract():
    if not login_required():
        return jsonify({
            "success": False,
            "error": "Unauthorized access."
        }), 401

    if "fir_file" not in request.files:
        return jsonify({
            "success": False,
            "error": "No FIR file was uploaded."
        }), 400

    file = request.files["fir_file"]

    if not file or file.filename == "":
        return jsonify({
            "success": False,
            "error": "Please select a FIR file."
        }), 400

    filename = file.filename
    extension = os.path.splitext(filename)[1].lower()

    if extension not in [".pdf", ".txt"]:
        return jsonify({
            "success": False,
            "error": "Only PDF and TXT files are supported."
        }), 400

    safe_filename = re.sub(
        r"[^A-Za-z0-9_.-]",
        "_",
        filename
    )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        safe_filename
    )

    try:
        file.save(file_path)

        text = extract_text_from_file(file_path)

        if not text.strip():
            return jsonify({
                "success": False,
                "error": (
                    "No readable text was found in the FIR file. "
                    "If this is a scanned PDF, OCR is required."
                )
            }), 400

        information = extract_document_information(text)

        return jsonify({
            "success": True,
            "data": information
        })

    except Exception as e:
        print("FIR Extraction Error:", e)

        return jsonify({
            "success": False,
            "error": "Unable to process the FIR file."
        }), 500

    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass


# ============================================================
# DOCUMENT VERIFICATION
# ============================================================

@app.route(
    "/verify",
    methods=["GET", "POST"]
)
def verify():

    if not login_required():

        return redirect("/")


    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        return render_template(
            "verify.html",

            username=session.get("username"),

            role=session.get("role")
        )


    # ========================================================
    # CHECK UPLOADED FILE
    # ========================================================

    if "document" not in request.files:

        return render_template(
            "verify.html",

            error="Please select a document.",

            username=session.get("username"),

            role=session.get("role")
        )


    file = request.files["document"]


    if file.filename == "":

        return render_template(
            "verify.html",

            error="Please select a document.",

            username=session.get("username"),

            role=session.get("role")
        )


    # ========================================================
    # CHECK EXTENSION
    # ========================================================

    filename = file.filename

    extension = os.path.splitext(
        filename
    )[1].lower()


    if extension not in [".pdf", ".txt"]:

        return render_template(
            "verify.html",

            error="Only PDF and TXT files are supported.",

            username=session.get("username"),

            role=session.get("role")
        )


    # ========================================================
    # SAFE FILENAME
    # ========================================================

    safe_filename = re.sub(
        r"[^A-Za-z0-9_.-]",
        "_",
        filename
    )


    file_path = os.path.join(
        UPLOAD_FOLDER,
        safe_filename
    )


    file.save(file_path)


    # ========================================================
    # EXTRACT TEXT
    # ========================================================

    try:

        text = extract_text_from_file(
            file_path
        )


    except Exception as e:

        try:
            os.remove(file_path)
        except OSError:
            pass


        return render_template(
            "verify.html",

            error=(
                "Unable to read the document: "
                +
                str(e)
            ),

            username=session.get("username"),

            role=session.get("role")
        )


    # ========================================================
    # NO TEXT
    # ========================================================

    if not text.strip():

        try:
            os.remove(file_path)
        except OSError:
            pass


        return render_template(
            "verify.html",

            error=(
                "No readable text was found "
                "in the document."
            ),

            username=session.get("username"),

            role=session.get("role")
        )


    # ========================================================
    # EXTRACT INFORMATION
    # ========================================================

    document_info = extract_document_information(
        text
    )


    # ========================================================
    # LOAD DATABASE
    # ========================================================

    data = load_case_data()


    # ========================================================
    # FIND MATCHING CASE
    # ========================================================

    matched_case = None


    # --------------------------------------------------------
    # FIRST TRY FIR ID
    # --------------------------------------------------------

    if document_info["fir_id"]:

        matches = data[
            data["fir_id"]
            .astype(str)
            .str.upper()
            ==
            document_info["fir_id"].upper()
        ]


        if not matches.empty:

            matched_case = (
                matches.iloc[0].to_dict()
            )


    # --------------------------------------------------------
    # TRY OTHER FIELDS
    # --------------------------------------------------------

    if matched_case is None:

        best_match = None

        best_count = 0


        for _, row in data.iterrows():

            match_count = 0


            if (
                document_info["phone"]
                and
                str(row["phone"]).strip()
                ==
                document_info["phone"].strip()
            ):

                match_count += 1


            if (
                document_info["vehicle"]
                and
                str(row["vehicle"]).strip().upper()
                ==
                document_info["vehicle"].strip().upper()
            ):

                match_count += 1


            if (
                document_info["person"]
                and
                str(row["person"]).strip().lower()
                ==
                document_info["person"].strip().lower()
            ):

                match_count += 1


            if (
                document_info["location"]
                and
                str(row["location"]).strip().lower()
                ==
                document_info["location"].strip().lower()
            ):

                match_count += 1


            if match_count > best_count:

                best_count = match_count

                best_match = row.to_dict()


        if best_count >= 2:

            matched_case = best_match


    # ========================================================
    # COMPARE DATA
    # ========================================================

    conflicts = []

    missing_info = []

    matched_fields = []


    fields = [
        "fir_id",
        "person",
        "phone",
        "vehicle",
        "location"
    ]


    if matched_case:

        for field in fields:

            document_value = document_info.get(
                field
            )


            database_value = matched_case.get(
                field
            )


            # ------------------------------------------------
            # MISSING FROM DOCUMENT
            # ------------------------------------------------

            if not document_value:

                missing_info.append(
                    field
                )

                continue


            # ------------------------------------------------
            # NORMALIZE
            # ------------------------------------------------

            if field in [
                "fir_id",
                "phone"
            ]:

                document_compare = (
                    str(document_value)
                    .strip()
                    .upper()
                )

                database_compare = (
                    str(database_value)
                    .strip()
                    .upper()
                )

            else:

                document_compare = (
                    str(document_value)
                    .strip()
                    .lower()
                )

                database_compare = (
                    str(database_value)
                    .strip()
                    .lower()
                )


            # ------------------------------------------------
            # MATCH
            # ------------------------------------------------

            if document_compare == database_compare:

                matched_fields.append({
                    "field": field,
                    "document": document_value,
                    "dataset": database_value
                })


            # ------------------------------------------------
            # CONFLICT
            # ------------------------------------------------

            else:

                conflicts.append({

                    "field": field,

                    "document": document_value,

                    "database": database_value,
                    "dataset": database_value

                })


    else:

        for field, value in document_info.items():

            if not value:

                missing_info.append(
                    field
                )


    # ========================================================
    # STATUS
    # ========================================================

    if matched_case:

        if len(conflicts) == 0:

            status = "MATCH"

            explanation = (
                "The available information extracted "
                "from the document matches the "
                "corresponding FIR record."
            )


        elif len(matched_fields) > 0:

            status = "PARTIAL"

            explanation = (
                "Some extracted information matches "
                "the FIR record, but one or more "
                "differences were detected."
            )


        else:

            status = "NO MATCH"

            explanation = (
                "The extracted information does not "
                "match the selected FIR record."
            )


    else:

        status = "NO MATCH"

        explanation = (
            "No matching FIR record was found "
            "using the extracted document information."
        )


    # ========================================================
    # RESULT OBJECT
    # ========================================================

    result = {

        "status": status,

        "filename": filename,

        "matches": matched_fields,

        "missing": missing_info,

        "conflicts": conflicts,

        "explanation": explanation

    }


    # ========================================================
    # DELETE UPLOADED FILE
    # ========================================================

    try:

        os.remove(file_path)

    except OSError:

        pass


    # ========================================================
    # DISPLAY RESULT
    # ========================================================

    return render_template(
        "verify.html",

        result=result,

        document_info=document_info,

        matched_case=matched_case,

        username=session.get("username"),

        role=session.get("role")
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
import pandas as pd
import re

from analysis import (
    get_network_score,
    get_crime_patterns,
    get_case_connections
)


CASE_FILE = "data/cases.csv"


# ============================================================
# LOAD DATA
# ============================================================

def load_cases():
    return pd.read_csv(CASE_FILE)


# ============================================================
# FIND PERSON IN QUESTION
# ============================================================

def find_person(question, data):

    question_lower = question.lower()

    for person in data["person"].astype(str).unique():

        if person.lower() in question_lower:
            return person

    return None


# ============================================================
# FIND FIR IDs
# ============================================================

def find_firs(question):

    matches = re.findall(
        r"\bFIR\d+\b",
        question,
        re.IGNORECASE
    )

    return [fir.upper() for fir in matches]


# ============================================================
# PERSON INVESTIGATION
# ============================================================

def analyze_person(person):

    data = load_cases()

    records = data[
        data["person"]
        .astype(str)
        .str.lower()
        == person.lower()
    ]

    if records.empty:

        return f"No records found for {person}."


    firs = (
        records["fir_id"]
        .astype(str)
        .unique()
        .tolist()
    )

    phones = (
        records["phone"]
        .astype(str)
        .unique()
        .tolist()
    )

    vehicles = (
        records["vehicle"]
        .astype(str)
        .unique()
        .tolist()
    )

    locations = (
        records["location"]
        .astype(str)
        .unique()
        .tolist()
    )


    score = get_network_score(person)


    response = []

    response.append(
        f"AI Investigation Report: {person}"
    )

    response.append(
        "\n1. CASE INFORMATION"
    )

    response.append(
        f"Total FIR records: {len(firs)}"
    )

    response.append(
        "FIRs: " + ", ".join(firs)
    )


    response.append(
        "\n2. ASSOCIATED INFORMATION"
    )

    response.append(
        "Phone numbers:"
    )

    for phone in phones:
        response.append(
            f"• {phone}"
        )


    response.append(
        "Vehicles:"
    )

    for vehicle in vehicles:
        response.append(
            f"• {vehicle}"
        )


    response.append(
        "Locations:"
    )

    for location in locations:
        response.append(
            f"• {location}"
        )


    # --------------------------------------------------------
    # NETWORK SCORE
    # --------------------------------------------------------

    if score:

        response.append(
            "\n3. NETWORK ANALYSIS"
        )

        response.append(
            f"Network indicator: "
            f"{score['score']}/10"
        )

        response.append(
            f"Level: {score['level']}"
        )

        response.append(
            f"FIR connections: {score['fir_count']}"
        )

        response.append(
            f"Phone connections: {score['phone_count']}"
        )

        response.append(
            f"Vehicle connections: "
            f"{score['vehicle_count']}"
        )

        response.append(
            f"Location connections: "
            f"{score['location_count']}"
        )


    # --------------------------------------------------------
    # INVESTIGATION INDICATORS
    # --------------------------------------------------------

    response.append(
        "\n4. POTENTIAL INVESTIGATIVE INDICATORS"
    )

    indicators = 0


    if len(firs) > 1:

        response.append(
            "• Person appears in multiple FIR records."
        )

        indicators += 1


    if len(phones) < len(firs):

        response.append(
            "• A phone number appears across "
            "multiple records."
        )

        indicators += 1


    if len(vehicles) < len(firs):

        response.append(
            "• A vehicle appears across "
            "multiple records."
        )

        indicators += 1


    if len(locations) < len(firs):

        response.append(
            "• A location is repeated across "
            "multiple records."
        )

        indicators += 1


    if indicators == 0:

        response.append(
            "• No repeated relationship indicators "
            "were detected in the available data."
        )


    response.append(
        "\n5. AI INVESTIGATION ASSESSMENT"
    )

    if indicators >= 3:

        response.append(
            "Multiple repeated data relationships "
            "were detected. An investigator may "
            "review the related FIR records and "
            "associated entities."
        )

    elif indicators >= 1:

        response.append(
            "Some repeated data relationships were "
            "detected and may be relevant for "
            "further investigation."
        )

    else:

        response.append(
            "No significant repeated relationships "
            "were detected in the available dataset."
        )


    response.append(
        "\n⚠ Important: These findings are based "
        "only on the available dataset. They are "
        "investigative indicators and do not "
        "establish guilt or criminal responsibility."
    )


    return "\n".join(response)


# ============================================================
# FIR ANALYSIS
# ============================================================

def analyze_fir(fir_id):

    data = load_cases()

    records = data[
        data["fir_id"]
        .astype(str)
        .str.upper()
        == fir_id.upper()
    ]


    if records.empty:

        return f"No record found for {fir_id}."


    row = records.iloc[0]


    response = []

    response.append(
        f"AI Investigation Report: {fir_id}"
    )


    response.append(
        "\nCASE DETAILS"
    )

    response.append(
        f"Person: {row['person']}"
    )

    response.append(
        f"Phone: {row['phone']}"
    )

    response.append(
        f"Vehicle: {row['vehicle']}"
    )

    response.append(
        f"Location: {row['location']}"
    )


    # --------------------------------------------------------
    # FIND RELATED FIRs
    # --------------------------------------------------------

    related = []


    for _, other in data.iterrows():

        other_fir = str(
            other["fir_id"]
        )

        if other_fir.upper() == fir_id.upper():
            continue


        reasons = []


        if (
            str(other["person"]).strip().lower()
            ==
            str(row["person"]).strip().lower()
        ):

            reasons.append("same person")


        if (
            str(other["phone"]).strip()
            ==
            str(row["phone"]).strip()
        ):

            reasons.append("same phone")


        if (
            str(other["vehicle"]).strip().lower()
            ==
            str(row["vehicle"]).strip().lower()
        ):

            reasons.append("same vehicle")


        if (
            str(other["location"]).strip().lower()
            ==
            str(row["location"]).strip().lower()
        ):

            reasons.append("same location")


        if reasons:

            related.append(
                (
                    other_fir,
                    reasons
                )
            )


    # --------------------------------------------------------
    # RELATED CASES
    # --------------------------------------------------------

    response.append(
        "\nRELATED CASES"
    )


    if related:

        for other_fir, reasons in related:

            response.append(
                f"• {other_fir}"
            )

            response.append(
                "  Connection: "
                + ", ".join(reasons)
            )

    else:

        response.append(
            "No directly connected FIRs "
            "were found."
        )


    response.append(
        "\nINVESTIGATION NOTE"
    )

    if related:

        response.append(
            "The case has shared information with "
            "one or more other records. These "
            "relationships may be reviewed by "
            "an investigator."
        )

    else:

        response.append(
            "No direct shared information was "
            "detected with other FIR records."
        )


    response.append(
        "\n⚠ Shared information represents "
        "potential investigative connections "
        "and does not establish wrongdoing."
    )


    return "\n".join(response)


# ============================================================
# COMPARE FIRs
# ============================================================

def compare_firs(fir1, fir2):

    data = load_cases()


    case1 = data[
        data["fir_id"]
        .astype(str)
        .str.upper()
        == fir1.upper()
    ]

    case2 = data[
        data["fir_id"]
        .astype(str)
        .str.upper()
        == fir2.upper()
    ]


    if case1.empty:

        return f"{fir1} was not found."


    if case2.empty:

        return f"{fir2} was not found."


    row1 = case1.iloc[0]
    row2 = case2.iloc[0]


    response = []

    response.append(
        f"AI Case Comparison"
    )

    response.append(
        f"\n{fir1}"
    )

    response.append(
        f"• Person: {row1['person']}"
    )

    response.append(
        f"• Phone: {row1['phone']}"
    )

    response.append(
        f"• Vehicle: {row1['vehicle']}"
    )

    response.append(
        f"• Location: {row1['location']}"
    )


    response.append(
        f"\n{fir2}"
    )

    response.append(
        f"• Person: {row2['person']}"
    )

    response.append(
        f"• Phone: {row2['phone']}"
    )

    response.append(
        f"• Vehicle: {row2['vehicle']}"
    )

    response.append(
        f"• Location: {row2['location']}"
    )


    response.append(
        "\nDETECTED CONNECTIONS"
    )


    connections = []


    if (
        str(row1["person"]).strip().lower()
        ==
        str(row2["person"]).strip().lower()
    ):

        connections.append(
            "Same person"
        )


    if (
        str(row1["phone"]).strip()
        ==
        str(row2["phone"]).strip()
    ):

        connections.append(
            "Same phone number"
        )


    if (
        str(row1["vehicle"]).strip().lower()
        ==
        str(row2["vehicle"]).strip().lower()
    ):

        connections.append(
            "Same vehicle"
        )


    if (
        str(row1["location"]).strip().lower()
        ==
        str(row2["location"]).strip().lower()
    ):

        connections.append(
            "Same location"
        )


    if connections:

        for connection in connections:

            response.append(
                f"• {connection}"
            )

    else:

        response.append(
            "• No directly shared fields detected."
        )


    response.append(
        "\nAI ASSESSMENT"
    )


    if len(connections) >= 2:

        response.append(
            "Multiple shared data attributes were "
            "detected between the two FIR records. "
            "These cases may warrant further review."
        )

    elif len(connections) == 1:

        response.append(
            "One shared data attribute was detected. "
            "Further investigation may be required "
            "to determine its significance."
        )

    else:

        response.append(
            "No direct shared attributes were detected "
            "between the two records."
        )


    response.append(
        "\n⚠ This comparison identifies data "
        "relationships only and does not establish guilt."
    )


    return "\n".join(response)


# ============================================================
# REPEATED PERSONS
# ============================================================

def repeated_persons():

    data = load_cases()

    counts = data["person"].value_counts()

    repeated = counts[counts > 1]


    if repeated.empty:

        return (
            "No persons appear in multiple FIR records."
        )


    response = []

    response.append(
        "AI Pattern Analysis: Repeated Persons"
    )

    response.append("")


    for person, count in repeated.items():

        response.append(
            f"• {person} → {count} FIRs"
        )


    response.append(
        "\nThese repeated appearances may be "
        "reviewed as potential investigative indicators."
    )


    return "\n".join(response)


# ============================================================
# REPEATED PHONES
# ============================================================

def repeated_phones():

    patterns = get_crime_patterns()


    if not patterns["phones"]:

        return (
            "No repeated phone numbers were found."
        )


    response = [
        "AI Pattern Analysis: Shared Phone Numbers",
        ""
    ]


    for item in patterns["phones"]:

        response.append(
            f"• {item['value']} → "
            f"{item['count']} records"
        )


    return "\n".join(response)


# ============================================================
# REPEATED VEHICLES
# ============================================================

def repeated_vehicles():

    patterns = get_crime_patterns()


    if not patterns["vehicles"]:

        return (
            "No repeated vehicles were found."
        )


    response = [
        "AI Pattern Analysis: Repeated Vehicles",
        ""
    ]


    for item in patterns["vehicles"]:

        response.append(
            f"• {item['value']} → "
            f"{item['count']} records"
        )


    return "\n".join(response)


# ============================================================
# REPEATED LOCATIONS
# ============================================================

def repeated_locations():

    patterns = get_crime_patterns()


    if not patterns["locations"]:

        return (
            "No repeated locations were found."
        )


    response = [
        "AI Pattern Analysis: Repeated Locations",
        ""
    ]


    for item in patterns["locations"]:

        response.append(
            f"• {item['value']} → "
            f"{item['count']} cases"
        )


    return "\n".join(response)


# ============================================================
# DATASET OVERVIEW
# ============================================================

def general_overview():

    data = load_cases()


    total_firs = data["fir_id"].nunique()

    total_persons = data["person"].nunique()

    total_phones = data["phone"].nunique()

    total_vehicles = data["vehicle"].nunique()

    total_locations = data["location"].nunique()


    response = []

    response.append(
        "AI Investigation Dataset Overview"
    )

    response.append(
        f"\nTotal FIRs: {total_firs}"
    )

    response.append(
        f"Unique persons: {total_persons}"
    )

    response.append(
        f"Unique phone numbers: {total_phones}"
    )

    response.append(
        f"Unique vehicles: {total_vehicles}"
    )

    response.append(
        f"Unique locations: {total_locations}"
    )


    counts = data["person"].value_counts()


    if not counts.empty:

        response.append(
            f"\nMost frequently appearing person: "
            f"{counts.index[0]} "
            f"({counts.iloc[0]} FIRs)"
        )


    response.append(
        "\nThe investigation agent can analyze "
        "FIR records, repeated entities and "
        "potential case relationships."
    )


    response.append(
        "\n⚠ The results are investigative indicators "
        "based on the available dataset."
    )


    return "\n".join(response)


# ============================================================
# MAIN AI AGENT
# ============================================================

def answer_question(question):

    data = load_cases()

    question_lower = question.lower().strip()


    if not question_lower:

        return (
            "Please enter an investigation question."
        )


    # ========================================================
    # COMPARE TWO FIRs
    # ========================================================

    firs = find_firs(question)


    if len(firs) >= 2:

        return compare_firs(
            firs[0],
            firs[1]
        )


    # ========================================================
    # SINGLE FIR
    # ========================================================

    if len(firs) == 1:

        return analyze_fir(
            firs[0]
        )


    # ========================================================
    # PERSON
    # ========================================================

    person = find_person(
        question,
        data
    )


    if person:

        return analyze_person(
            person
        )


    # ========================================================
    # REPEATED PERSONS
    # ========================================================

    if (
        "multiple fir" in question_lower
        or
        "repeated person" in question_lower
        or
        "repeat person" in question_lower
        or
        "persons appear" in question_lower
        or
        "people appear" in question_lower
        or
        "most fir" in question_lower
    ):

        return repeated_persons()


    # ========================================================
    # SHARED PHONE
    # ========================================================

    if (
        "phone" in question_lower
        or
        "mobile" in question_lower
        or
        "shared number" in question_lower
    ):

        return repeated_phones()


    # ========================================================
    # VEHICLE
    # ========================================================

    if (
        "vehicle" in question_lower
        or
        "vehicles" in question_lower
        or
        "shared vehicle" in question_lower
    ):

        return repeated_vehicles()


    # ========================================================
    # LOCATION
    # ========================================================

    if (
        "location" in question_lower
        or
        "locations" in question_lower
        or
        "shared location" in question_lower
    ):

        return repeated_locations()


    # ========================================================
    # OVERVIEW
    # ========================================================

    if (
        "summary" in question_lower
        or
        "overview" in question_lower
        or
        "dataset" in question_lower
        or
        "total" in question_lower
        or
        "analyse" in question_lower
        or
        "analyze" in question_lower
        or
        "all cases" in question_lower
    ):

        return general_overview()


    # ========================================================
    # HELP
    # ========================================================

    return (
        "I can help analyze the available "
        "investigation dataset.\n\n"

        "Try asking:\n"

        "• Tell me about FIR001\n"

        "• Find everything about Ravi\n"

        "• What connections does Ravi have?\n"

        "• Which persons appear in multiple FIRs?\n"

        "• Which phone numbers are shared?\n"

        "• Which vehicles are repeated?\n"

        "• Which locations have repeated cases?\n"

        "• Compare FIR001 and FIR002\n"

        "• Give me an overview\n\n"

        "⚠ Results are dataset-based "
        "investigative indicators only."
    )
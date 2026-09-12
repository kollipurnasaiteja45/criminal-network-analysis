import pandas as pd
import networkx as nx
import os


# ============================================================
# FILE PATH
# ============================================================

CASE_FILE = "data/cases.csv"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not os.path.exists(CASE_FILE):
        return pd.DataFrame(
            columns=[
                "fir_id",
                "person",
                "phone",
                "vehicle",
                "location"
            ]
        )

    data = pd.read_csv(CASE_FILE)

    # --------------------------------------------------------
    # REMOVE EXTRA SPACES FROM COLUMN NAMES
    # --------------------------------------------------------

    data.columns = (
        data.columns
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # --------------------------------------------------------
    # SUPPORT DIFFERENT COLUMN NAMES
    # --------------------------------------------------------

    column_aliases = {

        "fir_id": [
            "fir_id",
            "fir",
            "fir_no",
            "fir_number",
            "crime_fir_number"
        ],

        "person": [
            "person",
            "name",
            "accused",
            "accused_name",
            "person_name"
        ],

        "phone": [
            "phone",
            "phone_number",
            "mobile",
            "mobile_number",
            "contact"
        ],

        "vehicle": [
            "vehicle",
            "vehicle_number",
            "vehicle_no",
            "registration_number"
        ],

        "location": [
            "location",
            "incident_location",
            "incident_address",
            "exact_incident_location",
            "exact_incident_address",
            "place",
            "address"
        ]
    }

    # --------------------------------------------------------
    # RENAME ALIAS COLUMNS
    # --------------------------------------------------------

    rename_map = {}

    for standard_name, aliases in column_aliases.items():

        for alias in aliases:

            if alias in data.columns:

                rename_map[alias] = standard_name
                break

    data = data.rename(
        columns=rename_map
    )

    # --------------------------------------------------------
    # CREATE MISSING STANDARD COLUMNS
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

    # --------------------------------------------------------
    # CLEAN VALUES
    # --------------------------------------------------------

    for column in required_columns:

        data[column] = (
            data[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    return data


# ============================================================
# CREATE CRIMINAL NETWORK
# ============================================================

def create_network():

    data = load_data()

    graph = nx.Graph()

    for _, row in data.iterrows():

        person = str(row["person"]).strip()
        fir = str(row["fir_id"]).strip()
        phone = str(row["phone"]).strip()
        location = str(row["location"]).strip()
        vehicle = str(row["vehicle"]).strip()

        # ----------------------------------------------------
        # PERSON
        # ----------------------------------------------------

        if person:

            graph.add_node(
                person,
                type="Person"
            )

        # ----------------------------------------------------
        # FIR
        # ----------------------------------------------------

        if fir:

            graph.add_node(
                fir,
                type="FIR"
            )

            if person:
                graph.add_edge(
                    person,
                    fir
                )

        # ----------------------------------------------------
        # PHONE
        # ----------------------------------------------------

        if phone:

            graph.add_node(
                phone,
                type="Phone"
            )

            if person:
                graph.add_edge(
                    person,
                    phone
                )

        # ----------------------------------------------------
        # VEHICLE
        # ----------------------------------------------------

        if vehicle:

            graph.add_node(
                vehicle,
                type="Vehicle"
            )

            if person:
                graph.add_edge(
                    person,
                    vehicle
                )

        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        if location:

            graph.add_node(
                location,
                type="Location"
            )

            if person:
                graph.add_edge(
                    person,
                    location
                )

    return graph


# ============================================================
# GRAPH DATA FOR NETWORK PAGE
# ============================================================

def get_graph_data():

    graph = create_network()

    nodes = []
    edges = []

    for node in graph.nodes:

        nodes.append({
            "id": str(node),
            "label": str(node),
            "type": graph.nodes[node].get(
                "type",
                "Unknown"
            )
        })

    for source, target in graph.edges:

        edges.append({
            "source": str(source),
            "target": str(target)
        })

    return {
        "nodes": nodes,
        "edges": edges
    }


# ============================================================
# PERSON NETWORK
# ============================================================

def get_person_network(person_name):

    graph = create_network()

    person_name = (
        str(person_name)
        .strip()
        .lower()
    )

    actual_person = None

    for node in graph.nodes:

        if graph.nodes[node].get("type") == "Person":

            if str(node).lower() == person_name:

                actual_person = node
                break

    if actual_person is None:

        return None, []

    relationships = []

    for node in graph.neighbors(
        actual_person
    ):

        relationships.append({
            "name": node,
            "type": graph.nodes[node].get(
                "type",
                "Unknown"
            )
        })

    return actual_person, relationships


# ============================================================
# NETWORK SCORE
# ============================================================

def get_network_score(person_name):

    graph = create_network()

    person_name = (
        str(person_name)
        .strip()
        .lower()
    )

    actual_person = None

    for node in graph.nodes:

        if graph.nodes[node].get("type") == "Person":

            if str(node).lower() == person_name:

                actual_person = node
                break

    if actual_person is None:

        return None

    fir_count = 0
    phone_count = 0
    vehicle_count = 0
    location_count = 0

    for node in graph.neighbors(
        actual_person
    ):

        node_type = graph.nodes[node].get(
            "type"
        )

        if node_type == "FIR":
            fir_count += 1

        elif node_type == "Phone":
            phone_count += 1

        elif node_type == "Vehicle":
            vehicle_count += 1

        elif node_type == "Location":
            location_count += 1

    raw_score = (
        fir_count * 1.5
        + phone_count * 1
        + vehicle_count * 1.5
        + location_count * 1
    )

    score = min(
        raw_score,
        10
    )

    if score >= 7:

        level = "High"

    elif score >= 4:

        level = "Moderate"

    else:

        level = "Low"

    return {

        "person": actual_person,

        "fir_count": fir_count,

        "phone_count": phone_count,

        "vehicle_count": vehicle_count,

        "location_count": location_count,

        "score": round(
            score,
            1
        ),

        "level": level
    }


# ============================================================
# NETWORK INSIGHTS
# ============================================================

def get_insights():

    graph = create_network()

    degree = dict(
        graph.degree()
    )

    important_nodes = sorted(
        degree.items(),
        key=lambda x: x[1],
        reverse=True
    )

    insights = []

    for node, connections in important_nodes:

        if graph.nodes[node].get(
            "type"
        ) == "Person":

            insights.append({

                "person": node,

                "connections": connections

            })

    return insights


# ============================================================
# CRIME PATTERNS
# ============================================================

def get_crime_patterns():

    data = load_data()

    patterns = {

        "persons": [],

        "phones": [],

        "vehicles": [],

        "locations": []

    }

    # --------------------------------------------------------
    # PERSON PATTERNS
    # --------------------------------------------------------

    person_counts = (
        data["person"]
        .value_counts()
    )

    for person, count in person_counts.items():

        if person and count > 1:

            patterns["persons"].append({

                "value": person,

                "count": int(count)

            })

    # --------------------------------------------------------
    # PHONE PATTERNS
    # --------------------------------------------------------

    phone_counts = (
        data["phone"]
        .value_counts()
    )

    for phone, count in phone_counts.items():

        if phone and count > 1:

            patterns["phones"].append({

                "value": phone,

                "count": int(count)

            })

    # --------------------------------------------------------
    # VEHICLE PATTERNS
    # --------------------------------------------------------

    vehicle_counts = (
        data["vehicle"]
        .value_counts()
    )

    for vehicle, count in vehicle_counts.items():

        if vehicle and count > 1:

            patterns["vehicles"].append({

                "value": vehicle,

                "count": int(count)

            })

    # --------------------------------------------------------
    # LOCATION PATTERNS
    # --------------------------------------------------------

    location_counts = (
        data["location"]
        .value_counts()
    )

    for location, count in location_counts.items():

        if location and count > 1:

            patterns["locations"].append({

                "value": location,

                "count": int(count)

            })

    return patterns


# ============================================================
# CASE CONNECTIONS
# ============================================================

def get_case_connections():

    data = load_data()

    connections = {

        "persons": [],

        "phones": [],

        "vehicles": [],

        "locations": []

    }

    # --------------------------------------------------------
    # COMPARE EVERY CASE WITH EVERY OTHER CASE
    # --------------------------------------------------------

    for i in range(
        len(data)
    ):

        for j in range(
            i + 1,
            len(data)
        ):

            case1 = data.iloc[i]
            case2 = data.iloc[j]

            fir1 = str(
                case1["fir_id"]
            ).strip()

            fir2 = str(
                case2["fir_id"]
            ).strip()

            # ------------------------------------------------
            # PERSON CONNECTION
            # ------------------------------------------------

            person1 = (
                str(case1["person"])
                .strip()
                .lower()
            )

            person2 = (
                str(case2["person"])
                .strip()
                .lower()
            )

            if (
                person1
                and
                person1 == person2
            ):

                connections["persons"].append({

                    "fir1": fir1,

                    "fir2": fir2,

                    "value": str(
                        case1["person"]
                    )

                })

            # ------------------------------------------------
            # PHONE CONNECTION
            # ------------------------------------------------

            phone1 = (
                str(case1["phone"])
                .strip()
            )

            phone2 = (
                str(case2["phone"])
                .strip()
            )

            if (
                phone1
                and
                phone1 == phone2
            ):

                connections["phones"].append({

                    "fir1": fir1,

                    "fir2": fir2,

                    "value": phone1

                })

            # ------------------------------------------------
            # VEHICLE CONNECTION
            # ------------------------------------------------

            vehicle1 = (
                str(case1["vehicle"])
                .strip()
                .lower()
            )

            vehicle2 = (
                str(case2["vehicle"])
                .strip()
                .lower()
            )

            if (
                vehicle1
                and
                vehicle1 == vehicle2
            ):

                connections["vehicles"].append({

                    "fir1": fir1,

                    "fir2": fir2,

                    "value": str(
                        case1["vehicle"]
                    )

                })

            # ------------------------------------------------
            # LOCATION CONNECTION
            # ------------------------------------------------

            location1 = (
                str(case1["location"])
                .strip()
                .lower()
            )

            location2 = (
                str(case2["location"])
                .strip()
                .lower()
            )

            if (
                location1
                and
                location1 == location2
            ):

                connections["locations"].append({

                    "fir1": fir1,

                    "fir2": fir2,

                    "value": str(
                        case1["location"]
                    )

                })

    return connections
import json
from neo4j import GraphDatabase

# Function for list of dictionaries to json file
def list_to_json(data, json_file):
    """ Save list of dictionaries to json file """
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, indent=4))

# Connect to Neo4j
URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "password"
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

# Path queries
queries = [
    { # Query 1: Find all equipment with undesirable properties
        "query": "MATCH (o:PhysicalObject)-[:hasProperty]->(p:Property {subtype0: 'UndesirableProperty'}) "
                    "RETURN properties(o) AS object_properties, properties(p) AS property_properties",
        "outpair": "equipment_property_pairs",
        "event": "property",
        "relation": "hasProperty"
    },
    { # Query 2: Find all undesirable processes with agents
        "query": "MATCH (p:Process {subtype0: 'UndesirableProcess'})-[:hasParticipant_hasAgent]->(o:PhysicalObject) "
                    "RETURN properties(o) AS object_properties, properties(p) AS process_properties",
        "outpair": "process_agent_pairs",
        "event": "process",
        "relation": "hasAgent"
    },
    { # Query 3: Find all undesirable processes with patients
        "query": "MATCH (p:Process {subtype0: 'UndesirableProcess'})-[:hasParticipant_hasPatient]->(o:PhysicalObject) "
                    "RETURN properties(o) AS object_properties, properties(p) AS process_properties",
        "outpair": "process_patient_pairs",
        "event": "process",
        "relation": "hasPatient"
    },
    { # Query 4: Find all undesirable states with agents
        "query": "MATCH (s:State {subtype0: 'UndesirableState'})-[:hasParticipant_hasAgent]->(o:PhysicalObject) "
                    "RETURN properties(o) AS object_properties, properties(s) AS state_properties",
        "outpair": "state_agent_pairs",
        "event": "state",
        "relation": "hasAgent"
    },
    { # Query 5: Find all undesirable states with patients
        "query": "MATCH (s:State {subtype0: 'UndesirableState'})-[:hasParticipant_hasPatient]->(o:PhysicalObject) "
                    "RETURN properties(o) AS object_properties, properties(s) AS state_properties",
        "outpair": "state_patient_pairs",
        "event": "state",
        "relation": "hasPatient"
    }
]

with driver.session() as session:
    for query in queries:
        results = session.run(query["query"])
        pairs = []
        for record in results:
            object_properties = record["object_properties"]
            object_type = f"{object_properties['type']}"
            object_name = object_properties["text"]
            if "subtype0" in object_properties:
                object_type = object_type + f"/{object_properties['subtype0']}"
                
            event_properties = record[f"{query['event']}_properties"]
            event_type = f"{event_properties['type']}"
            if "subtype0" in event_properties:
                event_type = event_type + f"/{event_properties['subtype0']}"
            event_name = event_properties["text"]
            pair = {
                "object_type": object_type,
                "object_name": object_name,
                "relation": query["relation"],
                f"{query['event']}_type": event_type,
                f"{query['event']}_name": event_name
            }
            pairs.append(pair)
        list_to_json(pairs, f"pathPatterns/{query['outpair']}.json")

driver.close()
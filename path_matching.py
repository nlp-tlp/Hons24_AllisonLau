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
        "query": """
                MATCH (o:PhysicalObject)-[:hasProperty]->(p:Property {subtype0: "UndesirableProperty"})
                OPTIONAL MATCH (o)-[r]->(other:PhysicalObject)
                RETURN properties(o) AS object_properties, properties(p) AS property_properties, 
                       collect(type(r)) AS relations, collect(properties(other)) AS other_objects
                """,
        "outfile": "equipment_property_patterns",
        "event": "property",
        "relation": "hasProperty"
    },
    { # Query 2: Find all undesirable processes with agents
        "query": """
                MATCH (p:Process {subtype0: 'UndesirableProcess'})-[:hasParticipant_hasAgent]->(o:PhysicalObject)
                OPTIONAL MATCH (o)-[r]->(other:PhysicalObject)
                RETURN properties(o) AS object_properties, properties(p) AS process_properties, 
                       collect(type(r)) AS relations, collect(properties(other)) AS other_objects
                """,
        "outfile": "process_agent_patterns",
        "event": "process",
        "relation": "hasAgent"
    },
    { # Query 3: Find all undesirable processes with patients
        "query": """
                MATCH (p:Process {subtype0: 'UndesirableProcess'})-[:hasParticipant_hasPatient]->(o:PhysicalObject)
                OPTIONAL MATCH (o)-[r]->(other:PhysicalObject)
                RETURN properties(o) AS object_properties, properties(p) AS process_properties, 
                       collect(type(r)) AS relations, collect(properties(other)) AS other_objects
                """,
        "outfile": "process_patient_patterns",
        "event": "process",
        "relation": "hasPatient"
    },
    { # Query 4: Find all undesirable states with agents
        "query": """
                MATCH (s:State {subtype0: 'UndesirableState'})-[:hasParticipant_hasAgent]->(o:PhysicalObject)
                OPTIONAL MATCH (o)-[r]->(other:PhysicalObject)
                RETURN properties(o) AS object_properties, properties(s) AS state_properties, 
                       collect(type(r)) AS relations, collect(properties(other)) AS other_objects
                """,
        "outfile": "state_agent_patterns",
        "event": "state",
        "relation": "hasAgent"
    },
    { # Query 5: Find all undesirable states with patients
        "query": """
                MATCH (s:State {subtype0: 'UndesirableState'})-[:hasParticipant_hasPatient]->(o:PhysicalObject)
                OPTIONAL MATCH (o)-[r]->(other:PhysicalObject)
                RETURN properties(o) AS object_properties, properties(s) AS state_properties, 
                       collect(type(r)) AS relations, collect(properties(other)) AS other_objects
                """,
        "outfile": "state_patient_patterns",
        "event": "state",
        "relation": "hasPatient"
    }
]

with driver.session() as session:
    for query in queries:
        results = session.run(query["query"])
        patterns = []
        for record in results:
            # PhysicalObject - Equipment
            object_properties = record["object_properties"]
            object_name = object_properties["text"]
            object_type = f"{object_properties['type']}"
            if "subtype0" in object_properties:
                object_type = object_type + f"/{object_properties['subtype0']}"
                
            # Property / Process / State - Undesirable event
            event_properties = record[f"{query['event']}_properties"]
            event_name = event_properties["text"]
            event_type = f"{event_properties['type']}"
            if "subtype0" in event_properties:
                event_type = event_type + f"/{event_properties['subtype0']}"
            
            pattern = {
                "object_type": object_type,
                "object_name": object_name,
                "event_relation": query["relation"],
                f"{query['event']}_type": event_type,
                f"{query['event']}_name": event_name,
                "object_relations": []
            }
            
             # If PhysicalObject has relations to other PhysicalObjects
            for relation, other in zip(record["relations"], record["other_objects"]):
                other_name = other["text"]
                other_type = f"{other['type']}"
                if "subtype0" in other:
                    other_type = other_type + f"/{other['subtype0']}"
                
                pattern["object_relations"].append({
                    "relation": relation,
                    "object_type": other_type,
                    "object_name": other_name
                })
            
            patterns.append(pattern)
            
        print(f"Number of {query['outfile']}: {len(patterns)}")
        list_to_json(patterns, f"pathPatterns/{query['outfile']}.json")

driver.close()
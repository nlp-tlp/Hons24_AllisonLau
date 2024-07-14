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
PO_MATCH =  """
                OPTIONAL MATCH (connect_objects:PhysicalObject)-[connect_r:hasPart|contains]->(o)
                OPTIONAL MATCH (o)-[substitute_r:isA]->(substitute_objects:PhysicalObject)
            """
PO_RETURN = """
                collect(type(connect_r)) AS connect_relations, collect(type(substitute_r)) AS substitute_relations,  
                collect(properties(connect_objects)) AS connect_objects, collect(properties(substitute_objects)) AS substitute_objects
            """

direct_queries = [
    { # Query 1: Find all OBJECT with undesirable properties
        "query": f"""
                    MATCH (o:PhysicalObject)-[:hasProperty]->(p:Property {{subtype0: "UndesirableProperty"}}) {PO_MATCH}
                    RETURN properties(o) AS object_properties, properties(p) AS property_properties, {PO_RETURN}
                """,
        "outfile": "object_property_patterns",
        "event": "property",
        "relation": "hasProperty"
    },
    { # Query 2: Find all undesirable processes with agents OBJECT
        "query": f"""
                    MATCH (p:Process {{subtype0: 'UndesirableProcess'}})-[:hasParticipant_hasAgent]->(o:PhysicalObject) {PO_MATCH}
                    RETURN properties(o) AS object_properties, properties(p) AS process_properties, {PO_RETURN}
                """,
        "outfile": "process_agent_patterns",
        "event": "process",
        "relation": "hasAgent"
    },
    { # Query 3: Find all undesirable processes with patients OBJECT
        "query": f"""
                    MATCH (p:Process {{subtype0: 'UndesirableProcess'}})-[:hasParticipant_hasPatient]->(o:PhysicalObject) {PO_MATCH}
                    RETURN properties(o) AS object_properties, properties(p) AS process_properties, {PO_RETURN}
                """,
        "outfile": "process_patient_patterns",
        "event": "process",
        "relation": "hasPatient"
    },
    { # Query 4: Find all undesirable states with patients OBJECT
        "query": f"""
                    MATCH (s:State {{subtype0: 'UndesirableState'}})-[:hasParticipant_hasPatient]->(o:PhysicalObject) {PO_MATCH}
                    RETURN properties(o) AS object_properties, properties(s) AS state_properties, {PO_RETURN}
                """,
        "outfile": "state_patient_patterns",
        "event": "state",
        "relation": "hasPatient"
    }
]

complex_queries = [
    { # Query 5: Find all undesirable states with agents OBJECT
        "query": f"""
                    MATCH (s:State {{subtype0: 'UndesirableState'}})-[:hasParticipant_hasAgent]->(o:PhysicalObject) {PO_MATCH}
                    RETURN properties(o) AS object_properties, properties(s) AS state_properties, {PO_RETURN}
                """,
        "outfile": "state_agent_patterns",
        "event": "state",
        "relation": "hasAgent"
    },
    { # Query 6: Find all OBJECT with properties linked to undesirable states
        "query": f"""
                    MATCH (o:PhysicalObject)-[:hasProperty]->(p:Property)
                    MATCH (s:State {{subtype0: 'UndesirableState'}})-[:hasParticipant_hasPatient]->(p) {PO_MATCH}
                    RETURN properties(o) AS object_properties, properties(p) AS property_properties, properties(s) AS state_properties, {PO_RETURN}
                """,
        "outfile": "object_property_state_patterns",
        "event": "property",
        "helper": "state",
        "relation": "hasProperty"
    },
    { # Query 7: Find all undesirable states with agents OBJECT where states linked to activities
        "query": f"""
                    MATCH (s:State {{subtype0: 'UndesirableState'}})-[:hasParticipant_hasAgent]->(o:PhysicalObject)
                    MATCH (s)-[:hasParticipant_hasPatient]->(a:Activity) {PO_MATCH}
                    RETURN properties(o) AS object_properties, properties(s) AS state_properties, properties(a) AS activity_properties, {PO_RETURN}
                """,
        "outfile": "state_agent_activity_patterns",
        "event": "state",
        "helper": "activity",
        "relation": "hasAgent"
    }
]

# Function to get entity type
def get_entity_type(properties):
    """ Construct entity class/subclass from properties """
    entity_type = properties["type"]
    if "subtype0" in properties:
        entity_type += "/" + properties["subtype0"]
    if "subtype1" in properties:
        entity_type += "/" + properties["subtype1"]
    return entity_type

# Function to get entity information
def get_entity_info(record, entity):
    """ Extract entity information from record """
    properties = record[f"{entity}_properties"]
    return {
        "name": properties["text"],
        "type": get_entity_type(properties)
    }

# Function to get relation information
def get_relation_info(record, po_relation, po_type):
    """ Extract relation information from record """
    output = [
        {
            "relation": relation,
            "object_type": get_entity_type(object),
            "object_name": object["text"]
        }
        for relation, object in zip(record[po_relation], record[po_type])
    ]
    return output, len(output)

def process_query_results(results, patterns):
    """ Process query results and extract relevant information """

    alternate_pattern_count = 0
    for record in results:
        # PhysicalObject - Equipment
        object_info = get_entity_info(record, "object")
        
        # Property / Process / State - Undesirable event
        event_info = get_entity_info(record, query["event"])
        
        # If there are helper entities that describe the Undesirable event
        helper_info = get_entity_info(record, query["helper"]) if "helper" in query else None
        
        # If PhysicalObject has connect relations to other PhysicalObjects
        # connect_relations: hasPart, contains
        connect_info, num_connect = get_relation_info(record, "connect_relations", "connect_objects")
        
        # If PhysicalObject has substitute relations to other PhysicalObjects
        # substitute_relations: isA
        substitute_info, num_substitute = get_relation_info(record, "substitute_relations", "substitute_objects")
        
        pattern = {
            "object_type": object_info["type"],
            "object_name": object_info["name"],
            "event_relation": query["relation"],
            f"{query['event']}_type": event_info["type"],
            f"{query['event']}_name": event_info["name"],
            "helper_type": helper_info["type"] if helper_info else None,
            "helper_name": helper_info["name"] if helper_info else None,
            "object_relations": connect_info + substitute_info
        }
        
        patterns.append(pattern)
        alternate_pattern_count += num_connect + num_substitute

    return alternate_pattern_count

with driver.session() as session:
    for query in direct_queries:
        results = session.run(query["query"])
        patterns = []
        alternate_count = process_query_results(results, patterns)

        print("{:<40} {}".format(f"Number of {query['outfile']}:", len(patterns)))
        print(" - {:<37} {}".format(f"Number of alternate patterns:", alternate_count))
        list_to_json(patterns, f"pathPatterns/{query['outfile']}.json")
        
    
    # for query in complex_queries:
    #     results = session.run(query["query"])
    #     patterns = []
    #     process_query_results(results, patterns)

    #     print("{:<42} {}".format(f"Number of {query['outfile']}:", len(patterns)))
    #     list_to_json(patterns, f"pathPatterns/{query['outfile']}.json")

driver.close()
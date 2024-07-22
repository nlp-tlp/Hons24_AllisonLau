import json
from neo4j import GraphDatabase
from path_queries import direct_queries, complex_queries

# Function for list of dictionaries to json file
def list_to_json(data, json_file):
    """ Save list of dictionaries to json file """
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, indent=4))

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
        "type": get_entity_type(properties),
        "entry_id": properties["entry_id"]
    }

# Function to get relation information
def get_alternate_paths(query, record, object, event, valid, helper=None):
    """ Extract relation information from record """
    alternate_paths = []
    # If PhysicalObject has connect relations to other PhysicalObjects
    # connect_relations: hasPart, contains
    current_obj = object["name"]
    for connect_obj in record["connect_objects"]:
        current_obj = f"{connect_obj['text']} {current_obj}"
        path = {
            "object_type": get_entity_type(connect_obj),
            "object_name": current_obj,
            "event_relation": query["relation"],
            f"{query['event']}_type": event['type'],
            f"{query['event']}_name": event['name'],
        }
        if helper:
            path["helper_type"] = helper['type']
            path["helper_name"] = helper['name']
        path["valid"] = valid
        alternate_paths.append(path)

    # If PhysicalObject has substitute relations to other PhysicalObjects
    # substitute_relations: isA
    for substitute_obj in record["substitute_objects"]:
        path = {
            "object_type": get_entity_type(substitute_obj),
            "object_name": substitute_obj['text'],
            "event_relation": query["relation"],
            f"{query['event']}_type": event['type'],
            f"{query['event']}_name": event['name']
        }
        if helper:
            path["helper_type"] = helper['type']
            path["helper_name"] = helper['name']
        path["valid"] = valid
        alternate_paths.append(path)

    # If Event has substitute relations to its own Events (Property, Process, State
    # event_substitute: isA
    for substitute_event in record[f"substitute_{query['event']}"]:
        path = {
            "object_type": object['type'],
            "object_name": object['name'],
            "event_relation": query["relation"],
            f"{query['event']}_type": get_entity_type(substitute_event),
            f"{query['event']}_name": substitute_event['text']
        }
        if helper:
            path["helper_type"] = helper['type']
            path["helper_name"] = helper['name']
        path["valid"] = valid
        alternate_paths.append(path)
        
    alternate_paths = remove_duplicates(alternate_paths)    
    return alternate_paths, len(alternate_paths)

def remove_duplicates(paths):
    """ Remove duplicate paths """
    unique_paths = []
    for path in paths:
        if path not in unique_paths:
            unique_paths.append(path)
    return unique_paths

def process_query_results(results, paths, complex=False):
    """ Process query results and extract relevant information """

    num_direct_count = 0
    num_alternates_count = 0
    for record in results:
        # PhysicalObject - Equipment
        object_info = get_entity_info(record, "object")

        # Property / Process / State - Undesirable event
        event_info = get_entity_info(record, query["event"])

        path = {
            "object_type": object_info["type"],
            "object_name": object_info["name"],
            "event_relation": query["relation"],
            f"{query['event']}_type": event_info["type"],
            f"{query['event']}_name": event_info["name"],
        }
        
        # If complex (there are helper entities that describe Undesirable event)
        if complex:
            helper_info = get_entity_info(record, query["helper"])
            path["helper_type"] = helper_info["type"]
            path["helper_name"] = helper_info["name"]
            
        # Check if path is confirmed valid (entities come from same entry)
        path["valid"] = True if object_info["entry_id"] == event_info["entry_id"] else False
        
        # Alternate paths (if PhysicalObject has connect or substitute relations)
        if complex: # Pass helper_info in generating alternate paths if complex
            alternate_paths, num_alternates = get_alternate_paths(query, record, object_info, event_info, path['valid'], helper_info)
        else:       # No helper_info if not complex
            alternate_paths, num_alternates = get_alternate_paths(query, record, object_info, event_info, path['valid'])
        
        # Include paths only if they don't already exist
        potential_paths = [path] + alternate_paths
        for p in potential_paths:
            if p not in paths:
                paths.append(p)

        num_direct_count += 1
        num_alternates_count += num_alternates

    print("{:<40} {}".format(f"Number of {query['outfile']}:", num_direct_count))
    print(" - {:<37} {}".format("Number of alternate paths:", num_alternates_count))

if __name__ == "__main__":
    # Connect to Neo4j
    URI = "bolt://localhost:7687"
    USERNAME = "neo4j"
    PASSWORD = "password"
    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

    with driver.session() as session:
        for query in direct_queries:
            results = session.run(query["query"])
            paths = []
            process_query_results(results, paths, complex=False)
            list_to_json(paths, f"pathPatterns/{query['outfile']}.json")
        
        for query in complex_queries:
            results = session.run(query["query"])
            paths = []
            process_query_results(results, paths, complex=True)
            list_to_json(paths, f"pathPatterns/{query['outfile']}.json")

    driver.close()
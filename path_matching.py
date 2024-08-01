import csv
import json
from neo4j import GraphDatabase
from path_queries import direct_queries, complex_queries, get_connect_objects

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
def get_alternate_paths(query, record, object, connect_objects, event, valid, helper=None):
    """ Extract relation information from record """
    num_valid = 0
    alternate_paths = []
    
    # If PhysicalObject has connect relations to other PhysicalObjects
    # connect_relations: hasPart, contains
    for connect_obj in connect_objects:
        # Ignore connect relations with more than 4 objects
        if len(connect_obj) > 3:
            continue
        current_obj = object["name"]
        for obj in connect_obj:
            current_obj = f"{obj} {current_obj}"
            path = {
                "object_type": object['type'],
                "object_name": current_obj,
                "event_relation": query["relation"],
                "event_type": event['type'],
                "event_name": event['name'],
            }
            if helper:
                path["helper_type"] = helper['type']
                path["helper_name"] = helper['name']
            path["valid"] = valid
            path['alternate'] = True
            alternate_paths.append(path)

    # If PhysicalObject has substitute relations to other PhysicalObjects
    # substitute_relations: isA
    for substitute_obj in record["substitute_objects"]:
        path = {
            "object_type": get_entity_type(substitute_obj),
            "object_name": substitute_obj['text'],
            "event_relation": query["relation"],
            "event_type": event['type'],
            "event_name": event['name']
        }
        if helper:
            path["helper_type"] = helper['type']
            path["helper_name"] = helper['name']
        path["valid"] = valid
        path['alternate'] = True
        alternate_paths.append(path)

    # If Event has substitute relations to its own Events (Property, Process, State
    # event_substitute: isA
    for substitute_event in record[f"substitute_{query['event']}"]:
        path = {
            "object_type": object['type'],
            "object_name": object['name'],
            "event_relation": query["relation"],
            "event_type": get_entity_type(substitute_event),
            "event_name": substitute_event['text']
        }
        if helper:
            path["helper_type"] = helper['type']
            path["helper_name"] = helper['name']
        path["valid"] = valid
        path['alternate'] = True
        alternate_paths.append(path)

    alternate_paths = remove_duplicates(alternate_paths)
    return alternate_paths

# Function to remove duplicate paths
def remove_duplicates(paths):
    """ Remove duplicate paths """
    unique_paths = []
    for path in paths:
        if path not in unique_paths:
            unique_paths.append(path)
    return unique_paths

# Function to check validity of paths (if entities come from same entry)
def check_validity(object, event, helper=None):
    """ Check if entities come from same entry """
    if helper:  # Check for common entry_id in object, event, and helper entities
        object_set = set(object["entry_id"])
        event_set = set(event["entry_id"])
        helper_set = set(helper["entry_id"])
        common = object_set.intersection(event_set).intersection(helper_set)
        return True if common else False
    else:   # Check for common entry_id in object and event entities
        object_set = set(object["entry_id"])
        event_set = set(event["entry_id"])
        common = object_set.intersection(event_set)
        return True if common else False

# Function to print count of paths (valid and alternate paths)
def print_path_counts(paths):
    num_direct, valid_direct = 0, 0
    num_alternate, valid_alternate = 0, 0
    for path in paths:
        if path['alternate']:
            num_alternate += 1
            if path['valid']:
                valid_alternate += 1
        else:
            num_direct += 1
            if path['valid']:
                valid_direct += 1
    total_paths = num_direct + num_alternate
    total_valid = valid_direct + valid_alternate

    print(query["outfile"])
    print(f"{'Direct':<10}{num_direct:<6} ({valid_direct:<3} valid)")
    print(f"{'Alternate':<10}{num_alternate:<6} ({valid_alternate:<3} valid)")
    print(f"{'Total':<10}{total_paths:<6} ({total_valid:<3} valid)")
    print(f"{'-' * 30}")

# Function to process query results
def process_query_results(results, paths, complex=False):
    """ Process query results and extract relevant information """

    for record in results:
        # PhysicalObject - Equipment
        object_info = get_entity_info(record, "object")
        connect_objects = get_connect_objects(DRIVER, object_info["name"])

        # Property / Process / State - Undesirable event
        event_info = get_entity_info(record, query["event"])

        path = {
            "object_type": object_info["type"],
            "object_name": object_info["name"],
            "event_relation": query["relation"],
            "event_type": event_info["type"],
            "event_name": event_info["name"],
        }
        
        # If complex (there are helper entities that describe Undesirable event)
        if complex:
            helper_info = get_entity_info(record, query["helper"])
            path["helper_type"] = helper_info["type"]
            path["helper_name"] = helper_info["name"]
            # Check if path is confirmed valid (entities come from same entry)
            path["valid"] = check_validity(object_info, event_info, helper_info)
        else:
            # Check if path is confirmed valid (entities come from same entry)
            path["valid"] = check_validity(object_info, event_info)
            
        path['alternate'] = False
        
        # Alternate paths (if PhysicalObject has connect or substitute relations)
        if complex: # Pass helper_info in generating alternate paths if complex
            alternate_paths = get_alternate_paths(query, record, object_info, connect_objects, event_info, path['valid'], helper_info)
        else:       # No helper_info if not complex
            alternate_paths = get_alternate_paths(query, record, object_info, connect_objects, event_info, path['valid'])
        
        # Include paths only if they don't already exist
        potential_paths = [path] + alternate_paths
        for p in potential_paths:
            if p not in paths:
                paths.append(p)

# Function to update path json files with human validated unconfirmed paths
def update_paths_validated():
    """ Go through validated unconfirmed paths and update path json files """
    with open("pathPatterns/paths_to_validate.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader) # Ignore header
        for row in reader:
            if row[0].endswith("PATHS"):
                    # TODO
                    # Store validated paths in dictionary
                    # {pathtype: [{object_name: "", event_name: "", helper_name: "", valid: True/False}]}

                    # For each path type, open json file and update the fields


                
                # pathtype = row[0].lower()
                # pathfile = open(f"pathPatterns/{pathtype}.json", "r", encoding="utf-8")
                # pathdata = json.load(pathfile)
                # pathfile.close()
                # for path in pathdata:
                #     if not path['valid'] and not path['alternate']:
                #         if row[0] == path['object_name'] and row[1] == path['event_name'] and row[2] == path['helper_name']:
                #         pathdata['valid'] = True if row[3] == 'x' else False
                # list_to_json(pathdata, pathfile)
            
        
        

if __name__ == "__main__":
    # Connect to Neo4j
    URI = "bolt://localhost:7687"
    USERNAME = "neo4j"
    PASSWORD = "password"
    DRIVER = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    OUTPATH = "pathPatterns/"

    with DRIVER.session() as session:
        for query in direct_queries:
            results = session.run(query["query"])
            paths = []
            process_query_results(results, paths, complex=False)
            print_path_counts(paths)
            list_to_json(paths, f"{OUTPATH}{query['outfile']}.json")

        for query in complex_queries:
            results = session.run(query["query"])
            paths = []
            process_query_results(results, paths, complex=True)
            print_path_counts(paths)
            list_to_json(paths, f"{OUTPATH}{query['outfile']}.json")

    DRIVER.close()
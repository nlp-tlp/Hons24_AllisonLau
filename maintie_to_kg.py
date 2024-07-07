import re
import json
from neo4j import GraphDatabase

# Function to create label names
def create_label_name(tokens, start, end):
    """ Create label name from tokens. """
    label = "_".join(tokens[start:end])
    label = re.sub(r'\W', '', label)
    return label

# Function to create nodes
def create_nodes(tx, entities, unique_entities, tokens):
    """ Create nodes for entities. """
    current_entities = []
    for entity in entities:
        entity_text = create_label_name(tokens, entity["start"], entity["end"])
        entity_type = entity["type"].split('/')[0]
        sub_types = entity["type"].split('/')[1:]
        unique_entity_key = (entity_text, entity_type)
        current_entities.append(unique_entity_key)

        if unique_entity_key not in unique_entities:
            entity_id = len(unique_entities)
            unique_entities[unique_entity_key] = entity_id
            properties = {"id": entity_id, "text": entity_text, "type": entity_type}
            query = f"MERGE (n:{entity_type} {{id: $id, text: $text, type: $type}}) "
            for i, subtype in enumerate(sub_types):
                properties[f"subtype{i}"] = subtype
                query += f"SET n.subtype{i} = $subtype{i} "
            tx.run(query, properties)

    return current_entities, unique_entities

# Function to create relations
def create_relations(tx, relations, unique_entities, current_entities):
    """ Create relations between entities. """
    for relation in relations:
        head = relation["head"]
        tail = relation["tail"]
        rel_type = relation["type"].replace("/", "_")
        head_id = unique_entities[current_entities[head]]
        tail_id = unique_entities[current_entities[tail]]
        tx.run(
            f"MATCH (a {{id: $head_id}}), (b {{id: $tail_id}}) "
            f"MERGE (a)-[:{rel_type}]->(b)", 
            head_id=head_id, tail_id=tail_id, type=rel_type
        )

# Function to create graph
def create_graph(tx, data):
    """ Create graph from MaintIE dataset. """
    unique_entities = {}
    for entry in data:
        entities = entry["entities"]
        relations = entry["relations"]
        tokens = entry["tokens"]
        current_entities, unique_entities = create_nodes(tx, entities, unique_entities, tokens)
        create_relations(tx, relations, unique_entities, current_entities)

# Connect to Neo4j
URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "password"
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

# Get data from MaintIE dataset
with open('datasets/MaintIE/gold_release.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Process data
with driver.session() as session:
    session.execute_write(create_graph, data)

driver.close()

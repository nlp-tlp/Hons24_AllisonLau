import json
from neo4j import GraphDatabase

# Function to create label names
def create_label_name(tokens, start, end):
    """ Create label name from tokens. """
    label = " ".join(tokens[start:end])
    label = label.lower().strip()
    return label

# Function to create nodes
def create_nodes(tx, entities, unique_entities, tokens, entry_id):
    """ Create nodes for entities. """
    current_entities = []
    for entity in entities:
        entity_text = create_label_name(tokens, entity["start"], entity["end"])
        entity_type = entity["type"].split('/')[0]
        sub_types = entity["type"].split('/')[1:]
        unique_entity_key = (entity_text, entity_type, entry_id)
        current_entities.append(unique_entity_key)

        if unique_entity_key not in unique_entities:
            entity_id = len(unique_entities)
            unique_entities[unique_entity_key] = entity_id
            properties = {"id": entity_id, "text": entity_text, "type": entity_type, "entry_id": entry_id}
            query = f"MERGE (n:{entity_type} {{id: $id, text: $text, type: $type, entry_id: $entry_id}}) "
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
            "WHERE NOT a:Entry AND NOT b:Entry "
            f"MERGE (a)-[:{rel_type}]->(b)", 
            head_id=head_id, tail_id=tail_id, type=rel_type
        )

# Function to create entry nodes and connect to its entities
def create_entry(tx, entry_text, entry_id):
    """ Create nodes for entries and connect to its entities. """
    # Create entry node
    tx.run(
        "MERGE (n:Entry {id: $id, text: $text})",
        id=entry_id, text=entry_text
    )
    # Connect entry node to its entities
    tx.run(
        "MATCH (a:Entry {id: $id}), (b) "
        "WHERE b.entry_id = $entry_id "
        "MERGE (b)-[:comesFrom]->(a)",
        id=entry_id, entry_id=entry_id
    )

# Function to create graph
def create_graph(tx, data):
    """ Create graph from MaintIE dataset. """
    unique_entities = {}
    for entry_id, entry in enumerate(data):
        entities = entry["entities"]
        relations = entry["relations"]
        tokens = entry["tokens"]
        current_entities, unique_entities = create_nodes(tx, entities, unique_entities, tokens, entry_id)
        create_relations(tx, relations, unique_entities, current_entities)
        create_entry(tx, entry['text'], entry_id)

    print(f"Created {len(unique_entities)} entities.")
    print(f"Created {len(data)} entry entities.")
    print(f"Total number of nodes: {len(unique_entities) + len(data)}")

if __name__ == "__main__":
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

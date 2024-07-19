import json
import csv

verb = {
    "ControllingObject": "control",
    "CoveringObject": "cover",
    "DrivingObject": "drive",
    "HumanInteractionObject": "interact",
    "PresentingObject": "present",
    "MaintenanceActivity": "maintain",
    "GeneratingObject": "generate",
    "ProtectingObject": "protect",
    "HoldingObject": "hold",
    "RestrictingObject": "restrict",
    "TransformingObject": "transform",
    "InformationProcessingObject": "process information",
    "SensingObject": "sense",
    "GuidingObject": "guide",
    "MatterProcesingObject": "process matter",
    "InterfacingObject": "interface",
    "EmittingObject": "emit",
    "SupportingActivity": "support",
    "StoringObject": "store",
    "UndesirableState": "do something",
    "UndesirableProperty": "do something",
    "DesirableProperty": "do something",
}

def get_codes(lines):
    """ Get the failure mode codes from the lines of the file. """
    failure_mode_codes = {}
    for line in lines:
        line = line.strip()
        event, code = line.split(',')
        if code not in failure_mode_codes:
            failure_mode_codes[code] = 1
        else:
            failure_mode_codes[code] += 1
    return failure_mode_codes

def show_codes(lines):
    """ Show the failure mode codes from the lines of the file. """
    codes = get_codes(lines)
    total = 0
    for key, value in codes.items():
        print(value, key)
        total += value
    print("Total:", total)

def read_data():
    """ Read the data from the files. """
    with open('datasets/FMC-MWO2KG/train.txt', 'r', encoding='utf-8') as file:
        train_file = file.readlines()
        train_lines = [(line.split(',')[0], line.split(',')[1].strip()) for line in train_file]

    with open('datasets/FMC-MWO2KG/test.txt', 'r', encoding='utf-8') as file:
        test_file = file.readlines()
        test_lines = [(line.split(',')[0], line.split(',')[1].strip()) for line in test_file]

    with open('datasets/FMC-MWO2KG/dev.txt', 'r', encoding='utf-8') as file:
        val_file = file.readlines()
        val_lines = [(line.split(',')[0], line.split(',')[1].strip()) for line in val_file]

    with open('datasets/MaintIE/gold_release.json', 'r', encoding='utf-8') as file:
        gold_data = json.load(file)

    with open('datasets/MaintIE/silver_release.json', 'r', encoding='utf-8') as file:
        silver_data = json.load(file)

    return train_lines, test_lines, val_lines, gold_data, silver_data

def create_code(data):
    """ Create the failure modes using the Object. """
    entities = data['entities']
    relations = data['relations']
    failure_idx = -1
    for i, entity in enumerate(entities):
        if 'Undesirable' in entity['type']:
            for r in relations:
                if r['head'] == i:
                    failure_idx = r['tail']
            try:
                failure_object = entities[failure_idx]['type']
                failure_action = failure_object.split('/')[1]
                failure_verb = verb[failure_action]
                failure_code = "failure to " + failure_verb
                return failure_code
            except:
                return "failure to do something"

def get_events(maintie_data):
    """ Get the events from MaintIE data. """
    events = {'UndesirableState': [], 'UndesirableProperty': [], 'UndesirableProcess': []}
    for d in maintie_data:
        for entity in d['entities']:
            start_idx = entity['start']
            end_idx = entity['end']
            event = " ".join(d['tokens'][start_idx:end_idx])
            text = d['text']
            if 'UndesirableState' in entity['type']:
                events['UndesirableState'].append([event, text, create_code(d)])
            if 'UndesirableProperty' in entity['type']:
                events['UndesirableProperty'].append([event, text, create_code(d)])
            if 'UndesirableProcess' in entity['type']:
                events['UndesirableProcess'].append([event, text, create_code(d)])
    total_events = len(events['UndesirableState']) + len(events['UndesirableProperty']) + len(events['UndesirableProcess'])
    print("{:<20} {}".format("UndesirableState", len(events['UndesirableState'])))
    print("{:<20} {}".format("UndesirableProperty", len(events['UndesirableProperty'])))
    print("{:<20} {}".format("UndesirableProcess", len(events['UndesirableProcess'])))
    print("{:<20} {}".format("Total", total_events))
    return events

def write_csv(data, csv_file, header):
    """ Write the data to a CSV file. """
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(data)

def print_count(title, count_dict):
    """ Print the count dictionary in a table format. """
    print("{:<30} {}".format(f"{title}", "Count"))
    print("-" * 40)
    for key, value in count_dict.items():
        print("{:<30} {}".format(key, value))
    print("-" * 40)
    print("{:<30} {}".format("Total", sum(count_dict.values())))
    print()

def maintie_analysis(gold):
    """ Analyse the gold dataset from MaintIE. """
    entity_count, relation_count, unique_entity_count, unique_relation_count = {}, {}, {}, {}
    seen_entities, seen_relations = [], []

    for data in gold:
        # count number of entities {type: count}
        for entity in data['entities']:
            entity_type = entity['type'].split('/')[0]
            if entity_type not in entity_count:
                entity_count[entity_type] = 1
            else:
                entity_count[entity_type] += 1
        
        # count number of relations {type: count}
        for relation in data['relations']:
            relation_type = relation['type']
            if relation_type not in relation_count:
                relation_count[relation_type] = 1
            else:
                relation_count[relation_type] += 1
                
        # count number of unique entities {type: count}
        for entity in data['entities']:
            entity_type = entity['type'].split('/')[0]
            entity_text = " ".join(data['tokens'][entity['start']:entity['end']]).lower().strip()
            unique_entity_key = (entity_text, entity_type)
            if unique_entity_key not in seen_entities:
                seen_entities.append(unique_entity_key)
                if entity_type not in unique_entity_count:
                    unique_entity_count[entity_type] = 1
                else:
                    unique_entity_count[entity_type] += 1
                    
        # count number of unique relations {type: count}
        for relation in data['relations']:
            relation_type = relation['type']
            head = relation['head']
            tail = relation['tail']
            head_entity = data['entities'][head]
            tail_entity = data['entities'][tail]
            head_entity_type = head_entity['type'].split('/')[0]
            tail_entity_type = tail_entity['type'].split('/')[0]
            head_entity_text = " ".join(data['tokens'][head_entity['start']:head_entity['end']]).lower().strip()
            tail_entity_text = " ".join(data['tokens'][tail_entity['start']:tail_entity['end']]).lower().strip()
            unique_head_key = (head_entity_text, head_entity_type)
            unique_tail_key = (tail_entity_text, tail_entity_type)
            unique_relation_key = (unique_head_key, unique_tail_key, relation_type)

            if unique_relation_key not in seen_relations:
                seen_relations.append(unique_relation_key)
                if relation_type not in unique_relation_count:
                    unique_relation_count[relation_type] = 1
                else:
                    unique_relation_count[relation_type] += 1
    
    print_count("Entities", entity_count)
    print_count("Relations", relation_count)
    print_count("Unique Entities", unique_entity_count)
    print_count("Unique Relations", unique_relation_count)

def number_tokens_analysis(maintie_data, data_name):
    """ Analyse the number of tokens in the maintie data. """
    min_tokens = 1000 # Minimum number of tokens
    max_tokens = 0    # Maximum number of tokens
    sum_tokens = 0    # Sum of tokens

    for data in maintie_data:
        tokens = data['tokens']
        if len(tokens) > max_tokens:
            max_tokens = len(tokens)
        if len(tokens) < min_tokens:
            min_tokens = len(tokens)
        sum_tokens += len(tokens)

    # Average number of tokens
    avg_tokens = sum_tokens / len(maintie_data) 
    
    print(f"{data_name} Tokens Count")
    print("{:<20} {}".format("Minimum Tokens:", min_tokens))
    print("{:<20} {}".format("Maximum Tokens:", max_tokens))
    print("{:<20} {}".format("Average Tokens:", avg_tokens))
    print()

def raw_mwo2kg_analysis(obs_data):
    with open('datasets/FMC-MWO2KG/raw.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        lines = list(reader)

    raw_data = []
    for line in lines:
        if line[2] != "Not an observation":
            full = line[3].split("   ")[0].replace('"', '')
            raw_data.append((full, line[2]))

    aligned_data = []
    for d in obs_data:
        for r in raw_data:
            if d[0] in r[0] and d[1] == r[1] and r not in aligned_data:
                aligned_data.append(r)

    print(f"Aligned Data: {len(aligned_data)}")
    with open('datasets/FMC-MWO2KG/aligned.txt', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(aligned_data)

def maintie_head_tail(data):
    """ Get the head and tail entities from the MaintIE data. """
    head_tail_relation = []
    for d in data:
        for r in d['relations']:
            head = r['head']
            tail = r['tail']
            head_entity = d['entities'][head]
            tail_entity = d['entities'][tail]
            head_type = head_entity['type'].split('/')[0]
            tail_type = tail_entity['type'].split('/')[0]
            
            # Undesirable State / Property / Process
            if "Undesirable" in head_entity['type']:
                head_subtype = head_entity['type'].split('/')[1]
                head_tail_relation.append((head_subtype, tail_type, r['type']))
                continue
            
            if "Undesirable" in tail_entity['type']:
                tail_subtype = tail_entity['type'].split('/')[1]
                head_tail_relation.append((head_type, tail_subtype, r['type']))
                continue
            
            head_tail_relation.append((head_type, tail_type, r['type']))
    head_tail_relation = sorted(set(head_tail_relation))
    for h, t, r in head_tail_relation:
        print(f"{h} -> {r} -> {t}")
    print("Total:", len(head_tail_relation))
    
train, test, val, gold, silver = read_data()

maintie_analysis(gold)
# maintie_analysis(silver)
# maintie_head_tail(gold)
# maintie_head_tail(silver)

# number_tokens_analysis(gold, "MaintIE Gold")
# number_tokens_analysis(silver, "MaintIE Silver")
# number_tokens_analysis(gold+silver, "MaintIE Gold + Silver")

# raw_mwo2kg_analysis(train+test+val)

# events_list = get_events(gold)
# write_csv(events_list['UndesirableState'], 'undesirable_state.csv', ['Event', 'Text', 'Failure Mode'])
# write_csv(events_list['UndesirableProperty'], 'undesirable_property.csv', ['Event', 'Text', 'Failure Mode'])
# write_csv(events_list['UndesirableProcess'], 'undesirable_process.csv', ['Event', 'Text', 'Failure Mode'])

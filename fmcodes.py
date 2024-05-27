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
        train_lines = file.readlines()

    with open('datasets/FMC-MWO2KG/test.txt', 'r', encoding='utf-8') as file:
        test_lines = file.readlines()

    with open('datasets/FMC-MWO2KG/dev.txt', 'r', encoding='utf-8') as file:
        val_lines = file.readlines()

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
            except KeyError:
                return "failure to do something"

def get_events(data):
    """ Get the events from the data. """
    events = {'UndesirableState': [], 'UndesirableProperty': [], 'UndesirableProcess': []}
    codes = []
    for d in data:
        for entity in d['entities']:
            start_idx = entity['start']
            end_idx = entity['end']
            event = " ".join(d['tokens'][start_idx:end_idx])
            text = d['text']
            if 'UndesirableState' in entity['type']:
                events['UndesirableState'].append([event, text])
                code = create_code(d)
                codes.append(code)
                break
            elif 'UndesirableProperty' in entity['type']:
                events['UndesirableProperty'].append([event, text])
                code = create_code(d)
                codes.append(code)
                break
            elif 'UndesirableProcess' in entity['type']:
                events['UndesirableProcess'].append([event, text])
                code = create_code(d)
                codes.append(code)
                break
    return events, codes

def write_csv(data, csv_file, header):
    """ Write the data to a CSV file. """
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(data)

def remove_duplicates(input):
    """ Remove duplicates from the input. """
    output = []
    for i in input:
        if i not in output:
            output.append(i)
    return output


# train, test, val, gold, silver = read_data()
# events_list, codes_list = get_events(gold_data)

# print(codes)

# for key, value in events_list.items():
#     title = key.replace('Undesirable', '').lower()
    # write_csv(value, '/outputmaintie_' + title + '.csv', [key, 'Text'])

# write_csv(events_data, 'maintie_events.csv', ['Event', 'Full MWO Text'])
# write_csv(unique_events_data, 'maintie_unique_events.csv', ['Unique Event'])
# write_csv(unique_texts_data, 'maintie_unique_texts.csv', ['Unique Text'])

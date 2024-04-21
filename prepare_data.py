import ast
import csv
import json

MAX_ROWS = 10

SYSTEM_CONTENT = (
    "Generate observations (from maintenance work orders) for the given failure mode code."
)

SYSTEM_DICT = {"role": "system", "content": SYSTEM_CONTENT}

def prepare_data():
    """ Prepare data for training the model. """

    dataset = []
    with open("label2obs/data.csv", "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            data = {"messages": [SYSTEM_DICT]}
            failure_mode = row[0]
            observations = ",".join(ast.literal_eval(row[1]))
            user_dict = {"role": "user", "content": f"{failure_mode}"}
            assistant_dict = {"role": "assistant", "content": f"{observations}"}
            data["messages"].append(user_dict)
            data["messages"].append(assistant_dict)
            dataset.append(data)

    with open("label2obs/prepared_data.jsonl", "w", encoding="utf-8") as file:
        for data in dataset:
            file.write(json.dumps(data) + "\n")

prepare_data()
    
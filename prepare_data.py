import os
import ast
import csv
import json
import random
import pathlib
from generate_data import get_fewshot, FMCODES

MAX_ROWS = 10

SYSTEM_CONTENT = (
    "Generate observations (from maintenance work orders) for the given failure mode code."
)

SYSTEM_DICT = {"role": "system", "content": SYSTEM_CONTENT}

def prepare_data_for_LLM():
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

def prepare_data_for_FMC(dir_name='observations'):
    current_path = pathlib.Path(__file__).parent.resolve()
    data_folder = os.path.join(current_path, f"LLM_observations/{dir_name}")

    failure_names = get_fewshot().keys()
    training_data = [] # list of "observation,label" pairs
    for name in failure_names:
        code = FMCODES[name]
        filename = os.path.join(data_folder, f"{code}.csv")
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                pair = f"{row[0]},{name}"
                training_data.append(pair)

    # Create directory for LLM-generared data formatted for FMC
    os.makedirs(f"LLM_data/{dir_name}", exist_ok=True)

    random.shuffle(training_data)
    # write 80% of the data to train.txt
    with open(f"LLM_data/{dir_name}/train.txt", "w", encoding="utf-8") as file:
        train_data = training_data[:int(len(training_data) * 0.8)]
        for pair in train_data:
            file.write(pair + "\n")

    # write 20% of the data to val.txt
    with open(f"LLM_data/{dir_name}/val.txt", "w", encoding="utf-8") as file:
        val_data = training_data[int(len(training_data) * 0.8):]
        for pair in val_data:
            file.write(pair + "\n")

    print(f"Train ({len(train_data)}), Val ({len(val_data)}), Total ({len(training_data)})\t- {dir_name} prepared.")

if __name__ == "__main__":
    # prepare_data_for_LLM()
    # prepare_data_for_FMC("fs_all")
    # prepare_data_for_FMC("fs_specific")
    # prepare_data_for_FMC("ft_specific1")
    # prepare_data_for_FMC("ft_specific2")
    # prepare_data_for_FMC("no_fewshot")
    prepare_data_for_FMC("count")

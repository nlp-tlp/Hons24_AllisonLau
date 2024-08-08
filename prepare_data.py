""" Prepare data for training the GPT-3.5 model and Flair text classification model. """

import os
import ast
import csv
import json
import random
from GivenCodes.llm_generate_data import get_fewshot, FMCODES
from path_queries import direct_queries, complex_queries

def prepare_data_for_llm():
    """ Prepare data for finetuning the GPT-3.5 model. """
    SYSTEM_CONTENT = "Generate observations (from maintenance work orders) for the given failure mode code."
    SYSTEM_DICT = {"role": "system", "content": SYSTEM_CONTENT}
    
    dataset = []
    in_filepath = os.path.join(BASE_DIR, "label2obs", "data.csv")
    with open(in_filepath, "r", encoding="utf-8") as file:
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

    out_filepath = os.path.join(BASE_DIR, "label2obs", "prepared_data.jsonl")
    with open(out_filepath, "w", encoding="utf-8") as file:
        for data in dataset:
            file.write(json.dumps(data) + "\n")

def prepare_data_for_fmc_old(dir_name='observations'):
    """ Prepare data for training the Flair text classification model. """

    data_folder = os.path.join(BASE_DIR, "LLM_observations", dir_name)
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
    train_filepath = os.path.join(BASE_DIR,"LLM_data", dir_name, "train.txt")
    with open(train_filepath, "w", encoding="utf-8") as file:
        train_data = training_data[:int(len(training_data) * 0.8)]
        for pair in train_data:
            file.write(pair + "\n")

    # write 20% of the data to val.txt
    val_filepath = os.path.join(BASE_DIR,"LLM_data", dir_name, "val.txt")
    with open(val_filepath, "w", encoding="utf-8") as file:
        val_data = training_data[int(len(training_data) * 0.8):]
        for pair in val_data:
            file.write(pair + "\n")

    train_size, val_size, total_size = len(train_data), len(val_data), len(training_data)
    print(f"Train ({train_size}), Val ({val_size}), Total ({total_size})\t- {dir_name} prepared.")

def prepare_path_for_validation():
    """ Extract paths that are not confirmed valid for human validation in csv file. """
    queries = direct_queries + complex_queries
    requires_validation = {}
    for query in queries:
        with open(f"path_patterns/{query['outfile']}.json", encoding='utf-8') as f:
            requires_validation[query['outfile']] = []
            data = json.load(f)
            for path in data:
                # If path does not come from entry and is not an alternate path
                if not path['valid'] and not path['alternate']:
                    requires_validation[query['outfile']].append({
                        "Physical Object": path['object_name'],
                        "Undesirable Event": path['event_name'],
                        "Helper PO/Event": path['helper_name'] if 'helper_name' in path else "",
                        "Valid": ""
                    })

    # Only keep path types that require validation
    requires_validation = {k: v for k, v in requires_validation.items() if v}
                    
    # Save into csv file with headers = [PhysicalObject,UndesirableEvent,Valid]
    # where Valid is to be filled by human with x if valid, and empty if invalid
    with open("path_patterns/paths_to_validate.csv", "w", encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Physical Object", "Undesirable Event", "Helper PO/Event", "Valid"])
        writer.writeheader()
        for pathtype, paths in requires_validation.items():
            writer.writerow({"Physical Object": pathtype.upper(), "Undesirable Event": "", "Helper PO/Event": "", "Valid": ""})
            for path in paths:
                writer.writerow(path)

def prepare_data_for_fmc(pathlist):
    """ Prepare data for training the Flair text classification model. """
    pass

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # prepare_data_for_llm()
    # prepare_data_for_fmc_old("fs_all")
    # prepare_data_for_fmc_old("fs_specific")
    # prepare_data_for_fmc_old("ft_specific1")
    # prepare_data_for_fmc_old("ft_specific2")
    # prepare_data_for_fmc_old("no_fewshot")
    # prepare_data_for_fmc_old("count")
    prepare_path_for_validation()

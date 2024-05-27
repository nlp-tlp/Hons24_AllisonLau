""" Generate synthetic observations for each failure mode using GPT. """

import os
import csv
import ast
import openai

FMCODES = {
    "Breakdown": "BRD",
    'Plugged / choked': "PLU",
    'Leaking': "LEA",
    'Minor in-service problems': "SER",
    'Structural deficiency': "STD",
    'Noise': "NOI",
    'Failure to start on demand': "FTS",
    'Vibration': "VIB",
    'Overheating': "OHE",
    'Failure to function': "FTF",
    'Low output': "LOO",
    'Electrical': "ELE",
    'Failure to stop on demand': "STP",
    'Abnormal instrument reading': "AIR",
    'Other': "OTH",
    'Failure to close': "FTC",
    'Contamination': "CTM",
    'High output': "HIO",
    'Erratic output': "ERO",
    'Failure to rotate': "FRO",
    'Spurious stop': "UST",
    'Failure to open': "FTO"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Gets the set of labels (failure mode codes) from FULL ISO14224
def get_fmcodes():
    """ Returns a list of labels (failure mode codes) from ISO14224. """
    filepath = os.path.join(BASE_DIR, 'label2obs', 'ISO14224mappingToMaintIE.csv')
    with open(filepath, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)
        labels = []
        for row in reader:
            labels.append(row[:2])
    return labels[:-1] # Remove NOT_MAPPED

# Returns a dictionary of few-shot examples for each label from FMC-MWO2KG dataset
def get_fewshot_examples():
    """ Returns a dictionary of few-shot examples for each label from FMC-MWO2KG dataset. """
    # Read each line data from txt file
    examples = {}
    for ds in ["train", "dev", "test"]:
        filepath = os.path.join(BASE_DIR, 'FMC-MWO2KG', f'{ds}.txt')
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            lines = [line.strip() for line in lines]
            for line in lines:
                observation = line.split(',')[0]
                code_label = line.split(',')[1]
                if code_label not in examples:
                    examples[code_label] = [observation]
                else:
                    examples[code_label].append(observation)
    return examples

# Returns a dictionary of modified few-shot examples (based on FMC-MWO2KG dataset)
def get_fewshot():
    """ Returns a dictionary of modified few-shot examples for each label. """
    fewshot = {}
    filepath = os.path.join(BASE_DIR, 'label2obs', 'data.csv')
    with open(filepath, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            failure_mode = row[0]
            observations = ast.literal_eval(row[1])
            fewshot[failure_mode] = observations
    return fewshot

# Maps failure modes (ISO14224) to MWO2KG codes
def handle_differences(label):
    """ Maps failure modes (ISO14224) to MWO2KG codes. """
    labels = {
    "Failure to close on demand": "Fail to close",
    "Failure to open on demand": "Fail to open",
    "Failure to function on demand": "Fail to function",
    "Failure to function as intended": "Fail to function",
    "External leakage - fuel": "Leaking",
    "External leakage - process medium": "Leaking",
    "External leakage - utility medium": "Leaking",
    "Internal leakage-process medium": "Leaking",
    "Internal leakage-utility": "Leaking",
    "Internal leakage": "Leaking",
    }
    if label in labels:
        return labels[label]
    return label

# Get example prompt for few-shot learning for a specific label
def get_specific_prompt(label, fewshot_examples):
    """ Returns example prompt for few-shot learning for a specific label. """
    observation = handle_differences(label[1])
    if observation in fewshot_examples:
        fewshot = f"Examples of observations for failure mode code {label[0]} ({label[1]}) are:\n"
        examples = fewshot_examples[observation]
        for i, example in enumerate(examples):
            examples[i] = f"{i+1}. "+example
        example = ','.join(examples)
    else:
        fewshot = "Examples of observations for failure mode code STD (Structural deficiency):\n"
        example = "cracking,creeping,falling off,worn,bent,snapped,corroded"
    return fewshot + example + "\n"

# Get example prompt for few-shot learning for all labels
def get_example_prompt(fewshot_examples):
    """ Returns example prompt for few-shot learning for all labels. """
    fewshot_output = ""
    i = 1
    for label, examples in fewshot_examples.items():
        fewshot = f"Examples of observations for failure mode code {label} are:\n"
        example = ','.join(f"{i}. "+examples[:10]) # only first 10 examples
        fewshot_output += fewshot + example + "\n"
        i += 1
    return fewshot_output

def save_observations_to_csv(filename, observations):
    """ Save the generated observations for each label to csv file. """
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for obs in observations:
            writer.writerow([obs.strip()])

# Process generated data and return the list of generated observations and number of observations
def process_generated_data(response):
    """ Process the generated data. """
    observations = response.split(',')
    # Remove empty strings and whitespace
    observations = [item.strip() for item in observations if item.strip()]
    # Only keep observations
    observations = [item.split('. ')[1] for item in observations]
    # Remove duplicates
    observations = list(set(observations))
    return observations, len(observations)

# Generate synthetic observations for each failure mode using GPT
def generate_data(gpt_model, output_dir, is_fewshot, is_specific):
    """ Generate synthetic observations for each failure mode using GPT. """

    fewshot_examples = get_fewshot() # get_fewshot_examples() for unmodified version
    fmcodes = sorted(fewshot_examples.keys())
    num_samples = 100

    # Generate observations for each label
    generated_data = {} # key (failure mode) -> value (observations)
    for i, failure_name in enumerate(fmcodes):
        code = FMCODES[failure_name]
        generate_prompt = f"Generate {num_samples} different observations for failure mode code {code} ({failure_name}).\n"
        contraint_prompt = f"Your answer should contain only the observations numbered from 1 to {num_samples}, which are comma-separated, and nothing else.\n"
        format_prompt = "Each observation starts with the number followed by a period, then a space, then the content, ending with a comma."
        number_prompt = f"You must generate {num_samples} observations, no less and no more than {num_samples}.\n"
        fewshot_prompt = ""
        if is_fewshot:
            if is_specific:
                fewshot_prompt = get_specific_prompt([code, failure_name], fewshot_examples)
            else:
                fewshot_prompt = get_example_prompt(fewshot_examples)
        prompt = generate_prompt + contraint_prompt + format_prompt + number_prompt + fewshot_prompt
        # print(prompt)
        response = openai.ChatCompletion.create(
                        model=gpt_model,
                        messages=[
                            {"role": "system", "content": "You are a failure mode code expert."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.7
                    )

        observations, amount = process_generated_data(response['choices'][0]['message']['content'])
        generated_data[code] = observations

        print(f"[{i+1}/{len(fmcodes)}] Generated {amount} observations for {code} ({failure_name})")
        output_filepath = os.path.join(BASE_DIR, 'LLM_observations', output_dir, f'{code}.csv')
        save_observations_to_csv(output_filepath, observations)

    print(f"Data generation completed - saved to {output_dir}.\n")
    return generated_data

if __name__ == '__main__':
    # Set OpenAI API key
    openai.api_key = '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'

    # FT_MODEL = "ft:gpt-3.5-turbo-0125:uwa-system-health-lab::9H6zu921"
    # generate_data(gpt_model=FT_MODEL, output_dir="ft1_specific", is_fewshot=True, is_specific=True)
    # FT_MODEL = "ft:gpt-3.5-turbo-0125:uwa-system-health-lab::9H72oH8q"
    # generate_data(gpt_model=FT_MODEL, output_dir="ft2_specific", is_fewshot=True, is_specific=True)
    # FT_MODEL = "ft:gpt-3.5-turbo-0125:uwa-system-health-lab::9GJuFmqj"
    # generate_data(gpt_model=FT_MODEL, output_dir="ft3_specific", is_fewshot=True, is_specific=True)

    # FT_MODEL = "ft:gpt-3.5-turbo-0125:uwa-system-health-lab::9ItKIgm3"
    # generate_data(gpt_model=FT_MODEL, output_dir="ft_specific1", is_fewshot=True, is_specific=True)
    # FT_MODEL = "ft:gpt-3.5-turbo-0125:uwa-system-health-lab::9ItG7n1t"
    # generate_data(gpt_model=FT_MODEL, output_dir="ft_specific2", is_fewshot=True, is_specific=True)

    # FT_MODEL = "gpt-3.5-turbo"
    generate_data(gpt_model="gpt-3.5-turbo", output_dir="count", is_fewshot=True, is_specific=True)
    # generate_data(gpt_model=FT_MODEL, output_dir="no_fewshot", is_fewshot=False, is_specific=False)
    # generate_data(gpt_model=FT_MODEL, output_dir="fs_specific", is_fewshot=True, is_specific=True)
    # generate_data(gpt_model=FT_MODEL, output_dir="fs_all", is_fewshot=True, is_specific=False)
    print("Data generation completed!")
    
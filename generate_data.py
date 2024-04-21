import openai
import ast
import csv

# Gets the set of labels (failure mode codes)
def get_fmcodes():
    """ Returns a list of labels (failure mode codes) from ISO14224. """
    with open('label2obs/ISO14224mappingToMaintIE.csv', 'r', encoding='utf-8') as file:
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
        with open(f'FMC-MWO2KG/{ds}.txt', 'r', encoding='utf-8') as file:
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
    """ Returns a dictionary of modified few-shot examples for each label from FMC-MWO2KG dataset. """
    # read csv file
    fewshot = {}
    with open('label2obs/data.csv', 'r', encoding='utf-8') as file:
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

# Get example prompt for few-shot learning
def get_example_prompt(label, fewshot_examples):
    """ Returns example prompt for few-shot learning for a specific label. """
    observation = handle_differences(label[1])
    if observation in fewshot_examples:
        fewshot = f"Examples of observations for failure mode code {label[0]} ({label[1]}) are:\n"
        examples = fewshot_examples[observation]
        example = ','.join(examples)
    else:
        fewshot = "Examples of observations for failure mode code STD (Structural deficiency) are:\n"
        example = "cracking,creeping,falling off,worn,bent,snapped,corroded"
    return fewshot + example + "\n"

# Save the generated observations for each label to csv file
def save_observations_to_csv(filename, observations):
    """ Save the generated observations for each label to csv file. """
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for obs in observations:
            writer.writerow([obs.strip()])

# Generate synthetic observations for each failure mode using GPT
def generate_data():
    """ Generate synthetic observations for each failure mode using GPT. """
    fmcodes = get_fmcodes()
    fewshot_examples = get_fewshot() # get_fewshot_examples() for unmodified version
    num_samples = 100

    # Generate observations for each label
    generated_data = {} # key (failure mode) -> value (observations)
    for label in fmcodes:
        print(f"Generating observations for {label[0]} ({label[1]})...")
        generate_prompt = f"Generate 100 different observations for failure mode code {label[0]} ({label[1]}).\n"
        contraint_prompt = "Your answer should contain only the observations, which are comma-separated, and nothing else.\n"
        number_prompt = f"You must generate {num_samples} observations, no less and no more than {num_samples}.\n"
        fewshot_prompt = get_example_prompt(label, fewshot_examples)
        prompt = generate_prompt + contraint_prompt + number_prompt + fewshot_prompt
        # print(prompt)
        response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a failure mode code expert."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.7
                    )
        observations = response['choices'][0]['message']['content'].split(',')
        observations = list(set(observations)) # Remove duplicates
        generated_data[label[0]] = generated_data

        save_observations_to_csv(f'observations/{label[0]}.csv', observations)

# Set OpenAI API key
openai.api_key = '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'
# generate_data()
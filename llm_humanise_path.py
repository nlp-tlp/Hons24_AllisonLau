import re
import csv
import json
import random
import openai
from path_queries import direct_queries, complex_queries
from llm_paraphrase import initialise_prompts, get_prompt, process_mwo_response

# Read all the paths extracted from MaintIE KG
def get_all_paths(valid=True):
    """ Read all the paths extracted from MaintIE Gold Dataset KG """
    queries = direct_queries + complex_queries
    output = []
    for query in queries:
        with open(f"pathPatterns/{query['outfile']}.json", encoding='utf-8') as f:
            data = json.load(f)
            if valid:
                data = [path for path in data if path['valid'] == valid]
            print(f"{len(data)}\tpaths in {query['outfile']}")
            output.extend(data)
    print(f"Total number of paths: {len(output)}")
    return output

# Get fewshot message given fewshot csv file
# Header: object_name, event_name, helper_name, example0, example1, example2, example3, example4, example5
def get_fewshot_message(base_prompts, instructions, num_examples=5):
    """ Get fewshot message given fewshot csv file """
    message = [{"role": "system", "content": "You are a technician recording maintenance work orders."}]
    with open("fewshot.csv", encoding='utf-8') as f:
        data = csv.reader(f)
        next(data) # Ignore header

        # If single-example prompt
        if num_examples == 1:
            for row in data:
                if len(row) == 4:
                    if row[2] == "": # No helper
                        user = {"role": "user", "content": get_prompt(base_prompts, instructions, row[0], row[1])}
                    else:            # Has helper
                        user = {"role": "user", "content": get_prompt(base_prompts, instructions, row[0], row[1], row[2])}
                    assistant = {"role": "assistant", "content": row[3]}
                    message.append(user)
                    message.append(assistant)   

        # If multi-example prompt
        elif num_examples == 5:
            for row in data:
                if len(row) > 4:
                    if row[2] == "": # No helper
                        user = {"role": "user", "content": get_prompt(base_prompts, instructions, row[0], row[1])}
                    else:
                        user = {"role": "user", "content": get_prompt(base_prompts, instructions, row[0], row[1], row[2])}
                    example = f"1. {row[3]}\n2. {row[4]}\n3. {row[5]}\n4. {row[6]}\n5. {row[7]}"
                    assistant = {"role": "assistant", "content": example}
                    message.append(user)
                    message.append(assistant)

    # Save fewshot message to json file
    with open("fewshot.json", "w", encoding='utf-8') as f:
        json.dump(message, f, indent=4)

    return message

# Print some fewshot examples from MaintIE gold dataset
def print_examples(object, event, helper=None):
    """ Print some fewshot examples from the gold dataset """
    data = []
    with open("data/MaintIE/gold_release.json", encoding='utf-8') as f:
        gold = json.load(f)
        for d in gold:
            text = d['text'].replace("<id> ", "").replace(" <id>", "")
            data.append(text)
    for sentence in data:
        event_exists = re.search(rf'\b{event}\b', sentence)
        helper_exists = re.search(rf'\b{helper}\b', sentence) if helper else None
        if object in sentence and event_exists and helper_exists:
            print(f"{object},{event},{helper},{sentence}")
            return True
        elif object in sentence and event_exists:
            print(f"{object},{event},{sentence}")
            return True
    return False

# Process single response from the LLM
def process_single_response(response):
    response = response.lower()                     # Case folding
    response = re.sub(r'[^\w\s]', ' ', response)    # Remove punctuation
    response = re.sub(r"\s+", " ", response)        # Remove extra spaces
    return response

# Select random pattern and generate MWO sentences
def generate_MWO(data, base_prompts, instructions, num_sentences, num_iterations):

    while num_iterations > 0 and data:
        # Choose random pattern from data and remove it
        current_pattern = random.choice(data)
        data.remove(current_pattern)
        num_iterations -= 1

        # Get prompt for specific PhysicalObject and UndesirableEvent
        if 'helper_name' in current_pattern:
            prompt = get_prompt(base_prompts, instructions, current_pattern['object_name'], current_pattern['event_name'], current_pattern['helper_name'])
        else:
            prompt = get_prompt(base_prompts, instructions, current_pattern['object_name'], current_pattern['event_name'])

        # Get fewshot message and append prompt
        fewshot = get_fewshot_message(base_prompts, instructions, num_examples=num_sentences)
        messages = fewshot + [{"role": "user", "content": prompt}]

        # Get LLM to generate humanised sentences for the pattern
        response = openai.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=0.7,
                        n=1
                    )

        # Process the response from the LLM
        print(f"Equipment: {current_pattern['object_name']}")
        print(f"Undesirable Event: {current_pattern['event_name']}")
        print(f"Helper Event: {current_pattern['helper_name'] if 'helper_name' in current_pattern else 'None'}")
        with open("MWOsentences.txt", "a", encoding='utf-8') as f:
            for choice in response['choices']:
                output = choice['message']['content']

                output = process_mwo_response(output)
                for sentence in output:
                    print(f"- {sentence}")
                    f.write(f"{sentence}\n")

                # output = process_single_response(output)
                # print(f"- {output}")
                # f.write(f"{output}\n") # Append sentence to text file

if __name__ == "__main__":
    # Set OpenAI API key
    openai.api_key = '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'

    # Read all the paths extracted from Main tIE KG
    data = get_all_paths(valid=True)

    # Initialise list of prompt and instruction prompts
    # base_prompts, instructions = initialise_prompts(num_variants=5, num_examples=5)

    # Generate 5 humanised sentences for 1 path (equipment and undesirable event)
    # generate_MWO(data, base_prompts, instructions, num_sentences=5, num_iterations=1)

    # =============================================================================
    # Uncomment this if you want to get more fewshot examples
    # successful_calls = 0
    # while successful_calls < 5:
    #     current = random.choice(data)
    #     if 'helper_name' in current:
    #         if print_examples(current['object_name'], current['event_name'], current['helper_name']):
    #             successful_calls += 1
    #     else:
    #         if print_examples(current['object_name'], current['event_name']):
    #             successful_calls += 1


# Get GPT to generate different sentences
# "Generate five different ways to describe the same issue."
# "Provide varied descriptions for the following maintenance events."
# "Create five unique sentences for the same maintenance issue."
# "Write five different sentences for the same maintenance problem."
# "Formulate five distinct sentences for the same maintenance event."
# This requires different fewshot learning

# Synonyms

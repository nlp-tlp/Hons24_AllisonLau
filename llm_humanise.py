import re
import csv
import json
import random
import openai
from path_queries import direct_queries, complex_queries

# Read all the paths extracted from MaintIE KG
def get_all_paths(valid=True):
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

# Craft and return prompt for generating MWO sentences
def get_prompt(object, event, helper=None):
    base_prompts = [
        "Generate a Maintenance Work Order (MWO) sentence describing the following equipment and undesirable event.",
        "Create a Maintenance Work Order (MWO) sentence that includes the equipment and undesirable event listed below.",
        "Write a Maintenance Work Order (MWO) sentence detailing the specified equipment and undesirable event.",
        "Formulate a Maintenance Work Order (MWO) sentence mentioning the given equipment and undesirable event.",
        "Compose a Maintenance Work Order (MWO) sentence that describes the equipment and undesirable event provided."
    ]
    
    instructions = [
        "The sentence can have a maximum of 8 words.",
        "Ensure the sentence does not exceed 8 words.",
        "Limit the sentence to a maximum of 8 words.",
        "The sentence should be no more than 8 words.",
        "Keep the sentence within an 8-word limit."
    ]
    
    base = random.choice(base_prompts)
    instruction = random.choice(instructions)

    if helper:
        prompt = f"{base}\nEquipment: {object}\nUndesirable Event: {event}\nHelper Event: {helper}\n{instruction}"
    else:
        prompt = f"{base}\nEquipment: {object}\nUndesirable Event: {event}\n{instruction}"

    # prompt = f"Generate a Maintenance Work Order (MWO) sentence describing the "
    # prompt += "following equipment and undesirable event in natural language."
    # prompt += f"\nEquipment: {object}"
    # prompt += f"\nUndesirable Event: {event}"
    # prompt += "\nThe sentence can have a maximum of 8 words."
    return prompt

# Get fewshot message given fewshot csv file (object,event,sentence)
def get_fewshot_message():
    message = [{"role": "system", "content": "You are a technician recording maintenance work orders."}]
    with open("fewshot.csv", encoding='utf-8') as f:
        data = csv.reader(f)
        for row in data:
            if len(row) == 3:   # object, event, sentence
                user = {"role": "user", "content": get_prompt(row[0], row[1])}
                assistant = {"role": "assistant", "content": row[2]}
            elif len(row) == 4: # object, event, helper, sentence
                user = {"role": "user", "content": get_prompt(row[0], row[1], row[2])}
                assistant = {"role": "assistant", "content": row[3]}
            message.append(user)
            message.append(assistant)
    
    # Save fewshot message to json file
    with open("fewshot.json", "w", encoding='utf-8') as f:
        json.dump(message, f, indent=4)
    
    return message

# Print some fewshot examples from MaintIE gold dataset
def print_examples(object, event, helper=None):
    data = []
    with open("datasets/MaintIE/gold_release.json", encoding='utf-8') as f:
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

# Process the response from the LLM
def post_processing(response):
    response = response.lower()                     # Case folding
    response = re.sub(r'[^\w\s]', ' ', response)    # Remove punctuation
    response = re.sub(r"\s+", " ", response)        # Remove extra spaces
    return response
    
# Select random pattern and generate MWO sentences
def generate_MWO(data, num_sentences, num_iterations):
    
    while num_iterations > 0 and data:
        # Choose random pattern from data and remove it
        current_pattern = random.choice(data)
        data.remove(current_pattern)
        num_iterations -= 1
        
        # Get prompt for specific PhysicalObject and UndesirableEvent
        if 'helper_name' in current_pattern:
            prompt = get_prompt(current_pattern['object_name'], current_pattern['event_name'], current_pattern['helper_name'])
        else:
            prompt = get_prompt(current_pattern['object_name'], current_pattern['event_name'])
        
        # Get fewshot message and append prompt
        fewshot = get_fewshot_message()
        messages = fewshot + [{"role": "user", "content": prompt}]
        
        # Get LLM to generate humanised sentences for the pattern
        response = openai.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=0.7,
                        n=num_sentences
                    )

        # Process the response from the LLM
        print(f"Equipment: {current_pattern['object_name']}")
        print(f"Undesirable Event: {current_pattern['event_name']}")
        print(f"Helper Event: {current_pattern['helper_name'] if 'helper_name' in current_pattern else 'None'}")
        with open("MWOsentences.txt", "a", encoding='utf-8') as f:
            for choice in response['choices']:
                output = choice['message']['content']
                output = post_processing(output)
                print(f"- {output}")
                f.write(f"{output}\n") # Append sentence to text file

if __name__ == "__main__":
    # Set OpenAI API key
    openai.api_key = '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'
    
    # Read all the paths extracted from Main tIE KG
    data = get_all_paths(valid=True)

    # Generate 5 humanised sentences for 1 path (equipment and undesirable event)
    # generate_MWO(data, num_sentences=5, num_iterations=5)
    
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

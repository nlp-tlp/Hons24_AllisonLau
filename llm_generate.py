import os
import re
import csv
import json
import random
from openai import OpenAI
from dotenv import load_dotenv
from path_queries import direct_queries, complex_queries
from llm_prompt import initialise_prompts

BLACKLIST = ['shows signs of', 'showing signs of', 'detected', 
             'observed', 'requires attention', 'identified', "application"]

# Read all the paths extracted from MaintIE KG
def get_all_paths(valid=True):
    """ Read all the paths extracted from MaintIE Gold Dataset KG """
    queries = direct_queries + complex_queries
    paths_list = []
    paths_dict = {}
    for query in queries:
        with open(f"path_patterns/{query['outfile']}.json", encoding='utf-8') as f:
            paths_json = json.load(f)
            if valid:
                paths_json = [path for path in paths_json if path['valid'] == valid]
            print(f"{len(paths_json)}\tpaths in {query['outfile']}")
            paths_dict[query['outfile']] = paths_json
            paths_list.extend(paths_json)
    print(f"Total number of paths: {len(paths_list)}")
    return paths_list, paths_dict

# Craft and return prompt for generating MWO sentences
def get_generate_prompt(prompt_variations, object, event):
    """ Craft and return prompt for generating MWO sentences.
        Prompt: Generate 5 different Maintenance Work Order (MWO) sentence describing the
                following equipment undesirable event in natural language. 
                Equipment: {object}
                Undesirable Event: {event}
                You must use all terms given above and do not add new information.
                Avoid verbosity and use minimal stop words.
                Each sentence can have a maximum of 8 words.
    """
    # Randomly select base prompt and instruction prompt
    base_prompts, limit_words, limit_count = prompt_variations
    base = random.choice(base_prompts)
    words = random.choice(limit_words)
    count = random.choice(limit_count)
    blacklist = ["'"+word+"'" for word in BLACKLIST]
    blacklist = ', '.join(blacklist)
    prompt = f"{base}\nEquipment: {object}\nUndesirable Event: {event}"
    prompt += f"\nYou must use all terms given above and do not add new information.\n{words}\n{count}"
    prompt += f"Do not use these terms: {blacklist}."
    return prompt

# Get fewshot message from fewshot csv file
def get_generate_fewshot(prompt_variations):
    """ Get fewshot message from fewshot csv file """
    message = [{"role": "system", "content": "You are a technician recording maintenance work orders."}]
    with open("fewshot_messages/fewshot_generate.csv", encoding='utf-8') as f:
        fewshot_data = csv.reader(f)
        next(fewshot_data) # Ignore header
        for row in fewshot_data:
            object_name = row[0]
            event_name = f"{row[1]} {row[2]}".strip()
            prompt = get_generate_prompt(prompt_variations, object_name, event_name)
            user = {"role": "user", "content": prompt}
            example = f"1. {row[4]}\n2. {row[5]}\n3. {row[6]}\n4. {row[7]}\n5. {row[8]}"
            assistant = {"role": "assistant", "content": example}
            message.append(user)
            message.append(assistant)

    # Save fewshot message to json file
    with open("fewshot_messages/fewshot_generate.json", "w", encoding='utf-8') as f:
        json.dump(message, f, indent=4)

    return message

# Process LLM response and return list of MWO sentences
def process_mwo_response(response):
    """ Process LLM response and return list of MWO sentences """
    output = []
    sentences = response.split('\n')
    for sentence in sentences:
        processed = re.sub(r'^\d+\.\s*', '', sentence) # Remove numbering
        processed = re.sub(r',', '', processed)        # Remove commas
        processed = re.sub(r'\s+', ' ', processed)     # Remove extra spaces
        processed = processed.lower().strip()          # Case folding and strip
        output.append(processed)
    return output

# Overall generation process
def generate_mwo(client, prompt_variations, path):
    """ Generate MWO sentences for each path """
    num = 5
    # Get prompt for current path's PhysicalObject and UndesirableEvent
    object = path['object_name']
    event = path['event_name']
    prompt = get_generate_prompt(prompt_variations, object, event)

    # Get fewshot message
    fewshot = get_generate_fewshot(prompt_variations)

    # Generate 5 completions (max 5x5 sentences) for each path
    sentences = [] # Max 25 sentences (avg 10)
    for _ in range(num):
        message = fewshot + [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=message,
                        temperature=0.9,
                        top_p=0.9,
                        n=1
                )
        response_sentences = process_mwo_response(response.choices[0].message.content)
        sentences.extend(response_sentences)
    sentences = list(set(sentences)) # Remove duplicates
    print(f"{object} {event} - {len(sentences)} sentences")
    return sentences

# Get samples from different path types
def get_samples(paths_dict, num_samples=30):
    """ Get samples from different path types """
    samples = []
    for paths in paths_dict.values():
        if len(paths) < num_samples:
            paths = random.sample(paths, len(paths))
        else:
            paths = random.sample(paths, num_samples)
        samples.extend(paths)
    return samples

if __name__ == "__main__":
    # Set OpenAI API key
    load_dotenv()
    api_key = os.getenv("API_KEY")
    client = OpenAI(api_key=api_key)
    
    # Read all the paths extracted from MaintIE KG
    paths_list, paths_dict = get_all_paths(valid=True)
    
    # Initialise base prompts and instructions
    prompt_variations = initialise_prompts(client, num_variants=5, num_examples=5)
    
    # Sample random paths from each path type
    paths = get_samples(paths_dict, num_samples=30)
    
    # Custom path
    # paths = [{'object_name': 'fuel', 'event_name': 'leaking'}]
    
    # Generate MWO sentences for each path
    for path in paths:
        sentences = generate_mwo(client, prompt_variations, path)
        
        # Save generated sentences to log text file
        with open("mwo_sentences/generate.txt", "a", encoding='utf-8') as f:
            f.write("========================================\n")
            f.write(f"Object: {path['object_name']}\n")
            f.write(f"Event: {path['event_name']}\n")
            f.write(f"Number of sentences: {len(sentences)}\n")
            f.write("----------------------------------------\n")
            for sentence in sentences:
                f.write(f"~ {sentence}\n")
            f.write("========================================\n")
            
        # Save one random to synthetic_generate data
        with open('TuringTest/synthetic_generate.txt', 'a', encoding='utf-8') as f:
            f.write(f"{random.choice(sentences)}\n")

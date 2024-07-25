import json
import random
import openai
from path_queries import direct_queries, complex_queries

# Read all the paths extracted from MaintIE KG
def get_all_paths():
    queries = direct_queries + complex_queries
    paths = []
    for query in queries:
        with open(f"pathPatterns/{query['outfile']}.json", encoding='utf-8') as f:
            data = json.load(f)
            print(f"{len(data)}\tpaths in {query['outfile']}")
            paths.extend(data)
    print(f"Total number of paths: {len(paths)}")
    return paths

# Read fewshot MWO examples
def get_fewshot_MWO(object, event):
    data = []
    with open("datasets/MaintIE/gold_release.json", encoding='utf-8') as f:
        gold = json.load(f)
        for d in gold:
            data.append(d['text'])
    
    

# Process the response from the LLM
def process_response(response):
    sentences = response.split("\n")
    sentences = [sentence for sentence in sentences if sentence]
    return sentences

# Select random pattern and generate MWO sentences
def generate_MWO(data, num_sentences, num_iterations):
    
    while num_iterations > 0 and data:
        # Choose random pattern from data and remove it
        current_pattern = random.choice(data)
        data.remove(current_pattern)
        num_iterations -= 1
        
        # Get LLM to generate humanised sentences for the pattern
        prompt = f"Generate a Maintenance Work Order (MWO) sentence describing the "
        prompt += "following equipment and undesirable event in natural language."
        prompt += f"\nEquipment: {current_pattern['object_name']}"
        prompt += f"\nUndesirable Event: {current_pattern['event_name']}"
        prompt += "\nThe sentence can have a maximum of 8 words."
        
        # Fewshot (MWO examples) - show how MWOs should look like

        response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "?"},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.7,
                        n=num_sentences
                    )

        # Process the response from the LLM
        for choice in response['choices']:
            response = choice['message']['content']
            sentences = process_response(response)
        
        # Append sentences to text file
        with open("pathPatterns/MWOsentences.txt", "a", encoding='utf-8') as f:
            for sentence in sentences:
                f.write(f"{sentence}\n")

if __name__ == "__main__":
    # Set OpenAI API key
    openai.api_key = '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'
    
    # Read all the paths extracted from MaintIE KG
    data = get_all_paths()

    # Generate 5 humanised sentences for 1 path (equipment and undesirable event)
    # generate_MWO(data, num_sentences=5, num_iterations=1)
    current_pattern = random.choice(data)
    fewshot = get_fewshot_MWO(current_pattern['object_name'], current_pattern['property_name'])
    print(fewshot)

# Experiment 1: Strictly follow the given path (equipment and undesirable event)
# Experiment 2: Generate synonyms first then generate MWOs
# - Problem: How do you know the synonyms are correct?
# - Solution: cross-check with IEC 81346-2 standard?
# Experiment 3: Generate equipment and undesirable event given the class and example
# - Problem: How do you know the generated equipment and undesirable event are correct?
# - Solution: cross-check with IEC 81346-2 standard?


import json
import random
import openai

# Read fewshot MWO examples
def get_fewshot_MWO(dataset="FMC-MWO2KG"):
    with open(f"datasets/{dataset}/full_fewshot.txt", encoding='utf-8') as f:
        lines = f.readlines()
        examples = [line.strip() for line in lines]
        random.shuffle(examples)
    return examples

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
        
        # Get LLM to generate several humanised sentences for the pattern
        prompt = f"Generate {num_sentences} concise and technical Maintenance Work Order (MWO) sentences "
        prompt += "describing the following equipment and undesirable event in natural language."
        prompt += f"\nEquipment: {current_pattern['object_name'].replace('_', ' ')}"
        prompt += f"\nUndesirable Event: {current_pattern['property_name'].replace('_', ' ')}"
        prompt += "\nEach sentence should be unique and describe the equipment and event in a different way."
        prompt += "\nEach sentence should be short and not more than 8 words."
        
        print(prompt)
        
        response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a failure mode code expert."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.7,
                        # n=2 # number of completions to generate
                    )

        # Process the response from the LLM
        for choice in response['choices']:
            response = choice['message']['content']
            sentences = process_response(response)
        
        # Append sentences to text file
        with open("pathPatterns/MWOsentences.txt", "a", encoding='utf-8') as f:
            for sentence in sentences:
                f.write(f"{sentence}\n")
        
with open("pathPatterns/object_property_patterns.json", encoding='utf-8') as f:
    data = json.load(f)

openai.api_key = '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'

# generate_MWO(data, num_sentences=5, num_iterations=3)
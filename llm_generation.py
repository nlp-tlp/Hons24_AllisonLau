import os
import re
import csv
import json
import random
from openai import OpenAI
from dotenv import load_dotenv
from path_queries import direct_queries, complex_queries
from llm_paraphrase import initialise_prompts, get_generate_prompt, process_mwo_response, paraphrase_mwo, check_similarity

# Read all the paths extracted from MaintIE KG
def get_all_paths(valid=True):
    """ Read all the paths extracted from MaintIE Gold Dataset KG """
    queries = direct_queries + complex_queries
    all_paths = []
    for query in queries:
        with open(f"path_patterns/{query['outfile']}.json", encoding='utf-8') as f:
            paths_json = json.load(f)
            if valid:
                paths_json = [path for path in paths_json if path['valid'] == valid]
            print(f"{len(paths_json)}\tpaths in {query['outfile']}")
            all_paths.extend(paths_json)
    print(f"Total number of paths: {len(all_paths)}")
    return all_paths

# Get fewshot message given fewshot csv file
# Header: object_name, event_name, helper_name, example0, example1, example2, example3, example4, example5
def get_generate_fewshot(base_prompts, limit_words, limit_count):
    """ Get fewshot message given fewshot csv file """
    message = [{"role": "system", "content": "You are a technician recording maintenance work orders."}]
    with open("fewshot_messages/fewshot.csv", encoding='utf-8') as f:
        fewshot_data = csv.reader(f)
        next(fewshot_data) # Ignore header
        for row in fewshot_data:
            if len(row) > 4:
                if row[2] == "": # No helper
                    user = {"role": "user", "content": get_generate_prompt(base_prompts, limit_words, limit_count, row[0], row[1])}
                else:
                    user = {"role": "user", "content": get_generate_prompt(base_prompts, limit_words, limit_count, row[0], row[1], row[2])}
                example = f"1. {row[3]}\n2. {row[4]}\n3. {row[5]}\n4. {row[6]}\n5. {row[7]}"
                assistant = {"role": "assistant", "content": example}
                message.append(user)
                message.append(assistant)

    # Save fewshot message to json file
    with open("fewshot_messages/fewshot_generate.json", "w", encoding='utf-8') as f:
        json.dump(message, f, indent=4)

    return message

# Remove sentences that do not have the object and event terms
def filter_sentences(sentences, keywords):
    """ Remove sentences that do not have the object and event terms """
    for sentence in sentences:
        if not all(word in sentence for word in keywords):
            sentences.remove(sentence)
    return sentences

# Overall generation process
def generate_mwo(client, base_prompts, limit_words, limit_count, path):
    """ Generate MWO sentences for each path """
    num = 5
    # Get prompt for current path's PhysicalObject and UndesirableEvent
    if 'helper_name' in path:
        prompt = get_generate_prompt(base_prompts, limit_words, limit_count, path['object_name'], path['event_name'], path['helper_name'])
        keywords = [path['object_name'], path['event_name'], path['helper_name']]
    else:
        prompt = get_generate_prompt(base_prompts, limit_words, limit_count, path['object_name'], path['event_name'])
        keywords = [path['object_name'], path['event_name']]

    # Get fewshot message
    fewshot = get_generate_fewshot(base_prompts, limit_words, limit_count)

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
    # sentences = filter_sentences(sentences, keywords)
    print(f"{len(sentences)} unique number of sentences")

    # Generate 5 paraphrases (max 5x25=125 sentences) for each sentence
    paraphrases = [] # Max 125 sentences (avg 20)
    for sentence in sentences:
        response_paraphrases = paraphrase_mwo(client, sentence, keywords, num)
        response_similarities = check_similarity(sentence, response_paraphrases)
        for para, sim in zip(response_paraphrases, response_similarities):
            if sim > 0.9:
                paraphrases.append(para)
    paraphrases = list(set(paraphrases)) # Remove duplicates
    # paraphrases = filter_sentences(paraphrases, keywords)
    print(f"{len(paraphrases)} unique number of paraphrases")

    # Add paraphrases to sentences
    sentences.extend(paraphrases)
    sentences = list(set(sentences)) # Remove duplicates
    print(f"{len(sentences)} unique number of total sentences")

    return sentences

# Main function
if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("API_KEY")
    client = OpenAI(api_key=api_key)

    # Read all the paths extracted from MaintIE KG
    data = get_all_paths(valid=True)

    # Initialise base prompts and instructions
    base_prompts, limit_words, limit_count = initialise_prompts(client, num_variants=5, num_examples=5)

    # Select random path
    random.seed(123)
    path = random.choice(data)

    # Generate MWO sentences for the selected path
    sentences = generate_mwo(client, base_prompts, limit_words, limit_count, path)

    # Save sentences to text file
    with open("mwo_sentences/path_sentences.txt", "a", encoding='utf-8') as f:
        f.write("========================================\n")
        f.write(f"Object: {path['object_name']}\n")
        f.write(f"Event: {path['event_name']}\n")
        if 'helper_name' in path:
            f.write(f"Helper: {path['helper_name']}\n")
        f.write(f"Number of sentences: {len(sentences)}\n")
        f.write("----------------------------------------\n")
        for sentence in sentences:
            if 'failure_mode' in path:
                f.write(f"~ {sentence},{path['failure_mode']}\n")
            else:
                f.write(f"~ {sentence}\n")
        f.write("========================================\n")

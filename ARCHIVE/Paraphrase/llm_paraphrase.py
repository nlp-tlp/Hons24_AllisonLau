import os
import re
import csv
import json
import random
from openai import OpenAI
from dotenv import load_dotenv
from llm_generate import process_mwo_response
from sentence_transformers import SentenceTransformer

# Craft and return prompt for paraphrasing MWO sentences
def get_paraphrase_prompt(sentence, keywords, num_paraphrases=5):
    """ Craft and return prompt for paraphrasing MWO sentences. """
    prompt = f"Paraphrase the following sentence {num_paraphrases} times.\n{sentence}\n"
    string_keywords = ", ".join(keywords)
    prompt += "You must include the following keywords: " + string_keywords
    prompt += "\nYou may change the sentence from passive to active voice or vice versa."
    prompt += "\nAvoid verbosity and use minimal stop words."
    prompt += "\nThe sentence can have a maximum of 8 words."
    return prompt

def get_paraphrase_fewshot():
    message = [{"role": "system", "content": "You are a maintenance work order sentence paraphraser."}]
    with open("fewshot_messages/fewshot_generate.csv", encoding='utf-8') as f:
        fewshot_data = csv.reader(f)
        next(fewshot_data) # Ignore header
        for row in fewshot_data:
            if row[2] == "": # No helper
                keywords = [row[0], row[1]]
            else:
                keywords = [row[0], row[1], row[2]]
            user = {"role": "user", "content": get_paraphrase_prompt(row[3], keywords)}
            example = f"1. {row[4]}\n2. {row[5]}\n3. {row[6]}\n4. {row[7]}\n5. {row[8]}"
            assistant = {"role": "assistant", "content": example}
            message.append(user)
            message.append(assistant)
    
    # Save fewshot message to json file
    with open("fewshot_messages/fewshot_paraphrase.json", "w", encoding='utf-8') as f:
        json.dump(message, f, indent=4)

    return message

# Get LLM to paraphrase MWO sentences with PhysicalObject and UndesirableEvent
def paraphrase_mwo(openai, sentence, keywords=None, num_paraphrases=5):
    """ GPT paraphrases MWO sentences. """
    # Paraphrase the MWO sentence num_paraphrases times
    prompt = get_paraphrase_prompt(sentence, keywords, num_paraphrases)
    message = get_paraphrase_fewshot() + [{"role": "user", "content": prompt}]
    response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=message,
                    top_p=0.9,
                    temperature=0.9,
                    n=1
                )
    output = process_mwo_response(response.choices[0].message.content)
    return output

if __name__ == "__main__":
    # Set OpenAI API key
    load_dotenv()
    api_key = os.getenv("API_KEY")
    client = OpenAI(api_key=api_key)

    # Test Paraphrase MWO Sentencces
    # sentence = "air horn working intermittently"
    # keywords = ["air horn", "working intermittently"]
    # x = paraphrase_mwo(client, sentence, keywords=keywords, num_paraphrases=5)
    # print(x)
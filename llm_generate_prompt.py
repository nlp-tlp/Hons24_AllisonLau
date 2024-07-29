import re
import openai
import random
from sentence_transformers import SentenceTransformer, SimilarityFunction

# Post-process LLM response into a list of sentences
def process_response(response):
    """ Process the response from the LLM. """
    # Process the response from the LLM
    output = []
    sentences = response.split('\n')
    for sentence in sentences:
        processed = re.sub(r'^\d+\.\s*', '', sentence).strip() 
        output.append(processed)
    return output
    
# Get LLM to paraphrase prompts for generating more diverse responses
def paraphrase_prompt(prompt, num_paraphrases=5, keywords=None):
    """ Paraphrase the prompt to generate more diverse responses. """
    # Paraphrase the prompt num_paraphrases times
    paraphrase_prompt = f"Paraphrase the following sentence {num_paraphrases} times.\n{prompt}\n"
    if keywords:
        static_keywords = ", ".join(keywords)
        paraphrase_prompt += "Must include the following keywords: " + static_keywords
    paraphrase_prompt += "\n" + "Do not add any new information or alter the meaning."
    response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[
                            {"role": "system", "content": "You are a sentence paraphraser."},
                            {"role": "user", "content": paraphrase_prompt},
                        ],
                    top_p=0.9,
                    temperature=0.9,
                    n=1
                )
    output = process_response(response.choices[0].message.content)
    return output

# Check semantic similarity for the paraphrased sentences
def check_similarity(original, paraphrases):
    """ Check semantic similarity for the paraphrased sentences. """
    model = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L6-v2')
    original_embedding = model.encode(original)
    paraphrases_embeddings = model.encode(paraphrases)
    similarities = model.similarity(original_embedding, paraphrases_embeddings)
    
    # Uncomment this to print sentence and their similarity scores
    # for sentence, similarity in zip(paraphrases, similarities.tolist()[0]):
    #     print(f"{similarity:.4f} - {sentence}")
    return similarities.tolist()[0]

# Craft and return prompt for generating MWO sentences
def get_prompt(object, event, helper=None):
    NUM_VARIATIONS = 10
    
    # Base prompt for generating MWO sentences
    base_prompt = "Generate a Maintenance Work Order (MWO) sentence describing the following equipment and undesirable event."
    keywords = ["Maintenance Work Order", "MWO", "equipment", "undesirable event", "sentence"]
    base_prompts = paraphrase_prompt(base_prompt, NUM_VARIATIONS, keywords)
    similarity = check_similarity(base_prompt, base_prompts)
    base_prompts = [prompt for prompt, sim in zip(base_prompts, similarity) if sim > 0.9] # Filter prompts with 0.9 similarity

    # Word-limit instruction for generating MWO sentences
    instruction = "The sentence can have a maximum of 8 words."
    keywords = ["sentence", "8"]
    instructions = paraphrase_prompt(instruction, NUM_VARIATIONS, keywords)
    similarity = check_similarity(instruction, instructions)
    instructions = [prompt for prompt, sim in zip(instructions, similarity) if sim > 0.9] # Filter prompts with 0.9 similarity
    
    # Randomly select base prompt and instruction prompt
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

if __name__ == "__main__":
   # Set OpenAI API key
    openai.api_key = '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'
    prompt = get_prompt("Pump", "Overheating")
    print(prompt)

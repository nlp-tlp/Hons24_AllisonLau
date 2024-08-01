import re
import openai
import random
from sentence_transformers import SentenceTransformer, SimilarityFunction

# Post-process LLM response of prompt paraphrases into a list of sentences
def process_prompt_response(response):
    """ Process the response from the LLM. """
    output = []
    sentences = response.split('\n')
    for sentence in sentences:
        processed = re.sub(r'^\d+\.\s*', '', sentence).strip() 
        output.append(processed)
    return output

# Post-process LLM response of MWO paraphrases into a list of sentences
def process_mwo_response(response):
    """ Process the response from the LLM. """
    output = []
    sentences = response.split('\n')
    for sentence in sentences:
        processed = re.sub(r'^\d+\.\s*', '', sentence) # Remove numbering
        processed = re.sub(r'[^\w\s]', ' ', processed) # Remove punctuation
        processed = re.sub(r'\s+', ' ', processed)     # Remove extra spaces
        processed = processed.lower().strip()          # Case folding and strip
        output.append(processed)
    return output

# Get LLM to paraphrase prompts for generating more diverse responses
def paraphrase_prompt(prompt, keywords=None, num_paraphrases=5):
    """ Paraphrase the prompt to generate more diverse responses. """
    # Paraphrase the prompt num_paraphrases times
    paraphrase_prompt = f"Paraphrase the following sentence {num_paraphrases} times.\n{prompt}\n"
    paraphrase_prompt += "\n" + "Do not add any new information or alter the meaning."
    if keywords:
        string_keywords = ", ".join(keywords)
        paraphrase_prompt += "Must include the following keywords: " + string_keywords
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
    output = process_prompt_response(response.choices[0].message.content)
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

# Initialise list of prompt variants
def initialise_prompts(num_variants, num_examples):
    """ Initialise list of prompt variants. """

    # Base prompt for generating MWO sentences
    base_prompts = []
    while len(base_prompts) < num_variants:
        if num_examples == 1:
            base_prompt = "Generate a Maintenance Work Order (MWO) sentence describing the following equipment and undesirable event."
            keywords = ["Maintenance Work Order", "MWO", "equipment", "undesirable event", "sentence"]
        elif num_examples == 5:
            base_prompt = f"Generate {num_examples} different Maintenance Work Order (MWO) sentences describing the following equipment and undesirable event."
            keywords = [f"{num_examples}", "Maintenance Work Order", "MWO", "equipment", "undesirable event", "sentence"]
        base_prompts = paraphrase_prompt(base_prompt, keywords, num_variants)
        similarity = check_similarity(base_prompt, base_prompts)
        for prompt, sim in zip(base_prompts, similarity):
            if sim > 0.9:
                base_prompts.append(prompt)
        base_prompts = list(set(base_prompts)) # Remove duplicates

    # Word-limit instruction for generating MWO sentences
    instructions = []
    while len(instructions) < num_variants:
        if num_examples == 1:
            instruction = "The sentence can have a maximum of 8 words."
        elif num_examples == 5:
            instruction = "Each sentence can have a maximum of 8 words."
        keywords = ["sentence", "8"]
        instructions = paraphrase_prompt(instruction, keywords, num_variants)
        similarity = check_similarity(instruction, instructions)
        for prompt, sim in zip(instructions, similarity):
            if sim > 0.9:
                instructions.append(prompt)
        instructions = list(set(instructions)) # Remove duplicates

    # Make sure list has correct number of variants
    base_prompts = base_prompts[:num_variants]
    instructions = instructions[:num_variants]
    return base_prompts, instructions

# Craft and return prompt for generating MWO sentences
def get_prompt(base_prompts, instructions, object, event, helper=None):
    """ Craft and return prompt for generating MWO sentences. """    
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

# Get LLM to paraphrase MWO sentences with PhysicalObject and UndesirableEvent
def paraphrase_MWO(sentence, keywords=None, num_paraphrases=5):
    """ GPT paraphrases MWO sentences. """
    # Paraphrase the MWO sentence num_paraphrases times
    paraphrase_prompt = f"Paraphrase the following sentence {num_paraphrases} times.\n{sentence}\n"
    if keywords:
        string_keywords = ", ".join(keywords)
        paraphrase_prompt += "Must include the following keywords: " + string_keywords
    paraphrase_prompt += "\nYou may change the sentence from passive to active voice or vice versa."
    paraphrase_prompt += "\nThe sentence can have a maximum of 8 words."
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
    output = process_mwo_response(response.choices[0].message.content)
    return output

if __name__ == "__main__":
   # Set OpenAI API key
    openai.api_key = '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'
    # sentence = "air horn working intermittently"
    # keywords = ["air horn", "working intermittently"]
    # paraphrase_MWO(sentence, keywords=keywords, num_paraphrases=5)

    # instruction = "The sentence can have a maximum of 8 words."
    # instructions_dummy = [
    #     "The sentence can have a maximum of 8 words.",
    #     "Each sentence can have a maximum of 8 words.",
    #     "The sentence should have a maximum of 8 words.",
    #     "Each sentence should have a maximum of 8 words.",
    #     "The sentence must have a maximum of 8 words."
    # ]
    # similarity = check_similarity(instruction, instructions_dummy)
    # for prompt, sim in zip(instructions_dummy, similarity):
    #     print(f"{sim:.4f} - {prompt}")

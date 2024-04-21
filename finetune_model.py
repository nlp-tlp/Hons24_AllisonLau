import sys
import time
import json
import openai
from generate_data import get_fewshot, get_example_prompt, save_observations_to_csv


# Set OpenAI API key
openai.api_key = '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'

FT_MODEL = "gpt-3.5-turbo"
FT_MODEL = "ft:gpt-3.5-turbo-0125:uwa-system-health-lab::9GJuFmqj"

# Fine-tune a model
def finetune_model():
    """ Fine-tune a model. """

    # Sent the prepared data to OpenAI
    train_data = openai.File.create(
        file=open("label2obs/prepared_data.jsonl", encoding='utf-8'),
        purpose="fine-tune"
    )

    # Wait for the file to be processed
    print("Waiting for file processing...")
    while True:
        train_status = openai.File.retrieve(train_data["id"])["status"]

        if train_status == "processed":
            break

        # Check every 5 seconds
        time.sleep(5)
        print(".", end="")
        sys.stdout.flush()

    # Fine-tune the model
    ft_job = openai.FineTuningJob.create(
        model="gpt-3.5-turbo",
        training_file=train_data["id"],
    )
    ft_job_id = ft_job["id"]

    print(f"Fine-tuning job ID: {ft_job_id}")

    # Save the fine-tuning job to a file
    with open(f"FinetuneModels/{ft_job_id}.json", "w", encoding='utf-8') as file:
        json.dump(ft_job, file)

    # Wait for fine-tuning to complete
    print("Waiting for fine-tuning to complete...")
    messages = set()
    while True:
        ft_job_status = openai.FineTuningJob.retrieve(ft_job_id)["status"]

        if ft_job_status == "succeeded" or ft_job_status == "failed":
            break

        # Print out the messages (fine tuning status)
        # Only print out messages that have not been seen before
        events = openai.FineTuningJob.list_events(ft_job_id, limit=10)
        for e in events["data"][::-1]:
            message = e["message"]
            if message not in messages:
                print(message)
                messages.add(message)

        # Check every 5 seconds
        time.sleep(5)

    print("Fine-tuning completed.")
    ft_job_result = openai.FineTuningJob.retrieve(ft_job_id)
    print(ft_job_result)

    with open("FinetuneModels/results-{ft_job_id}.json", "w", encoding='utf-8') as file:
        json.dump(ft_job_result, file)

FMCODES = {
    "Breakdown": "BRD",
    'Plugged / choked': "PLU",
    'Leaking': "LEA",
    'Minor in-service problems': "SER",
    'Structural deficiency': "STD",
    'Noise': "NOI",
    'Failure to start on demand': "FTS",
    'Vibration': "VIB",
    'Overheating': "OHE",
    'Failure to function': "FTF",
    'Low output': "LOO",
    'Electrical': "ELE",
    'Failure to stop on demand': "STP",
    'Abnormal instrument reading': "AIR",
    'Other': "OTH",
    'Failure to close': "FTC",
    'Contamination': "CTM",
    'High output': "HIO",
    'Erratic output': "ERO",
    'Failure to rotate': "FRO",
    'Spurious stop': "UST",
    'Failure to open': "FTO"
}

# Use the fine-tuned model to generate data
def use_model():
    """ Use the fine-tuned model to generate data. """

    fewshot_examples = get_fewshot() # get_fewshot_examples() for unmodified version
    fmcodes = sorted(fewshot_examples.keys()) # sorted in alphabetical order
    num_samples = 50

    # Generate observations for each label
    generated_data = {} # key (failure mode) -> value (observations)
    for observation in fmcodes:
        code = FMCODES[observation]
        print(f"Generating observations for {code} ({observation})...")
        generate_prompt = f"Generate 100 different observations for failure mode code {code} ({observation}).\n"
        contraint_prompt = "Your answer should contain only the observations, which are comma-separated, and nothing else.\n"
        number_prompt = f"You must generate {num_samples} observations, no less and no more than 100.\n"
        fewshot_prompt = get_example_prompt([code, observation], fewshot_examples)
        prompt = generate_prompt + contraint_prompt + number_prompt + fewshot_prompt
        # print(prompt)
        response = openai.ChatCompletion.create(
                        model=FT_MODEL,
                        messages=[
                            {"role": "system", "content": "Generate observations (from maintenance work orders) for the given failure mode code."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.7
                    )
        observations = response['choices'][0]['message']['content'].split(',')
        observations = list(set(observations)) # Remove duplicates
        generated_data[code] = generated_data

        save_observations_to_csv(f'observations/{code}.csv', observations)
        
use_model()
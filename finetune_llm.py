import os
import sys
import time
import json
import openai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Set OpenAI API key
openai.api_key = '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'

# Fine-tune LLM
def finetune_llm():
    """ Fine-tune a large language model. """

    # Sent the prepared data to OpenAI
    train_file = os.path.join(BASE_DIR, "label2obs", "prepared_data.jsonl")
    train_data = openai.File.create(
        file=open(train_file, encoding='utf-8'),
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

    # Fine-tune the LLM
    ft_job = openai.FineTuningJob.create(
        model="gpt-4o-mini",
        training_file=train_data["id"],
    )
    ft_job_id = ft_job["id"]

    print(f"Fine-tuning job ID: {ft_job_id}")

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

    out_filepath = os.path.join(BASE_DIR, "FinetuneModels", f"results-{ft_job_id}.json")
    with open(out_filepath, "w", encoding='utf-8') as file:
        json.dump(ft_job_result, file, indent=4)

if __name__ == '__main__':
    finetune_llm()

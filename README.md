# Hons24_AllisonLau
## Instructions
### Dataset Analysis
1. Run `python data_analysis.py` to analyse MaintIE or FMC-MWO2KG datasets.

This python script contains code for dataset preparation and dataset analysis.

### Load MaintIE Dataset into Neo4j Knowledge Graph
1. Create a project and an instance of a graph database in Neo4j Desktop.
2. Start the database and open the browser.
3. Run `python maintie_to_kg.py` to load the MaintIE dataset into Neo4j.

### Extracting paths (equipment and undesirable event combination) from Neo4j
1. Queries for extracting paths are stored in `path_queries.py`.
2. Run `python path_matching.py` to extract paths from Neo4j.
3. Different paths are stored in their respective json files in `path_patterns` directory.

### LLM Generate data given Path (equipment and undesirable event combination)
1. Run `python llm_humanise.py` to generate MWO sentences from valid paths.

### Flair Text Classification
1. Run `python flair_fmc.py` to train the flair text classification model.

- `train_fmc(dir_name)`: Train the flair text classification model for FMC.
- `test_fmc(dir_name)`: Test the flair text classification model for FMC.
### LLM Generate data given Failure Mode Code
1. Run `python llm_generate.py` to generate data.

```python
generate_data(gpt_model, output_dir, is_fewshot, is_specific):
```
- `gpt_model`: The GPT model to generate data.
- `output_dir`: The directory to save the generated data.
- `is_fewshot`: Whether to use few-shot learning.
- `is_specific`: Whether to use specific prompting.

### Fine-tuning
1. Run `python finetune_model.py` to fine-tune the model.

Fine-tuning jobs for each model can be found under the `FinetuneModels` directory. These models can be used as the `gpt_model` parameter in the `generate_data` function.

### Prepare data
1. Run `python prepare_data.py` to prepare data for training.

- `prepare_data_for_llm()`: Prepare data for training the GPT-3.5 model.
- `prepare_data_for_fmc(dir_name)`: Prepare data for fine-tuning the flair text classification model for FMC.
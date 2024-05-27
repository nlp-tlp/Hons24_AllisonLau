# Hons24_AllisonLau
## Instructions
### Generate data
1. Run `python generate_data.py` to generate data.

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

### Flair Text Classification
1. Run `python flair_fmc.py` to train the flair text classification model.

- `train_fmc(dir_name)`: Train the flair text classification model for FMC.
- `test_fmc(dir_name)`: Test the flair text classification model for FMC.
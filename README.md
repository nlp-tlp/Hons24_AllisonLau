# Hons24_AllisonLau
## Instructions
### Datasets

The datasets can be found in the `data` directory. The following datasets are used/analysed in this project:

- [FMC-MWO2KG dataset](https://paperswithcode.com/dataset/fmc-mwo2kg): labelled dataset of failure mode classification (FMC) from failure observations
- [MaintIE dataset](https://github.com/nlp-tlp/maintie): annotated dataset of maintenance work orders with entities and relations in the MaintIE schema
- [MaintNorm dataset](https://github.com/nlp-tlp/maintnorm): maintenance work order dataset with pre- and post-lexically normalised text (combined)
- [Corrections dictionary](): dictionary of corrections used for the humanisation step of synthetic data generation pipeline

### Dataset Analysis

The data analysis code can be found in the (`DataAnalysis`)[https://github.com/nlp-tlp/Hons24_AllisonLau/tree/main/DataAnalysis] directory. The following analyses are performed:

- (`mwo2kg_analysis.ipynb`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/DataAnalysis/mwo2kg_analysis.ipynb]: analysis of the FMC-MWO2KG dataset - frequency of failure mode codes (classes), aligning the failure observations with the MWOs in the dataset
- (`maintie_analysis.ipynb`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/DataAnalysis/maintie_analysis.ipynb]: analysis of the MaintIE dataset - frequency of total entities and relations, frequency of unique entities and relations, types of triples, number of tokens in the MWOs (min, max, average), number of hierarchical relations between equipment and their components, extract undesirable events (failure modes), analysis of manual FMC mapping, frequency distribution of sentence lengths
- (`maintnorm_analysis.ipynb`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/DataAnalysis/maintnorm_analysis.ipynb]: extract relevant pairs of pre- and post-lexically normalised MWO tokens for compiling a corrections dictionary
- (`synthetic_analysis.ipynb`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/DataAnalysis/synthetic_analysis.ipynb]: number of tokens in the MWOs (min, max, average), sentence length distribution (human vs synthetic data), filter potential LLM hallucinations for analysis (output not strictly following given prompt)
- (`typos_analysis.ipynb`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/DataAnalysis/typos_analysis.ipynb]: loading corrections dictionaries, reordering corrections dictionaries

### Equipment-Failure Path Extraction from MaintIE Knowledge Graph (Neo4j)

The code for extracting equipment-failure paths from the MaintIE Knowledge Graph can be found in the (`PathExtraction`)[https://github.com/nlp-tlp/Hons24_AllisonLau/tree/main/PathExtraction] directory. The following steps are performed:

#### Load MaintIE Dataset into Neo4j Knowledge Graph

1. Create a project and an instance of a graph database in Neo4j Desktop.
2. Start the database and open the browser.
3. Run `python maintie_to_kg.py` to load the MaintIE dataset into Neo4j.
Note: This will take a while to load the dataset into Neo4j.

#### Extracting paths (equipment and undesirable event combination) from Neo4j

1. Queries for extracting paths are stored in `path_queries.py`.
2. Run `python path_matching.ipynb` to extract paths from Neo4j.
3. Different paths are stored in their respective json files in `path_patterns` directory.
4. Analysis of paths can be found - total number of paths, frequency of equipment, frequency of undesirable events, frequency of inherent function of *PhysicalObjects*.

#### Path Types

| Path Type               | Number of Valid Paths | Direct | Additional | Total before SME Validation | Total after SME Validation |
|-------------------------|-----------------------|--------|------------|-----------------------------|----------------------------|
| Object-Property          | 26                    | 23     | 49         | 49                          | 49                         |
| Process-Agent            | 77                    | 314    | 391        | 391                         | 391                        |
| Process-Patient          | 38                    | 231    | 269        | 269                         | 269                        |
| State-Patient            | 293                   | 915    | 1208       | 1208                        | 1208                       |
| Object-Property-State    | 1                     | 2      | 3          | 3                           | 3                          |
| State-Agent-Activity     | 25                    | 111    | 136        | 607                         | 607                        |
| State-Agent-Patient      | 7                     | 24     | 31         | 37                          | 37                         |
| Process-Agent-Patient    | 31                    | 119    | 150        | 1230                        | 1230                       |
| **Total**                | **498**               | **1739**| **2237**   | **3794**                     | **3794**                    |

### MWO Sentence Generation via LLM (GPT-4o mini)

The code for generating synthetic MWO sentences using LLM can be found in the (`Generate`)[https://github.com/nlp-tlp/Hons24_AllisonLau/tree/main/Generate] directory. 

#### Generate Synthetic MWO Sentences

1. Run `python llm_generate.py` to generate synthetic MWO sentences using GPT-4o mini.
- Function used to generate synthetic MWO sentences: `generate_mwo()` and `generate_diverse_mwo()`
- Generated synthetic MWO sentences are stored in the `mwo_sentences` directory. There is a log file (`mwo_sentences/log.txt`) detailing the given equipment + failure mode and the generated sentences. There is also a csv file (`mwo_sentences/order_synthetic.txt`) containing just the generated synthetic MWO sentences.
- You can alter the number of path samples by changing the `num_samples` parameter in `get_samples()` function. You can also choose to exclude certain path types by including their path names (json file) in the `exclude` list in `get_samples()` function.

#### Documentation

The following functionalities are implemented:

- (`llm_generate.py`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/Generate/llm_generate.py]: code to prepare few-shot examples, generate synthetic MWO sentences using GP-4o mini, processing of LM outputs
    - `get_all_paths()`: get all paths from json files in `path_patterns` directory
    - `get_generate_prompt()`: prepare prompt for LLM
    - `get_generate_fewshot()`: prepare few-shot examples for LLM 
    - `generate_mwo()`: generate synthetic MWO sentences using LLM (simple)
    - `generate_diverse_mwo()`: generate diverse synthetic MWO sentences using LLM
    - `process_mwo_response()`: process LLM outputs of synthetic MWO sentences
    - `get_samples()`: samples paths from each path type
- (`llm_prompt.py`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/Generate/llm_prompt.py]: code to get list of prompt variations, processing of LLM outputs, and paraphrasing the prompts
    - `initialise_prompts()`: get list of prompt variations for LLM
    - `process_prompt_response()`: process LLM outputs of prompt variations
    - `paraphrase_prompt()`: paraphrase the prompts for LLM
- (`diversity_experiment.ipynb`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/Generate/diversity_experiment.ipynb]: experiments for increasing the diversity of the LLM-generated MWO sentences per path
    - Same prompt VS Variations of prompt
    - Single generation VS Batch generation
    - Generation VS Paraphrasing
- You can find the few-shot examples used in the `fewshot_messages` directory.
- Some logs of the LLM-generated MWO sentences can be found in the `mwo_sentences` directory.

### MWO Sentence Humanisation via Rule-based Approach (Probabilistic Rules)

The code for humanising synthetic MWO sentences can be found in the (`Humanise`)[https://github.com/nlp-tlp/Hons24_AllisonLau/tree/main/Humanise] directory. 

#### Humanise Synthetic MWO Sentences

1. Run `python humanise.py` to test humanising synthetic MWO sentences using a rule-based approach.
- Function used to humanise synthetic MWO sentences: `humanise_sentence()`

#### Documentation

The following functionalities are implemented:

- (`humanise_experiment.ipynb`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/Humanise/humanise_experiment.ipynb]: experiments for humanising synthetic MWO sentences
- (`humanise.py`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/Humanise/humanise.py]: rule-based approach for humanising synthetic MWO sentences
    - `introduce_contractions()`: introduce English contractions to synthetic MWO sentences (50% probability)
    - `introduce_abbreviations()`: introduce abbreviations/jargon to synthetic MWO sentences (40% probability)
    - `rule_introduce_typos()`: introduce up to 3 typos in the synthetic MWO sentences 
    - `humanise_sentence()`: apply the above rules to humanise synthetic MWO sentences

### Evaluation of Synthetic MWO Sentences

The code for evaluating the synthetic MWO sentences can be found in the (`Evaluation`)[https://github.com/nlp-tlp/Hons24_AllisonLau/tree/main/Evaluation] directory under `evaluation.ipynb`. The following evaluations are performed:
- Turing Test
- Ranking Test (replicated from (Bikaun 2022)[https://github.com/nlp-tlp/cfg_technical_short_text])

### Synthetic MWOs Files

The synthetic MWOs generated over the course of the project can be found in different files:
- `Generate/mwo_sentences/order_synthetic.txt`: synthetic MWO sentences generated, including the inherent function of the equipment, the equipment, and the failure mode
- `Generate/mwo_sentences/synthetic.txt`: shuffled version of above
- `Generate/mwo_sentences/log.txt`: logs of MWO sentences generated, including the path (equipment + failure mode) and the number of sentences generated
- `Evaluation/Turing2/synthetic_generate_v2.txt`: synthetic MWO sentences generated for the Turing Test evaluation
- `Evaluation/Turing2/synthetic_humanise_v2.txt`: humanised synthetic MWO sentences for the Turing Test evaluation

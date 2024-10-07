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

- (`mwo2kg_analysis.py`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/DataAnalysis/mwo2kg_analysis.ipynb]: analysis of the FMC-MWO2KG dataset - frequency of failure mode codes (classes), aligning the failure observations with the MWOs in the dataset
- (`maintie_analysis.py`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/DataAnalysis/maintie_analysis.ipynb]: analysis of the MaintIE dataset - frequency of total entities and relations, frequency of unique entities and relations, types of triples, number of tokens in the MWOs (min, max, average), number of hierarchical relations between equipment and their components, extract undesirable events (failure modes), analysis of manual FMC mapping, frequency distribution of sentence lengths
- (`maintnorm_analysis.py`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/DataAnalysis/maintnorm_analysis.ipynb]: extract relevant pairs of pre- and post-lexically normalised MWO tokens for compiling a corrections dictionary
- (`synthetic_analysis.py`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/DataAnalysis/synthetic_analysis.ipynb]: number of tokens in the MWOs (min, max, average), sentence length distribution (human vs synthetic data), filter potential LLM hallucinations for analysis (output not strictly following given prompt)
- (`typos_analysis.py`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/DataAnalysis/typos_analysis.ipynb]: loading corrections dictionaries, reordering corrections dictionaries

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

### MWO Sentence Generation via LLM (GPT-4o mini)

The code for generating synthetic MWO sentences using LLM can be found in the (`Generate`)[https://github.com/nlp-tlp/Hons24_AllisonLau/tree/main/Generate] directory. The following functionalities are implemented:

- (`llm_generate.py`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/Generate/llm_generate.py]: code to prepare few-shot examples, generate synthetic MWO sentences using GP-4o mini, processing of LM outputs
    - `get_generate_prompt()`: prepare prompt for LLM
    - `get_generate_fewshot()`: prepare few-shot examples for LLM 
    - `generate_mwo()`: generate synthetic MWO sentences using LLM (simple)
    - `generate_diverse_mwo()`: generate diverse synthetic MWO sentences using LLM
    - `process_mwo_response()`: process LLM outputs of synthetic MWO sentences
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

The code for humanising synthetic MWO sentences can be found in the (`Humanise`)[https://github.com/nlp-tlp/Hons24_AllisonLau/tree/main/Humanise] directory. The following functionalities are implemented:

- (`humanise_experiment.ipynb`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/Humanise/humanise_experiment.ipynb]: experiments for humanising synthetic MWO sentences
- (`humanise.py`)[https://github.com/nlp-tlp/Hons24_AllisonLau/blob/main/Humanise/humanise.py]: rule-based approach for humanising synthetic MWO sentences
    - `introduce_contractions()`: introduce English contractions to synthetic MWO sentences (50% probability)
    - `introduce_abbreviations()`: introduce abbreviations/jargon to synthetic MWO sentences (40% probability)
    - `rule_introduce_typos()`: introduce up to 3 typos in the synthetic MWO sentences 
    - `humanise_sentence()`: apply the above rules to humanise synthetic MWO sentences
# Hons24_AllisonLau
## Instructions
### Datasets

The datasets can be found in the `data` directory. The following datasets are used/analysed in this project:

- [FMC-MWO2KG dataset](https://paperswithcode.com/dataset/fmc-mwo2kg): labelled dataset of failure mode classification (FMC) from failure observations
- [MaintIE dataset](https://github.com/nlp-tlp/maintie): annotated dataset of maintenance work orders with entities and relations in the MaintIE schema
- [MaintNorm dataset](https://github.com/nlp-tlp/maintnorm): maintenance work order dataset with pre- and post-lexically normalised text (combined)
- [Corrections dictionary](): dictionary of corrections used for the humanisation step of synthetic data generation pipeline

### Dataset Analysis

The data analysis code can be found in the `DataAnalysis` directory. The following analyses are performed:

- `mwo2kg_analysis.py`: analysis of the FMC-MWO2KG dataset - frequency of failure mode codes (classes), aligning the failure observations with the MWOs in the dataset
- `maintie_analysis.py`: analysis of the MaintIE dataset - frequency of total entities and relations, frequency of unique entities and relations, types of triples, number of tokens in the MWOs (min, max, average), number of hierarchical relations between equipment and their components, extract undesirable events (failure modes), analysis of manual FMC mapping, frequency distribution of sentence lengths
- `maintnorm_analysis.py`: extract relevant pairs of pre- and post-lexically normalised MWO tokens for compiling a corrections dictionary
- `synthetic_analysis.py`: number of tokens in the MWOs (min, max, average), sentence length distribution (human vs synthetic data), filter potential LLM hallucinations for analysis (output not strictly following given prompt)
- `typos_analysis.py`: loading corrections dictionaries, reordering corrections dictionaries

### Equipment-Failure Path Extraction from MaintIE Knowledge Graph (Neo4j)

The code for extracting equipment-failure paths from the MaintIE Knowledge Graph can be found in the `PathExtraction` directory. The following steps are performed:

#### Load MaintIE Dataset into Neo4j Knowledge Graph

1. Create a project and an instance of a graph database in Neo4j Desktop.
2. Start the database and open the browser.
3. Run `python maintie_to_kg.py` to load the MaintIE dataset into Neo4j.

#### Extracting paths (equipment and undesirable event combination) from Neo4j
1. Queries for extracting paths are stored in `path_queries.py`.
2. Run `python path_matching.py` to extract paths from Neo4j.
3. Different paths are stored in their respective json files in `path_patterns` directory.
4. Analysis of paths can be found - total number of paths, frequency of equipment, frequency of undesirable events, frequency of inherent function of *PhysicalObjects*.

### MWO Sentence Generation via LLM (GPT-4o mini)



### MWO Sentence Humanisation via Rule-based Approach (Probabilistic Rules)

#### Introduce Contractions


#### Introduce Abbreviations

#### Introduce Typographical Errors


###
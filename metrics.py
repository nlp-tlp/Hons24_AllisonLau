""" Code for metrics to measure the quality of the generated observations. """

import os
import csv
import nltk
import numpy as np
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize
from generate_data import FMCODES
from scipy.spatial import distance
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Get vocabulary size
def get_vocab_size(observations):
    """ Get the vocabulary size of the generated observations. """
    all_obs = ' '.join(observations)
    tokens = word_tokenize(all_obs)
    vocab_size = len(set(tokens))
    return vocab_size

# Word frequency distribution (Type-Token Ratio)
def word_freq_dist(observations):
    """ Get the word frequency distribution of the generated observations. """
    all_obs = ' '.join(observations)
    tokens = word_tokenize(all_obs)
    fdist = FreqDist(tokens)
    num_types = len(fdist)
    num_tokens = len(tokens)
    
    ttr = num_types / num_tokens
    return round(ttr, 4)

def measure_similarity(observations):
    """ Measure the semantic similarity of the generated observations. """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(observations)
    similarity = 0
    for i, emb1 in enumerate(embeddings):
        for emb2 in embeddings[i+1:]:
            similarity += 1 - distance.cosine(emb1, emb2)
    average_similarity = similarity / (len(embeddings) * (len(embeddings) - 1) / 2)
    return round(average_similarity, 4)

if __name__ == '__main__':
    for code in FMCODES.values():
        filepath = os.path.join(BASE_DIR, f'LLM_observations/count/{code}.csv')
        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            observations = [row[0] for row in reader]
        ttr = word_freq_dist(observations)
        print(f"{code}'s TTR = {ttr}")

import os
import json

MAX_ROWS = 10

SYSTEM_CONTENT = (
    "Generate observations (from maintenance work orders) for the given failure mode code."
)

def prepare_data():
    """ Prepare data for training the model. """
    
    
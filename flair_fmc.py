from flair.embeddings import PooledFlairEmbeddings, DocumentRNNEmbeddings
from flair.datasets import CSVClassificationCorpus
from flair.visual.training_curves import Plotter
from flair.trainers import ModelTrainer
from flair.models import TextClassifier
from flair.data import Sentence
import os

def train_fmc(dir_name='datasets/FMC-MWO2KG'):
    current_path = os.path.dirname(os.path.abspath(__file__))

    # 1. what label do we want to predict?
    label_type = 'failure_mode'

    # 2. get the corpus
    column_name_map = {0: 'text', 1: "label_failure_mode"}
    data_folder = os.path.join(current_path, dir_name)
    corpus = CSVClassificationCorpus(data_folder, column_name_map, label_type=label_type, delimiter=",")
    print(corpus)
    # 3. create the label dictionary
    label_dict = corpus.make_label_dictionary(label_type=label_type)

    # 4. initialize embeddings
    word_embeddings = [
        #FlairEmbeddings('resources/taggers/geo_language_model/best-lm.pt')

        # comment in this line to use character embeddings
        #CharacterEmbeddings(),
        #BertEmbeddings(),

        # comment in these lines to use flair embeddings
        PooledFlairEmbeddings('mix-forward'),
        PooledFlairEmbeddings('mix-backward'),
    ]

    document_embeddings = DocumentRNNEmbeddings(word_embeddings, hidden_size=512)
    #document_embeddings = TransformerDocumentEmbeddings('distilbert-base-uncased', fine_tune=True)
    #embeddings: StackedEmbeddings = StackedEmbeddings(embeddings=embedding_types)

    # 5. initialize sequence tagger
    classifier  = TextClassifier(document_embeddings, label_dictionary=label_dict, label_type=label_type)

    # 6. initialize trainer
    trainer = ModelTrainer(classifier, corpus)

    # 7. start training
    trainer.train(os.path.join(current_path, 'resources/taggers/failure-mode-classifier'),
                    learning_rate=0.1,
                    mini_batch_size=32,
                    #anneal_factor=0.5,
                    max_epochs=20,
                    patience=5,
                    embeddings_storage_mode='gpu')

def test_fmc(dir_name='datasets/FMC-MWO2KG'):
    model = TextClassifier.load('resources/taggers/failure-mode-classifier/final-model.pt')

    test_sents = []
    with open(f'{dir_name}/test.txt', 'r', encoding='utf-8') as f:
        for line in f:
            phrase = line.split(',')[0].strip()
            label = line.split(',')[1].strip()
            test_sents.append({ 'input': phrase, 'ground_truth': label})

    for sent in test_sents:
        s = Sentence(sent['input'])
        model.predict(s)

        label = str(s.labels[0]).split(' (', maxsplit=1)[0]
        conf = str(s.labels[0]).split(' (')[1].split(')')[0]

        sent['prediction'] = label
        sent['confidence'] = conf

    with open('flair_output.csv', 'w', encoding='utf-8') as f:
        f.write(','.join(test_sents[0].keys()))
        f.write('\n')
        for sent in test_sents:
            f.write(','.join(sent.values()))
            f.write('\n')

    print("Results written to flair_output.csv.")

if __name__=="__main__":
	# train_fmc(dir_name="datasets/FMC-MWO2KG")
    train_fmc(dir_name="LLM_data/fs_all")
    # train_fmc(dir_name="LLM_data/fs_specific")
    # train_fmc(dir_name="LLM_data/no_fewshot")
    # train_fmc(dir_name="LLM_data/ft_specific1")
    # train_fmc(dir_name="LLM_data/ft_specific2")
	# test_fmc()
 	# test_fmc("LLM_data")
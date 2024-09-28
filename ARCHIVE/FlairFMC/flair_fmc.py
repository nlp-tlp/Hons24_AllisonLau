from flair.embeddings import PooledFlairEmbeddings, DocumentRNNEmbeddings
from flair.datasets import CSVClassificationCorpus
from flair.visual.training_curves import Plotter
from flair.trainers import ModelTrainer
from flair.models import TextClassifier
from flair.data import Sentence
import os

def train_fmc(data_dir='../data/FMC-MWO2KG', model='fmc-mwo2kg'):
    current_path = os.path.dirname(os.path.abspath(__file__))

    # 1. what label do we want to predict?
    label_type = 'failure_mode'

    # 2. get the corpus
    column_name_map = {0: 'text', 1: "label_failure_mode"}
    data_folder = os.path.join(current_path, data_dir)
    corpus = CSVClassificationCorpus(data_folder, column_name_map, label_type=label_type, delimiter=",")

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
    trainer.train(os.path.join(current_path, f"FlairModels/{model}"),
                    learning_rate=0.1,
                    mini_batch_size=32,
                    #anneal_factor=0.5,
                    max_epochs=20,
                    patience=5,
                    embeddings_storage_mode='gpu')

def test_fmc(data_dir='../data/FMC-MWO2KG', model='fmc-mwo2kg'):
    model = TextClassifier.load(f'FlairModels/{model}/final-model.pt')

    test_sents = []
    with open(f'{data_dir}/test.txt', 'r', encoding='utf-8') as f:
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

    with open(f'FlairResults/{model}.csv', 'w', encoding='utf-8') as f:
        f.write(','.join(test_sents[0].keys()))
        f.write('\n')
        for sent in test_sents:
            f.write(','.join(sent.values()))
            f.write('\n')

    print(f"Results written to FlairResults/{model}.csv.")
    
def predict_fmc(model, infile, outfile):
    model = TextClassifier.load(f'FlairModels/{model}/final-model.pt')

    test_sents = []
    with open(infile, 'r', encoding='utf-8') as f:
        for line in f:
            input = line.strip()
            sent = Sentence(input)
            model.predict(sent)
            label = str(sent.labels[0]).split(' (', maxsplit=1)[0]
            conf = str(sent.labels[0]).split(' (')[1].split(')')[0]
            test_sents.append({ 'input': input, 'prediction': label, 'confidence': conf})
    
    with open(outfile, 'w', encoding='utf-8') as f:
        f.write(','.join(test_sents[0].keys()))
        f.write('\n')
        for sent in test_sents:
            f.write(','.join(sent.values()))
            f.write('\n')  

if __name__=="__main__":
    # train_fmc(data_dir="../data/FMC-MWO2KG", model='fmc-mwo2kg')
    # test_fmc(model='fmc-mwo2kg')
 
    # train_fmc(data_dir="../GivenCodes/LLM_fmc_data/fs_specific", model='fmc-fs_specific')
    # test_fmc(model='fmc-fs_specific')
    
    # train_fmc(data_dir="../GivenCodes/LLM_fmc_data/count", model='fmc-count')
    # test_fmc(model='fmc-count')
    
    predict_fmc(model='fmc-mwo2kg',
                infile="../data/MaintIE/gold_undesirable.txt",
                outfile="../data/MaintIE/flair_gold_pred.csv")
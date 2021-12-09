import nltk
from nltk.stem.lancaster import LancasterStemmer

import numpy as np
import tflearn
import tensorflow
import random
import json
import pickle
import time


stemmer = LancasterStemmer()

print("CHAT MODULE ACTIVE")

print("loading data file")
with open("intents.json") as file:
    data = json.load(file)
print("data file loaded")

print("...")
try:
    with open("data.pickle", "rb") as f:
        words, labels, training, output = pickle.load(f) 
except: 
    words = []
    labels = []
    docs_x = []
    docs_y = []
    print("tokenizing...")
    intentcounter = 0
    for intent in data['intents']:
        for pattern in intent['patterns']:
            wrds = nltk.word_tokenize(pattern)
            words.extend(wrds)
            docs_x.append(wrds)
            docs_y.append(intent['tag'])

        if intent['tag'] not in labels:
            labels.append(intent['tag']) 
        intentcounter += 1
        if intentcounter % 500 == 0:
            print("Intents tokenized: " + str(intentcounter))
    print("stemming...")
    words = [stemmer.stem(w.lower()) for w in words if w != '?']
    print("sorting and setting")
    # remove duplicates
    words = sorted(list(set(words))) 
    print("sorting labels")
    # sort labels
    labels = sorted(labels)

   
    training = []
    output = []
    print("creating initial out_empty list")
    out_empty = [0 for _ in range(len(labels))]

    print("creating bag of words")
    # bag of words
    bagcounter = 0
    for x, doc in enumerate(docs_x):
        bag = []

        wrds = [stemmer.stem(w) for w in doc]

        for w in words:
            if w in wrds:
                bag.append(1) # if word exists
            else:
                bag.append(0) # if word doesnt exist


        output_row = out_empty[:]
        output_row[labels.index(docs_y[x])] = 1

        training.append(bag)
        output.append(output_row)

        bagcounter += 1
        if bagcounter % 500 == 0:
            print("Bagged: " + str(bagcounter))


    print("creating training array")
    training = np.array(training) 
    print("creating output array")
    output = np.array(output)

    print("saving data pickle file")
    # save
    with open("data.pickle", "wb") as f:
        pickle.dump((words, labels, training, output), f) 

# the model
tensorflow.compat.v1.reset_default_graph() 

print("creating model")
# create the model:
net = tflearn.input_data(shape=[None, len(training[0])]) 
net = tflearn.fully_connected(net, 8) 
net = tflearn.fully_connected(net, 8) 
net = tflearn.fully_connected(net, len(output[0]), activation="softmax") 
net = tflearn.regression(net)

print("ready for training...")

# begin = input("Begin training?")
# if "no" in begin:
#     exit()

print("beginning model training...")
# train model
model = tflearn.DNN(net)

# dont train if model exists
try:
    model.load("model.tflearn")
    print("model loaded")
except:
    print("training model")
    model = tflearn.DNN(net)
    # train the model
    model.fit(training, output, n_epoch=150, batch_size=8, show_metric=True)
    # save the model
    model.save("model.tflearn")

print("TRAINING COMPLETE")

def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))] 

    s_words = nltk.word_tokenize(s) 
    s_words = [stemmer.stem(word.lower()) for word in s_words]

    # generate bag of words
    for se in s_words:
        for i, w in enumerate(words):
            if w == se: 
                bag[i] = 1 

    return np.array(bag)

def chat(usermessage, username, userid):
    """
    Predict the intent and select a random response from the tag responses
    """
    unknown_msg_responses = ["Sorry, can you try rephrasing that?", "I don't quite get what you're saying", "I don't understand - can you say it again a different way?", "I'm not sure what you want...can you be more specific?", "Please be more clear, I don't get what you're saying"]
    results = model.predict([bag_of_words(usermessage, words)])[0] 
    print(results)
    results_index = np.argmax(results) 
    tag = labels[results_index]
    print(tag) 
    print(results[results_index])
    print("-----") 

    if results[results_index] > 0.2:
        time.sleep(1)
        # pick a matching response
        for tg in data['intents']:
            if tg['tag'] == tag:
                responses = tg['responses']
        print("Response:")
        response = random.choice(responses)
 
        print(response)
        return response
    else:
        time.sleep(3)
        response = random.choice(unknown_msg_responses)
        return response
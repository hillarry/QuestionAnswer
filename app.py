# -*- coding: utf-8 -*-
"""
Created on Mon Sep  7 19:56:54 2020

@author: User
"""
import os
import sys
import requests

import nltk
nltk.download('punkt')
nltk.download('wordnet')
from nltk.stem import WordNetLemmatizer
lemmatizer=WordNetLemmatizer()
import pickle
import numpy as np
from flask import Flask,request
#from bot import Bot

from tensorflow import keras
from keras.models import load_model
model=load_model('chatbot_model.h5')
import json
import random
intents=json.loads(open('ques4.json').read())
words=pickle.load(open('words.pkl','rb'))
classes=pickle.load(open('classes.pkl','rb'))

def clean_up_sentence(sentence):
    sentence_words=nltk.word_tokenize(sentence)
    sentence_words=[lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

def bow(sentence,words,show_details=True):
    sentence_words=clean_up_sentence(sentence)
    bag=[0]*len(words)
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s:
                bag[i]=1
                if show_details:
                    print("found in bag: %s" %w)
    return(np.array(bag))
    
def predict_class(sentence,model):
    p=bow(sentence,words,show_details=False)
    res=model.predict(np.array([p]))[0]
    ERROR_THRESHOLD=0.25
    results=[[i,r] for i,r in enumerate(res) if r>ERROR_THRESHOLD]
    
    results.sort(key=lambda x:x[1], reverse=True)
    return_list=[]
    for r in results:
        return_list.append({"intent":classes[r[0]],"probability":str(r[1])})
    return return_list

def getResponse(ints, intents_json):
    tag=ints[0]['intent']
    list_of_intents=intents_json['intents']
    for i in list_of_intents:
        if(i['tag']==tag):
            result=random.choice(i['responses'])
    return result

def chatbot_response(text):
    ints=predict_class(text,model)
    res=getResponse(ints,intents)
    return res

app=Flask(__name__)

@app.route('/',methods=['GET'])
def verify():
    if request.args.get("hub.mode")=="subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token")==os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"],200
    return "Hello world",200


@app.route('/',methods=['POST'])
def webhook():
    data=request.get_json()
    print(data)
    
    if data["object"]=="page":
        
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"):
                    sender_id=messaging_event["sender"]["id"]
                    recipient_id=messaging_event["recipient"]["id"]
                    message_text=messaging_event["message"]["text"]
                    
                    responseai=chatbot_response(message_text)
                    send_message(sender_id,responseai)
                
                if messaging_event.get("delivery"):
                    pass
                
                if messaging_event.get("optin"):
                    pass
                
                if messaging_event.get("postback"):
                    pass
    return "ok",200

def send_message(recipient_id,message_text):
    print("sending message to {recipient}:{text}".format(recipient=recipient_id,text=message_text))
    
    params={
          "access_token":os.environ["PAGE_ACCESS_TOKEN"]
          
        }
    
    headers={
         "Content-Type":"application/json"
        }
    data=json.dumps({
           "recipient":{
                 "id":recipient_id  
            },
           "message":{
                 "text":message_text
            }
    })
    r=requests.post("https://graph.facebook.com/v8.0/me/messages",params=params,headers=headers,data=data)
    if r.status_code != 200:
        print(r.status_code)
        print(r.text)


if __name__=='__main__':
    app.run(debug=True)

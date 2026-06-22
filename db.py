import pymongo
from contextlib import contextmanager
import os
import word_processes as wp

@contextmanager
def connect():
    client = pymongo.MongoClient(os.environ.get('MONGO_URI', 'mongodb://localhost:27017/'))
    try:
        yield client[os.environ.get('MONGO_DB', 'vocab-database')]
    finally:
        client.close()

def init_database():
    with connect() as db:
        db.vocabList.create_index(['word', 'type'], unique=True)
init_database()

def add_word(word, notes, types):
    with connect() as db:
        db.vocabList.insert_many([{'word': word, 'notes': notes, 'type': t} for t in types])

def insert_words(wordList):
    if len(wordList) == 0:
        return
    with connect() as db:
        collection = db['vocabList']
        word_type_objs = [
            { 'word': o['word'], 'pinyin': o['pinyin'], 'notes': o['notes'], 'type': t, 'data': wp.get_word_data(o['word'], t) or {}}
            for o in wordList for t in o['types']
        ]
        operations = [
            pymongo.UpdateOne({'word': word['word'], 'type': word['type']}, {'$set': word}, upsert=True)
            for word in word_type_objs
        ]
        return collection.bulk_write(operations)

def get_words_for_type(word_type):
    with connect() as db:
        collection = db['vocabList']
        return list(collection.find({'type': word_type}, {'_id': 0}))

def get_duplicate_words(matchlist):
    with connect() as db:
        query = {
            "$or": [
                {'word': word }
                for word, _, _, _ in matchlist
            ]
        }
        duplicates = db.vocabList.find(query, {'_id': 0, 'word': 1}).to_list()
        return [o['word'] for o in duplicates]

def get_word_data(word, word_type):
    with connect() as db:
        collection = db['vocabList']
        return collection.find_one({'word': word, 'type': word_type}, {'_id': 0, 'data': 1})['data'] or {}

def get_word(word, word_type):
    with connect() as db:
        collection = db['vocabList']
        return collection.find_one({'word': word, 'type': word_type}, {'_id': 0})
    
def update_word(word, word_type, new_word):
    with connect() as db:
        collection = db['vocabList']
        return collection.update_one({'word': word, 'type': word_type}, {'$set': new_word})

def delete_word(word, word_type):
    with connect() as db:
        collection = db['vocabList']
        return collection.delete_one({'word': word, 'type': word_type})
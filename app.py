#!/usr/bin/env python3

from flask import *

import re

import db, word_processes as wp, ai

app = Flask(__name__)

categories = [
    {
        "id": 'idiom',
        "label": '📜 成语',
        "icon": '🏮',
        "games": [
        {
            "label": "成语填空",
            "icon": "（）",
            "url": "/games/fill"
        },
        {
            "label": "拼音默写",
            "icon": "（）",
            "url": "/games/拼音默写/idiom"
        }
    ]},
    {
        "id": 'word', "label": '📖 词语', "icon": '📚',
        "games": [
            {
                "label": "拼音默写",
                "icon": "（）",
                "url": "/games/拼音默写/word"
            }
        ]
    },
    { "id": 'char', "label": '🖌️ 字', "icon": '✍️' },
    { "id": 'xiehouyu', "label": '🎭 歇后语', "icon": '🤣' },
    { "id": 'internet_slang', "label": '💻 网络用语', "icon": '📱' },
    { "id": 'quote', "label": '🗣️ 名人名言', "icon": '👤' },
    { "id": 'saying', "label": "🔖 俗语", "icon": "🔖"},
    {
        "id": "poem", "label": "📜 诗词", "icon": "📜",
        "games": [
            {
                "label": "默写诗词",
                "icon": "（）",
                "url": "/games/fill-full-poem"
            }
        ]
    },
];

@app.route('/')
def index():
    return render_template('word-list.html', categories=categories)

@app.route('/import-list-raw', methods=['POST'])
def import_word_list_raw():
    data = request.get_data(as_text=True).replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
    # Seperate all the words and find the matches in the database
    match_list = wp.get_wordlist_matches(data)
    duplicates = db.get_duplicate_words(match_list)
    
    new_words = [(word, notes, pinyin, types)  for (word, notes, pinyin, types) in match_list if word not in duplicates]
    existing_words = [(word, notes, pinyin, types) for (word, notes, pinyin, types) in match_list if word in duplicates]
    
    matched_new_words = [(word, notes, pinyin, types) for word, notes, pinyin, types in new_words if types != []]
    unmatched_new_words = [(word, notes, pinyin, types) for word, notes, pinyin, types in new_words if types == []]

    # Return match list for confirmation
    return jsonify({"matched_new_words": matched_new_words, "unmatched_new_words": unmatched_new_words, "existing_words": existing_words})

@app.route('/import-list-confirmed', methods=['POST'])
def import_word_list_confirmed():
    data = request.get_json()
    entries = data.get("entries", [])
    # Add the words to the database
    db.insert_words(entries)
    return jsonify({"status": "success", "added_count": len(entries)})

@app.route('/api/words')
def api_words():
    word_type = request.args.get('type')
    query = request.args.get('query', '').strip()
    if not word_type:
        return jsonify({"error": "Missing 'type' parameter"}), 400
    words = db.query_words(word_type, query)
    return jsonify({"words": words})

@app.route('/api/word-data')
def api_word_data():
    word = request.args.get('word')
    word_type = request.args.get('type')
    if not word or not word_type:
        return jsonify({"error": "Missing 'word' or 'type' parameter"}), 400
    data = db.get_word_data(word, word_type)
    return jsonify({"data": data})

@app.route('/games/fill')
def fill_game():
    return render_template('games/idiom-fill.html', categories=categories)

@app.route('/edit-word', methods=['GET', 'POST'])
def edit_word():
    if request.method == 'POST':
        data = request.get_json()
        word = request.args.get('word')
        word_type = request.args.get('type')
        if not word or not word_type:
            return jsonify({"error": "Missing 'word' or 'type' parameter"}), 400
        db.update_word(word, word_type, data)
        return jsonify({"status": "success"})
    db_word = db.get_word(request.args.get('word'), request.args.get('type'))
    if not db_word:
        return jsonify({"error": "Word not found"}), 404
    return render_template('edit-word.html', word=db_word)

@app.route('/generate-word-data-with-ai', methods=['POST'])
def generate_word_data_with_ai():
    word = request.args.get('word')
    word_type = request.args.get('type')
    current_data = request.json.get('currentData', None)
    if not word or not word_type:
        return jsonify({"error": "Missing 'word' or 'type' parameter"}), 400

    ai_generated_data = ai.generate_relevant_information(word, current_data)
    while True:
        try:
            s = ai_generated_data[ai_generated_data.index('{'): ai_generated_data.rfind('}') + 1]
            json.loads(s)
            break
        except json.JSONDecodeError as e:
            print("Failed to parse JSON from AI response, retrying...")
            ai_generated_data = ai.generate_relevant_information(word, current_data)
    return jsonify({"data": json.loads(s)})

@app.route('/games/fill-full-poem')
def fill_full_poem_game():
    return render_template('games/fill-full-poem.html', poems=db.get_words_for_type('poem'))

@app.route('/delete-word', methods=['POST'])
def delete_word():
    word = request.args.get('word')
    word_type = request.args.get('type')
    if not word or not word_type:
        return jsonify({"error": "Missing 'word' or 'type' parameter"}), 400
    db.delete_word(word, word_type)
    return jsonify({"status": "success"})

@app.route('/games/拼音默写/word')
def pinyin_word_fill_game():
    return render_template('games/pinyin-fill.html', words=db.get_words_for_type('word'))

@app.route('/games/拼音默写/idiom')
def pinyin_idiom_fill_game():
    return render_template('games/pinyin-fill.html', words=db.get_words_for_type('idiom'))

@app.route('/api/similar-chars')
def api_similar_chars():
    word = request.args.get('word')
    if not word:
        return jsonify({"error": "Missing 'word' parameter"}), 400
    similar_chars = wp.get_similar_chars_for_word(word)
    return jsonify({"similar_chars": similar_chars[:5]})
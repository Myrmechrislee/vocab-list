import json, re
import unicodedata
import hanzidentifier

# with open('chinese-xinhua/data/ci.json', 'r') as f:
#     cis = json.load(f)

# with open('chinese-xinhua/data/idiom.json', 'r') as f:
#     idioms = json.load(f)

# with open('chinese-xinhua/data/word.json', 'r') as f:
#     words = json.load(f)

# with open('chinese-xinhua/data/xiehouyu.json', 'r') as f:
#     xiehouyus = json.load(f)

def remove_non_chinese_characters(text):
    return re.sub(r'[^\u4e00-\u9fff]+', '', text)

with open('chinese-dictionary/character/char_detail.json', 'r') as f:
    char_details = json.loads("[" + f.read() + "]")
    char_details_map = {c['char'] : c for c in char_details }

with open('chinese-dictionary/word/word.json', 'r') as f:
    words = json.load(f)
    words_map = {remove_non_chinese_characters(w['word']): w for w in words if remove_non_chinese_characters(w['word'])}

with open('chinese-dictionary/idiom/idiom.json', 'r') as f:
    idioms = json.load(f)
    idioms_map = {remove_non_chinese_characters(i['word']): i for i in idioms if remove_non_chinese_characters(i['word'])}

with open('character-compositions.json', 'r') as f:
    character_compositions_map = json.load(f)

def find_matches(word):
    matches = []
    word_cleaned = remove_non_chinese_characters(word)
    if word_cleaned in char_details_map:
        matches.append(('char', char_details_map[word_cleaned]))
    if word_cleaned in words_map:
        matches.append(('word', words_map[word_cleaned]))
    if word_cleaned in idioms_map:
        matches.append(('idiom', idioms_map[word_cleaned]))
    return matches

def get_wordlist_matches(s: str):
    raw_words = [line.strip() for line in s.strip().splitlines() if line.strip()]
    word_notes_seperated = [(re.sub(r'\s*[（\(].+?[）\)]', '', line).strip(), line.strip()) for line in raw_words]
    word_notes_seperated = [ (word, notes) if word != notes else (word, '') for (word, notes) in word_notes_seperated]
    word_notes_matches = [(word, notes, find_matches(word)) for word, notes in word_notes_seperated]
    word_notes_pinyin_types = [(word, notes, extract_pinyin_from_match(matches[0]) if len(matches) > 0 else get_pinyin_from_chars(word), [t for t, _ in matches]) for (word, notes, matches) in word_notes_matches]
    return word_notes_pinyin_types

def extract_pinyin_from_match(match):
    if match[0] == 'char':
        return '/'.join([p['pinyin'] for p in match[1]['pronunciations']])
    else:
        return match[1].get('pinyin', '')
def get_pinyin_from_chars(word):
    pinyin = []
    for char in word:
        if char in char_details_map:
            pinyin.append(char_details_map[char]['pronunciations'][0]['pinyin'])
    return ' '.join(pinyin)
def get_pinyin_abbreviation(pinyin):
    return ''.join([s[0] for s in pinyin.split() if s])
def get_word_data(word, type):
    if type == 'char' and word in char_details_map:
        return char_details_map[word]
    elif type == 'word' and word in words_map:
        return words_map[word]
    elif type == 'idiom' and word in idioms_map:
        return idioms_map[word]
    else:
        return None

def remove_accents(text):
    # Normalize to NFD form (decomposes accented characters)
    normalized = unicodedata.normalize('NFD', text)
    # Filter out combining characters (accents)
    return ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')

def get_similar_chars_with_same_lazy_pinyin(char):
    if char not in char_details_map:
        return []
    target_pinyin = remove_accents(char_details_map[char]['pronunciations'][0]['pinyin'])
    similar_chars = [c['char'] for c in char_details if remove_accents(c['pronunciations'][0]['pinyin']) == target_pinyin and c['char'] != char]
    return similar_chars

def get_similar_chars_with_same_tone_pinyin(char):
    if char not in char_details_map:
        return []
    target_pinyin = char_details_map[char]['pronunciations'][0]['pinyin']
    similar_chars = [c['char'] for c in char_details if c['pronunciations'][0]['pinyin'] == target_pinyin and c['char'] != char]
    return similar_chars

def get_similar_chars_with_same_components(char):
    all_compositions =  character_compositions_map[char]['compositions'] + character_compositions_map[char]['supercompositions'] + character_compositions_map[char]['variants']
    return all_compositions

def get_similar_chars(char):
    scored = [{"char": c, "score": 1} for c in get_similar_chars_with_same_lazy_pinyin(char)] + \
           [{"char": c, "score": 3} for c in get_similar_chars_with_same_tone_pinyin(char)] + \
           [{"char": c, "score": 2} for c in get_similar_chars_with_same_components(char)]
    
    # Group by char and sum scores
    char_scores = {}
    for item in scored:
        char_scores[item["char"]] = char_scores.get(item["char"], 0) + item["score"]
    
    # Return unique chars with total scores
    return sorted([{"char": c, "score": s} for c, s in char_scores.items()], key=lambda x: x["score"], reverse=True)

def get_similar_chars_for_word(word, similarity_threshold=1):
    similar_chars = {}
    for char in word:
        char_similar_chars = get_similar_chars(char)
        for similar_char in char_similar_chars:
            if similar_char['char'] not in word and hanzidentifier.is_simplified(similar_char['char']) and similar_char['score'] > similarity_threshold:
                if similar_char['char'] not in similar_chars:
                    similar_chars[similar_char['char']] = 0
                similar_chars[similar_char['char']] += similar_char['score']
    return sorted([{"char": c, "score": s} for c, s in similar_chars.items() if s >= 2], key=lambda x: x["score"], reverse=True)
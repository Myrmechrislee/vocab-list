import json

from cjkradlib import RadicalFinder

finder = RadicalFinder()

with open('chinese-dictionary/character/char_detail.json', 'r') as f:
    char_details = json.loads("[" + f.read() + "]")
    chars = [c['char'] for c in char_details]

compositionsInfo = {c['char']: finder.search(c['char']) for c in char_details}
compositionsInfo = {k: {'character': v.character, 'compositions': v.compositions, 'supercompositions': v.supercompositions, 'variants': v.variants} for k, v in compositionsInfo.items()}

with open('character-compositions.json', 'w+') as f:
    json.dump(compositionsInfo, f, ensure_ascii=False, indent=2)
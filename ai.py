from openai import OpenAI
import ollama

import os, json

def generate_relevant_information(word, current_data=None):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPEN_ROUTER_API_KEY")
    )
    message = f"""
    You are a chinese vocabulary learning app designed for chinese children (no need for english).
    Please generate a json object with all the relevent learning information for '{word}' with the keys in english and values in chinese.
    Some helpful keys include: 'word', 'pinyin', 'explanation', 'example', 'source'.
    If it is a word or phrase, include 'abbr' (pinyin abbreviation), 'oposite' (array), 'similar' (array), 'usage'.
    If it is poem quote, include 'title', 'author', 'dynasty', 'full poem', 'background'.
    If there is a story, add 'story'.
    """
    if current_data:
        message += f"Here is the current data for the word: {json.dumps(current_data)}. Please use this response and add to it where it is needed."
    
    response = client.chat.completions.create(
        model="qwen/qwen3.5-flash-02-23",
        messages=[
            {
                "role": "system",
                "content": message
            }
        ],
        tools=[
            {
                "type": "openrouter:web_search"
            }
        ]
    )

    return response.choices[0].message.content
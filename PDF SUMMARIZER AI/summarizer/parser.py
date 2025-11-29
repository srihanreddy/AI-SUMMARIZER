# PDF SUMMARIZER AI/summarizer/parser.py

import tiktoken

def count_tokens(text: str, model_name: str = "llama-3.3-70b-versatile") -> int:
    """
    Counts the number of tokens in a string using the specified model's encoding.
    """
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))
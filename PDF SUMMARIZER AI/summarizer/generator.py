# PDF SUMMARIZER AI/summarizer/generator.py

import json
import time
from openai import OpenAI, APIError, RateLimitError, APIConnectionError

def get_prompt(prompts_data: dict, task: str, chunk: str, word_count: int, page_label: str) -> tuple[str, str]:
    """Constructs the system and user prompts for a given task."""
    genesis_directive = prompts_data.get("genesis_directive", "")
    protocol = prompts_data.get("protocols", {}).get(task, {})
    
    system_prompt_parts = [genesis_directive, protocol.get("description", "")]
    
    if "rules" in protocol:
        rules = "\n".join(protocol.get("rules", []))
        system_prompt_parts.append(f"\nSTRICT RULES:\n{rules}")
        
    if "structure" in protocol:
        structure = json.dumps(protocol.get("structure", {}), indent=2)
        system_prompt_parts.append(f"\nYOUR OUTPUT MUST BE IN THIS EXACT JSON STRUCTURE:\n{structure}")
        
    if word_count:
        system_prompt_parts.append(prompts_data.get("word_limit_instruction", "").format(word_count=word_count))

    system_prompt = "\n".join(system_prompt_parts)
    user_prompt = f"Source page(s): {page_label}\n\nInitiate protocol on the following data stream:\n\n{chunk}"
    return system_prompt, user_prompt

def send_request_with_retry(client: OpenAI, model_name: str, messages: list, max_retries: int, retry_delay: int, is_json: bool) -> str:
    """Sends a request to the LLM with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            response_format = {"type": "json_object"} if is_json else {"type": "text"}
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=4000,
                response_format=response_format
            )
            return response.choices[0].message.content.strip()
        except (RateLimitError, APIError, APIConnectionError) as e:
            print(f"⚠️ API Error on attempt {attempt + 1}/{max_retries}: {e}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay * (attempt + 1))
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
            return '{"error": "An unexpected error occurred."}' if is_json else "Error: An unexpected error occurred."
    
    return '{"error": "API operation failed after multiple retries."}' if is_json else "Error: API operation failed after all retries."

def process_chunks(client, model_name, prompts_data, max_retries, retry_delay, chunks: list[tuple[str, str]], task: str, word_count: int) -> list[str]:
    """Processes a list of text chunks based on the selected task."""
    summaries = []
    # For the initial extraction, we don't pass the word count.
    wc = None if task == 'research_summary' else word_count
    for chunk_text, page_label in chunks:
        system_prompt, user_prompt = get_prompt(prompts_data, task, chunk_text, wc, page_label)
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        is_json = "JSON" in system_prompt
        summary = send_request_with_retry(client, model_name, messages, max_retries, retry_delay, is_json)
        summaries.append(summary)
    return summaries

def synthesize_chunks(summaries: list[str], task: str) -> str:
    """Synthesizes multiple processed chunks. For JSON, it merges them."""
    if not summaries: return ""
    if len(summaries) == 1: return summaries[0]

    if task in ["research_summary", "multi_doc_compare"]:
        try:
            master_obj = json.loads(summaries[0])
            for summary_str in summaries[1:]:
                child_obj = json.loads(summary_str)
                for key, value in master_obj.items():
                    if isinstance(value, list) and key in child_obj and isinstance(child_obj[key], list):
                        value.extend(child_obj[key])
            return json.dumps(master_obj, indent=2)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"⚠️ Could not merge JSON objects: {e}. Returning raw text.")
            return "\n\n---\n\n".join(summaries)
    
    return "\n\n---\n\n".join(summaries)

def final_synthesis_task(client, model_name, prompts_data, max_retries, retry_delay, structured_data_json: str, word_count: int, foresight_mode: bool = False) -> str:
    """Performs the final synthesis from structured data to a narrative summary or the cognitive foresight task."""
    
    task = "cognitive_foresight" if foresight_mode else "final_synthesis"
    
    wc = None if foresight_mode else word_count
    is_json = True if foresight_mode else False

    system_prompt, user_prompt = get_prompt(prompts_data, task, structured_data_json, wc, "Entire Document")
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    
    final_output = send_request_with_retry(client, model_name, messages, max_retries, retry_delay, is_json=is_json)
    return final_output
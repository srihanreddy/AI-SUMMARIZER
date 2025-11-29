import os
import json
from openai import OpenAI, APIError, RateLimitError
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Load prompts from the JSON file
with open('prompts.json', 'r') as f:
    prompts_data = json.load(f)

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

MODEL_NAME = "llama3-70b-8192"

def get_prompt(task: str, chunk: str, word_count: int = None) -> tuple[str, str]:
    """
    Generates a system and user prompt based on the task and word count.
    """
    genesis_directive = prompts_data["genesis_directive"]
    protocol_prompt = prompts_data["protocols"].get(task, prompts_data["protocols"]['research_summary'])
    
    system_prompt = f"{genesis_directive} {protocol_prompt}"

    if word_count and task not in ['paraphrase', 'glossary']:
        word_limit_instruction = prompts_data["word_limit_instruction"].format(word_count=word_count)
        system_prompt += " " + word_limit_instruction

    user_prompt = f"Initiate protocol on the following data stream:\n\n{chunk}"
    return system_prompt, user_prompt

def process_chunks(chunks: list[str], task: str, word_count: int = None) -> str:
    """
    Processes a list of text chunks based on the selected task.
    """
    initial_summaries = []
    
    for i, chunk in enumerate(chunks):
        print(f"🧠 Initiating Cognitive Protocol on chunk {i+1}/{len(chunks)} for task: '{task}'...")
        system_prompt, user_prompt = get_prompt(task, chunk, word_count if len(chunks) == 1 else None)
        
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                max_tokens=2000,
            )
            summary = response.choices[0].message.content.strip()
            initial_summaries.append(summary)
        except RateLimitError as e:
            print(f"❌ Rate limit exceeded on chunk {i+1}: {e}")
            initial_summaries.append(f"Could not process chunk {i+1} due to rate limiting.")
        except APIError as e:
            print(f"❌ API error on chunk {i+1}: {e}")
            initial_summaries.append(f"Could not process chunk {i+1} due to an API error.")
        except Exception as e:
            print(f"❌ An unexpected error occurred on chunk {i+1}: {e}")
            initial_summaries.append(f"Could not process chunk {i+1}.")

    # === Final Synthesis Step ===
    if word_count and len(initial_summaries) > 1 and task not in ['paraphrase', 'glossary']:
        print("✍️  Synthesizing final intelligence product...")
        combined_text = "\n\n---\n\n".join(initial_summaries)
        
        final_system_prompt = (
            "You are the final stage of the Cognitive Insight Engine. Your task is to synthesize the following intelligence fragments into a single, master document. "
            f"The final product must be approximately **{word_count} words**. "
            "Execute a final synthesis protocol: create a master outline, write the full text with seamless logical flow, and perform a final fidelity check to eliminate all redundancy and ensure absolute coherence."
        )
        final_user_prompt = f"Synthesize the following data fragments into the final intelligence product:\n\n{combined_text}"

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": final_system_prompt},
                    {"role": "user", "content": final_user_prompt}
                ],
                temperature=0.2,
                max_tokens=2500,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Final synthesis failed: {e}")
            return combined_text

    return "\n\n---\n\n".join(initial_summaries)
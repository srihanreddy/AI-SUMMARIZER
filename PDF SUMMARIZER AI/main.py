# PDF SUMMARIZER AI/main.py

import os
import json
import tkinter as tk
from tkinter import filedialog
from rich.console import Console
from rich.panel import Panel
from rich.status import Status
from summarizer.extractor import extract_all_data_by_page, intelligent_chunking
from summarizer.generator import process_chunks, synthesize_chunks, final_synthesis_task
from summarizer.formatter import save_summary, format_json_output
from openai import OpenAI
import config

def select_pdf_files(title: str, multiple: bool = False) -> list[str]:
    """Selects one or more PDF files using a file dialog."""
    root = tk.Tk()
    root.withdraw()
    root.lift()
    root.attributes('-topmost', True)
    if multiple:
        file_paths = filedialog.askopenfilenames(parent=root, title=title, filetypes=[("PDF Files", "*.pdf")])
    else:
        file_paths = [filedialog.askopenfilename(parent=root, title=title, filetypes=[("PDF Files", "*.pdf")])]
    root.destroy()
    return list(file_paths) if file_paths and file_paths[0] else []

def get_word_count(console: Console) -> int:
    """Prompts the user to enter a desired word count."""
    while True:
        try:
            count_str = console.input("[bold]Enter desired word count (e.g., 250):[/bold] ")
            count = int(count_str)
            if count > 0:
                return count
            console.print("❌ Please enter a positive number.", style="bold red")
        except ValueError:
            console.print("❌ Invalid input. Please enter a number.", style="bold red")

def get_user_choice(console: Console) -> tuple[str, int, str]:
    """Displays the main menu and gets the user's task choice."""
    console.print(Panel.fit("[bold cyan]Cognitive Insight Engine[/bold cyan]\n[dim]Version 2.0[/dim]", title="[bold green]Welcome[/bold green]"))
    tasks = {
        "1": ("Executive Summary", "summarize"),
        "2": ("Evidence-Based Research Summary", "research_summary"),
        "3": ("Multi-Document Comparison", "multi_doc_compare"),
    }
    for key, (display_name, _) in tasks.items():
        console.print(f"  [yellow]{key}[/yellow]. {display_name}")
    console.print("\n  [red]0[/red]. Exit Engine")

    while True:
        choice = console.input("\n[bold]Enter the number of your choice:[/bold] ")
        if choice == "0":
            return None, None, None
        if choice in tasks:
            display_name, task_name = tasks[choice]
            word_count = None
            if task_name == 'research_summary':
                word_count = get_word_count(console)
            else:
                word_count = 150 # Default for other tasks
            return task_name, word_count, display_name
        console.print("❌ Invalid selection.", style="bold red")

def main():
    """Main function to run the PDF Summarizer AI application."""
    console = Console()
    try:
        client = OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL)
        with open("prompts.json", "r", encoding="utf-8") as f:
            prompts_data = json.load(f)
    except FileNotFoundError:
        console.print("❌ [bold red]Fatal Error:[/bold red] `prompts.json` not found.", style="bold red")
        return
    except Exception as e:
        console.print(f"❌ [bold red]An unexpected error during initialization:[/bold red] {e}", style="bold red")
        return

    while True:
        task, word_count, display_name = get_user_choice(console)
        if not task:
            console.print("\n[bold green]Exiting Cognitive Insight Engine.[/bold green]")
            break

        is_multi_doc = task == "multi_doc_compare"
        pdf_paths = select_pdf_files(f"Select Document(s) for '{display_name}'", multiple=is_multi_doc)
        if not pdf_paths or (is_multi_doc and len(pdf_paths) < 2):
            if is_multi_doc: console.print("⚠️ Please select at least two documents for comparison.", style="bold yellow")
            continue

        with Status("[bold green]Initiating Cognitive Protocol...[/bold green]", spinner="earth", console=console) as status:
            final_output = ""
            if is_multi_doc:
                 all_docs_content = []
                 for path in pdf_paths:
                    doc_name = os.path.basename(path)
                    status.update(f"Extracting data from [cyan]{doc_name}[/cyan]...")
                    pages = extract_all_data_by_page(path)
                    full_text = "\n\n".join(p['text'] for p in pages)
                    all_docs_content.append(f"--- DOCUMENT: {doc_name} ---\n{full_text}")
                
                 status.update("🧠 Synthesizing comparative analysis across documents...")
                 final_output = process_chunks(client, config.MODEL_NAME, prompts_data, config.MAX_RETRIES, config.RETRY_DELAY, [("\n\n".join(all_docs_content), "Multiple Docs")], task, word_count)[0]

            else:
                pdf_path = pdf_paths[0]
                doc_name = os.path.basename(pdf_path)
                status.update(f"📤 [Step 1/2] Extracting data from [cyan]{doc_name}[/cyan]...")
                pages = extract_all_data_by_page(pdf_path)
                if not pages:
                    console.print(f"❌ Could not extract data from '{doc_name}'.", style="bold red")
                    continue
                
                chunks = intelligent_chunking(pages, token_limit=3500)
                
                if task == 'research_summary':
                    status.update(f"🧠 [Step 2/2] Analyzing {len(chunks)} chunk(s) and writing final summary...")
                    analysis_task = 'research_summary'
                    processed_chunks = process_chunks(client, config.MODEL_NAME, prompts_data, config.MAX_RETRIES, config.RETRY_DELAY, chunks, analysis_task, word_count)
                    structured_data_json = synthesize_chunks(processed_chunks, analysis_task)
                    final_output = final_synthesis_task(client, config.MODEL_NAME, prompts_data, config.MAX_RETRIES, config.RETRY_DELAY, structured_data_json, word_count)
                
                else: # Handles the standard "summarize" task
                    status.update(f"🧠 [Step 2/2] Analyzing {len(chunks)} chunk(s) to extract key findings...")
                    final_output = process_chunks(client, config.MODEL_NAME, prompts_data, config.MAX_RETRIES, config.RETRY_DELAY, chunks, task, word_count)[0]
            
            # Formatting and Saving
            if final_output:
                formatted_content = format_json_output(final_output, task)
                output_basename = f"{os.path.splitext(os.path.basename(pdf_paths[0]))[0]}_{task}"
                save_summary(formatted_content, output_basename, config.OUTPUT_DIR)
                console.print(f"\n✅ [bold green]Success![/bold green] Output saved to the '[cyan]{config.OUTPUT_DIR}[/cyan]' directory.", style="bold green")
                console.print(Panel(formatted_content, title="[bold blue]Final Output[/bold blue]", expand=False))

if __name__ == "__main__":
    main()
# PDF SUMMARIZER AI/summarizer/formatter.py

import os
import json

def save_summary(content: str, basename: str, output_dir: str):
    """Saves content to .txt and .md files."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save raw text file
    txt_path = os.path.join(output_dir, f"{basename}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    # Save markdown file (which might be the same as raw text or formatted)
    md_path = os.path.join(output_dir, f"{basename}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)

def format_json_output(content: str, task: str) -> str:
    """Formats JSON string output into human-readable markdown."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return content # Return as is if not valid JSON

    if task == "research_summary":
        lines = [f"# {data.get('title', 'Research Summary')}\n"]
        lines.append(f"**High-Level Analysis:** {data.get('high_level_analysis', 'N/A')}\n")
        lines.append("## Key Findings")
        for finding in data.get('key_findings', []):
            lines.append(f"- **Finding:** {finding.get('finding', 'N/A')}")
            lines.append(f"  - **Evidence:** *\"{finding.get('evidence', 'N/A')}\"*")
            lines.append(f"  - **Quantitative Support:** `{finding.get('quantitative_support', 'N/A')}`")
            lines.append(f"  - **Confidence:** {finding.get('confidence', 'N/A')} | **Source Page(s):** {finding.get('source_page', 'N/A')}")
        lines.append(f"\n**Strategic Conclusion:** {data.get('strategic_conclusion', 'N/A')}")
        return "\n".join(lines)

    if task == "multi_doc_compare":
        lines = ["# Multi-Document Comparative Analysis\n"]
        lines.append(f"**Synthesis Summary:** {data.get('synthesis_summary', 'N/A')}\n")
        lines.append("## Common Themes")
        for theme in data.get('common_themes', []): lines.append(f"- {theme}")
        lines.append("\n## Contrasting Points")
        for point in data.get('contrasting_points', []): lines.append(f"- {point}")
        lines.append("\n## Unique Insights by Document")
        for insight in data.get('unique_insights', []):
            lines.append(f"- **{insight.get('document_name', 'Unknown Document')}:** {insight.get('insight', 'N/A')}")
        return "\n".join(lines)
        
    return content # Return original content for other tasks
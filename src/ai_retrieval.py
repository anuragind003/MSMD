from typing import List, Tuple, Dict, Optional
import os
import json
from dotenv import load_dotenv
load_dotenv()

# Lazy import inside function to avoid hard dependency for non-AI paths


def rank_mechanisms_by_similarity(query_description: str, building_blocks: List[Dict]) -> List[Tuple[str, float]]:
    """
    Rank building blocks by semantic similarity using Gemini AI.
    This replaces the previous TF-IDF approach with more intelligent semantic understanding.

    Args:
        query_description: Natural language description of the target EF or task.
        building_blocks: List of mechanism dicts from the knowledge base.

    Returns:
        List of tuples (mechanism_name, similarity_score) sorted by score desc.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        print("Warning: google-generativeai not installed. Falling back to simple ranking.")
        # Fallback: return all mechanisms with equal score
        return [(block.get("name", f"mechanism_{i}"), 0.5) for i, block in enumerate(building_blocks)]

    # Get API key from environment or prompt user
    try:
        from .config import get_gemini_api_key
        api_key = get_gemini_api_key()
    except ImportError:
        api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("⚠ Gemini API key not available. Using fallback ranking.")
        # Fallback: return all mechanisms with equal score
        return [(block.get("name", f"mechanism_{i}"), 0.5) for i, block in enumerate(building_blocks)]

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
    except Exception as e:
        print(f"Warning: Failed to configure Gemini AI: {e}")
        print("Falling back to simple ranking.")
        return [(block.get("name", f"mechanism_{i}"), 0.5) for i, block in enumerate(building_blocks)]

    # Prepare building blocks summary for prompt
    mechanisms_summary = []
    for block in building_blocks:
        mechanisms_summary.append({
            "name": block.get("name", "Unknown"),
            "description": block.get("description", ""),
            "text_description": block.get("text_description", ""),
            "motion_conversion": block.get("motion_conversion", ""),
            "num_elements": block.get("num_elements", 0)
        })

    # Create prompt for Gemini
    prompt = f"""You are a mechanical design expert. Given a design task description, rank the available building block mechanisms by how well they match the requirements.

TASK DESCRIPTION:
{query_description}

AVAILABLE MECHANISMS:
{json.dumps(mechanisms_summary, indent=2)}

INSTRUCTIONS:
1. Analyze how well each mechanism matches the task requirements
2. Consider motion conversion type, complexity, and functional fit
3. Return a JSON array with rankings (score 0.0 to 1.0, where 1.0 is perfect match)
4. Include brief reasoning for top 3 matches

Return ONLY valid JSON in this exact format:
[
  {{"name": "mechanism_name", "score": 0.95, "reasoning": "brief explanation"}},
  {{"name": "mechanism_name", "score": 0.85, "reasoning": "brief explanation"}},
  ...
]

Do not include any text before or after the JSON array."""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean response - remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # Parse JSON response
        rankings = json.loads(response_text)
        
        # Convert to list of tuples and ensure all mechanisms are included
        ranked_dict = {item["name"]: item["score"] for item in rankings}
        
        # Create full ranking list (include mechanisms not in Gemini response with lower scores)
        ranked: List[Tuple[str, float]] = []
        for block in building_blocks:
            name = block.get("name", "Unknown")
            score = ranked_dict.get(name, 0.1)  # Default low score if not ranked
            ranked.append((name, float(score)))
        
        # Sort by score descending
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        # Print top 3 with reasoning
        print("\n[Gemini AI Ranking Results]")
        for i, item in enumerate(rankings[:3], 1):
            print(f"  {i}. {item['name']}: {item['score']:.2f} - {item.get('reasoning', 'N/A')}")
        
        return ranked

    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse Gemini response as JSON: {e}")
        print(f"Response was: {response_text[:200]}...")
        # Fallback: return all with equal score
        return [(block.get("name", f"mechanism_{i}"), 0.5) for i, block in enumerate(building_blocks)]
    except Exception as e:
        print(f"Warning: Error calling Gemini AI: {e}")
        # Fallback: return all with equal score
        return [(block.get("name", f"mechanism_{i}"), 0.5) for i, block in enumerate(building_blocks)]


def rank_mechanisms_by_gemini(
    task_description: str,
    elemental_functions: List[Dict],
    building_blocks: List[Dict]
) -> List[Tuple[str, float]]:
    """
    Enhanced Gemini AI ranking that considers full task context including all elemental functions.
    
    Args:
        task_description: Full task description
        elemental_functions: List of all EFs in the task
        building_blocks: List of mechanism dicts from knowledge base
        
    Returns:
        List of tuples (mechanism_name, similarity_score) sorted by score desc.
    """
    # Build comprehensive query including all EFs
    ef_summary = "\n".join([
        f"- {ef.get('ef_id', 'EF')}: {ef.get('type', '')} - {ef.get('description', '')}"
        for ef in elemental_functions
    ])
    
    full_query = f"""TASK: {task_description}

ELEMENTAL FUNCTIONS REQUIRED:
{ef_summary}

Please rank mechanisms that can serve as a good starting point to satisfy these requirements."""
    
    return rank_mechanisms_by_similarity(full_query, building_blocks)



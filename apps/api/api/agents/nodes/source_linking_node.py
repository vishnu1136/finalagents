from typing import Any, Dict, List
import re
from collections import defaultdict


def categorize_document(title: str, snippet: str = "") -> str:
    """Categorize a document based on its title and content"""
    title_lower = title.lower()
    snippet_lower = snippet.lower()
    content = f"{title_lower} {snippet_lower}"
    
    # Define category patterns
    categories = {
        "Implementation Guides": [
            "implementation", "setup", "install", "configuration", "deployment",
            "getting started", "quick start", "tutorial", "guide", "how to"
        ],
        "Best Practices": [
            "best practice", "recommendation", "guideline", "standard",
            "policy", "procedure", "methodology", "approach"
        ],
        "Evaluation & Metrics": [
            "evaluation", "assessment", "metrics", "measurement", "kpi",
            "performance", "effectiveness", "analysis", "testing"
        ],
        "Use Cases": [
            "use case", "scenario", "example", "case study", "application",
            "workflow", "process", "business case"
        ],
        "Technical Documentation": [
            "api", "technical", "specification", "architecture", "design",
            "system", "integration", "development", "code"
        ],
        "Research & Studies": [
            "research", "study", "paper", "analysis", "findings",
            "survey", "report", "investigation", "experiment"
        ],
        "Training & Education": [
            "training", "education", "learning", "course", "workshop",
            "certification", "tutorial", "lesson", "module"
        ],
        "Policies & Compliance": [
            "policy", "compliance", "regulation", "standard", "requirement",
            "governance", "audit", "security", "privacy"
        ]
    }
    
    # Score each category based on keyword matches
    category_scores = {}
    for category, keywords in categories.items():
        score = 0
        for keyword in keywords:
            if keyword in content:
                score += content.count(keyword)
        category_scores[category] = score
    
    # Return the category with the highest score, or "General" if no clear match
    if category_scores and max(category_scores.values()) > 0:
        return max(category_scores, key=category_scores.get)
    else:
        return "General Documents"


def group_documents_by_category(sources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group documents by their determined categories"""
    grouped = defaultdict(list)
    
    for source in sources:
        title = source.get("title", "")
        snippet = source.get("snippet", "")
        category = categorize_document(title, snippet)
        grouped[category].append(source)
    
    return dict(grouped)


async def run_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = inputs.get("results", [])
    sources = []
    
    # Process all results into sources
    for r in results:
        sources.append({
            "title": r.get("title") or r.get("url") or "Document",
            "url": r.get("url"),
            "snippet": r.get("snippet")
        })
    
    # Group documents by category
    grouped_sources = group_documents_by_category(sources)
    
    # Create a summary of grouped sources
    grouped_summary = {}
    for category, docs in grouped_sources.items():
        grouped_summary[category] = {
            "count": len(docs),
            "documents": docs
        }
    
    return {
        "sources": sources,  # Keep original flat list for backward compatibility
        "grouped_sources": grouped_summary,  # New grouped structure
        "results": results
    }



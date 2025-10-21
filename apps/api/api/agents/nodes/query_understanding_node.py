from typing import Dict, Any
import re


async def run_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    query = inputs.get("query", "").strip()
    
    # Extract meaningful keywords from the query
    # Remove common question words and phrases
    stop_words = {
        "can", "you", "please", "list", "all", "the", "files", "related", "to",
        "show", "me", "find", "search", "for", "about", "what", "is", "are",
        "how", "do", "does", "will", "would", "could", "should", "may", "might",
        "tell", "give", "get", "help", "assist", "with", "regarding", "concerning",
        "information", "resources", "documents", "data", "content"
    }
    
    # Convert to lowercase and split into words
    words = re.findall(r'\b\w+\b', query.lower())
    
    # Filter out stop words and keep only meaningful terms
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Subject expansion for better search coverage
    subject_expansions = {
        "health": ["healthcare", "medical", "clinical", "patient", "hospital"],
        "healthcare": ["health", "medical", "clinical", "patient", "hospital"],
        "medical": ["health", "healthcare", "clinical", "patient", "hospital"],
        "clinical": ["health", "healthcare", "medical", "patient", "hospital"],
        "ai": ["artificial intelligence", "machine learning", "ml", "automation"],
        "artificial": ["ai", "intelligence", "machine learning", "ml"],
        "intelligence": ["ai", "artificial", "machine learning", "ml"],
        "data": ["analytics", "analysis", "insights", "metrics"],
        "analytics": ["data", "analysis", "insights", "metrics"],
        "business": ["enterprise", "corporate", "organization", "company"],
        "technology": ["tech", "technical", "system", "platform"],
        "system": ["platform", "technology", "tech", "solution"]
    }
    
    # Expand keywords with related terms
    expanded_keywords = set(keywords)
    for keyword in keywords:
        if keyword in subject_expansions:
            expanded_keywords.update(subject_expansions[keyword])
    
    # If no keywords found, use the original query
    if not keywords:
        normalized_query = query
    else:
        # Join expanded keywords with spaces for better search coverage
        normalized_query = " ".join(sorted(expanded_keywords))
    
    # Determine intent based on query patterns
    intent = "qa"
    if any(word in query.lower() for word in ["list", "show", "find", "search"]):
        intent = "search"
    elif any(word in query.lower() for word in ["what", "how", "why", "when", "where"]):
        intent = "qa"
    
    # Detect if this is a broad subject query (asking for overview)
    is_broad_subject = (
        len(keywords) <= 2 and 
        any(word in query.lower() for word in ["what", "show", "list", "find"]) and
        not any(specific in query.lower() for specific in ["cdss", "implementation", "guide", "manual", "document"])
    )
    
    return {
        "intent": intent, 
        "normalized_query": normalized_query,
        "original_query": query,
        "is_broad_subject": is_broad_subject,
        "expanded_keywords": list(expanded_keywords)
    }



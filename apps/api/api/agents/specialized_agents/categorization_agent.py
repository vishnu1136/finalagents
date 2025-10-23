"""
Categorization Agent
===================
Specialized agent for document categorization and grouping.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
import logging
from collections import defaultdict
import re

from ..base_agent import BaseAgent
from ..protocol.agent_communication import (
    AgentMessage, MessageType, AgentType,
    CategorizationRequest, CategorizationResponse, create_message
)


class SourceLinkingAgent(BaseAgent):
    """Agent specialized in document categorization and source linking."""
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.SOURCE_LINKING_AGENT,
            name="SourceLinkingAgent",
            max_concurrent_tasks=5,
            timeout_seconds=60
        )
        
        # Define category patterns with improved handling for technical files
        self.categories = {
            "Implementation Guides": [
                "implementation", "setup", "install", "configuration", "deployment",
                "getting started", "quick start", "tutorial", "guide", "how to",
                "setup guide", "installation", "configuration", "deployment"
            ],
            "Best Practices": [
                "best practice", "recommendation", "guideline", "standard",
                "policy", "procedure", "methodology", "approach", "tips",
                "do's and don'ts", "guidelines", "standards"
            ],
            "Evaluation & Metrics": [
                "evaluation", "assessment", "metrics", "measurement", "kpi",
                "performance", "effectiveness", "analysis", "testing", "benchmark",
                "score", "rating", "measure", "indicator"
            ],
            "Use Cases": [
                "use case", "scenario", "example", "case study", "application",
                "workflow", "process", "business case", "demo", "sample",
                "real-world", "practical", "implementation example"
            ],
            "Technical Documentation": [
                "api", "technical", "specification", "architecture", "design",
                "system", "integration", "development", "code", "programming",
                "technical spec", "system design", "integration guide", "tsx", "component"
            ],
            "Database Files": [
                "sql", "database", "export", "dump", "schema", "table", "query",
                "insert", "update", "delete", "select", "create table", "alter table"
            ],
            "Meeting Notes": [
                "meeting", "notes", "transcript", "discussion", "agenda", "minutes",
                "review meeting", "attended", "invited", "participants"
            ],
            "Business Requirements": [
                "brd", "business requirement", "requirement document", "specification",
                "functional requirement", "non-functional requirement", "stakeholder"
            ],
            "Research & Studies": [
                "research", "study", "paper", "analysis", "findings",
                "survey", "report", "investigation", "experiment", "white paper",
                "academic", "scientific", "empirical", "data analysis"
            ],
            "Training & Education": [
                "training", "education", "learning", "course", "workshop",
                "certification", "tutorial", "lesson", "module", "curriculum",
                "learning path", "educational", "training material"
            ],
            "Policies & Compliance": [
                "policy", "compliance", "regulation", "standard", "requirement",
                "governance", "audit", "security", "privacy", "legal",
                "regulatory", "compliance guide", "policy document"
            ],
            "Troubleshooting": [
                "troubleshooting", "debug", "error", "issue", "problem",
                "fix", "solution", "resolve", "debugging", "troubleshoot",
                "common issues", "error handling", "problem solving"
            ],
            "Reference Materials": [
                "reference", "manual", "documentation", "cheat sheet",
                "quick reference", "glossary", "dictionary", "index",
                "lookup", "handbook", "encyclopedia"
            ]
        }
        
        # Register message handlers
        self.register_handler(MessageType.CATEGORIZATION_REQUEST, self._handle_categorization_request)
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
    
    async def _send_message_to_orchestrator(self, message: AgentMessage) -> None:
        """Send message to orchestrator."""
        if hasattr(self, 'orchestrator_callback'):
            await self.orchestrator_callback(message)
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a source linking task using the proven logic."""
        try:
            # Use the exact logic from the old source_linking_node
            return await self._link_sources(task_data)
        except Exception as e:
            self.logger.error(f"Error processing source linking task: {e}")
            raise
    
    async def _handle_categorization_request(self, message: AgentMessage) -> None:
        """Handle categorization request messages."""
        try:
            categorization_request = CategorizationRequest(**message.payload)
            categorization_response = await self._perform_categorization(categorization_request)
            
            # Send response back
            response = create_message(
                sender=self.agent_type,
                recipient=message.sender,
                message_type=MessageType.CATEGORIZATION_RESPONSE,
                payload=categorization_response,
                correlation_id=message.id
            )
            await self._send_message_to_orchestrator(response)
            
        except Exception as e:
            self.logger.error(f"Error handling categorization request: {e}")
            await self._send_error_response(message, str(e))
    
    async def _handle_heartbeat(self, message: AgentMessage) -> None:
        """Handle heartbeat messages."""
        self.logger.debug("Received heartbeat")
    
    async def _link_sources(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Link sources using the exact logic from the old source_linking_node."""
        results = inputs.get("results", inputs.get("documents", []))
        sources = []
        
        # Process all results into sources
        for r in results:
            sources.append({
                "title": r.get("title") or r.get("url") or "Document",
                "url": r.get("url"),
                "snippet": r.get("snippet")
            })
        
        # Group documents by category using the exact logic
        grouped_sources = self._group_documents_by_category(sources)
        
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
    
    def _categorize_document(self, title: str, snippet: str = "") -> str:
        """Categorize a document based on its title and content using the exact logic."""
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        content = f"{title_lower} {snippet_lower}"
        
        # Define category patterns with improved handling for technical files
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
                "system", "integration", "development", "code", "tsx", "component"
            ],
            "Database Files": [
                "sql", "database", "export", "dump", "schema", "table", "query",
                "insert", "update", "delete", "select", "create table", "alter table"
            ],
            "Meeting Notes": [
                "meeting", "notes", "transcript", "discussion", "agenda", "minutes",
                "review meeting", "attended", "invited", "participants"
            ],
            "Business Requirements": [
                "brd", "business requirement", "requirement document", "specification",
                "functional requirement", "non-functional requirement", "stakeholder"
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
        
        # Return the category with the highest score, or determine fallback category
        if category_scores and max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        else:
            # Improved fallback logic based on file type and content
            if title_lower.endswith('.sql') or 'sql' in title_lower:
                return "Database Files"
            elif any(word in title_lower for word in ['meeting', 'notes', 'transcript', 'discussion']):
                return "Meeting Notes"
            elif any(word in title_lower for word in ['brd', 'requirement', 'specification']):
                return "Business Requirements"
            elif any(word in title_lower for word in ['tsx', 'component', 'react', 'frontend']):
                return "Technical Documentation"
            else:
                return "Other Documents"
    
    def _group_documents_by_category(self, sources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group documents by their determined categories using the exact logic."""
        grouped = defaultdict(list)
        
        for source in sources:
            title = source.get("title", "")
            snippet = source.get("snippet", "")
            category = self._categorize_document(title, snippet)
            grouped[category].append(source)
        
        return dict(grouped)
    
    async def _perform_categorization(self, categorization_request: CategorizationRequest) -> Dict[str, Any]:
        """Perform the actual categorization operation."""
        start_time = time.time()
        
        try:
            if categorization_request.categorization_type == "smart":
                categories = await self._smart_categorization(categorization_request.documents)
            elif categorization_request.categorization_type == "simple":
                categories = await self._simple_categorization(categorization_request.documents)
            else:  # custom
                categories = await self._custom_categorization(categorization_request.documents)
            
            # Generate category metadata
            category_metadata = self._generate_category_metadata(categories)
            
            categorization_time = time.time() - start_time
            
            # Create response
            categorization_response = CategorizationResponse(
                categories=categories,
                category_metadata=category_metadata
            )
            
            return {
                "categories": categories,
                "category_metadata": category_metadata,
                "categorization_time": categorization_time
            }
            
        except Exception as e:
            self.logger.error(f"Error performing categorization: {e}")
            raise
    
    async def _smart_categorization(self, documents: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Perform smart categorization using multiple algorithms."""
        try:
            # Group documents by category
            grouped = defaultdict(list)
            
            for doc in documents:
                title = doc.get("title", "")
                snippet = doc.get("snippet", "")
                
                # Use multiple categorization methods
                category = self._categorize_document_smart(title, snippet)
                grouped[category].append(doc)
            
            return dict(grouped)
            
        except Exception as e:
            self.logger.error(f"Error in smart categorization: {e}")
            return {"General Documents": documents}
    
    async def _simple_categorization(self, documents: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Perform simple keyword-based categorization."""
        try:
            grouped = defaultdict(list)
            
            for doc in documents:
                title = doc.get("title", "")
                snippet = doc.get("snippet", "")
                
                category = self._categorize_document_simple(title, snippet)
                grouped[category].append(doc)
            
            return dict(grouped)
            
        except Exception as e:
            self.logger.error(f"Error in simple categorization: {e}")
            return {"General Documents": documents}
    
    async def _custom_categorization(self, documents: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Perform custom categorization based on specific rules."""
        try:
            # This could be extended with custom rules
            return await self._smart_categorization(documents)
            
        except Exception as e:
            self.logger.error(f"Error in custom categorization: {e}")
            return {"General Documents": documents}
    
    def _categorize_document_smart(self, title: str, snippet: str) -> str:
        """Smart categorization using multiple algorithms."""
        content = f"{title.lower()} {snippet.lower()}"
        
        # Method 1: Keyword matching with scoring
        category_scores = {}
        for category, keywords in self.categories.items():
            score = 0
            for keyword in keywords:
                # Weight title matches higher
                title_matches = title.lower().count(keyword)
                snippet_matches = snippet.lower().count(keyword)
                score += title_matches * 2 + snippet_matches
            category_scores[category] = score
        
        # Method 2: Pattern matching
        pattern_scores = self._pattern_matching(content)
        
        # Method 3: Length and structure analysis
        structure_scores = self._structure_analysis(title, snippet)
        
        # Combine scores
        final_scores = {}
        for category in self.categories.keys():
            final_scores[category] = (
                category_scores.get(category, 0) +
                pattern_scores.get(category, 0) +
                structure_scores.get(category, 0)
            )
        
        # Return category with highest score
        if final_scores and max(final_scores.values()) > 0:
            return max(final_scores, key=final_scores.get)
        else:
            # Improved fallback logic based on file type and content
            if title.lower().endswith('.sql') or 'sql' in title.lower():
                return "Database Files"
            elif any(word in title.lower() for word in ['meeting', 'notes', 'transcript', 'discussion']):
                return "Meeting Notes"
            elif any(word in title.lower() for word in ['brd', 'requirement', 'specification']):
                return "Business Requirements"
            elif any(word in title.lower() for word in ['tsx', 'component', 'react', 'frontend']):
                return "Technical Documentation"
            else:
                return "Other Documents"
    
    def _categorize_document_simple(self, title: str, snippet: str) -> str:
        """Simple keyword-based categorization with improved fallback."""
        content = f"{title.lower()} {snippet.lower()}"
        
        category_scores = {}
        for category, keywords in self.categories.items():
            score = sum(1 for keyword in keywords if keyword in content)
            category_scores[category] = score
        
        if category_scores and max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        else:
            # Improved fallback logic based on file type and content
            if title.lower().endswith('.sql') or 'sql' in title.lower():
                return "Database Files"
            elif any(word in title.lower() for word in ['meeting', 'notes', 'transcript', 'discussion']):
                return "Meeting Notes"
            elif any(word in title.lower() for word in ['brd', 'requirement', 'specification']):
                return "Business Requirements"
            elif any(word in title.lower() for word in ['tsx', 'component', 'react', 'frontend']):
                return "Technical Documentation"
            else:
                return "Other Documents"
    
    def _pattern_matching(self, content: str) -> Dict[str, int]:
        """Pattern-based categorization."""
        patterns = {
            "Implementation Guides": [
                r"how to", r"step by step", r"getting started", r"quick start",
                r"installation", r"setup", r"configuration"
            ],
            "Best Practices": [
                r"best practice", r"recommended", r"guideline", r"should",
                r"avoid", r"do's and don'ts"
            ],
            "Evaluation & Metrics": [
                r"kpi", r"metric", r"measure", r"score", r"rating",
                r"performance", r"effectiveness"
            ],
            "Use Cases": [
                r"use case", r"scenario", r"example", r"case study",
                r"real-world", r"practical"
            ],
            "Technical Documentation": [
                r"api", r"endpoint", r"parameter", r"response",
                r"technical spec", r"integration"
            ],
            "Research & Studies": [
                r"research", r"study", r"analysis", r"findings",
                r"survey", r"empirical"
            ],
            "Training & Education": [
                r"training", r"course", r"lesson", r"module",
                r"learning", r"education"
            ],
            "Policies & Compliance": [
                r"policy", r"compliance", r"regulation", r"legal",
                r"governance", r"audit"
            ],
            "Troubleshooting": [
                r"troubleshoot", r"debug", r"error", r"issue",
                r"problem", r"fix"
            ]
        }
        
        scores = {}
        for category, pattern_list in patterns.items():
            score = 0
            for pattern in pattern_list:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                score += matches
            scores[category] = score
        
        return scores
    
    def _structure_analysis(self, title: str, snippet: str) -> Dict[str, int]:
        """Analyze document structure for categorization hints."""
        scores = {}
        
        # Title analysis
        title_lower = title.lower()
        if any(word in title_lower for word in ["guide", "manual", "tutorial"]):
            scores["Implementation Guides"] = 2
        if any(word in title_lower for word in ["best", "practice", "recommendation"]):
            scores["Best Practices"] = 2
        if any(word in title_lower for word in ["case", "example", "scenario"]):
            scores["Use Cases"] = 2
        if any(word in title_lower for word in ["api", "technical", "spec"]):
            scores["Technical Documentation"] = 2
        
        # Snippet analysis
        snippet_lower = snippet.lower()
        if len(snippet) > 500:  # Longer content might be comprehensive
            scores["Research & Studies"] = 1
        if any(word in snippet_lower for word in ["step", "first", "then", "next"]):
            scores["Implementation Guides"] = scores.get("Implementation Guides", 0) + 1
        
        return scores
    
    def _generate_category_metadata(self, categories: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        """Generate metadata for each category."""
        metadata = {}
        
        for category, documents in categories.items():
            if not documents:
                continue
            
            # Calculate metadata
            total_docs = len(documents)
            avg_snippet_length = sum(len(doc.get("snippet", "")) for doc in documents) / total_docs
            has_urls = sum(1 for doc in documents if doc.get("url"))
            
            # Extract common themes
            themes = self._extract_themes(documents)
            
            metadata[category] = {
                "document_count": total_docs,
                "average_snippet_length": avg_snippet_length,
                "documents_with_urls": has_urls,
                "url_percentage": (has_urls / total_docs) * 100 if total_docs > 0 else 0,
                "common_themes": themes,
                "category_description": self._get_category_description(category)
            }
        
        return metadata
    
    def _extract_themes(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Extract common themes from documents in a category."""
        all_text = " ".join(doc.get("title", "") + " " + doc.get("snippet", "") for doc in documents)
        
        # Simple theme extraction using word frequency
        words = re.findall(r'\b\w+\b', all_text.lower())
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Only consider words longer than 3 characters
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top themes
        themes = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        return [theme[0] for theme in themes]
    
    def _get_category_description(self, category: str) -> str:
        """Get description for a category."""
        descriptions = {
            "Implementation Guides": "Step-by-step guides and tutorials for setting up and using systems",
            "Best Practices": "Recommended approaches and guidelines for optimal results",
            "Evaluation & Metrics": "Performance measurements, KPIs, and assessment methods",
            "Use Cases": "Real-world examples and scenarios demonstrating practical applications",
            "Technical Documentation": "API references, specifications, and technical details",
            "Research & Studies": "Analytical reports, studies, and research findings",
            "Training & Education": "Educational materials, courses, and learning resources",
            "Policies & Compliance": "Regulatory requirements, policies, and compliance guidelines",
            "Troubleshooting": "Problem-solving guides and debugging information",
            "Reference Materials": "Quick reference guides, glossaries, and lookup materials",
            "General Documents": "Miscellaneous documents that don't fit other categories"
        }
        return descriptions.get(category, "Document category")

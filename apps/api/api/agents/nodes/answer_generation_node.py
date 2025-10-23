from typing import Any, Dict, List
import os
import openai


async def run_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = inputs.get("results", [])
    query: str = inputs.get("normalized_query") or inputs.get("query") or ""
    is_broad_subject: bool = inputs.get("is_broad_subject", False)
    expanded_keywords: List[str] = inputs.get("expanded_keywords", [])
    
    if not results:
        return {"answer": "I couldn't find relevant information.", "results": []}
    
    # Prepare context from search results
    context_parts = []
    for i, result in enumerate(results, 1):  # Remove the [:5] limit to use all results
        title = result.get("title", "Unknown Document")
        snippet = result.get("snippet", "")
        context_parts.append(f"Source {i}: {title}\n{snippet}\n")
    
    context = "\n".join(context_parts)
    
    # Generate a comprehensive answer using OpenAI
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Fallback to simple concatenation
            answer_parts = []
            answer_parts.append(f"I found {len(results)} relevant documents for your query: '{query}'")
            
            if results:
                answer_parts.append("\nHere are the relevant sources:\n")
                for i, result in enumerate(results[:10], 1):
                    title = result.get("title", "Unknown Document")
                    snippet = result.get("snippet", "")
                    answer_parts.append(f"{i}. {title}")
                    if snippet:
                        answer_parts.append(f"   {snippet[:100]}...")
                    answer_parts.append("")
            
            return {
                "answer": "\n".join(answer_parts),
                "results": results
            }
        
        client = openai.AsyncOpenAI(api_key=api_key)
        
        # Customize system prompt based on query type
        if is_broad_subject:
            system_prompt = f"""You are a helpful assistant that provides comprehensive overviews of subjects based on available documents. 
            
            The user is asking about a broad subject: "{query}". They want to understand what information is available about this topic.
            
            Based on the provided documents, give them:
            1. A brief overview of what this subject covers
            2. The main categories/types of information available
            3. Key topics and areas covered
            4. A summary of the available resources
            
            Be informative but concise. Help them understand the scope and depth of information available."""
        else:
            system_prompt = "You are a helpful assistant that provides comprehensive explanations based on the provided context. When given search results, synthesize the information into a clear, well-structured answer that directly addresses the user's query."
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Query: {query}\n\nContext from documents:\n{context}\n\nPlease provide a comprehensive explanation based on the above context. Structure your answer clearly and cite the sources when relevant."
                }
            ],
            max_tokens=1500,  # Increased for broader subject queries
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
    except Exception as e:
        print(f"Error generating answer with LLM: {e}")
        # Fallback to simple concatenation
        snippets = [r.get("snippet", "") for r in results]  # Remove the [:3] limit
        answer = f"Based on the search results for '{query}':\n\n" + "\n\n".join(snippets)
    
    return {"answer": answer, "results": results}



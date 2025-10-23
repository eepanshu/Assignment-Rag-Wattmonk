import google.generativeai as genai
from typing import List, Dict, Any, Optional
from document_processor import DocumentProcessor
import re
import json
from datetime import datetime

class RAGChatbot:
    def __init__(self, gemini_api_key: str, chroma_persist_directory: str = "./chroma_db"):
        """Initialize the RAG chatbot."""
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.document_processor = DocumentProcessor(gemini_api_key, chroma_persist_directory)
        self.conversation_history = []
        
    def classify_intent(self, query: str) -> Dict[str, Any]:
        nec_keywords = ['nec', 'electrical code', 'electrical standard', 'wiring', 'circuit', 'voltage', 'amperage', 'grounding', 'electrical safety']
        wattmonk_keywords = ['wattmonk', 'company', 'service', 'solar design', 'permitting', 'zippy', 'site survey', 'solar', 'engineering', 'platform', 'tool', 'automation']

        query_lower = query.lower()

        nec_score = sum(1 for keyword in nec_keywords if keyword in query_lower)
        wattmonk_score = sum(1 for keyword in wattmonk_keywords if keyword in query_lower)
        if nec_score > wattmonk_score and nec_score > 0:
            return {"intent": "nec", "confidence": nec_score, "document_type": "nec"}
        elif wattmonk_score > nec_score and wattmonk_score > 0:
            return {"intent": "wattmonk", "confidence": wattmonk_score, "document_type": "wattmonk"}
        elif "nec" in query_lower or "electrical" in query_lower:
            return {"intent": "nec", "confidence": 1, "document_type": "nec"}
        elif "wattmonk" in query_lower or "company" in query_lower:
            return {"intent": "wattmonk", "confidence": 1, "document_type": "wattmonk"}
        else:
            return {"intent": "general", "confidence": 0, "document_type": None}
    
    def retrieve_context(self, query: str, document_type: str = None, n_results: int = 3) -> List[Dict[str, Any]]:
        results = self.document_processor.search_documents(query, document_type, n_results)

        specific_terms = ['zippy', 'tool', 'automation', 'machine learning', 'diagrams']
        high_priority_terms = ['zippy']
        query_lower = query.lower()

        should_try_keyword = False

        if any(term in query_lower for term in high_priority_terms):
            should_try_keyword = True
            print(f"🔍 High priority term detected, using keyword search for: {query}")
        elif any(term in query_lower for term in specific_terms) and len(results) < 2:
            should_try_keyword = True
            print(f"🔍 Trying keyword search for specific terms in query: {query}")

        if should_try_keyword:
            keyword_results = self.document_processor.keyword_search(query, document_type, n_results)

            combined_results = keyword_results + results
            seen_content = set()
            unique_results = []
            for result in combined_results:
                content_key = result['content'][:100]
                if content_key not in seen_content:
                    seen_content.add(content_key)
                    unique_results.append(result)

            return unique_results[:n_results]

        return results
    
    def format_context(self, context_results: List[Dict[str, Any]]) -> str:
        """Format the retrieved context for the prompt."""
        if not context_results:
            return ""
        
        formatted_context = "Relevant information from knowledge base:\n\n"
        
        for i, result in enumerate(context_results, 1):
            source = result['metadata'].get('source', 'Unknown')
            doc_type = result['metadata'].get('document_type', 'Unknown')
            content = result['content']
            
            formatted_context += f"[Source {i}: {source} ({doc_type.upper()})]\n"
            formatted_context += f"{content}\n\n"
        
        return formatted_context
    
    def generate_response(self, query: str, context: str = "", intent_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a response using Gemini with retrieved context."""
        try:

            if intent_info and intent_info["intent"] in ["nec", "wattmonk"]:
                if context:
                    prompt = f"""You are a helpful assistant specializing in {intent_info["intent"].upper()} information. 
Use the provided context to answer the user's question accurately and comprehensively.

{context}

User Question: {query}

Instructions:
1. Answer based primarily on the provided context
2. If the context doesn't contain enough information, clearly state this
3. Always cite your sources when using information from the context
4. Be specific and technical when appropriate
5. If asked about {intent_info["intent"].upper()}, focus on that domain

Answer:"""
                else:
                    prompt = f"""You are a helpful assistant. The user is asking about {intent_info["intent"].upper()} related topics, but I don't have specific context available in my knowledge base for this query.

User Question: {query}

Please provide a helpful response based on your general knowledge, but clearly indicate that this information is not from the specific {intent_info["intent"].upper()} knowledge base and recommend consulting official sources for authoritative information.

Answer:"""
            else:

                prompt = f"""You are a helpful AI assistant. Answer the user's question in a friendly and informative manner.

User Question: {query}

Answer:"""
            

            response = self.model.generate_content(prompt)
            
            return {
                "response": response.text,
                "intent": intent_info["intent"] if intent_info else "general",
                "sources_used": len(context.split("[Source")) - 1 if context else 0,
                "has_context": bool(context)
            }
            
        except Exception as e:
            return {
                "response": f"I apologize, but I encountered an error while generating a response: {str(e)}",
                "intent": "error",
                "sources_used": 0,
                "has_context": False
            }
    
    def chat(self, query: str, maintain_history: bool = True) -> Dict[str, Any]:
        """Main chat function that handles the complete RAG pipeline."""
        try:
            if maintain_history:
                self.conversation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "user_query": query,
                    "type": "user"
                })

            intent_info = self.classify_intent(query)

            context_results = []
            context_text = ""

            if intent_info["intent"] in ["nec", "wattmonk"]:
                context_results = self.retrieve_context(query, intent_info["document_type"])
                context_text = self.format_context(context_results)

            response_info = self.generate_response(query, context_text, intent_info)
            chat_response = {
                "query": query,
                "response": response_info["response"],
                "intent": intent_info,
                "context_used": context_results,
                "sources_count": response_info["sources_used"],
                "has_context": response_info["has_context"],
                "timestamp": datetime.now().isoformat()
            }
            

            if maintain_history:
                self.conversation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "bot_response": chat_response,
                    "type": "bot"
                })
            
            return chat_response
            
        except Exception as e:
            error_response = {
                "query": query,
                "response": f"I apologize, but I encountered an error: {str(e)}",
                "intent": {"intent": "error", "confidence": 0},
                "context_used": [],
                "sources_count": 0,
                "has_context": False,
                "timestamp": datetime.now().isoformat()
            }
            
            if maintain_history:
                self.conversation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "bot_response": error_response,
                    "type": "bot"
                })
            
            return error_response
    
    def search_knowledge_base(self, query: str, document_type: str = None, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base and return formatted results."""
        results = self.retrieve_context(query, document_type, n_results)
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result["content"],
                "source": result["metadata"].get("source", "Unknown"),
                "document_type": result["metadata"].get("document_type", "Unknown"),
                "relevance_score": 1 - result.get("distance", 0),
                "chunk_index": result["metadata"].get("chunk_index", 0)
            })
        
        return formatted_results
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history."""
        return self.conversation_history[-limit:] if limit > 0 else self.conversation_history
    
    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        doc_stats = self.document_processor.get_collection_stats()
        
        return {
            "document_stats": doc_stats,
            "conversation_length": len(self.conversation_history),
            "available_intents": ["general", "nec", "wattmonk"]
        }

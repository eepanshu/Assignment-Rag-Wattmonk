import os
import PyPDF2
import google.generativeai as genai
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
import hashlib
import json
from pathlib import Path
from docx import Document

class DocumentProcessor:
    def __init__(self, gemini_api_key: str, chroma_persist_directory: str = "./chroma_db"):
        """Initialize the document processor with Gemini API and ChromaDB."""
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

        self.chroma_client = chromadb.PersistentClient(path=chroma_persist_directory)

        self.nec_collection = self._get_or_create_collection("nec_documents")
        self.wattmonk_collection = self._get_or_create_collection("wattmonk_documents")
        
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        try:
            return self.chroma_client.get_collection(name=name)
        except:
            return self.chroma_client.create_collection(name=name)
    
    def extract_text_from_pdf(self, pdf_path: str, max_pages: int = 100) -> str:
        """Extract text from PDF file with page limit to prevent memory issues."""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                pages_to_process = min(max_pages, total_pages)

                print(f"PDF has {total_pages} pages, processing first {pages_to_process} pages")

                for i in range(pages_to_process):
                    try:
                        page_text = pdf_reader.pages[i].extract_text()
                        text += page_text + "\n"


                        if (i + 1) % 10 == 0:
                            print(f"Processed {i + 1}/{pages_to_process} pages...")

                    except Exception as e:
                        print(f"Error extracting text from page {i+1}: {e}")
                        continue

                print(f"Extracted {len(text)} characters from {pages_to_process} pages")

        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
        return text

    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX file."""
        text = ""
        try:
            doc = Document(docx_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
        return text
    
    def chunk_text(self, text: str, chunk_size: int = 2000, overlap: int = 200, max_chunks: int = 500) -> List[str]:
        """Split text into overlapping chunks with strict limits."""
        chunks = []
        start = 0
        text_length = len(text)

        print(f"Chunking text of {text_length} characters into chunks of {chunk_size} chars (max {max_chunks} chunks)")


        if text_length > 500000:  
            print(f"⚠️ Text too long ({text_length} chars), truncating to 500KB")
            text = text[:500000]
            text_length = len(text)

        while start < text_length and len(chunks) < max_chunks:
            end = start + chunk_size
            if end > text_length:
                end = text_length

            chunk = text[start:end]

            if end < text_length:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)

                if break_point > start + chunk_size // 2:
                    chunk = text[start:break_point + 1]
                    end = break_point + 1

            chunk = chunk.strip()
            if len(chunk) > 100:  
                chunks.append(chunk)

            start = end - overlap

            if len(chunks) % 50 == 0 and len(chunks) > 0:
                print(f"Created {len(chunks)} chunks so far...")

        if len(chunks) >= max_chunks:
            print(f"⚠️ Reached maximum chunk limit of {max_chunks}")

        print(f"Created {len(chunks)} total chunks")
        return chunks
    
    def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings using Gemini."""
        try:

            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            print(f"Generated embedding of length: {len(result['embedding'])}")
            return result['embedding']
        except Exception as e:
            print(f"Error generating embeddings: {e}")

            try:
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type="retrieval_document"
                )
                print(f"Generated embedding with fallback model, length: {len(result['embedding'])}")
                return result['embedding']
            except Exception as e2:
                print(f"Fallback embedding also failed: {e2}")
                return []
    
    def process_document(self, file_path: str, document_type: str) -> bool:
        """Process a document and store it in the vector database."""
        try:
            print(f"Processing document: {file_path}")

            if file_path.lower().endswith('.pdf'):
                text = self.extract_text_from_pdf(file_path)
                print(f"Extracted {len(text)} characters from PDF")
            elif file_path.lower().endswith('.docx'):
                text = self.extract_text_from_docx(file_path)
                print(f"Extracted {len(text)} characters from DOCX")
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                print(f"Extracted {len(text)} characters from text file")

            if not text.strip():
                print(f"No text extracted from {file_path}")
                return False

            if len(text) > 1000000:  
                print(f"⚠️ Text very large ({len(text)} chars), this may take a while...")

            chunks = self.chunk_text(text, max_chunks=200)  
            
            collection = self.nec_collection if document_type.lower() == 'nec' else self.wattmonk_collection
            
            batch_size = 10
            successful_chunks = 0

            for batch_start in range(0, len(chunks), batch_size):
                batch_end = min(batch_start + batch_size, len(chunks))
                batch_chunks = chunks[batch_start:batch_end]

                print(f"Processing batch {batch_start//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size} ({len(batch_chunks)} chunks)")

                for i, chunk in enumerate(batch_chunks):
                    actual_index = batch_start + i
                    try:
                        embedding = self.generate_embeddings(chunk)

                        if embedding:

                            chunk_id = hashlib.md5(f"{file_path}_{actual_index}_{chunk[:100]}".encode()).hexdigest()

                            collection.add(
                                embeddings=[embedding],
                                documents=[chunk],
                                metadatas=[{
                                    "source": os.path.basename(file_path),
                                    "chunk_index": actual_index,
                                    "document_type": document_type,
                                    "file_path": file_path
                                }],
                                ids=[chunk_id]
                            )
                            successful_chunks += 1
                        else:
                            print(f"Failed to generate embedding for chunk {actual_index}")

                    except Exception as e:
                        print(f"Error processing chunk {actual_index}: {e}")
                        continue

                import time
                time.sleep(0.1)

            print(f"Successfully processed {successful_chunks}/{len(chunks)} chunks from {file_path}")
            return successful_chunks > 0
            
        except Exception as e:
            print(f"Error processing document {file_path}: {e}")
            return False
    
    def search_documents(self, query: str, document_type: str = None, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents based on query."""
        try:
            print(f"Searching for: '{query}' in document_type: {document_type}")

            query_embedding = self.generate_embeddings(query)

            if not query_embedding:
                print("Failed to generate query embedding")
                return []

            results = []

            collections_to_search = []
            if document_type is None or document_type.lower() == 'nec':
                collections_to_search.append(('nec', self.nec_collection))
            if document_type is None or document_type.lower() == 'wattmonk':
                collections_to_search.append(('wattmonk', self.wattmonk_collection))

            print(f"Searching in collections: {[name for name, _ in collections_to_search]}")

            for collection_name, collection in collections_to_search:
                try:
                    count = collection.count()
                    print(f"Collection '{collection_name}' has {count} documents")

                    if count == 0:
                        print(f"Skipping empty collection: {collection_name}")
                        continue

                    search_results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=min(n_results, count)
                    )

                    print(f"Found {len(search_results['documents'][0])} results in {collection_name}")

                    for i in range(len(search_results['documents'][0])):
                        results.append({
                            'content': search_results['documents'][0][i],
                            'metadata': search_results['metadatas'][0][i],
                            'distance': search_results['distances'][0][i] if 'distances' in search_results else 0,
                            'collection': collection_name
                        })
                except Exception as e:
                    print(f"Error searching in {collection_name} collection: {e}")

            results.sort(key=lambda x: x['distance'])
            print(f"Total search results: {len(results)}")
            return results[:n_results]

        except Exception as e:
            print(f"Error searching documents: {e}")
            return []

    def keyword_search(self, query: str, document_type: str = None, n_results: int = 3) -> List[Dict[str, Any]]:
        """Search for documents containing specific keywords."""
        try:
            results = []
            query_lower = query.lower()

            keywords = []
            for word in query_lower.split():
                if len(word) > 2:  
                    keywords.append(word)

            print(f"🔍 Keyword search for: {keywords}")

            collections_to_search = []
            if document_type is None or document_type.lower() == 'nec':
                collections_to_search.append(('nec', self.nec_collection))
            if document_type is None or document_type.lower() == 'wattmonk':
                collections_to_search.append(('wattmonk', self.wattmonk_collection))

            for collection_name, collection in collections_to_search:
                try:
                    all_docs = collection.get()

                    if all_docs['documents']:
                        for i, doc in enumerate(all_docs['documents']):
                            doc_lower = doc.lower()

                            match_count = sum(1 for keyword in keywords if keyword in doc_lower)

                            if match_count > 0:
                                metadata = all_docs['metadatas'][i] if all_docs['metadatas'] else {}

                                results.append({
                                    'content': doc,
                                    'metadata': metadata,
                                    'collection': collection_name,
                                    'distance': 1.0 - (match_count / len(keywords)),  
                                    'keyword_matches': match_count
                                })

                                print(f"Found {match_count} keyword matches in {collection_name}")

                except Exception as e:
                    print(f"❌ Error in keyword search for {collection_name}: {e}")
                    continue

            results.sort(key=lambda x: (-x.get('keyword_matches', 0), x.get('distance', float('inf'))))
            print(f"Keyword search found {len(results)} results")
            return results[:n_results]

        except Exception as e:
            print(f"❌ Error in keyword_search: {e}")
            return []

    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about the collections."""
        try:
            nec_count = self.nec_collection.count()
            wattmonk_count = self.wattmonk_collection.count()

            print(f"Collection stats - NEC: {nec_count}, Wattmonk: {wattmonk_count}")

            return {
                "nec_documents": nec_count,
                "wattmonk_documents": wattmonk_count,
                "total_documents": nec_count + wattmonk_count
            }
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {"nec_documents": 0, "wattmonk_documents": 0, "total_documents": 0}

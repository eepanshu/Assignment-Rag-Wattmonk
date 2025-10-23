# RAG Chatbot - Wattmonk & NEC Assistant

A Retrieval-Augmented Generation (RAG) based chatbot that can answer queries from multiple knowledge sources while maintaining conversational capabilities for general questions.

## 🎯 Features

- **Multi-Context Handling**: Distinguishes between NEC, Wattmonk, and general queries
- **Source Attribution**: Clearly indicates information sources
- **Conversation Memory**: Maintains context across multiple exchanges
- **Fallback Responses**: Handles queries outside knowledge base gracefully
- **Search Functionality**: Allows users to search specific topics
- **Document Upload**: Process and add new documents to the knowledge base

## 🏗️ Architecture

### Backend (FastAPI)
- **Document Processing**: PDF text extraction, chunking, and preprocessing
- **Vector Store**: ChromaDB for document embeddings and similarity search
- **Query Processing**: Intent classification and context-aware response generation
- **LLM Integration**: Google Gemini for embeddings and response generation

### Frontend (Streamlit)
- **Chat Interface**: User-friendly conversational interface
- **Document Management**: Upload and process new documents
- **Search Interface**: Direct knowledge base search
- **System Monitoring**: View statistics and manage conversation history

## 📋 Requirements

- Python 3.8+
- Google Gemini API Key
- Internet connection for API calls

## 🚀 Quick Start

### 1. Setup

```bash
# Clone or download the project
# Navigate to the project directory

# Run the setup script
python setup.py
```

### 2. Configure API Key

1. Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Edit `Backend/.env` file and add your API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

### 3. Run the Application

**Option 1: Using run scripts (Recommended)**
```bash
# Terminal 1 - Start Backend
python run_backend.py

# Terminal 2 - Start Frontend
python run_frontend.py
```

**Option 2: Manual start**
```bash
# Terminal 1 - Backend
cd Backend
python main.py

# Terminal 2 - Frontend
cd Frontend
streamlit run app.py
```

### 4. Access the Application

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📚 Usage

### Initial Setup
1. Open the frontend application
2. Click "🚀 Initialize System" in the sidebar to process the provided documents
3. Wait for the documents to be processed and indexed

### Chatting
- Type your questions in the chat input
- The system will automatically detect if you're asking about:
  - **NEC codes**: Technical electrical standards
  - **Wattmonk**: Company information and services
  - **General topics**: Uses base AI knowledge

### Search
- Use the search panel to find specific information
- Filter by document type (NEC, Wattmonk, or All)
- Adjust the number of results

### Document Upload
- Upload new PDF, TXT, or DOCX files
- Specify the document type (NEC or Wattmonk)
- The system will process and index the new content

## 🔧 API Endpoints

### Chat
- `POST /chat` - Send a chat message
- `GET /conversation-history` - Get conversation history
- `DELETE /conversation-history` - Clear conversation history

### Search
- `POST /search` - Search the knowledge base

### Documents
- `POST /upload-document` - Upload and process a new document
- `POST /initialize-documents` - Process default documents

### System
- `GET /system-stats` - Get system statistics
- `GET /` - Health check

## 📁 Project Structure

```
RAG-Chatbot/
├── Backend/
│   ├── main.py                 # FastAPI application
│   ├── rag_chatbot.py         # RAG implementation
│   ├── document_processor.py   # Document processing pipeline
│   ├── requirements.txt       # Backend dependencies
│   ├── .env.example          # Environment variables template
│   └── chroma_db/            # Vector database (created automatically)
├── Frontend/
│   ├── app.py                # Streamlit application
│   └── requirements.txt      # Frontend dependencies
├── setup.py                  # Setup script
├── run_backend.py           # Backend runner script
├── run_frontend.py          # Frontend runner script
├── README.md               # This file
├── 2017-NEC-Code-2 (1).pdf # NEC document
└── Wattmonk Information.docx # Wattmonk document
```

## 🛠️ Technical Details

### Document Processing
1. **Text Extraction**: Extracts text from PDF and DOCX files
2. **Chunking**: Splits documents into overlapping chunks (1000 chars with 200 char overlap)
3. **Embedding Generation**: Uses Gemini's embedding model
4. **Storage**: Stores in ChromaDB with metadata

### Intent Classification
- Keyword-based classification for NEC and Wattmonk queries
- Fallback to general conversation for other topics

### Response Generation
- Retrieves relevant context using similarity search
- Injects context into Gemini prompts
- Provides source attribution

## 🔍 Troubleshooting

### Common Issues

1. **API Key Error**
   - Ensure your Gemini API key is correctly set in `Backend/.env`
   - Verify the API key is valid and has proper permissions

2. **Backend Connection Error**
   - Make sure the backend is running on port 8000
   - Check for port conflicts

3. **Document Processing Fails**
   - Ensure documents are in the correct format (PDF, TXT, DOCX)
   - Check file permissions and accessibility

4. **ChromaDB Issues**
   - Delete the `Backend/chroma_db` folder and restart to reset the database
   - Ensure sufficient disk space

### Performance Tips

- For large documents, processing may take several minutes
- The first query after startup may be slower due to model initialization
- Consider using smaller chunk sizes for very large documents

## 📝 License

This project is created for educational and demonstration purposes.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the chatbot.

## 📞 Support

For questions or issues, please refer to the troubleshooting section or create an issue in the project repository.

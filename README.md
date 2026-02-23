# Resume Agent

An end-to-end ML Agent system for quickly screening and understanding multiple candidates. Supports text input and file uploads, uses optimized chunking strategies (Semantic Chunking) for resume processing, helping HR and recruiters efficiently manage candidate information.

## 🌟 Features

- ✅ **Text Input**: Directly insert candidate information into the knowledge base
- ✅ **File Upload**: Batch upload support for PDF and TXT files
- ✅ **Smart Chunking**: Uses Semantic Chunking strategy optimized for resumes (chunk_size=500, similarity_threshold=0.5)
- ✅ **Fast Screening**: Quickly find qualified candidates based on semantic search
- ✅ **Knowledge Q&A**: Agent can answer various questions about candidates
- ✅ **Auto Ingestion**: Supports automatic monitoring and ingestion from dropbox folder
- ✅ **Vector Storage**: Uses LanceDB for local storage, no external services required

## 🏗️ Architecture

- **Knowledge Base**: Agno Knowledge Module
- **Vector Store**: LanceDB (local storage)
- **LLM**: OpenRouter (supports multiple models)
- **Embeddings**: OpenRouter API (using OpenAI embedding models)
- **Chunking**: Semantic Chunking (optimized for resumes)
- **File Processing**: PDF and TXT file support

## 📋 Project Structure

```
resume agent/
├── dropbox/              # Drop files folder (auto-ingestion)
├── knowledge/           # Knowledge base modules
│   ├── config.py       # Configuration management
│   └── setup.py        # Knowledge base initialization
├── tools/               # Tools modules
│   └── knowledge_tool.py  # Knowledge insert tool
├── ingestion/          # Ingestion modules
│   └── dropbox_monitor.py  # File monitoring
├── agent/              # Agent modules
│   └── knowledge_agent.py  # Knowledge agent
├── main.py             # Main entry point
├── batch_upload.py     # Batch upload script
└── requirements.txt    # Dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Using Anaconda (recommended)
conda activate base
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example config file and add your OpenRouter API key:

```bash
cp config.example.env .env
# Edit .env file and add your OPENROUTER_API_KEY
```

### 3. Run the Application

**Interactive Mode (Recommended):**
```bash
python main.py interactive
```

**Batch Upload Resumes:**
```bash
python batch_upload.py /path/to/resumes/
```

**Monitor Mode:**
```bash
python main.py monitor
# Then drop PDF files into dropbox/ folder
```

## 💡 Usage Examples

### Insert Text
```
> insert My name is John Doe. I have 5 years of experience in Python...
```

### Upload File
```
> file ./dropbox/john_doe_resume.pdf
```

### Query Candidates
```
> What is John Doe's education background?
> Who has experience with machine learning?
> Find candidates with Python skills
```

## ⚙️ Configuration

### Chunking Strategy

Optimized for resumes using Semantic Chunking:
- `chunk_size=500`: Optimal chunk size for resumes
- `similarity_threshold=0.5`: Semantic similarity threshold

### LLM Model

Default: `openai/gpt-4o-mini`, configurable in `.env` file:
```bash
LLM_MODEL=openai/gpt-4o-mini  # Or other OpenRouter supported models
```

### API Keys

**Only one OpenRouter API key is needed!**
- LLM queries: Through OpenRouter
- Embeddings: Also through OpenRouter (using OpenAI embedding models)

Get your API key from: https://openrouter.ai/settings/keys

**Optional**: Use FastEmbed for local embeddings (no API key needed for embeddings):
```bash
# In .env file
EMBEDDER_TYPE=fastembed
```

### Gmail Toolkit (Optional)

Enable Agno Gmail tools in the main agent:
```bash
# In .env file
ENABLE_GMAIL_TOOLS=true
GOOGLE_CREDENTIALS_PATH=./google_api_server/credentials.json
GOOGLE_TOKEN_PATH=./google_api_server/token.json
```

When enabled, the agent loads GmailTools in read-only mode (where supported), so it can query inbox content for resume screening workflows.

### Usage Tips

**Important**: When inserting text, you must use the `insert` command prefix:
```
> insert My name is John Doe...
```

**Common Commands**:
- `insert <text>` - Insert text into knowledge base
- `file <path>` - Insert file (PDF/TXT) into knowledge base
- `<question>` - Query the knowledge base
- `exit` - Exit the program

## 🔧 Tech Stack

- **Python 3.9+**
- **Agno** - Knowledge Module
- **LanceDB** - Vector Database
- **OpenRouter** - LLM API Gateway
- **Chonkie** - Semantic Chunking
- **pypdf** - PDF Processing
- **watchdog** - File Monitoring

## 📝 License

This project is for learning and research purposes only.

## 🤝 Contributing

Issues and Pull Requests are welcome!

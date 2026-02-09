# Architecture Documentation

## System Overview

The Knowledge Ingestion Tool is a local system that enables agents to expand their vector knowledge store through text input and file ingestion. It uses Agno Knowledge Module for knowledge management and LanceDB for vector storage.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Knowledge Ingestion Tool                 │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Text       │    │   File       │    │   Dropbox    │
│   Input      │    │   Input      │    │   Monitor    │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
              ┌──────────────────────┐
              │  InsertKnowledgeTool │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Knowledge Base     │
              │   (Agno Knowledge)   │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   LanceDB Vector DB  │
              │   (Local Storage)    │
              └──────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Knowledge Agent    │
              │   (Query & Search)   │
              └──────────────────────┘
```

## Component Details

### 1. Knowledge Configuration (`knowledge/config.py`)

**Purpose**: Manages all configuration settings for the knowledge base.

**Key Features**:
- LanceDB configuration (table name, URI)
- Embedder configuration (default or FastEmbed)
- Chunking strategy configuration
- Dropbox folder path
- Environment variable support

**Configuration Options**:
- `table_name`: Name of the LanceDB table
- `uri`: Storage location for LanceDB
- `embedder_type`: "default" (OpenAI) or "fastembed" (local)
- `chunking_strategy`: "semantic", "document", or "fixed_size"
- `chunk_size`: Size of chunks for fixed_size strategy
- `chunk_overlap`: Overlap between chunks
- `dropbox_path`: Path to dropbox folder

### 2. Knowledge Setup (`knowledge/setup.py`)

**Purpose**: Initializes the knowledge base with proper configuration.

**Key Functions**:
- `create_knowledge_base()`: Creates and configures Knowledge instance
- `create_chunking_strategy()`: Creates chunking strategy based on config
- `create_embedder()`: Creates embedder based on config

**Process**:
1. Load configuration
2. Create embedder (if specified)
3. Create LanceDB vector store
4. Initialize Knowledge base
5. Return configured Knowledge instance

### 3. Insert Knowledge Tool (`tools/knowledge_tool.py`)

**Purpose**: Provides interface for inserting knowledge into the knowledge base.

**Supported Operations**:
- Insert raw text content
- Insert PDF files
- Insert TXT files

**Key Methods**:
- `insert_knowledge(text=None, file_path=None)`: Main insertion method

**Error Handling**:
- Validates input (either text or file_path required)
- Checks file existence
- Validates file extensions
- Provides detailed error messages

### 4. Dropbox Monitor (`ingestion/dropbox_monitor.py`)

**Purpose**: Automatically monitors dropbox folder and ingests new files.

**Key Features**:
- File system event monitoring using watchdog
- Automatic file ingestion
- Support for existing files
- Configurable file extensions

**Components**:
- `DropboxFileHandler`: Handles file system events
- `DropboxMonitor`: Main monitoring class

**Process**:
1. Monitor dropbox folder for new files
2. Detect file creation events
3. Validate file type
4. Ingest file into knowledge base
5. Track processed files to avoid duplicates

### 5. Knowledge Agent (`agent/knowledge_agent.py`)

**Purpose**: Creates an agent that can query the knowledge base.

**Key Features**:
- Agentic RAG (searches knowledge when needed)
- Semantic search capabilities
- Natural language queries

**Configuration**:
- `search_knowledge=True`: Enables knowledge search
- Uses Knowledge base for context

## Data Flow

### Text Insertion Flow

```
User Input (Text)
    │
    ▼
InsertKnowledgeTool.insert_knowledge(text=...)
    │
    ▼
Knowledge.insert(text_content=...)
    │
    ▼
Chunking Strategy (Semantic/Document/Fixed)
    │
    ▼
Embedder (OpenAI/FastEmbed)
    │
    ▼
LanceDB Vector Store
```

### File Ingestion Flow

```
File in Dropbox Folder
    │
    ▼
DropboxMonitor detects file
    │
    ▼
InsertKnowledgeTool.insert_knowledge(file_path=...)
    │
    ▼
Reader (PDFReader/TextReader)
    │
    ▼
Knowledge.insert(path=..., reader=...)
    │
    ▼
Chunking Strategy
    │
    ▼
Embedder
    │
    ▼
LanceDB Vector Store
```

### Query Flow

```
User Query
    │
    ▼
Knowledge Agent
    │
    ▼
Agent decides to search knowledge
    │
    ▼
Query Embedding
    │
    ▼
LanceDB Vector Search
    │
    ▼
Retrieve Relevant Chunks
    │
    ▼
Agent generates response with context
    │
    ▼
User receives answer
```

## Chunking Strategies

### Semantic Chunking (Default)
- Splits content at natural breakpoints
- Maintains meaning and context
- Best for general text content

### Document Chunking
- Preserves document structure
- Keeps sections and pages together
- Best for structured documents

### Fixed Size Chunking
- Uniform chunk sizes
- Predictable dimensions
- Configurable overlap

## Embedders

### Default Embedder (OpenAI)
- High quality embeddings
- Requires API key
- Cloud-based
- Best for production use

### FastEmbed (Local)
- No API key required
- Runs locally
- Privacy-focused
- Good for development/testing

## Storage

### LanceDB
- Local file-based storage
- No external dependencies
- Fast vector search
- Configurable storage location

## Error Handling

The system includes comprehensive error handling:

1. **Validation Errors**: Input validation before processing
2. **File Errors**: File existence and type validation
3. **Processing Errors**: Graceful handling of processing failures
4. **Logging**: Detailed logging for debugging

## Extensibility

The system is designed to be easily extensible:

1. **New File Types**: Add new readers in `knowledge_tool.py`
2. **New Chunking Strategies**: Add to `setup.py`
3. **New Embedders**: Add to `setup.py`
4. **Custom Tools**: Extend `InsertKnowledgeTool` class

## Performance Considerations

1. **Async Operations**: Uses async/await for non-blocking operations
2. **Batch Processing**: Supports batch file ingestion
3. **Efficient Monitoring**: Uses watchdog for efficient file monitoring
4. **Local Storage**: LanceDB provides fast local access

## Security Considerations

1. **Local Storage**: All data stored locally
2. **No External Dependencies**: Optional (FastEmbed) for privacy
3. **File Validation**: Validates file types before processing
4. **Error Messages**: Doesn't expose sensitive information

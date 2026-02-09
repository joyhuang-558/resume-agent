# Project Structure

```
resume agent/
├── dropbox/                      # Drop files here for auto-ingestion
│   └── (empty - files will be added here)
│
├── knowledge/                    # Knowledge base modules
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Configuration management
│   └── setup.py                 # Knowledge base initialization
│
├── tools/                        # Custom tools
│   ├── __init__.py              # Package initialization
│   └── knowledge_tool.py        # Knowledge insert tool
│
├── ingestion/                    # Ingestion modules
│   ├── __init__.py              # Package initialization
│   └── dropbox_monitor.py       # File monitoring and auto-ingestion
│
├── agent/                        # Agent modules
│   ├── __init__.py              # Package initialization
│   └── knowledge_agent.py       # Knowledge-enabled agent
│
├── main.py                       # Main entry point
├── requirements.txt              # Python dependencies
├── config.example.env            # Example configuration file
├── .gitignore                    # Git ignore rules
│
├── README.md                     # Main documentation
├── QUICKSTART.md                 # Quick start guide
├── ARCHITECTURE.md               # Architecture documentation
├── EXAMPLES.md                   # Usage examples
└── PROJECT_STRUCTURE.md          # This file
```

## File Descriptions

### Core Modules

- **`knowledge/config.py`**: Configuration management with environment variable support
- **`knowledge/setup.py`**: Knowledge base initialization with LanceDB
- **`tools/knowledge_tool.py`**: Tool for inserting text and files
- **`ingestion/dropbox_monitor.py`**: File system monitoring and auto-ingestion
- **`agent/knowledge_agent.py`**: Agent creation with knowledge base integration
- **`main.py`**: Main entry point with demo, interactive, and monitor modes

### Documentation

- **`README.md`**: Comprehensive documentation
- **`QUICKSTART.md`**: Quick start guide
- **`ARCHITECTURE.md`**: System architecture and design
- **`EXAMPLES.md`**: Code examples and use cases
- **`PROJECT_STRUCTURE.md`**: This file

### Configuration

- **`requirements.txt`**: Python package dependencies
- **`config.example.env`**: Example environment configuration
- **`.gitignore`**: Git ignore patterns

## Module Dependencies

```
main.py
├── knowledge/
│   ├── config.py
│   └── setup.py
├── tools/
│   └── knowledge_tool.py (depends on knowledge/)
├── ingestion/
│   └── dropbox_monitor.py (depends on tools/)
└── agent/
    └── knowledge_agent.py (depends on knowledge/)
```

## Key Components

1. **Knowledge Base**: Core knowledge management using Agno Knowledge Module
2. **Vector Store**: LanceDB for local vector storage
3. **Insert Tool**: Interface for adding knowledge
4. **Monitor**: Automatic file ingestion from dropbox
5. **Agent**: Query interface for knowledge base

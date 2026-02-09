# Usage Examples

This document provides practical examples of using the Knowledge Ingestion Tool.

## Basic Setup

```python
from knowledge.config import KnowledgeConfig
from knowledge.setup import create_knowledge_base
from tools.knowledge_tool import InsertKnowledgeTool
from agent.knowledge_agent import create_knowledge_agent

# Create knowledge base
config = KnowledgeConfig()
knowledge_base = create_knowledge_base(config)

# Create insert tool
knowledge_tool = InsertKnowledgeTool(knowledge_base)

# Create agent
agent = create_knowledge_agent(knowledge_base)
```

## Example 1: Insert Text

```python
# Insert raw text
text = """
Artificial Intelligence (AI) is transforming industries across the globe.
Machine learning, a subset of AI, enables systems to learn from data.
Deep learning uses neural networks with multiple layers.
"""

result = knowledge_tool.insert_knowledge(text=text)
print(result)  # Successfully inserted text content (XXX characters) into knowledge base
```

## Example 2: Insert PDF File

```python
# Insert a PDF file
result = knowledge_tool.insert_knowledge(file_path="./documents/resume.pdf")
print(result)  # Successfully inserted PDF file 'resume.pdf' into knowledge base
```

## Example 3: Insert Text File

```python
# Insert a text file
result = knowledge_tool.insert_knowledge(file_path="./documents/notes.txt")
print(result)  # Successfully inserted text file 'notes.txt' into knowledge base
```

## Example 4: Query Knowledge Base

```python
import asyncio

async def query_example():
    # Query the knowledge base
    response = await agent.arun("What is machine learning?")
    print(response.content)

asyncio.run(query_example())
```

## Example 5: Dropbox Auto-Ingestion

```python
from ingestion.dropbox_monitor import DropboxMonitor
import asyncio

async def monitor_example():
    # Create monitor
    monitor = DropboxMonitor(knowledge_tool, dropbox_path="./dropbox")
    
    # Ingest existing files
    monitor.ingest_existing_files()
    
    # Start monitoring (runs indefinitely)
    await monitor.run_async()

# Run in background
# asyncio.run(monitor_example())
```

## Example 6: Custom Configuration

```python
from knowledge.config import KnowledgeConfig

# Custom configuration
config = KnowledgeConfig(
    table_name="my_knowledge_base",
    uri="./data/vectors",
    embedder_type="fastembed",  # Use local embeddings
    chunking_strategy="document",  # Preserve document structure
    chunk_size=8000,
    chunk_overlap=300,
    dropbox_path="./my_dropbox"
)

knowledge_base = create_knowledge_base(config)
```

## Example 7: Batch Insertion

```python
# Insert multiple files
files = [
    "./documents/doc1.pdf",
    "./documents/doc2.txt",
    "./documents/doc3.pdf"
]

for file_path in files:
    try:
        result = knowledge_tool.insert_knowledge(file_path=file_path)
        print(f"✓ {result}")
    except Exception as e:
        print(f"✗ Failed to insert {file_path}: {e}")
```

## Example 8: Error Handling

```python
try:
    # Insert with validation
    result = knowledge_tool.insert_knowledge(
        text="Some content",
        file_path="./file.pdf"  # Error: can't provide both
    )
except ValueError as e:
    print(f"Validation error: {e}")

try:
    # Insert non-existent file
    result = knowledge_tool.insert_knowledge(file_path="./nonexistent.pdf")
except FileNotFoundError as e:
    print(f"File error: {e}")

try:
    # Insert unsupported file type
    result = knowledge_tool.insert_knowledge(file_path="./document.docx")
except ValueError as e:
    print(f"Unsupported type: {e}")
```

## Example 9: Interactive Agent Session

```python
import asyncio

async def interactive_session():
    while True:
        query = input("\nAsk a question (or 'exit' to quit): ")
        if query.lower() == "exit":
            break
        
        response = await agent.arun(query)
        print(f"\n{response.content}\n")

asyncio.run(interactive_session())
```

## Example 10: Resume-Specific Use Case

```python
# Insert resume
knowledge_tool.insert_knowledge(file_path="./resumes/john_doe.pdf")

# Query about candidate
response = await agent.arun("What are John Doe's technical skills?")
print(response.content)

# Insert more resumes
knowledge_tool.insert_knowledge(file_path="./resumes/jane_smith.pdf")

# Find candidates with specific skills
response = await agent.arun("Who has experience with Python and machine learning?")
print(response.content)
```

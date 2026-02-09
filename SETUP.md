# Setup Guide

## Initial Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

**Important**: The `.env` file contains sensitive API keys and is already in `.gitignore`. Never commit this file to git.

#### Option A: Use .env file (Recommended)

1. Copy the example config:
```bash
cp config.example.env .env
```

2. Edit `.env` and add your OpenRouter API key:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

#### Option B: Set Environment Variables

```bash
export OPENROUTER_API_KEY="sk-or-v1-your-actual-key-here"
```

Get your OpenRouter API key from: https://openrouter.ai/settings/keys

### 3. Optional: Configure Embedder

If you want to use a different embedder, edit `.env`:

```bash
# For local embeddings (no API key needed for embeddings)
EMBEDDER_TYPE=fastembed

# For OpenAI embedder (requires OpenAI API key)
EMBEDDER_TYPE=default
OPENAI_API_KEY=your-openai-key
```

### 4. Verify Setup

Run the demo to verify everything works:

```bash
python main.py demo
```

## Configuration Options

All configuration options can be set in `.env` file or as environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | **Required** - OpenRouter API key for LLM queries | - |
| `KNOWLEDGE_TABLE_NAME` | LanceDB table name | `knowledge_base` |
| `KNOWLEDGE_URI` | LanceDB storage path | `./knowledge/lancedb` |
| `EMBEDDER_TYPE` | Embedder type: `default`, `fastembed`, `openrouter` | `default` |
| `FASTEMBED_MODEL` | FastEmbed model name | `BAAI/bge-small-en-v1.5` |
| `CHUNKING_STRATEGY` | Chunking strategy: `semantic`, `document`, `fixed_size` | `semantic` |
| `CHUNK_SIZE` | Chunk size for fixed_size strategy | `5000` |
| `CHUNK_OVERLAP` | Chunk overlap | `200` |
| `DROPBOX_PATH` | Path to dropbox folder | `./dropbox` |
| `OPENAI_API_KEY` | OpenAI API key (only if using default embedder) | - |

## Security Notes

1. **Never commit `.env` file** - It contains your API keys
2. **`.env` is already in `.gitignore`** - Don't remove it
3. **Use `config.example.env`** - This is safe to commit (no real keys)
4. **Rotate keys if exposed** - If you accidentally commit a key, rotate it immediately

## Troubleshooting

### "OPENROUTER_API_KEY environment variable is required"

Make sure you've:
1. Created `.env` file from `config.example.env`
2. Added your actual OpenRouter API key
3. Or set the environment variable manually

### Import errors

```bash
pip install -r requirements.txt
```

### API key not working

1. Verify your key at: https://openrouter.ai/settings/keys
2. Check for typos in `.env` file
3. Ensure no extra spaces around the key

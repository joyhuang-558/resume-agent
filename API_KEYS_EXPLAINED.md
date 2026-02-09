# API Keys 说明

## 为什么只需要 OpenRouter API Key？

你说得对！既然使用 OpenRouter 并且选择 OpenAI 模型，理论上应该只需要 OpenRouter API key。

## 工作原理

### LLM 查询（Agent 回答）
- ✅ 使用 OpenRouter API key
- ✅ 调用 OpenAI 模型（如 `openai/gpt-4o-mini`）
- ✅ 通过 OpenRouter 的 API

### 嵌入向量（Embeddings）
- ✅ **现在也使用 OpenRouter API key！**
- ✅ 通过 OpenRouter 的 endpoint (`https://openrouter.ai/api/v1`)
- ✅ 使用 OpenAI 的 embedding 模型（如 `text-embedding-3-small`）

## 已修复

代码已更新，现在：
- 如果只设置了 `OPENROUTER_API_KEY`，会自动用于：
  - LLM 查询 ✅
  - 嵌入向量 ✅
- 如果同时设置了 `OPENAI_API_KEY`，会优先使用 OpenAI key 用于嵌入向量

## 配置

### 只需要 OpenRouter（推荐）

```bash
# .env 文件
OPENROUTER_API_KEY=sk-or-v1-your-key-here
# 不需要设置 OPENAI_API_KEY
```

### 或者使用 FastEmbed（完全本地，不需要任何 API key）

```bash
# .env 文件
OPENROUTER_API_KEY=sk-or-v1-your-key-here  # 用于 LLM 查询
EMBEDDER_TYPE=fastembed  # 本地嵌入，不需要 API key
```

## 总结

✅ **只需要一个 OpenRouter API key 就够了！**
- LLM 查询：通过 OpenRouter
- 嵌入向量：也通过 OpenRouter（使用 OpenAI embedding 模型）

不再需要单独的 OpenAI API key！

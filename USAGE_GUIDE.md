# 使用指南

## 交互模式正确使用方法

### ✅ 正确：插入文本

```
> insert My name is Daniel Carter. I graduated from the University of Washington...
```

**注意**：必须在文本前加上 `insert ` 命令

### ✅ 正确：插入文件

```
> file ./dropbox/resume.pdf
```

### ✅ 正确：查询知识库

```
> What is Daniel Carter's education background?
> What skills does Daniel Carter have?
```

## 常见错误

### ❌ 错误 1: 直接输入文本（没有 insert 命令）

**错误示例：**
```
> My name is Daniel Carter...
```

**问题**：系统会把这段文本当作查询问题，而不是要插入的内容

**正确做法：**
```
> insert My name is Daniel Carter...
```

### ❌ 错误 2: `list index out of range`

**原因**：
- 知识库是空的，没有数据可以搜索
- 或者搜索时出现了问题

**解决方法**：
1. 先插入一些数据：
   ```
   > insert Your text here
   ```
2. 然后再查询

### ❌ 错误 3: OpenAI API Key 警告

**原因**：
- Embedder 需要 OpenAI API key 来生成嵌入向量
- 你只设置了 OpenRouter API key（用于 LLM 查询）

**解决方法**：

**选项 1**: 设置 OpenAI API key（用于 embeddings）
```bash
export OPENAI_API_KEY="your-openai-key"
```

**选项 2**: 使用 FastEmbed（本地，不需要 API key）
```bash
# 在 .env 文件中设置
EMBEDDER_TYPE=fastembed

# 然后安装
pip install fastembed
```

## 完整使用流程示例

```bash
# 1. 启动交互模式
python main.py interactive

# 2. 插入简历信息
> insert My name is Daniel Carter. I graduated from the University of Washington with a Bachelor's degree in Computer Science. During my studies, I focused on machine learning, distributed systems, and data engineering.

# 3. 查询信息
> What is Daniel Carter's education?
> What are Daniel Carter's skills?
> What is Daniel Carter interested in?

# 4. 插入文件
> file ./dropbox/daniel_resume.pdf

# 5. 查询文件内容
> What information is in Daniel's resume?

# 6. 退出
> exit
```

## 命令总结

| 命令 | 用途 | 示例 |
|------|------|------|
| `insert <text>` | 插入文本到知识库 | `insert My name is John...` |
| `file <path>` | 插入文件到知识库 | `file ./dropbox/resume.pdf` |
| `<question>` | 查询知识库 | `What is Python?` |
| `exit` | 退出程序 | `exit` |

## 注意事项

1. **插入文本**：必须使用 `insert ` 前缀
2. **插入文件**：必须使用 `file ` 前缀
3. **查询**：直接输入问题即可
4. **API Keys**：
   - OpenRouter API key：用于 LLM 查询和嵌入向量（必需，一个 key 就够了！）
   - OpenAI API key：可选，如果设置了会优先使用（否则自动使用 OpenRouter）

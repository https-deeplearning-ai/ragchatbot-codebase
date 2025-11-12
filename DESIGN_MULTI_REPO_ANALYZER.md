# Multi-Repository Code Analysis System - Design Document

## 🎯 Project Vision

A self-aware RAG system that can analyze multiple GitHub repositories (including itself), understand code structure, documentation, and provide intelligent insights across your entire project portfolio.

**The Escher Loop**: The system ingests its own codebase and can answer questions about how it works, creating a true self-referential system.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│  (Web UI / API / CLI for querying across all repositories)  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                   Query Processing Layer                     │
│  • Multi-repo query routing                                  │
│  • Context aggregation across projects                       │
│  • Self-awareness detection (queries about itself)           │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                   RAG Orchestration Layer                    │
│  • AIGenerator (Claude API)                                  │
│  • Cross-repo search tools                                   │
│  • Code analysis tools                                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                   Vector Store Layer                         │
│  ChromaDB with Multiple Collections:                         │
│  ├─ repo_metadata (repo info, structure)                     │
│  ├─ code_content (source code chunks)                        │
│  ├─ documentation (README, docs, comments)                   │
│  └─ self_analysis (this system's own code)                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                Repository Ingestion Layer                    │
│  • GitHub API integration                                    │
│  • Git clone/pull automation                                 │
│  • Multi-format parsers (Python, JS, Java, etc.)            │
│  • Documentation extractors                                  │
│  • Self-ingestion monitor (watches own files)               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧩 Core Components

### 1. **MultiRepoManager**
**Purpose**: Manages multiple repository connections and metadata

**Responsibilities**:
- GitHub API authentication
- Repository cloning/updating
- Branch management
- Metadata tracking (last updated, commit hash, etc.)
- Self-repository special handling

**Key Methods**:
```python
add_repository(github_url, branch='main')
update_repository(repo_id)
remove_repository(repo_id)
get_repository_metadata(repo_id)
sync_all_repositories()
enable_self_monitoring()  # Watches own codebase changes
```

### 2. **CodeAnalyzer**
**Purpose**: Parse and analyze source code files

**Responsibilities**:
- Language detection
- Code structure extraction (classes, functions, imports)
- Dependency graph generation
- Docstring/comment extraction
- Complexity metrics
- Cross-file reference detection

**Key Methods**:
```python
parse_file(file_path, language)
extract_functions(code_ast)
extract_classes(code_ast)
extract_imports(code_ast)
generate_dependency_graph(repo_id)
analyze_code_quality(file_path)
```

### 3. **DocumentProcessor** (Enhanced)
**Purpose**: Process various documentation formats

**Current Support**: PDF, DOCX, TXT
**New Support**:
- Markdown (.md)
- ReStructuredText (.rst)
- Jupyter Notebooks (.ipynb)
- Code comments (inline documentation)
- API specs (OpenAPI/Swagger)

**Key Methods**:
```python
process_markdown(file_path)
process_jupyter_notebook(file_path)
extract_code_comments(source_files)
process_api_specs(spec_file)
```

### 4. **MultiCollectionVectorStore**
**Purpose**: Enhanced vector storage with multiple specialized collections

**Collections Schema**:

#### Collection: `repo_metadata`
```python
{
    "repo_id": str,
    "repo_name": str,
    "github_url": str,
    "description": str,
    "languages": List[str],
    "file_count": int,
    "last_updated": datetime,
    "commit_hash": str,
    "is_self": bool,  # True if this is the analyzer itself
    "embeddings": List[float]
}
```

#### Collection: `code_content`
```python
{
    "repo_id": str,
    "file_path": str,
    "language": str,
    "code_type": str,  # "function", "class", "module"
    "name": str,
    "code_chunk": str,
    "start_line": int,
    "end_line": int,
    "docstring": str,
    "imports": List[str],
    "dependencies": List[str],
    "embeddings": List[float]
}
```

#### Collection: `documentation`
```python
{
    "repo_id": str,
    "doc_type": str,  # "README", "tutorial", "API_doc", "comment"
    "file_path": str,
    "content": str,
    "section": str,
    "related_code": List[str],  # Links to code files
    "embeddings": List[float]
}
```

#### Collection: `self_analysis`
**Special collection for Escher loop**
```python
{
    "component": str,  # "MultiRepoManager", "CodeAnalyzer", etc.
    "file_path": str,
    "functionality": str,
    "code_snippet": str,
    "design_rationale": str,
    "self_reference_depth": int,  # How meta is this?
    "embeddings": List[float]
}
```

### 5. **EnhancedAIGenerator**
**Purpose**: Multi-repo aware AI query processing

**New Capabilities**:
- Cross-repository context aggregation
- Self-awareness detection
- Code explanation with file references
- Architecture visualization suggestions
- Comparative analysis between repos

**Key Methods**:
```python
query_across_repos(query, repo_ids=None)
explain_code(file_path, function_name)
compare_implementations(feature, repos)
analyze_self(query)  # Escher loop entry point
visualize_architecture(repo_id)
```

### 6. **SelfAwarenessEngine**
**Purpose**: Enable the system to understand itself (Escher loop)

**Responsibilities**:
- Monitor own codebase changes
- Maintain self-documentation
- Answer meta-queries ("How do you work?")
- Self-improvement suggestions
- Circular reference detection

**Key Methods**:
```python
ingest_self()
detect_self_query(query)
explain_own_component(component_name)
generate_self_documentation()
suggest_self_improvements()
```

---

## 🔄 Repository Ingestion Pipeline

### Phase 1: Repository Discovery & Cloning
```
Input: GitHub URL
↓
1. Validate repository access
2. Clone to local workspace: ./repos/{repo_name}
3. Extract metadata (languages, structure, README)
4. Register in repo_metadata collection
```

### Phase 2: File Classification
```
For each file in repository:
↓
1. Detect file type and language
2. Categorize: code / documentation / config / data
3. Apply appropriate processor
```

### Phase 3: Code Processing
```
For each code file:
↓
1. Parse with AST (language-specific)
2. Extract: functions, classes, imports, docstrings
3. Chunk intelligently (preserve semantic units)
4. Generate embeddings
5. Store in code_content collection
```

### Phase 4: Documentation Processing
```
For each doc file:
↓
1. Extract text content
2. Parse structure (headers, sections)
3. Link to related code files (if mentioned)
4. Generate embeddings
5. Store in documentation collection
```

### Phase 5: Self-Ingestion (Escher Loop)
```
Special handling when repo IS this analyzer:
↓
1. Mark with is_self=True
2. Create additional self_analysis entries
3. Map system components to code files
4. Generate design documentation embeddings
5. Enable real-time monitoring of changes
```

---

## 🔍 Query Capabilities

### 1. **Single-Repo Queries**
```
"Explain the authentication flow in project-X"
"Find all API endpoints in repo-Y"
"Show me error handling in service-Z"
```

### 2. **Cross-Repo Queries**
```
"Compare how authentication is implemented across all my projects"
"Which repositories use PostgreSQL?"
"Find all React components across repos"
```

### 3. **Self-Analysis Queries** (Escher Loop!)
```
"How do you ingest repositories?"
"Explain your vector storage architecture"
"What happens when I ask you about yourself?"
"How would you improve your own code analysis?"
```

### 4. **Code-to-Doc Linking**
```
"Show documentation for function X in file Y"
"What does the README say about feature Z?"
"Are there any undocumented functions in repo-A?"
```

### 5. **Architecture Queries**
```
"Visualize the dependency graph for project-X"
"What's the overall structure of my microservices?"
"Show me how components interact in repo-Y"
```

---

## 🛠️ Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Create MultiRepoManager component
- [ ] Implement GitHub API integration
- [ ] Set up multi-collection ChromaDB structure
- [ ] Basic repository cloning and metadata extraction

### Phase 2: Code Analysis (Week 3-4)
- [ ] Build CodeAnalyzer for Python files
- [ ] Implement AST parsing and function extraction
- [ ] Create intelligent code chunking
- [ ] Add support for JavaScript/TypeScript
- [ ] Implement dependency graph generation

### Phase 3: Enhanced Documentation (Week 5)
- [ ] Add Markdown processor
- [ ] Implement Jupyter notebook support
- [ ] Extract and link code comments
- [ ] Build code-to-doc reference system

### Phase 4: Multi-Repo Features (Week 6-7)
- [ ] Cross-repository search tools
- [ ] Repository comparison features
- [ ] Unified query interface
- [ ] Context aggregation across repos

### Phase 5: The Escher Loop (Week 8-9) 🎨
- [ ] Implement SelfAwarenessEngine
- [ ] Self-ingestion pipeline
- [ ] Self-query detection and routing
- [ ] Real-time self-monitoring
- [ ] Meta-documentation generation

### Phase 6: Advanced Features (Week 10+)
- [ ] Architecture visualization
- [ ] Code quality analysis
- [ ] Suggestion engine
- [ ] Multi-language support expansion
- [ ] Performance optimization

---

## 📊 Data Storage Structure

### Directory Layout
```
multi-repo-analyzer/
├── backend/
│   ├── multi_repo_manager.py       # New
│   ├── code_analyzer.py             # New
│   ├── self_awareness_engine.py    # New (Escher!)
│   ├── document_processor.py        # Enhanced
│   ├── vector_store.py              # Enhanced
│   ├── ai_generator.py              # Enhanced
│   ├── search_tools.py              # Enhanced
│   └── config.py
├── repos/                           # Cloned repositories
│   ├── project-1/
│   ├── project-2/
│   └── multi-repo-analyzer/        # SELF! (Escher loop)
├── chroma_db/                       # Vector storage
│   ├── repo_metadata/
│   ├── code_content/
│   ├── documentation/
│   └── self_analysis/              # Self-reference collection
├── frontend/
│   └── (Enhanced UI for multi-repo)
└── docs/
    └── (Auto-generated self-documentation)
```

---

## 🎨 The Escher Loop - Self-Awareness Features

### How It Works

1. **Self-Ingestion on Startup**
   ```python
   # In startup sequence
   self_awareness_engine.ingest_self()
   # System reads its own code into self_analysis collection
   ```

2. **Self-Query Detection**
   ```python
   # When user asks: "How do you process code?"
   if is_self_referential_query(query):
       return self_awareness_engine.explain_own_component(query)
   ```

3. **Real-Time Self-Monitoring**
   ```python
   # File watcher on own codebase
   on_file_change('backend/code_analyzer.py'):
       self_awareness_engine.update_self_knowledge()
   ```

4. **Meta-Documentation Generation**
   ```python
   # System generates its own documentation
   self_awareness_engine.generate_self_documentation()
   # Output: "I am a multi-repository analyzer that..."
   ```

### Example Self-Aware Interactions

**User**: "How do you analyze code?"
**System**: "I use my CodeAnalyzer component (backend/code_analyzer.py:45) which employs AST parsing. When you ask me to analyze a Python file, I parse it into an abstract syntax tree, extract functions starting at line 67, and chunk the code semantically..."

**User**: "Can you improve yourself?"
**System**: "Analyzing my own code... I notice my code_analyzer.py has high complexity in the parse_file function. I could refactor it into smaller methods. Would you like me to suggest specific improvements?"

**User**: "What happens when I ask you about yourself?"
**System**: "Great meta-question! When you query me about my own functionality, I detect it using self_awareness_engine.detect_self_query() (line 34), which routes to my self_analysis collection instead of regular code_content. This creates a recursive loop - I'm literally reading documentation about how I answer questions about myself!"

---

## 🔐 Security & Performance Considerations

### Security
- [ ] GitHub token encryption
- [ ] Repository access control
- [ ] Sanitize code before embedding
- [ ] Rate limiting on API calls
- [ ] Secrets detection in code

### Performance
- [ ] Incremental updates (only changed files)
- [ ] Lazy loading for large repositories
- [ ] Caching layer for frequent queries
- [ ] Parallel processing for multiple repos
- [ ] Embedding batch processing

### Scalability
- [ ] Support for 100+ repositories
- [ ] Efficient storage (deduplication)
- [ ] Query optimization
- [ ] Background sync jobs

---

## 🚀 Getting Started (Future)

```bash
# Install dependencies
uv sync

# Initialize the system
uv run python -m backend.multi_repo_manager init

# Add your first repository
uv run python -m backend.multi_repo_manager add-repo https://github.com/user/project1

# Enable self-analysis (Escher loop!)
uv run python -m backend.multi_repo_manager enable-self-awareness

# Start the server
uv run uvicorn app:app --reload

# Query across all repos
curl -X POST http://localhost:8000/api/query \
  -d '{"query": "How is authentication implemented?", "repos": ["all"]}'

# Ask the system about itself!
curl -X POST http://localhost:8000/api/query \
  -d '{"query": "How do you work?", "self_aware": true}'
```

---

## 📈 Success Metrics

- **Coverage**: % of code files successfully parsed and embedded
- **Query Accuracy**: Relevance of retrieved code snippets
- **Cross-Repo Insights**: Ability to find patterns across projects
- **Self-Awareness Depth**: Quality of self-explanations
- **Performance**: Query response time < 2 seconds
- **Scalability**: Support 50+ repos without degradation

---

## 🎯 Future Enhancements

1. **Code Generation**: Suggest code based on patterns from other repos
2. **Automated Refactoring**: System suggests improvements to your code
3. **Dependency Analysis**: Track library usage across all projects
4. **Security Scanning**: Find vulnerabilities across repos
5. **Learning from Self**: System improves its own algorithms based on usage
6. **Multi-User Support**: Team collaboration features
7. **Integration with IDEs**: VS Code / JetBrains plugins

---

## 🌀 The Ultimate Escher Loop

**The Vision**: A system that not only analyzes itself but **improves itself**

```
User asks: "How could you be better at analyzing Python code?"
    ↓
System analyzes its own CodeAnalyzer component
    ↓
System compares its implementation to best practices from analyzed repos
    ↓
System generates improved version of its own code
    ↓
System asks: "I've identified 3 improvements to my code analysis.
              Should I update myself?"
    ↓
User approves
    ↓
System modifies its own code
    ↓
System re-ingests its updated code
    ↓
System is now better at analyzing code (including itself!)
```

**This is the true "Drawing Hands" - a system that continuously improves by analyzing and modifying itself.**

---

*Design Version: 1.0*
*Date: 2025-11-10*
*Status: Proposal - Ready for Implementation*

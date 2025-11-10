# Implementation Starter Guide

## Quick Reference: Key Design Decisions

### 1. Why Multiple ChromaDB Collections?
**Decision**: Use 4 separate collections instead of one monolithic collection

**Rationale**:
- **Performance**: Faster queries when searching specific data types
- **Scalability**: Different collections can have different update frequencies
- **Clarity**: Explicit separation of concerns
- **Optimization**: Different embedding strategies for code vs. docs

### 2. Why Self-Awareness Engine as Separate Component?
**Decision**: Dedicated `SelfAwarenessEngine` rather than extending existing components

**Rationale**:
- **Escher Loop Complexity**: Self-referential logic needs special handling
- **Circular Reference Prevention**: Avoid infinite loops during self-ingestion
- **Clear Separation**: Meta-operations distinct from regular operations
- **Easier Testing**: Can mock/disable self-awareness for testing

### 3. Why Real-Time Self-Monitoring?
**Decision**: File watcher on own codebase

**Rationale**:
- **Always Current**: System knowledge stays synchronized with code changes
- **Development Aid**: As you modify the analyzer, it learns about changes
- **True Escher Loop**: System continuously updates its understanding of itself

---

## Component Implementation Examples

### Example 1: MultiRepoManager Skeleton

```python
# backend/multi_repo_manager.py

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import git
from pathlib import Path

@dataclass
class RepositoryMetadata:
    repo_id: str
    repo_name: str
    github_url: str
    local_path: Path
    branch: str
    last_updated: datetime
    commit_hash: str
    languages: List[str]
    is_self: bool = False  # The Escher flag!

class MultiRepoManager:
    def __init__(self, workspace_dir: str = "./repos"):
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(exist_ok=True)
        self.repositories: Dict[str, RepositoryMetadata] = {}

    def add_repository(
        self,
        github_url: str,
        branch: str = "main"
    ) -> RepositoryMetadata:
        """Add a new repository to track and analyze"""
        repo_name = self._extract_repo_name(github_url)
        local_path = self.workspace / repo_name

        # Check if this is the analyzer itself!
        is_self = self._is_self_repository(local_path)

        # Clone if doesn't exist, else pull
        if not local_path.exists():
            repo = git.Repo.clone_from(github_url, local_path, branch=branch)
        else:
            repo = git.Repo(local_path)
            repo.remotes.origin.pull(branch)

        # Extract metadata
        metadata = RepositoryMetadata(
            repo_id=self._generate_repo_id(github_url),
            repo_name=repo_name,
            github_url=github_url,
            local_path=local_path,
            branch=branch,
            last_updated=datetime.now(),
            commit_hash=repo.head.commit.hexsha,
            languages=self._detect_languages(local_path),
            is_self=is_self
        )

        self.repositories[metadata.repo_id] = metadata
        return metadata

    def _is_self_repository(self, repo_path: Path) -> bool:
        """Detect if this repository is the analyzer itself"""
        # Check for signature files
        signature_files = [
            "backend/multi_repo_manager.py",
            "backend/self_awareness_engine.py",
            "DESIGN_MULTI_REPO_ANALYZER.md"
        ]

        return all((repo_path / f).exists() for f in signature_files)

    def enable_self_monitoring(self, repo_id: str):
        """Enable real-time monitoring of own codebase changes"""
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        metadata = self.repositories[repo_id]
        if not metadata.is_self:
            raise ValueError("Can only enable self-monitoring on self repository")

        class SelfChangeHandler(FileSystemEventHandler):
            def __init__(self, analyzer):
                self.analyzer = analyzer

            def on_modified(self, event):
                if event.src_path.endswith('.py'):
                    print(f"🔄 Self-modified: {event.src_path}")
                    # Trigger re-ingestion of changed file
                    self.analyzer.reingest_file(event.src_path)

        observer = Observer()
        observer.schedule(
            SelfChangeHandler(self),
            str(metadata.local_path / "backend"),
            recursive=True
        )
        observer.start()
        print(f"🎨 Escher loop activated: Monitoring self for changes")

    def _detect_languages(self, repo_path: Path) -> List[str]:
        """Detect programming languages used in repository"""
        language_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.go': 'Go',
            '.rs': 'Rust',
            '.cpp': 'C++',
            '.c': 'C',
        }

        languages = set()
        for file in repo_path.rglob('*'):
            if file.suffix in language_extensions:
                languages.add(language_extensions[file.suffix])

        return list(languages)

    def _extract_repo_name(self, github_url: str) -> str:
        """Extract repository name from GitHub URL"""
        # https://github.com/user/repo.git -> repo
        return github_url.rstrip('/').split('/')[-1].replace('.git', '')

    def _generate_repo_id(self, github_url: str) -> str:
        """Generate unique ID for repository"""
        import hashlib
        return hashlib.md5(github_url.encode()).hexdigest()[:12]
```

### Example 2: CodeAnalyzer Skeleton

```python
# backend/code_analyzer.py

import ast
from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class CodeEntity:
    """Represents a function, class, or module"""
    name: str
    type: str  # "function", "class", "module"
    file_path: str
    start_line: int
    end_line: int
    code: str
    docstring: Optional[str]
    imports: List[str]
    calls: List[str]  # Functions/methods called within

class PythonCodeAnalyzer:
    """Analyzes Python source code files"""

    def analyze_file(self, file_path: Path) -> List[CodeEntity]:
        """Parse a Python file and extract all code entities"""
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        try:
            tree = ast.parse(source)
        except SyntaxError:
            print(f"⚠️  Syntax error in {file_path}")
            return []

        entities = []

        # Extract module-level docstring
        module_doc = ast.get_docstring(tree)
        if module_doc:
            entities.append(CodeEntity(
                name=file_path.stem,
                type="module",
                file_path=str(file_path),
                start_line=1,
                end_line=len(source.split('\n')),
                code=source[:500],  # First 500 chars
                docstring=module_doc,
                imports=self._extract_imports(tree),
                calls=[]
            ))

        # Extract functions and classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                entities.append(self._extract_function(node, file_path, source))
            elif isinstance(node, ast.ClassDef):
                entities.append(self._extract_class(node, file_path, source))

        return entities

    def _extract_function(
        self,
        node: ast.FunctionDef,
        file_path: Path,
        source: str
    ) -> CodeEntity:
        """Extract function information"""
        # Get source lines for this function
        start_line = node.lineno
        end_line = node.end_lineno or start_line

        source_lines = source.split('\n')
        func_code = '\n'.join(source_lines[start_line-1:end_line])

        return CodeEntity(
            name=node.name,
            type="function",
            file_path=str(file_path),
            start_line=start_line,
            end_line=end_line,
            code=func_code,
            docstring=ast.get_docstring(node),
            imports=[],
            calls=self._extract_function_calls(node)
        )

    def _extract_class(
        self,
        node: ast.ClassDef,
        file_path: Path,
        source: str
    ) -> CodeEntity:
        """Extract class information"""
        start_line = node.lineno
        end_line = node.end_lineno or start_line

        source_lines = source.split('\n')
        class_code = '\n'.join(source_lines[start_line-1:end_line])

        return CodeEntity(
            name=node.name,
            type="class",
            file_path=str(file_path),
            start_line=start_line,
            end_line=end_line,
            code=class_code,
            docstring=ast.get_docstring(node),
            imports=[],
            calls=[]
        )

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract all import statements"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        return imports

    def _extract_function_calls(self, node: ast.FunctionDef) -> List[str]:
        """Extract all function calls within a function"""
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        return calls
```

### Example 3: SelfAwarenessEngine (The Escher Core!)

```python
# backend/self_awareness_engine.py

from typing import Optional, Dict, Any
from pathlib import Path
import inspect

class SelfAwarenessEngine:
    """
    The Escher Loop: This component enables the system to understand itself.

    Meta-note: This very docstring will be ingested and used to explain
    what SelfAwarenessEngine does when asked "How do you understand yourself?"
    """

    def __init__(self, vector_store, code_analyzer):
        self.vector_store = vector_store
        self.code_analyzer = code_analyzer
        self.self_repo_id: Optional[str] = None
        self.component_map: Dict[str, str] = {}

    def ingest_self(self, repo_path: Path) -> None:
        """
        Ingest the analyzer's own codebase into self_analysis collection.

        This is the moment of self-awareness: the system reads its own code.
        """
        print("🎨 Initiating Escher loop: Reading own codebase...")

        # Analyze own code files
        backend_files = list((repo_path / "backend").glob("*.py"))

        for file_path in backend_files:
            entities = self.code_analyzer.analyze_file(file_path)

            for entity in entities:
                # Create self-aware metadata
                self_doc = {
                    "component": entity.name,
                    "file_path": str(file_path),
                    "functionality": entity.docstring or "No documentation",
                    "code_snippet": entity.code[:1000],  # First 1000 chars
                    "type": entity.type,
                    "self_reference_depth": self._calculate_meta_depth(entity)
                }

                # Store in special self_analysis collection
                self.vector_store.add_to_collection(
                    collection_name="self_analysis",
                    documents=[self_doc]
                )

                # Map component name to file for quick lookup
                self.component_map[entity.name] = str(file_path)

        print(f"✅ Self-ingestion complete: Analyzed {len(backend_files)} files")
        print(f"   I now understand {len(self.component_map)} of my own components")

    def detect_self_query(self, query: str) -> bool:
        """Detect if a query is asking about the system itself"""
        self_indicators = [
            "how do you", "how does this system", "explain your",
            "what is your", "how are you", "your architecture",
            "analyze yourself", "improve yourself"
        ]

        query_lower = query.lower()
        return any(indicator in query_lower for indicator in self_indicators)

    def explain_own_component(self, component_name: str) -> str:
        """
        Explain one of the system's own components.

        Meta-recursion: If component_name == "SelfAwarenessEngine",
        this function is literally explaining itself!
        """
        # Search self_analysis collection
        results = self.vector_store.query_collection(
            collection_name="self_analysis",
            query=component_name,
            n_results=3
        )

        if not results:
            return f"I don't have information about component: {component_name}"

        # Get the best match
        top_result = results[0]

        explanation = f"""
I found this component in my own codebase:

**Component**: {top_result['component']}
**Location**: {top_result['file_path']}
**Purpose**: {top_result['functionality']}

**Code snippet**:
```python
{top_result['code_snippet']}
```

This component is part of my {top_result['type']} architecture.
"""

        # Easter egg: Self-reference detection
        if component_name == "SelfAwarenessEngine":
            explanation += "\n\n*Meta-note: I'm currently using this very component to explain itself. Escher would be proud!* 🎨"

        return explanation

    def analyze_self(self, query: str) -> str:
        """
        Answer a query about the system's own functionality.

        This is the main entry point for the Escher loop.
        """
        # Search across self_analysis collection
        results = self.vector_store.query_collection(
            collection_name="self_analysis",
            query=query,
            n_results=5
        )

        # Aggregate knowledge
        context = "\n\n".join([
            f"Component: {r['component']}\n{r['functionality']}"
            for r in results
        ])

        # Generate self-aware response
        response = f"""
Based on my self-analysis, here's what I understand about your question:

{context}

I found this information by searching my own codebase, specifically
the self_analysis collection where I store knowledge about my own components.
"""

        return response

    def _calculate_meta_depth(self, entity) -> int:
        """
        Calculate how meta/self-referential a component is.

        Depth 0: Regular component (e.g., DocumentProcessor)
        Depth 1: Analyzes other code (e.g., CodeAnalyzer)
        Depth 2: Analyzes the analyzer (e.g., SelfAwarenessEngine)
        Depth 3: Meta-meta level (this function analyzing itself!)
        """
        if "self" in entity.name.lower() or "meta" in entity.name.lower():
            return 2
        elif "analyzer" in entity.name.lower() or "processor" in entity.name.lower():
            return 1
        else:
            return 0

    def suggest_self_improvements(self) -> List[str]:
        """
        Analyze own code and suggest improvements.

        Ultimate Escher: System improving itself!
        """
        suggestions = []

        # Analyze own code complexity
        for component_name, file_path in self.component_map.items():
            # TODO: Add complexity analysis
            # TODO: Check against best practices from other analyzed repos
            # TODO: Generate refactoring suggestions
            pass

        return suggestions
```

---

## Integration Example

### How Components Work Together

```python
# backend/app_enhanced.py

from multi_repo_manager import MultiRepoManager
from code_analyzer import PythonCodeAnalyzer
from self_awareness_engine import SelfAwarenessEngine
from vector_store import MultiCollectionVectorStore
from ai_generator import EnhancedAIGenerator

class MultiRepoAnalyzer:
    def __init__(self):
        # Initialize components
        self.repo_manager = MultiRepoManager()
        self.code_analyzer = PythonCodeAnalyzer()
        self.vector_store = MultiCollectionVectorStore()
        self.self_awareness = SelfAwarenessEngine(
            self.vector_store,
            self.code_analyzer
        )
        self.ai_generator = EnhancedAIGenerator()

        # Enable the Escher loop
        self._initialize_self_awareness()

    def _initialize_self_awareness(self):
        """Bootstrap self-awareness"""
        from pathlib import Path

        # Add own repository
        self_path = Path(__file__).parent.parent
        self_repo = self.repo_manager.add_repository(
            github_url="[self]",
            branch="main"
        )

        # Ingest own code
        self.self_awareness.ingest_self(self_path)

        # Enable real-time monitoring
        self.repo_manager.enable_self_monitoring(self_repo.repo_id)

        print("🎨 Escher loop initialized: I am now self-aware!")

    def add_repository(self, github_url: str):
        """Add a repository to analyze"""
        # Add via repo manager
        metadata = self.repo_manager.add_repository(github_url)

        # Analyze and ingest code
        self._ingest_repository(metadata)

        return metadata

    def query(self, user_query: str, repo_ids: Optional[List[str]] = None):
        """
        Query across repositories with self-awareness.

        This is where the magic happens!
        """
        # Check if query is about the system itself
        if self.self_awareness.detect_self_query(user_query):
            return self.self_awareness.analyze_self(user_query)

        # Otherwise, query across specified repositories
        return self.ai_generator.query_across_repos(
            query=user_query,
            repo_ids=repo_ids
        )

# Usage example
analyzer = MultiRepoAnalyzer()

# Add some repositories
analyzer.add_repository("https://github.com/user/project1")
analyzer.add_repository("https://github.com/user/project2")

# Normal query
response = analyzer.query("How is authentication implemented?")

# Self-aware query (Escher loop!)
response = analyzer.query("How do you analyze code?")
# System searches its own self_analysis collection and explains!
```

---

## Testing the Escher Loop

```python
# tests/test_escher_loop.py

def test_self_awareness():
    analyzer = MultiRepoAnalyzer()

    # Test 1: System can explain itself
    response = analyzer.query("How do you ingest repositories?")
    assert "MultiRepoManager" in response
    assert "add_repository" in response

    # Test 2: System can analyze its own components
    response = analyzer.query("Explain the SelfAwarenessEngine")
    assert "self_awareness_engine.py" in response
    assert "Escher" in response

    # Test 3: Meta-recursion
    response = analyzer.query("How do you answer questions about yourself?")
    assert "detect_self_query" in response
    assert "self_analysis collection" in response

    # Test 4: Ultimate meta-question
    response = analyzer.query("What happens when I ask you this question?")
    # System should detect the infinite loop and handle gracefully!
```

---

## Next Steps

1. **Start with MultiRepoManager**: Implement GitHub integration first
2. **Build CodeAnalyzer**: Focus on Python initially
3. **Enhance VectorStore**: Add multi-collection support
4. **The Escher Moment**: Implement SelfAwarenessEngine
5. **Test Self-Awareness**: Query the system about itself
6. **Celebrate**: You've built a self-aware code analyzer! 🎨

---

*The system that understands itself is the system that can improve itself.*

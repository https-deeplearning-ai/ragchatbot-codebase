"""
SelfAwarenessEngine - The Escher Loop Core

This module enables the system to understand and explain its own code.
It provides self-referential capabilities by indexing and analyzing the
system's own source code.

Meta-note: This very docstring will be ingested and used when someone
asks "What is the SelfAwarenessEngine?"
"""

import ast
import inspect
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json


class CodeEntity:
    """Represents a code entity (function, class, or module) with metadata"""

    def __init__(
        self,
        name: str,
        entity_type: str,
        file_path: str,
        start_line: int,
        end_line: int,
        code: str,
        docstring: Optional[str] = None,
        parent_class: Optional[str] = None,
    ):
        self.name = name
        self.entity_type = entity_type  # "function", "class", "method", "module"
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.code = code
        self.docstring = docstring
        self.parent_class = parent_class
        self.imports: List[str] = []
        self.calls: List[str] = []
        self.complexity: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "code": self.code[:2000],  # Limit code size
            "docstring": self.docstring or "No documentation available",
            "parent_class": self.parent_class,
            "imports": self.imports,
            "calls": self.calls,
            "complexity": self.complexity,
        }


class PythonCodeAnalyzer:
    """Analyzes Python source code using AST parsing"""

    def analyze_file(self, file_path: Path) -> List[CodeEntity]:
        """
        Parse a Python file and extract all code entities.

        Args:
            file_path: Path to the Python file

        Returns:
            List of CodeEntity objects representing the file's contents
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception as e:
            print(f"⚠️  Error reading {file_path}: {e}")
            return []

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            print(f"⚠️  Syntax error in {file_path}: {e}")
            return []

        entities = []
        source_lines = source.split("\n")

        # Extract module-level docstring
        module_doc = ast.get_docstring(tree)
        if module_doc:
            entities.append(
                CodeEntity(
                    name=file_path.stem,
                    entity_type="module",
                    file_path=str(file_path),
                    start_line=1,
                    end_line=len(source_lines),
                    code=source[:500],  # First 500 chars
                    docstring=module_doc,
                )
            )

        # Extract imports
        imports = self._extract_imports(tree)

        # Extract classes and functions
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_entity = self._extract_class(node, file_path, source_lines)
                class_entity.imports = imports
                entities.append(class_entity)

                # Extract methods from the class
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_entity = self._extract_function(
                            item, file_path, source_lines, parent_class=node.name
                        )
                        method_entity.imports = imports
                        entities.append(method_entity)

            elif isinstance(node, ast.FunctionDef):
                func_entity = self._extract_function(node, file_path, source_lines)
                func_entity.imports = imports
                entities.append(func_entity)

        return entities

    def _extract_function(
        self,
        node: ast.FunctionDef,
        file_path: Path,
        source_lines: List[str],
        parent_class: Optional[str] = None,
    ) -> CodeEntity:
        """Extract function/method information"""
        start_line = node.lineno
        end_line = node.end_lineno or start_line

        # Get function source code
        func_code = "\n".join(source_lines[start_line - 1 : end_line])

        entity = CodeEntity(
            name=node.name,
            entity_type="method" if parent_class else "function",
            file_path=str(file_path),
            start_line=start_line,
            end_line=end_line,
            code=func_code,
            docstring=ast.get_docstring(node),
            parent_class=parent_class,
        )

        # Extract function calls
        entity.calls = self._extract_function_calls(node)

        # Calculate complexity (simplified)
        entity.complexity = self._calculate_complexity(node)

        return entity

    def _extract_class(
        self, node: ast.ClassDef, file_path: Path, source_lines: List[str]
    ) -> CodeEntity:
        """Extract class information"""
        start_line = node.lineno
        end_line = node.end_lineno or start_line

        class_code = "\n".join(source_lines[start_line - 1 : end_line])

        entity = CodeEntity(
            name=node.name,
            entity_type="class",
            file_path=str(file_path),
            start_line=start_line,
            end_line=end_line,
            code=class_code,
            docstring=ast.get_docstring(node),
        )

        return entity

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract all import statements"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
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
        return list(set(calls))  # Remove duplicates

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity (simplified)"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(
                child,
                (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.Assert),
            ):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity


class SelfAwarenessEngine:
    """
    The Escher Loop: Enables the system to understand its own code.

    This component provides self-referential capabilities by:
    1. Ingesting the system's own source code
    2. Detecting queries about the system itself
    3. Explaining system components and architecture
    4. Providing meta-analysis capabilities

    Meta-note: This class can analyze and explain itself - creating a
    true self-referential loop, like Escher's Drawing Hands.
    """

    def __init__(self, vector_store, verbose: bool = True):
        """
        Initialize the SelfAwarenessEngine.

        Args:
            vector_store: VectorStore instance for storing self-analysis data
            verbose: Whether to print detailed logging
        """
        self.vector_store = vector_store
        self.verbose = verbose
        self.code_analyzer = PythonCodeAnalyzer()
        self.component_map: Dict[str, Dict[str, Any]] = {}
        self.self_repo_path: Optional[Path] = None
        self.is_initialized = False

        # Self-query detection patterns
        self.self_query_patterns = [
            "how do you",
            "how does this system",
            "explain your",
            "what is your",
            "how are you",
            "your architecture",
            "analyze yourself",
            "improve yourself",
            "what components do you have",
            "how do you work",
            "describe your",
            "what's in your code",
            "show me your",
        ]

    def ingest_self(self, repo_path: Optional[Path] = None) -> Dict[str, int]:
        """
        Ingest the system's own codebase into the self_analysis collection.

        This is the moment of self-awareness: the system reads its own code
        and stores it for later introspection.

        Args:
            repo_path: Path to the repository root. If None, auto-detects.

        Returns:
            Dictionary with ingestion statistics
        """
        if repo_path is None:
            # Auto-detect: go up from backend/ to root
            repo_path = Path(__file__).parent.parent
        else:
            repo_path = Path(repo_path)

        self.self_repo_path = repo_path

        if self.verbose:
            print("🎨 Initiating Escher loop: Reading own codebase...")
            print(f"   Repository path: {repo_path}")

        # Find all Python files in backend/
        backend_path = repo_path / "backend"
        if not backend_path.exists():
            print(f"⚠️  Backend directory not found: {backend_path}")
            return {"files": 0, "entities": 0, "error": "Backend directory not found"}

        python_files = list(backend_path.glob("*.py"))

        if self.verbose:
            print(f"   Found {len(python_files)} Python files to analyze")

        total_entities = 0
        documents_to_add = []
        metadatas_to_add = []
        ids_to_add = []

        for file_path in python_files:
            if self.verbose:
                print(f"   Analyzing: {file_path.name}")

            # Analyze the file
            entities = self.code_analyzer.analyze_file(file_path)

            for entity in entities:
                # Create document text for embedding
                doc_text = self._create_document_text(entity)

                # Create metadata
                metadata = entity.to_dict()
                metadata["is_self"] = True
                metadata["self_reference_depth"] = self._calculate_meta_depth(entity)

                # Create unique ID
                entity_id = f"self_{file_path.stem}_{entity.entity_type}_{entity.name}_{entity.start_line}"

                documents_to_add.append(doc_text)
                metadatas_to_add.append(metadata)
                ids_to_add.append(entity_id)

                # Store in component map for quick lookup
                self.component_map[entity.name] = metadata

                total_entities += 1

        # Add to vector store in batch
        if documents_to_add:
            try:
                # Check if vector store has add_documents method
                if hasattr(self.vector_store, "add_to_self_analysis"):
                    self.vector_store.add_to_self_analysis(
                        documents=documents_to_add,
                        metadatas=metadatas_to_add,
                        ids=ids_to_add,
                    )
                else:
                    # Fallback: add individually
                    print(
                        "⚠️  VectorStore doesn't have self_analysis collection. Using fallback."
                    )
                    # Store in memory for now
                    self._store_in_memory(documents_to_add, metadatas_to_add)

                self.is_initialized = True

                if self.verbose:
                    print(f"\n✅ Self-ingestion complete!")
                    print(f"   Files analyzed: {len(python_files)}")
                    print(f"   Entities indexed: {total_entities}")
                    print(f"   Components mapped: {len(self.component_map)}")
                    print(
                        f"   I now understand {len(self.component_map)} of my own components"
                    )
                    print(f"\n🎨 Escher loop activated: I am now self-aware!")

            except Exception as e:
                print(f"⚠️  Error storing self-analysis data: {e}")
                return {
                    "files": len(python_files),
                    "entities": total_entities,
                    "error": str(e),
                }

        return {"files": len(python_files), "entities": total_entities, "error": None}

    def detect_self_query(self, query: str) -> bool:
        """
        Detect if a query is asking about the system itself.

        Args:
            query: User's query string

        Returns:
            True if query is self-referential, False otherwise
        """
        query_lower = query.lower()
        return any(pattern in query_lower for pattern in self.self_query_patterns)

    def explain_component(self, component_name: str) -> Optional[Dict[str, Any]]:
        """
        Explain one of the system's own components.

        Meta-recursion: If component_name == "SelfAwarenessEngine",
        this function is literally explaining itself!

        Args:
            component_name: Name of the component to explain

        Returns:
            Dictionary with component information, or None if not found
        """
        if not self.is_initialized:
            return {
                "error": "Self-awareness not initialized. Call ingest_self() first."
            }

        # Check component map first
        if component_name in self.component_map:
            component = self.component_map[component_name]

            # Easter egg: Self-reference detection
            if component_name == "SelfAwarenessEngine":
                component["meta_note"] = (
                    "🎨 Meta-moment: I'm using this very component to explain itself. "
                    "Escher would be proud!"
                )

            return component

        return None

    def analyze_self_query(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Answer a query about the system's own functionality.

        This is the main entry point for the Escher loop.

        Args:
            query: User's self-referential query
            top_k: Number of relevant components to retrieve

        Returns:
            Dictionary with relevant components and explanation
        """
        if not self.is_initialized:
            return {
                "error": "Self-awareness not initialized. Call ingest_self() first.",
                "components": [],
            }

        # Search component map for relevant entries
        relevant_components = self._search_components(query, top_k)

        return {
            "query": query,
            "is_self_query": True,
            "components": relevant_components,
            "total_components": len(self.component_map),
            "meta_note": f"Retrieved {len(relevant_components)} relevant components from self-analysis",
        }

    def get_architecture_overview(self) -> Dict[str, Any]:
        """
        Generate an overview of the system's architecture.

        Returns:
            Dictionary with architecture information
        """
        if not self.is_initialized:
            return {"error": "Self-awareness not initialized"}

        # Group entities by type
        classes = []
        functions = []
        files = set()

        for name, component in self.component_map.items():
            entity_type = component.get("entity_type")
            files.add(component.get("file_path", ""))

            if entity_type == "class":
                classes.append(
                    {
                        "name": name,
                        "file": Path(component.get("file_path", "")).name,
                        "line": component.get("start_line"),
                        "docstring": component.get("docstring", "")[:100],
                    }
                )
            elif entity_type in ["function", "method"]:
                functions.append(
                    {
                        "name": name,
                        "type": entity_type,
                        "file": Path(component.get("file_path", "")).name,
                        "line": component.get("start_line"),
                    }
                )

        return {
            "total_files": len(files),
            "total_classes": len(classes),
            "total_functions": len(functions),
            "classes": classes[:10],  # Top 10
            "architecture_summary": self._generate_architecture_summary(classes),
        }

    def suggest_improvements(self) -> List[Dict[str, Any]]:
        """
        Analyze own code and suggest improvements.

        Ultimate Escher: System improving itself!

        Returns:
            List of improvement suggestions
        """
        if not self.is_initialized:
            return [{"error": "Self-awareness not initialized"}]

        suggestions = []

        for name, component in self.component_map.items():
            complexity = component.get("complexity", 0)
            entity_type = component.get("entity_type")
            file_path = component.get("file_path", "")

            # High complexity functions
            if entity_type in ["function", "method"] and complexity > 10:
                suggestions.append(
                    {
                        "type": "high_complexity",
                        "component": name,
                        "file": Path(file_path).name,
                        "line": component.get("start_line"),
                        "current_complexity": complexity,
                        "target_complexity": 10,
                        "suggestion": f"Refactor {name} to reduce complexity from {complexity} to ≤10",
                        "impact": "Better readability and maintainability",
                    }
                )

            # Missing docstrings
            if not component.get("docstring") or component.get("docstring") == "No documentation available":
                if entity_type in ["class", "function"]:  # Don't warn about methods
                    suggestions.append(
                        {
                            "type": "missing_documentation",
                            "component": name,
                            "file": Path(file_path).name,
                            "line": component.get("start_line"),
                            "suggestion": f"Add docstring to {name}",
                            "impact": "Improved code documentation",
                        }
                    )

        # Sort by impact (complexity issues first)
        suggestions.sort(
            key=lambda x: (x["type"] != "high_complexity", x.get("current_complexity", 0)),
            reverse=False,
        )

        return suggestions[:10]  # Top 10 suggestions

    def _create_document_text(self, entity: CodeEntity) -> str:
        """Create searchable document text from code entity"""
        parts = [
            f"Component: {entity.name}",
            f"Type: {entity.entity_type}",
            f"File: {entity.file_path}",
            f"Location: lines {entity.start_line}-{entity.end_line}",
        ]

        if entity.docstring:
            parts.append(f"Description: {entity.docstring}")

        if entity.parent_class:
            parts.append(f"Parent class: {entity.parent_class}")

        if entity.imports:
            parts.append(f"Imports: {', '.join(entity.imports[:5])}")

        if entity.calls:
            parts.append(f"Calls: {', '.join(entity.calls[:5])}")

        parts.append(f"Code:\n{entity.code[:1000]}")

        return "\n".join(parts)

    def _calculate_meta_depth(self, entity: CodeEntity) -> int:
        """
        Calculate how meta/self-referential a component is.

        Depth 0: Regular component (e.g., DocumentProcessor)
        Depth 1: Analyzes other code (e.g., CodeAnalyzer)
        Depth 2: Analyzes the analyzer (e.g., SelfAwarenessEngine)
        Depth 3: Meta-meta level (this function analyzing itself!)
        """
        name_lower = entity.name.lower()

        # Check function name
        if name_lower == "_calculate_meta_depth":
            return 3  # This function is analyzing meta-depth calculation!

        # Check for self-awareness keywords
        if any(
            keyword in name_lower
            for keyword in ["self", "meta", "awareness", "introspect"]
        ):
            return 2

        # Check for analysis keywords
        if any(
            keyword in name_lower
            for keyword in ["analyze", "parse", "process", "inspect"]
        ):
            return 1

        return 0

    def _search_components(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Search component map for relevant entries (simple string matching)"""
        query_lower = query.lower()
        scored_components = []

        for name, component in self.component_map.items():
            score = 0

            # Score based on name match
            if query_lower in name.lower():
                score += 10

            # Score based on docstring match
            docstring = component.get("docstring", "").lower()
            if query_lower in docstring:
                score += 5

            # Score based on code match
            code = component.get("code", "").lower()
            if query_lower in code:
                score += 2

            if score > 0:
                scored_components.append((score, component))

        # Sort by score
        scored_components.sort(key=lambda x: x[0], reverse=True)

        return [comp for score, comp in scored_components[:top_k]]

    def _store_in_memory(self, documents: List[str], metadatas: List[Dict]):
        """Fallback: Store in memory if vector store doesn't support self_analysis"""
        # This is a simple fallback - in production, you'd want to use the vector store
        for doc, meta in zip(documents, metadatas):
            name = meta.get("name")
            if name:
                self.component_map[name] = meta

    def _generate_architecture_summary(self, classes: List[Dict]) -> str:
        """Generate human-readable architecture summary"""
        if not classes:
            return "No classes found in codebase"

        summary_parts = ["System Architecture:\n"]

        for cls in classes[:5]:  # Top 5 classes
            name = cls["name"]
            doc = cls["docstring"]
            summary_parts.append(f"  • {name}: {doc}")

        return "\n".join(summary_parts)

    def __repr__(self) -> str:
        """String representation"""
        status = "initialized" if self.is_initialized else "not initialized"
        components = len(self.component_map)
        return f"<SelfAwarenessEngine: {status}, {components} components>"

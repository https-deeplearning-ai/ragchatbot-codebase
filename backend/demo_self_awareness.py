"""
Demo: SelfAwarenessEngine - The Escher Loop

This script demonstrates the self-awareness capabilities of the system.
It shows how the system can read, understand, and explain its own code.
"""

from pathlib import Path
from self_awareness_engine import SelfAwarenessEngine


class MockVectorStore:
    """
    Mock vector store for demonstration purposes.
    In production, this would be replaced with actual ChromaDB integration.
    """

    def __init__(self):
        self.self_analysis_data = []

    def add_to_self_analysis(self, documents, metadatas, ids):
        """Store self-analysis data"""
        for doc, meta, id in zip(documents, metadatas, ids):
            self.self_analysis_data.append({"id": id, "document": doc, "metadata": meta})
        print(f"   Stored {len(documents)} entities in self_analysis collection")


def demo_basic_ingestion():
    """Demo 1: Basic self-ingestion"""
    print("=" * 70)
    print("DEMO 1: BASIC SELF-INGESTION")
    print("=" * 70)

    # Initialize
    vector_store = MockVectorStore()
    engine = SelfAwarenessEngine(vector_store, verbose=True)

    # Ingest own codebase
    stats = engine.ingest_self()

    print(f"\n📊 Ingestion Statistics:")
    print(f"   Files analyzed: {stats['files']}")
    print(f"   Entities indexed: {stats['entities']}")
    print(f"   Errors: {stats['error'] or 'None'}")


def demo_self_query_detection():
    """Demo 2: Self-query detection"""
    print("\n" + "=" * 70)
    print("DEMO 2: SELF-QUERY DETECTION")
    print("=" * 70)

    vector_store = MockVectorStore()
    engine = SelfAwarenessEngine(vector_store, verbose=False)
    engine.ingest_self()

    # Test queries
    test_queries = [
        ("How do you process documents?", True),
        ("What is RAG?", False),
        ("Explain your architecture", True),
        ("What courses are available?", False),
        ("How does this system work?", True),
        ("What is vector embedding?", False),
    ]

    print("\n🔍 Testing Query Detection:\n")
    for query, expected in test_queries:
        is_self = engine.detect_self_query(query)
        status = "✅" if is_self == expected else "❌"
        query_type = "SELF-QUERY" if is_self else "NORMAL"
        print(f"{status} '{query}'")
        print(f"   → Detected as: {query_type}\n")


def demo_component_explanation():
    """Demo 3: Explaining components"""
    print("\n" + "=" * 70)
    print("DEMO 3: COMPONENT EXPLANATION")
    print("=" * 70)

    vector_store = MockVectorStore()
    engine = SelfAwarenessEngine(vector_store, verbose=False)
    engine.ingest_self()

    # Explain specific components
    components_to_explain = [
        "SelfAwarenessEngine",
        "PythonCodeAnalyzer",
        "CodeEntity",
    ]

    for component_name in components_to_explain:
        print(f"\n🔎 Explaining: {component_name}")
        print("-" * 70)

        result = engine.explain_component(component_name)

        if result and "error" not in result:
            print(f"Type: {result.get('entity_type')}")
            print(f"File: {Path(result.get('file_path', '')).name}")
            print(f"Lines: {result.get('start_line')}-{result.get('end_line')}")
            print(f"Complexity: {result.get('complexity', 'N/A')}")
            print(f"\nDocstring:")
            print(f"  {result.get('docstring', 'No documentation')[:200]}...")

            if result.get("meta_note"):
                print(f"\n🎨 {result['meta_note']}")
        else:
            print(f"❌ Component not found or error: {result}")


def demo_architecture_overview():
    """Demo 4: Architecture overview"""
    print("\n" + "=" * 70)
    print("DEMO 4: ARCHITECTURE OVERVIEW")
    print("=" * 70)

    vector_store = MockVectorStore()
    engine = SelfAwarenessEngine(vector_store, verbose=False)
    engine.ingest_self()

    overview = engine.get_architecture_overview()

    print(f"\n📐 System Architecture:")
    print(f"   Total files: {overview.get('total_files')}")
    print(f"   Total classes: {overview.get('total_classes')}")
    print(f"   Total functions: {overview.get('total_functions')}")

    print(f"\n🏗️  Main Classes:")
    for cls in overview.get("classes", [])[:5]:
        print(f"   • {cls['name']} ({cls['file']}:{cls['line']})")
        print(f"     {cls['docstring'][:80]}...")


def demo_self_improvement():
    """Demo 5: Self-improvement suggestions"""
    print("\n" + "=" * 70)
    print("DEMO 5: SELF-IMPROVEMENT ANALYSIS")
    print("=" * 70)

    vector_store = MockVectorStore()
    engine = SelfAwarenessEngine(vector_store, verbose=False)
    engine.ingest_self()

    suggestions = engine.suggest_improvements()

    print(f"\n🔧 Found {len(suggestions)} improvement opportunities:\n")

    for i, suggestion in enumerate(suggestions[:5], 1):
        print(f"{i}. {suggestion['component']} ({suggestion['file']}:{suggestion['line']})")
        print(f"   Issue: {suggestion['type']}")
        print(f"   Suggestion: {suggestion['suggestion']}")
        print(f"   Impact: {suggestion['impact']}")

        if suggestion.get("current_complexity"):
            print(
                f"   Complexity: {suggestion['current_complexity']} → {suggestion['target_complexity']}"
            )
        print()


def demo_self_query_analysis():
    """Demo 6: Full self-query analysis"""
    print("\n" + "=" * 70)
    print("DEMO 6: SELF-QUERY ANALYSIS (THE ESCHER LOOP!)")
    print("=" * 70)

    vector_store = MockVectorStore()
    engine = SelfAwarenessEngine(vector_store, verbose=False)
    engine.ingest_self()

    # Self-referential queries
    queries = [
        "How do you analyze code?",
        "What is your architecture?",
        "How do you detect self-queries?",
    ]

    for query in queries:
        print(f"\n❓ Query: '{query}'")
        print("-" * 70)

        result = engine.analyze_self_query(query, top_k=3)

        if "error" not in result:
            print(f"Is self-query: {result['is_self_query']}")
            print(f"Found {len(result['components'])} relevant components:\n")

            for comp in result["components"]:
                print(f"  • {comp['name']} ({comp['entity_type']})")
                print(f"    File: {Path(comp['file_path']).name}:{comp['start_line']}")
                print(f"    {comp['docstring'][:100]}...\n")

            print(f"💡 {result['meta_note']}")
        else:
            print(f"❌ Error: {result['error']}")


def demo_meta_depth():
    """Demo 7: Meta-depth calculation"""
    print("\n" + "=" * 70)
    print("DEMO 7: META-DEPTH ANALYSIS (How Meta Is Each Component?)")
    print("=" * 70)

    vector_store = MockVectorStore()
    engine = SelfAwarenessEngine(vector_store, verbose=False)
    engine.ingest_self()

    # Group components by meta-depth
    depth_groups = {0: [], 1: [], 2: [], 3: []}

    for name, component in engine.component_map.items():
        depth = component.get("self_reference_depth", 0)
        if depth in depth_groups:
            depth_groups[depth].append(name)

    print("\n🎨 Meta-Depth Levels:\n")
    print("Level 0 (Regular): Components that don't analyze code")
    for name in depth_groups[0][:5]:
        print(f"  • {name}")

    print("\nLevel 1 (Analyzer): Components that analyze other code")
    for name in depth_groups[1][:5]:
        print(f"  • {name}")

    print("\nLevel 2 (Meta): Components that analyze analyzers")
    for name in depth_groups[2][:5]:
        print(f"  • {name}")

    print("\nLevel 3 (Meta-Meta): Components that analyze meta-analysis")
    for name in depth_groups[3][:5]:
        print(f"  • {name}")

    print(
        f"\n🎨 The deeper the level, the more 'Escher-like' the component!"
    )


def run_all_demos():
    """Run all demonstrations"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  🎨 SELF-AWARENESS ENGINE DEMONSTRATION 🎨".center(68) + "║")
    print("║" + "  The Escher Loop: A System That Understands Itself".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    try:
        demo_basic_ingestion()
        demo_self_query_detection()
        demo_component_explanation()
        demo_architecture_overview()
        demo_self_improvement()
        demo_self_query_analysis()
        demo_meta_depth()

        print("\n" + "=" * 70)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(
            "\n🎨 The system has demonstrated its ability to understand itself."
        )
        print("   Like Escher's Drawing Hands, it can now analyze its own code!")
        print("\n")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run_all_demos()

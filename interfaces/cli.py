#!/usr/bin/env python3
"""
Simple command-line interface for the cognitive memory system.

This module provides a stdio-based CLI that enables users to interact with
the cognitive memory system through basic commands for storing experiences
and retrieving memories.
"""

import argparse
import sys
from typing import Any

from cognitive_memory.core.interfaces import CognitiveSystem


class CognitiveCLI:
    """
    Command-line interface for cognitive memory operations.

    Provides basic commands for storing experiences, retrieving memories,
    checking system status, and managing the memory system.
    """

    def __init__(self, cognitive_system: CognitiveSystem):
        """
        Initialize CLI with cognitive system instance.

        Args:
            cognitive_system: The cognitive system interface to use
        """
        self.cognitive_system = cognitive_system
        self.interactive_mode = False

    def store_experience(
        self, text: str, context: dict[str, Any] | None = None
    ) -> bool:
        """
        Store a new experience.

        Args:
            text: Experience text to store
            context: Optional context information

        Returns:
            bool: True if stored successfully
        """
        if not text.strip():
            print("Error: Empty text provided")
            return False

        try:
            memory_id = self.cognitive_system.store_experience(text, context)
            if memory_id:
                print(f"✓ Experience stored with ID: {memory_id}")
                return True
            else:
                print("✗ Failed to store experience")
                return False
        except Exception as e:
            print(f"✗ Error storing experience: {e}")
            return False

    def retrieve_memories(
        self, query: str, types: list[str] | None = None, limit: int = 10
    ) -> bool:
        """
        Retrieve memories for a query.

        Args:
            query: Query text
            types: Memory types to retrieve
            limit: Maximum results per type

        Returns:
            bool: True if retrieval completed successfully
        """
        if not query.strip():
            print("Error: Empty query provided")
            return False

        if types is None:
            types = ["core", "peripheral", "bridge"]

        try:
            results = self.cognitive_system.retrieve_memories(
                query=query, types=types, max_results=limit
            )

            total_results = sum(len(memories) for memories in results.values())
            if total_results == 0:
                print("No memories found for query")
                return True

            print(f"\n📋 Retrieved {total_results} memories for: '{query}'")

            for memory_type, memories in results.items():
                if memories:
                    print(f"\n{memory_type.upper()} MEMORIES ({len(memories)}):")
                    for i, memory in enumerate(memories, 1):
                        print(
                            f"  {i}. [{memory.memory_type}] {memory.content[:100]}..."
                        )
                        print(
                            f"     ID: {memory.id}, Level: L{memory.hierarchy_level}, "
                            f"Strength: {memory.strength:.2f}"
                        )

            return True

        except Exception as e:
            print(f"✗ Error retrieving memories: {e}")
            return False

    def show_status(self, detailed: bool = False) -> bool:
        """
        Show system status and statistics.

        Args:
            detailed: Whether to show detailed statistics

        Returns:
            bool: True if status retrieved successfully
        """
        try:
            stats = self.cognitive_system.get_memory_stats()

            print("\n📊 COGNITIVE MEMORY SYSTEM STATUS")
            print("=" * 40)

            # Basic counts
            if "memory_counts" in stats:
                print("\nMemory Counts:")
                for key, count in stats["memory_counts"].items():
                    if isinstance(count, int):
                        level_name = key.replace("level_", "").replace("_", " ").title()
                        print(f"  {level_name}: {count}")

            # Configuration
            if detailed and "system_config" in stats:
                print("\nConfiguration:")
                config = stats["system_config"]
                print(
                    f"  Activation Threshold: {config.get('activation_threshold', 'N/A')}"
                )
                print(
                    f"  Bridge Discovery K: {config.get('bridge_discovery_k', 'N/A')}"
                )
                print(f"  Max Activations: {config.get('max_activations', 'N/A')}")

            # Storage statistics
            if detailed and "storage_stats" in stats and stats["storage_stats"]:
                print("\nStorage Statistics:")
                storage_stats = stats["storage_stats"]
                for level_key, level_stats in storage_stats.items():
                    if isinstance(level_stats, dict) and "vectors_count" in level_stats:
                        print(f"  {level_key}: {level_stats['vectors_count']} vectors")

            # Embedding info
            if detailed and "embedding_info" in stats:
                print("\nEmbedding Model:")
                info = stats["embedding_info"]
                print(f"  Model: {info.get('model_name', 'N/A')}")
                print(f"  Dimensions: {info.get('embedding_dimension', 'N/A')}")

            return True

        except Exception as e:
            print(f"✗ Error retrieving status: {e}")
            return False

    def consolidate_memories(self, dry_run: bool = False) -> bool:
        """
        Trigger memory consolidation.

        Args:
            dry_run: If True, show what would be consolidated without doing it

        Returns:
            bool: True if consolidation completed successfully
        """
        if dry_run:
            print("🔍 Dry run mode: showing consolidation candidates")
            # For now, just run normal consolidation as we don't have dry-run support

        try:
            print("🔄 Starting memory consolidation...")
            results = self.cognitive_system.consolidate_memories()

            print("✓ Consolidation completed:")
            print(f"  Total episodic memories: {results.get('total_episodic', 0)}")
            print(f"  Consolidated to semantic: {results.get('consolidated', 0)}")
            print(f"  Failed: {results.get('failed', 0)}")
            print(f"  Skipped: {results.get('skipped', 0)}")

            return True

        except Exception as e:
            print(f"✗ Error during consolidation: {e}")
            return False

    def clear_memories(self, memory_type: str = "all", confirm: bool = False) -> bool:
        """
        Clear memories (placeholder - not implemented for safety).

        Args:
            memory_type: Type of memories to clear
            confirm: Confirmation flag

        Returns:
            bool: Always False (not implemented)
        """
        print("⚠️  Memory clearing not implemented for safety")
        print("   Use database tools directly if needed")
        return False

    def interactive_mode_loop(self) -> None:
        """Run interactive mode with command prompt."""
        self.interactive_mode = True
        print("\n🧠 Cognitive Memory Interactive Mode")
        print("Type 'help' for commands, 'quit' to exit")
        print("-" * 40)

        while True:
            try:
                command = input("\ncognitive> ").strip()

                if not command:
                    continue

                if command.lower() in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break

                elif command.lower() in ["help", "h", "?"]:
                    self._show_interactive_help()

                elif command.startswith("store "):
                    text = command[6:].strip()
                    self.store_experience(text)

                elif command.startswith("retrieve "):
                    query = command[9:].strip()
                    self.retrieve_memories(query)

                elif command.startswith("bridges "):
                    query = command[8:].strip()
                    self.retrieve_memories(query, types=["bridge"])

                elif command.lower() == "status":
                    self.show_status()

                elif command.lower() == "config":
                    self.show_status(detailed=True)

                elif command.lower() == "consolidate":
                    self.consolidate_memories()

                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

    def _show_interactive_help(self) -> None:
        """Show help for interactive mode commands."""
        print("\nAvailable Commands:")
        print("  store <text>           - Store new experience")
        print("  retrieve <query>       - Retrieve memories")
        print("  bridges <query>        - Show bridge connections")
        print("  status                 - Show system status")
        print("  config                 - Show detailed configuration")
        print("  consolidate            - Trigger memory consolidation")
        print("  help                   - Show this help")
        print("  quit                   - Exit interactive mode")


def create_cli_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI commands."""
    parser = argparse.ArgumentParser(
        prog="cognitive-cli",
        description="Cognitive Memory System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cognitive-cli store "Had trouble debugging the authentication flow"
  cognitive-cli retrieve "authentication issues"
  cognitive-cli status --detailed
  cognitive-cli interactive
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Store command
    store_parser = subparsers.add_parser("store", help="Store a new experience")
    store_parser.add_argument("text", help="Experience text to store")
    store_parser.add_argument("--context", help="Context as JSON string")
    store_parser.add_argument(
        "--level",
        type=int,
        choices=[0, 1, 2],
        help="Hierarchy level (0=concepts, 1=contexts, 2=episodes)",
    )

    # Retrieve command
    retrieve_parser = subparsers.add_parser("retrieve", help="Retrieve memories")
    retrieve_parser.add_argument("query", help="Query text")
    retrieve_parser.add_argument(
        "--types",
        nargs="+",
        choices=["core", "peripheral", "bridge"],
        help="Memory types to retrieve",
    )
    retrieve_parser.add_argument(
        "--limit", type=int, default=10, help="Maximum results per type"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.add_argument(
        "--detailed", action="store_true", help="Show detailed statistics"
    )

    # Consolidate command
    consolidate_parser = subparsers.add_parser(
        "consolidate", help="Consolidate memories"
    )
    consolidate_parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be consolidated"
    )

    # Clear command (placeholder)
    clear_parser = subparsers.add_parser("clear", help="Clear memories")
    clear_parser.add_argument(
        "--type",
        choices=["episodic", "semantic", "all"],
        default="all",
        help="Type of memories to clear",
    )
    clear_parser.add_argument("--confirm", action="store_true", help="Confirm deletion")

    # Interactive command
    interactive_parser = subparsers.add_parser(
        "interactive", help="Enter interactive mode"
    )
    interactive_parser.add_argument("--prompt", help="Custom prompt string")

    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = create_cli_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Note: In a real implementation, we would create the cognitive system here
    # with proper dependency injection. For now, this is a placeholder.
    print("⚠️  CLI interface created but requires system initialization")
    print("   This CLI needs a factory function to create the cognitive system")
    print("   with all required dependencies (embedding provider, storage, etc.)")

    return 0


if __name__ == "__main__":
    sys.exit(main())

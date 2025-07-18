# Git Integration Architecture Plan

## Executive Overview

This document specifies the architecture for integrating git repository history analysis into the cognitive memory system. The integration leverages the existing MemoryLoader interface to store git commits directly as cognitive memories, enabling LLMs to automatically understand development history, file relationships, and project evolution.

**Key Features:**
- **Direct Commit Storage**: Stores each git commit as a cognitive memory with full metadata
- **File Change Tracking**: Preserves detailed file change information (additions, deletions, modifications)
- **Memory Integration**: Commits stored as cognitive memories using the existing MemoryLoader interface
- **Incremental Loading**: Automatic state tracking with memory-based incremental updates (default behavior)
- **Real-time Integration**: Git hook support for automatic memory creation on commit
- **Project Isolation**: Docker container integration for project-specific memory systems

## Core Components

### 1. GitHistoryLoader
**Responsibility**: Load git commits as cognitive memories from git repository history
- Implements the existing `MemoryLoader` interface
- Uses CommitLoader to convert git commits to CognitiveMemory objects
- Transforms git commit data into memory objects with deterministic IDs
- **Supports both full repository analysis and incremental updates with automatic state tracking**

**Key Dependencies**:
- CommitLoader (commit to memory conversion)
- GitHistoryMiner (data extraction)
- Existing CognitiveConfig
- SQLite persistence for incremental state tracking

**Memory Architecture**:
- Uses deterministic commit IDs: `git::commit::<commit_hash>`
- Each commit becomes one memory with full metadata
- File changes embedded in memory content as natural language
- **Automatic incremental loading based on existing SQLite state**

**Incremental Features**:
- `get_latest_processed_commit()` queries SQLite for most recent commit
- Memory-based state tracking using existing deterministic IDs
- Graceful fallback to full history when incremental state is unavailable
- `force_full_load` parameter for explicit full repository reprocessing

### 2. GitHistoryMiner
**Responsibility**: Raw data extraction from git repository
- Execute git commands to gather commit history
- Parse commit data, file changes, and timestamps
- Return structured Commit objects with FileChange details
- **Supports incremental extraction via `since_commit` parameter**

**Output Data Structures**:
- Commit: commit_hash, message, author, timestamp, files_changed list
- FileChange: file_path, change_type, lines_added, lines_deleted

**Incremental Capabilities**:
- `since_commit` parameter for efficient incremental traversal
- Git revision range syntax: `{since_commit}..HEAD`
- Commit hash validation with format checking (SHA-1, SHA-256)
- Cross-branch commit references supported
- All existing security limits maintained

### 3. CommitLoader
**Responsibility**: Transform git commits into cognitive memories
- Convert Commit objects to CognitiveMemory format
- Generate natural language descriptions of commits
- Embed file change information in memory content
- Assign appropriate hierarchy levels and importance scores

**Memory Content Generation**:
- Commit Summary: Natural language description of commit purpose
- File Changes: Detailed list of modified files with change types
- Context Information: Author, timestamp, commit message integration

### 4. Security and Validation
**Responsibility**: Ensure safe processing of git data
- Validate commit hashes, file paths, and metadata
- Sanitize input data to prevent injection attacks
- Limit data sizes to prevent memory exhaustion
- Filter sensitive information from commit content


## Data Flow Architecture

### Complete Data Flow
```
Git Repository (.git/)
        ↓
GitHistoryLoader.get_latest_processed_commit() [SQLite state check]
        ↓
GitHistoryMiner.extract_commit_history(since_commit=latest_hash)
        ↓
List[Commit] with FileChange details (incremental)
        ↓
CommitLoader.convert_to_memories()
        ↓
Commit Descriptions (natural language text with metadata)
        ↓
GitHistoryLoader.load_from_source()
        ↓
List[CognitiveMemory] with embedded commit data
        ↓
CognitiveSystem.load_memories_from_source()
        ↓
Existing Memory Pipeline:
• Multi-dimensional encoding (Sentence-BERT + dimensions)
• Hierarchical storage (Qdrant L0/L1/L2 collections)
• Connection extraction and storage (SQLite)
• Indexing and retrieval preparation
```

### Integration-Specific Data Flow

**Repository Loading:**
```
CLI Command: ./scripts/load_project_content.sh --git-only
        ↓
GitHistoryLoader instantiation
        ↓
GitHistoryLoader.validate_source() [verify .git exists]
        ↓
GitHistoryLoader.load_from_source() [incremental by default]
        ├── get_latest_processed_commit() [SQLite state check]
        ├── extract_commit_history(since_commit=latest) [if state exists]
        └── extract_commit_history() [full history if no state]
        ↓
CognitiveSystem.load_memories_from_source() [existing]
        ↓
Memories stored with deterministic IDs in Qdrant + SQLite [existing]
        ↓
Available for retrieval via existing interfaces [existing]
```

**Real-time Git Hook Integration:**
```
Git Commit (post-commit hook)
        ↓
Docker Container Detection [project-specific]
        ↓
memory_system load-git incremental --max-commits=1
        ↓
GitHistoryLoader.load_from_source() [single commit processing]
        ↓
New commit memory created and stored
        ↓
Available immediately for MCP tool retrieval
```

## Key Methods and Responsibilities

### GitHistoryLoader Methods

**validate_source(source_path: str) -> bool**
- Must verify source_path contains a .git directory
- Must check git repository accessibility
- Must return boolean validation result

**load_from_source(source_path: str, **kwargs) -> List[CognitiveMemory]**
- Must extract git commits from repository (incremental by default)
- **Automatically detects existing processed commits via SQLite state**
- Must convert commits to CognitiveMemory objects with deterministic IDs
- Must embed commit metadata in natural language content
- Must assign appropriate hierarchy levels (L1 for significant commits, L2 for routine commits)
- Must return list compatible with existing memory pipeline
- **Supports `force_full_load` parameter to bypass incremental behavior**

**get_latest_processed_commit(repo_path: str) -> tuple[str, datetime] | None**
- **Queries SQLite memories for most recent git commit**
- **Extracts commit hash from deterministic memory IDs**
- **Returns (commit_hash, timestamp) for incremental loading**
- **Handles edge cases (no existing memories, corrupted state)**

**get_supported_extensions() -> List[str]**
- Must return empty list (git repos don't have file extensions)

**extract_connections(memories: List[CognitiveMemory]) -> List[tuple]**
- Must identify relationships between git pattern memories
- Must return connection tuples in existing format

### GitHistoryMiner Methods

**extract_commit_history(since_commit: str | None = None, max_commits: int = 1000, ...) -> Iterator[Commit]**
- Must execute git log commands to gather commit data
- **Supports incremental extraction via `since_commit` parameter**
- **Uses git revision range syntax: `{since_commit}..HEAD`**
- Must parse commit messages, file changes, and metadata
- Must filter commits by time window and relevance (when not using since_commit)
- Must include detailed file change information (lines added/deleted)
- **Maintains existing max_commits safety limits in incremental mode**

**_validate_commit_hash(commit_hash: str) -> bool**
- **Validates that commit hash exists in repository**
- **Supports SHA-1 (40 char) and SHA-256 (64 char) formats**
- **Handles whitespace and mixed-case input**
- **Cross-branch commit references supported**

**parse_commit_data(raw_commit: str) -> Commit**
- Must parse git log output into structured Commit objects
- Must extract author, timestamp, hash, and message
- Must parse file changes with change types and line counts

**validate_and_sanitize(commit: Commit) -> Commit**
- Must validate commit hash format and data integrity
- Must sanitize commit messages and file paths
- Must enforce size limits on commit data

### CommitLoader Methods

**convert_to_memories(commits: List[Commit]) -> List[CognitiveMemory]**
- Must convert each commit to a CognitiveMemory object
- Must generate natural language descriptions of commits
- Must embed file change details in memory content
- Must assign hierarchy levels based on commit significance
- Must create deterministic memory IDs from commit hashes

**generate_commit_description(commit: Commit) -> str**
- Must create readable description of commit purpose
- Must include file changes and their types
- Must embed metadata (author, timestamp) naturally
- Must make content searchable through existing retrieval

**assess_commit_importance(commit: Commit) -> float**
- Must calculate importance score based on files changed
- Must consider commit message indicators (fix, feature, refactor)
- Must account for file change volume and scope
- Must assign appropriate hierarchy level (L0/L1/L2)

### Security and Validation Methods

**validate_repository_path(repo_path: str) -> bool**
- Must verify the path contains a valid git repository
- Must check for .git directory existence
- Must validate path safety and accessibility

**sanitize_git_data(data: str) -> str**
- Must remove potentially harmful characters
- Must limit string lengths to prevent memory issues
- Must preserve essential git information while ensuring safety

**validate_commit_hash(hash_str: str) -> bool**
- Must verify commit hash format (40-character hex)
- Must check for valid git hash patterns
- Must reject malformed or suspicious hashes

## System Structure

### File Organization
```
cognitive_memory/
├── loaders/
│   ├── __init__.py                    # Add GitHistoryLoader export
│   ├── markdown_loader.py             # Existing
│   └── git_loader.py                  # GitHistoryLoader implementation
└── git_analysis/                      # Git analysis module
    ├── __init__.py
    ├── commit.py                      # Commit and FileChange data classes
    ├── commit_loader.py               # CommitLoader for memory conversion
    ├── history_miner.py               # GitHistoryMiner for data extraction
    └── security.py                    # Security validation and sanitization
```

### Memory Content Embedding Strategy

Since the system embeds all commit information into memory content text rather than separate metadata fields, git commits must be embedded as natural language:

**Commit Memory Embedding**:
```
"Git commit abc1234 by John Doe on 2024-01-15: 'Fix authentication timeout in Redis connection'. Modified 3 files: auth/middleware.py (15 lines added, 3 deleted), auth/config.py (8 lines added, 2 deleted), tests/test_auth.py (25 lines added). This commit addresses timeout issues by increasing Redis connection pool size and adjusting timeout parameters."
```

**Feature Commit Embedding**:
```
"Git commit def5678 by Jane Smith on 2024-01-16: 'Add user profile caching system'. Created 2 files, modified 4 files: users/cache.py (156 lines added), users/models.py (12 lines added, 4 deleted), users/views.py (23 lines added, 8 deleted), users/serializers.py (18 lines added), settings/base.py (3 lines added), requirements.txt (1 line added). This feature commit introduces Redis-based caching for user profiles to improve API response times."
```

**Bug Fix Commit Embedding**:
```
"Git commit ghi9012 by Bob Wilson on 2024-01-17: 'Fix memory leak in background tasks'. Modified 1 file: tasks/background.py (8 lines added, 15 deleted). This bug fix resolves memory accumulation by properly closing database connections in background task workers."
```

## Git Hook Architecture

### Overview
Git hooks provide automatic memory creation on commit, enabling real-time project memory building without manual intervention. The architecture uses embedded Python hooks for cross-platform compatibility and direct integration with the cognitive memory system.

### Hook Components

**Hook Installation System**:
- **Command Interface**: `heimdall git-hook install/uninstall/status`
- **Embedded Templates**: Post-commit hook script embedded in CLI commands (no external file dependencies)
- **Safe Installation**: Automatic backup and chaining of existing hooks
- **Cross-Platform**: Pure Python implementation works on Windows/macOS/Linux

**Hook Execution Flow**:
```
Git Commit
    ↓
Post-commit hook triggered (.git/hooks/post-commit)
    ↓
Embedded Python script execution
    ├── Repository validation (GitPython)
    ├── Project initialization check (Qdrant collections exist)
    ├── Cognitive system initialization
    └── Incremental git loading (max_commits=1)
    ↓
Latest commit processed and stored
    ↓
Colored console output + log file (.heimdall/monitor.log)
    ↓
Git operation completes (hook always exits 0)
```

**Data Flow Architecture**:
```
New Git Commit (abc1234)
    ↓
Hook Script (.git/hooks/post-commit)
    ↓
get_project_paths(repo_root) → .heimdall/monitor.log
    ↓
initialize_system() → CognitiveOperations
    ↓
operations.load_git_patterns(max_commits=1)
    ↓
GitHistoryLoader.load_from_source() [incremental mode]
    ↓
Single commit → CognitiveMemory object
    ↓
Multi-dimensional encoding + Qdrant storage
    ↓
Hook output: "Processed commit abc1234: 1 memory loaded"
```

### Hook Safety Features

**Git Operation Safety**:
- **Never fails commits**: Always exits with code 0 regardless of memory processing success
- **Graceful degradation**: Continues if Qdrant unavailable or project uninitialized
- **Timeout protection**: 5-minute execution limit prevents hanging
- **Error isolation**: Memory processing errors don't affect git operations

**Existing Hook Preservation**:
- **Backup and chain**: Existing hooks moved to `.heimdall-backup` and executed first
- **Safe uninstallation**: Original hooks restored from backup during removal
- **Force installation**: `--force` flag creates chained hooks preserving existing functionality

**Project Integration**:
- **Project-specific**: Each repository gets isolated memory collections
- **Automatic detection**: Uses `get_project_id()` from repository path for collection naming
- **Initialization check**: Verifies Qdrant connection and project collections exist
- **Helpful errors**: Clear messages when project needs `heimdall project init`

### Hook Management Commands

**Installation**:
```bash
# Install in current repository
heimdall git-hook install

# Install with existing hook chaining
heimdall git-hook install --force

# Preview installation
heimdall git-hook install --dry-run
```

**Status and Maintenance**:
```bash
# Check hook status
heimdall git-hook status

# Remove hook (restore original if exists)
heimdall git-hook uninstall

# Preview uninstallation
heimdall git-hook uninstall --dry-run
```

**Integration with Project Workflow**:
```bash
# Complete project setup
cd /path/to/project
heimdall project init          # Create collections + start Qdrant
heimdall git-hook install      # Enable automatic memory creation
git commit -m "Test"          # Hook automatically processes commit
```

### Hook Implementation Details

**Embedded Script Architecture**:
- **Template Storage**: Hook script stored as string constant in `git_hook_commands.py`
- **Dynamic Creation**: Script written to `.git/hooks/heimdall_post_commit_hook.py` on install
- **Symlink Strategy**: Main hook file symlinks to generated script for easy updates
- **Package Independence**: No external file dependencies, works after pip install

**Error Handling and Logging**:
- **Colored Output**: Green for success, blue for info, red for errors during commit
- **File Logging**: All activity logged to `.heimdall/monitor.log` with timestamps
- **Silent Operation**: Verbose system logging suppressed during hook execution
- **Contextual Messages**: Specific guidance for common issues (Qdrant not running, project not initialized)

**Performance Characteristics**:
- **Execution Time**: 2-5 seconds per commit for single commit processing
- **Resource Usage**: Minimal memory footprint, only processes latest commit
- **Startup Cost**: One-time cognitive system initialization per hook execution
- **Storage Efficiency**: Incremental storage, no duplicate commit processing

## Integration Benefits

### For LLM Context Enhancement
- Automatic access to complete development history during debugging
- Understanding of file evolution and change patterns over time
- Context about when and why specific changes were made
- Enhanced understanding of codebase architecture through commit history
- Direct access to actual development decisions and rationales
- **Real-time memory creation via git hooks for continuous context building**

### For Development Workflow
- Zero-configuration commit history access from existing git repository
- Integration with existing memory retrieval mechanisms
- Compatibility with current CLI and MCP interfaces
- Batch loading via project scripts
- Real commit data instead of derived statistical patterns
- **Incremental loading by default - only process new commits**
- **Git hook integration for automatic memory creation on commit**
- **Docker container integration for project-specific memory isolation**

### Performance Improvements
- **Before**: Full git history reprocessed every time (O(n) where n = total commits)
- **After**: Only new commits processed (O(1) per hook execution)
- **Hook execution**: ~3-5 seconds per commit vs potentially minutes for full history
- **Memory usage**: Constant per commit vs growing with repository size

## Immutable Memory Architecture

### Commit Identity and Storage
Git commits are **immutable historical records** that provide stable memories:

**Deterministic Commit IDs:**
```python
# Commit memories
memory_id = f"git::commit::{commit_hash}"

# File-based grouping for retrieval
file_tag = f"git::file::{file_path}"

# Author-based grouping
author_tag = f"git::author::{author_email}"
```

**Storage Operations:**
- Each commit becomes one memory with stable commit hash ID
- No updates needed - commits are immutable historical facts
- Qdrant stores vectors with commit metadata in payload
- SQLite stores commit relationships and file associations
- New commits simply add new memories without affecting existing ones

**Incremental Loading:**
- **Memory-based state tracking using SQLite persistence**
- **Automatic detection of latest processed commit via deterministic IDs**
- **Git revision range syntax for efficient incremental traversal**
- Avoid duplicate storage through commit hash checking
- Maintain chronological order for temporal relationships
- **Graceful fallback to full history when incremental state is corrupted**

### Payload Structure
```python
payload = {
    "commit_hash": "abc1234567890",
    "author": "john.doe@example.com",
    "timestamp": "2024-01-20T10:30:00Z",
    "files_changed": ["auth/middleware.py", "auth/config.py"],
    "change_types": ["M", "M"],
    "lines_added": 23,
    "lines_deleted": 5,
    "is_merge": False,
    "is_fix": True
}

## Testing Architecture

### E2E Test Suite

The git hook functionality is validated through comprehensive end-to-end tests that verify the complete workflow from hook installation to memory processing.

**Prerequisites:**
- Python environment with pytest installed
- Git available in PATH
- **Qdrant running locally** (for memory processing tests only)

**Test Structure:**
```
tests/e2e/
├── test_git_hook_commands.py          # Core hook management functions
├── test_git_hook_cli_integration.py   # CLI command integration
└── test_git_hook_memory_processing.py # Memory system integration
```

**Test Coverage:**
- **Hook Installation** (no services required): Fresh repos, existing hooks, chaining, permissions
- **Hook Uninstallation** (no services required): Backup restoration, cleanup, edge cases
- **Hook Status Detection** (no services required): All hook states, repository validation
- **CLI Integration** (no services required): All heimdall git-hook commands with various flags
- **Memory Processing** (requires Qdrant): Actual hook execution, commit processing, error handling
- **Safety Features** (no services required): Git operation safety, concurrent execution, error isolation

**Running Tests:**
```bash
# Hook management tests (no services required)
python -m pytest tests/e2e/test_git_hook_commands.py -v
python -m pytest tests/e2e/test_git_hook_cli_integration.py -v

# Memory processing tests (requires Qdrant running)
heimdall qdrant start  # Start Qdrant first
python -m pytest tests/e2e/test_git_hook_memory_processing.py -v

# All git hook tests (requires Qdrant)
heimdall qdrant start
python -m pytest tests/e2e/test_git_hook*.py -v
```

**Test Isolation:**
- Each test creates temporary git repositories
- No shared state between tests
- Cleanup automatically handled by pytest fixtures

**Service Dependencies:**
- **Hook management tests**: No external services required
- **Memory processing tests**: Require Qdrant running locally (uses `initialize_system('test')`)
- **Hook safety features**: Gracefully handle missing services via try/catch blocks

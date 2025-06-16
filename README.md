# LibPaper 📚

> A headless library for academic paper management with intelligent organization, metadata extraction, and comprehensive CLI tools.

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)](#)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview

LibPaper is a powerful, self-hosted academic paper management library designed for researchers, students, and academics. As a headless library, it focuses on providing robust backend functionality without UI constraints, making it perfect for integration into existing workflows or building custom applications.

## ✨ Features

### 📄 Paper Management

- **PDF Storage**: Secure local storage with hash-based deduplication
- **Metadata Extraction**: Automatic extraction from PDF files and online databases
- **File Organization**: Hierarchical storage with date-based structure
- **Batch Operations**: Import and manage multiple papers efficiently

### 🏷️ Smart Organization

- **Collections**: Hierarchical folder system for logical grouping
- **Tagging System**: Flexible multi-tag support with custom colors
- **Search & Filter**: Advanced search across titles, authors, content, and metadata
- **Auto-categorization**: Intelligent suggestions based on content analysis

### 🛠️ Developer-Friendly

- **CLI Interface**: Complete command-line tool for all operations
- **Python API**: Clean, intuitive API for programmatic access
- **Type Safety**: Full type hints and Pydantic models
- **Extensible**: Plugin architecture for custom integrations

### 🔒 Privacy-First

- **Self-Hosted**: No external dependencies or cloud services required
- **Local Storage**: All data stays on your machine
- **Open Source**: MIT licensed, fully auditable codebase

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (coming soon)
pip install libpaper

# Or install from source
git clone https://github.com/yourusername/libpaper.git
cd libpaper
pip install -e .
```

### Initialize Your Library

```bash
# Initialize a new paper library
libpaper init

# Add your first paper
libpaper add /path/to/paper.pdf

# List all papers
libpaper list
```

### Basic Usage

```python
from libpaper import LibPaper

# Initialize library
library = LibPaper()

# Add a paper
paper = library.add_paper("/path/to/paper.pdf")

# Create collections
collection = library.create_collection("Machine Learning")

# Add tags
library.add_tag_to_paper(paper.id, "deep-learning")

# Search papers
results = library.search_papers("neural networks")
```

## 📖 Documentation

### CLI Commands

```bash
# Paper management
libpaper add <file>                    # Add a paper
libpaper list                          # List all papers
libpaper show <paper-id>               # Show paper details
libpaper remove <paper-id>             # Remove a paper

# Collection management
libpaper collection create <name>      # Create collection
libpaper collection list               # List collections
libpaper collection add <id> <paper>   # Add paper to collection

# Tag management
libpaper tag create <name>             # Create tag
libpaper tag list                      # List all tags
libpaper tag add <paper> <tag>         # Tag a paper

# Search and filter
libpaper search <query>                # Search papers
libpaper filter --author "Smith"      # Filter by author
libpaper filter --tag "ml"            # Filter by tag
```

### Configuration

LibPaper stores its configuration and database in `~/.libpaper/`:

```
~/.libpaper/
├── config.yaml           # Configuration file
├── library.db            # SQLite database
└── storage/
    ├── papers/           # PDF files
    └── metadata/         # Extracted metadata cache
```

## 🏗️ Architecture

LibPaper follows a clean, modular architecture:

```
src/libpaper/
├── models/               # Data models (Paper, Collection, Tag)
├── storage/              # Database and file storage
├── services/             # Business logic services
├── extractors/           # Metadata extraction
└── cli/                  # Command-line interface
```

### Data Models

- **Paper**: Core entity with metadata, file path, and relationships
- **Collection**: Hierarchical organization structure
- **Tag**: Flexible labeling system with colors and descriptions

### Storage

- **Database**: SQLite for metadata and relationships
- **Files**: Local filesystem with organized directory structure
- **Cache**: Extracted metadata caching for performance

## 🧪 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/libpaper.git
cd libpaper

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Format code
black src tests
isort src tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=libpaper --cov-report=html

# Run specific test file
pytest tests/test_paper_service.py
```

## 🗺️ Roadmap

### Phase 1: Core Foundation ✅

- [x] Basic project structure
- [x] Data models and database design
- [ ] File storage management
- [ ] PDF metadata extraction
- [ ] CLI interface

### Phase 2: Enhanced Features

- [ ] Full-text search with indexing
- [ ] Advanced filtering and sorting
- [ ] BibTeX import/export
- [ ] Plugin system architecture

### Phase 3: Integrations

- [ ] Zotero synchronization
- [ ] DOI lookup and metadata enrichment
- [ ] Citation network analysis
- [ ] Web API for external applications

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Principles

- **Privacy-first**: No external dependencies for core functionality
- **Type-safe**: Comprehensive type hints and validation
- **Well-tested**: High test coverage for reliability
- **Developer-friendly**: Clean APIs and comprehensive documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [SQLModel](https://sqlmodel.tiangolo.com/) for database operations
- PDF processing powered by [pypdf](https://github.com/py-pdf/pypdf)
- CLI interface using [Click](https://click.palletsprojects.com/)
- Beautiful terminal output with [Rich](https://rich.readthedocs.io/)

## 📞 Support

- 📧 Email: your.email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/libpaper/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/libpaper/discussions)

---

<p align="center">
  <strong>Built with ❤️ for the research community</strong>
</p>

# Contributing to ODGS
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)]()
[![AI Safety](https://img.shields.io/badge/AI%20Safety-EU%20AI%20Act%20Compliant-blueviolet)]()
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)]()
[![PRs](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

Thank you for your interest in contributing to the Open Data Governance Schema (ODGS)! We welcome contributions from researchers, engineers, and domain experts.


> **"The Protocol for Algorithmic Accountability"**
## 🎯 How to Contribute

### Expanding the Protocol

#### 1. Data Quality Dimensions
Add new dimensions to `protocol/lib/standard_dq_dimensions.json`:
- **Process**: Research industry standards (ISO 8000, DAMA-DMBOK)
- **Propose**: Open an issue with your proposed dimension
- **Document**: Provide clear definition and examples
- **Submit**: Create a PR with the addition

#### 2. Root Cause Taxonomy
Refine `protocol/lib/root_cause_factors.json`:
- Add domain-specific failure modes (e.g., Healthcare: "HIPAA_Violation")
- Improve categorization
- Add real-world examples

#### 3. Industry Templates
Create new `odgs init --template` options:
- Healthcare (HIPAA compliance metrics)
- Finance (Basel III, Solvency II)
- Retail (Customer 360°)
- Manufacturing (OEE, Six Sigma)

### Building Adapters

We need adapters for:
- **Looker** (LookML generator)
- **Qlik Sense** (QVD generator)
- **Sisense** (ElastiCube generator)
- **Metabase** (Native schema)
- **Redash** (Query templates)

**Adapter Template:**
```python
# adapters/[tool]/generate_[format].py
import json

def generate_adapter(metrics):
    """
    Generate [tool]-specific format from ODGS metrics.
    
    Args:
        metrics: List of metric objects from standard_metrics.json
    
    Returns:
        String containing [tool] configuration
    """
    # Your implementation here
    pass
```

### Documentation

- **Tutorials**: Write guides for specific use cases (e.g., "ODGS for dbt Cloud")
- **Translations**: Translate docs to Dutch, German, French
- **Case Studies**: Document real-world implementations
- **Videos**: Create walkthrough screencasts

### Bug Fixes & Enhancements

- Fix typos in schemas or docs
- Improve CLI error messages
- Add validation checks
- Optimize build performance

---

## 🔧 Development Setup

### Prerequisites
- Python 3.9+
- Node.js 16+ (for NPM package testing)
- Git

### Setup Steps

1. **Fork the repository**
```bash
git clone https://github.com/[your-username]/headless-data-governance.git
cd headless-data-governance
```

2. **Install dependencies**
```bash
# Python
pip install -e ".[dev]"

# Node.js (for NPM testing)
npm install
```

3. **Create a feature branch**
```bash
git checkout -b feature/my-awesome-contribution
```

4. **Make your changes**
- Edit files in `protocol/lib/` or `protocol/schemas/`
- Update documentation in `docs/`
- Add tests if applicable

5. **Validate your changes**
```bash
odgs validate
python scripts/validate_schema.py
```

6. **Commit with clear messages**
```bash
git commit -m "feat: add healthcare template with HIPAA metrics"
```

Use conventional commit prefixes:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `refactor:` Code refactoring
- `test:` Adding tests

---

## 📝 Pull Request Process

1. **Update the documentation**
   - If you add a feature, update `docs/guide.md`
   - If you add schemas, update `docs/vision.md` if relevant

2. **Run validation**
   ```bash
   odgs validate
   ```

3. **Write a clear PR description**
   - What problem does this solve?
   - What changes did you make?
   - How did you test it?

4. **Example PR Template:**
```markdown
## Problem
Users need a Looker adapter to compile ODGS to LookML.

## Solution
Created `adapters/looker/generate_lookml.py` that:
- Reads `standard_metrics.json`
- Generates LookML `view` files
- Handles dimension vs. measure logic

## Testing
- [x] Tested with 10 sample metrics
- [x] Validated generated LookML syntax
- [x] Ran `odgs validate`

## Checklist
- [x] Documentation updated
- [x] Tests passing
- [x] Follows coding standards
```

5. **Respond to feedback**
   - Address reviewer comments promptly
   - Update your branch as needed

6. **Celebrate!**
   - Once merged, you'll be listed in our contributors
   - We'll tag you in release notes

---

## 🎨 Coding Standards

### JSON Schemas
- Use lowercase_snake_case for field names
- Include `description` fields for all properties
- Follow existing schema structure
- Validate against JSON Schema Draft 7

### Python Code
- Follow PEP 8
- Use type hints
- Add docstrings to functions
- Keep functions under 50 lines

### Documentation
- Use GitHub Flavored Markdown
- Add code examples for new features
- Include Mermaid diagrams where helpful
- Keep line length under 120 characters

---

## 🤝 Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

---

## 🏆 Recognition

Contributors are recognized in:
- **README.md** (Contributors section)
- **Release Notes** (with GitHub handle)
- **Hall of Fame** (for major contributions)

---

## 💬 Questions?

- **GitHub Discussions**: Ask questions in [Discussions](https://github.com/Authentic-Intelligence-Labs/headless-data-governance/discussions)
- **Issues**: Report bugs in [Issues](https://github.com/Authentic-Intelligence-Labs/headless-data-governance/issues)
- **Email**: For sensitive questions, email [contact email]

---

Thank you for contributing to ODGS! Together, we're building the standard for Algorithmic Accountability. 🚀

# Contributing to the Open Data Governance Standard (ODGS)

Thank you for your interest in contributing to the **ODGS Protocol**. We are building a "Headless" standard for data governance, decoupling business logic from BI tools.

## 🌟 How to Contribute

We welcome contributions in three main areas:
1.  **Core Protocol**: Improving the JSON schemas for Metrics, Rules, and Lineage.
2.  **Agent Logic**: Enhancing the `odgs agent` capabilities using Google Gemini 3.0.
3.  **Visualizers**: Improving the reference Frontend (React + D3/Mermaid).

## 🛠 Development Setup

1.  **Clone the Repo**:
    ```bash
    git clone https://github.com/Authentic-Intelligence-Labs/headless-data-governance.git
    cd headless-data-governance
    ```

2.  **Environment**:
    Create a `.env` file with your Gemini API Key:
    ```bash
    cp .env.example .env
    # Edit .env and add GEMINI_API_KEY=AIza...
    ```

3.  **Install**:
    We use `pip` with `pyproject.toml` for modern dependency management.
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -e .
    ```

4.  **Run the Stack**:
    *   **Backend**: `uvicorn server.api:app --reload`
    *   **Frontend**: `cd demo/frontend && npm install && npm run dev`

## 🧪 Testing
Run the agent manually to verify your environment:
```bash
odgs agent generate "Retail"
```

## 📜 License
This project is licensed under the Apache 2.0 License.

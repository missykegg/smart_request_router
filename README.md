# Smart Request Router

A modular request classification and routing service written in Python for processing multi-channel incoming customer support requests.

## 📌 Architecture
- **Text Normalization**: Unicode handling, lowercasing, stopword stripping.
- **Rule-based Classification**: Keyword and regex pattern matcher for high-confidence intents (`billing`, `auth`, `bug`, `feature`).
- **Priority Scoring**: Dynamic priority evaluation (P1 Critical, P2 High, P3 Normal, P4 Low) based on keywords and customer SLA metadata.
- **Output Formats**: Standardized JSON payload delivery and CSV batch reports.

## 💻 Quickstart

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python src/main.py --input examples/requests.json --output results.json
```

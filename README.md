<<<<<<< HEAD
# SupplySight AI – Visual Supply Chain Intelligence

For genovate hackathon

This is a hackathon prototype that analyzes an uploaded image of a business environment (warehouse, retail shelf, packaging line) and generates supply chain insights and startup ideas.

Getting started

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. (Optional) Add your Gemini API key to a `.env` file in the project root:

```
GEMINI_API_KEY=your_real_gemini_api_key_here
```

3. Run the Streamlit app:

```bash
streamlit run app.py
```

Notes

- The repository includes a local heuristic fallback so the app runs without a Gemini API key. To enable real multimodal analysis, provide a valid `GEMINI_API_KEY` and adapt `gemini_service.py` to the exact client method for the library version you use.
- The app will attempt to call the endpoint configured in the `GEMINI_ENDPOINT` environment variable, or the default model endpoint derived from `GEMINI_MODEL`.

Bonus features included

- Market opportunity score (0-100)
- Investor pitch summary
- Download analysis report (TXT, MD, PDF)
- Multi-image comparison (upload multiple images)

Files:

- `app.py` - Streamlit interface
- `image_utils.py` - image helpers
- `gemini_service.py` - Gemini integration + fallback
- `prompts.py` - prompt templates
>>>>>>> df7241d (chore: add SupplySight AI app sources)

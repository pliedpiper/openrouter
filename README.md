# OpenRouter Multi-Model Guessing Game

Small CLI game that sends the same prompt to several OpenRouter-hosted models, shuffles the responses, and asks you to guess which model wrote which answer.

## Prerequisites

- Python 3.11+ (the code relies on modern typing)
- OpenRouter API key with access to the listed models

## Setup

1. **Clone & create a virtual environment**
   ```powershell
   git clone <repo-url> && cd openrouter
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
2. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```
3. **Configure environment**
   - Copy `.env.example` to `.env` (or create `.env`) and add your key:
     ```
     openRouter=sk-or-...
     ```
   - The helper in `main.py` also falls back to `OPENROUTER_API_KEY` from your shell environment if `.env` is missing.

## Running the Game

```powershell
python main.py
```

You will be prompted to:

1. Enter any user prompt.
2. Review the randomized model responses.
3. Guess which numbered model produced each response.
4. See your score and optionally play another round.

Type `exit`/`quit` at any prompt (or press `Ctrl+D`) to leave the app.

## Persistent Scoring

- The CLI asks for a player name on startup and stores round results in `scores.db` (SQLite).
- After each round you see your lifetime accuracy plus a multi-player leaderboard.
- Delete `scores.db` or pick a new player name if you want a clean slate.

## Customizing Models

The `MODELS` list in `main.py` controls which providers are queried. To swap models:

1. Replace or add `(label, model_id)` tuples.
2. Ensure your OpenRouter account has access to the new IDs.

## Testing

Unit tests live in `tests/`. Activate your environment and run:

```powershell
pytest
```

## Troubleshooting

- **Missing API key**: Verify `.env` contains `openRouter=<key>` with no quotes.
- **Model errors**: Some providers rate-limit or require allowlisting -- double-check your OpenRouter dashboard.
- **Network issues**: The script retries per run; simply re-run the round or swap to available models.

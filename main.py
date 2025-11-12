import os
import random
from pathlib import Path

from openai import OpenAI

from scoreboard import ScoreStore


SYSTEM_PROMPT = "You are a helpful CLI assistant. Keep answers concise unless asked otherwise."
MODELS = [
    ("grok-fast", "x-ai/grok-code-fast-1"),
    ("google/gemini-2.5-flash", "google/gemini-2.5-flash"),
    ("openrouter/polaris-alpha", "openrouter/polaris-alpha"),
    ("openai/gpt-5-mini", "openai/gpt-5-mini"),
]


def load_env_value(key: str, env_path: str = ".env") -> str | None:
    """Minimal .env parser so we do not rely on external packages."""
    path = Path(env_path)
    if not path.exists():
        return os.environ.get(key)

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        env_key, env_val = line.split("=", 1)
        if env_key.strip() == key:
            cleaned = env_val.strip().strip('"').strip("'")
            os.environ.setdefault(env_key.strip(), cleaned)
            return cleaned

    return os.environ.get(key)


def fetch_model_response(client: OpenAI, model_id: str, prompt: str) -> str:
    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "<YOUR_SITE_URL>",
            "X-Title": "<YOUR_SITE_NAME>",
        },
        extra_body={},
        model=model_id,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return completion.choices[0].message.content.strip()


def gather_responses(client: OpenAI, prompt: str) -> list[tuple[str, str]]:
    responses: list[tuple[str, str]] = []
    for label, model_id in MODELS:
        try:
            answer = fetch_model_response(client, model_id, prompt)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Failed to query {label}: {exc}") from exc
        responses.append((label, answer))
    return responses


def prompt_for_guess(valid_selections: dict[str, str], response_number: int) -> str:
    while True:
        guess = input(f"Enter model # for response {response_number}: ").strip()
        if guess in {"exit", "quit"}:
            raise KeyboardInterrupt
        if guess in valid_selections:
            return valid_selections[guess]
        print(f"Unknown choice. Pick one of: {', '.join(sorted(valid_selections))}")


def prompt_for_player_name() -> str:
    while True:
        player = input("Enter a player name: ").strip()
        if player.lower() in {"exit", "quit"}:
            raise KeyboardInterrupt
        if player:
            return player
        print("Player name cannot be blank.")


def render_summary(store: ScoreStore, player_name: str) -> None:
    summary = store.get_player_summary(player_name)
    if not summary:
        print(f"Welcome, {player_name}! New scores start now.\n")
        return

    accuracy = summary.accuracy * 100
    print(
        f"Welcome back, {player_name}! "
        f"{summary.total_correct}/{summary.total_questions} correct "
        f"over {summary.rounds_played} rounds ({accuracy:.1f}% accuracy).\n"
    )


def show_leaderboard(store: ScoreStore) -> None:
    leaders = store.leaderboard()
    if not leaders:
        return

    print("Leaderboard:")
    for idx, entry in enumerate(leaders, start=1):
        accuracy = entry.accuracy * 100
        print(
            f"{idx}. {entry.player} "
            f"- {entry.total_correct}/{entry.total_questions} "
            f"across {entry.rounds_played} rounds ({accuracy:.1f}%)"
        )
    print()


def main() -> None:
    api_key = load_env_value("openRouter")
    if not api_key:
        raise RuntimeError(
            "Missing OpenRouter API key. Add openRouter=<key> to your .env file."
        )

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    store = ScoreStore()

    print("OpenRouter Multi-Model Guessing Game")
    print("Type 'exit' or press Ctrl+D to quit.\n")

    try:
        player_name = prompt_for_player_name()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        return

    render_summary(store, player_name)

    while True:
        try:
            user_prompt = input("Enter a prompt: ").strip()
        except EOFError:
            print("\nGoodbye!")
            break

        if not user_prompt:
            continue
        if user_prompt.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        try:
            responses = gather_responses(client, user_prompt)
        except RuntimeError as exc:
            print(f"[Error] {exc}")
            continue

        shuffled = responses[:]
        random.shuffle(shuffled)

        print("\nModel responses (order randomized):")
        for idx, (_, answer) in enumerate(shuffled, start=1):
            print(f"\nResponse {idx}:\n{'-' * 40}\n{answer}\n{'-' * 40}")

        print("\nAvailable models:")
        selectable = {str(idx): label for idx, (label, _) in enumerate(MODELS, start=1)}
        for key, label in selectable.items():
            print(f"{key}. {label}")

        guesses: dict[int, str] = {}
        try:
            for idx in range(1, len(shuffled) + 1):
                guesses[idx] = prompt_for_guess(selectable, idx)
        except KeyboardInterrupt:
            print("\nGuessing aborted. Returning to main menu.\n")
            continue

        print("\nResults:")
        correct_total = 0
        for idx, (actual_label, _) in enumerate(shuffled, start=1):
            guessed_label = guesses[idx]
            is_correct = guessed_label == actual_label
            if is_correct:
                correct_total += 1
            status = "[OK]" if is_correct else "[X]"
            print(f"{status} - Response {idx} was {actual_label} (you guessed {guessed_label})")

        if correct_total == len(shuffled):
            print("Perfect round!")
        else:
            print(f"You matched {correct_total}/{len(shuffled)} correctly.")

        store.record_round(player_name, len(shuffled), correct_total)
        summary = store.get_player_summary(player_name)
        if summary:
            accuracy = summary.accuracy * 100
            print(
                f"\nLifetime totals for {player_name}: "
                f"{summary.total_correct}/{summary.total_questions} "
                f"over {summary.rounds_played} rounds ({accuracy:.1f}%)."
            )

        print()
        show_leaderboard(store)

        play_again = input("\nPlay another round? (y/n): ").strip().lower()
        if play_again not in {"y", "yes"}:
            print("Goodbye!")
            break
        print()


if __name__ == "__main__":
    main()

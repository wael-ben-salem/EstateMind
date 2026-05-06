import argparse
from dotenv import load_dotenv

from src.agents.rag_agent import RAGAgent

load_dotenv()

DEFAULT_QUERY = (
    "Quelles sont les obligations d'un tuteur légal pour un mineur en Tunisie ? "
    "Cherche aussi les sanctions en cas de manquement."
)


def run_agent_test(query: str, max_iterations: int = 5, max_context_size: int = 50) -> str:
    """Run a quick RAGAgent test and print the final result."""
    agent = RAGAgent(max_iterations=max_iterations, max_context_size=max_context_size)
    response = agent.ask(query)

    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    print(response)
    print("=" * 80)
    print("SUMMARY")
    print(f"Query: {query}")
    print(f"Context items: {len(agent.memory['accumulated_context'])}")
    print(f"Drafts: {len(agent.memory['drafts'])}")
    print(f"Steps: {len(agent.memory['steps'])}")
    print("=" * 80)

    return response


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a RAGAgent legal test query.")
    parser.add_argument(
        "--query",
        type=str,
        default=DEFAULT_QUERY,
        help="Legal question to send to the agent."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Maximum reasoning iterations for the agent."
    )
    parser.add_argument(
        "--context-size",
        type=int,
        default=50,
        help="Maximum number of context snippets to retain."
    )

    args = parser.parse_args()
    query = args.query.strip() or DEFAULT_QUERY

    try:
        run_agent_test(query, max_iterations=args.iterations, max_context_size=args.context_size)
    except Exception as error:
        print("Agent test failed:", str(error))
        raise


if __name__ == "__main__":
    main()

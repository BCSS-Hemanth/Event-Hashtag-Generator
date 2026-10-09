"""
Keyword Generator Main Entrypoint.
"""


def main() -> None:
    """Run the FastAPI application with Uvicorn server."""
    import uvicorn

    uvicorn.run("keyword_generator_main.app:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()

def pytest_addoption(parser):
    parser.addoption(
        "--generate-test-cache",
        action="store_true",
        default=False,
        help="Use the real GeminiEmbeddingManager cache file instead of the dummy test cache."
    )
def pytest_configure(config):
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "performance: performance tests")


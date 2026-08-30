import os

import pytest


os.environ.setdefault("INNGEST_DEV", "1")


@pytest.fixture
def anyio_backend():
    return "asyncio"

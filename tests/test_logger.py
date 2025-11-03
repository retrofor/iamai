"""
Test cases for the Loguru-based logging system.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from iamai.logger import get_logger, setup_logger


def test_get_logger():
    """Test getting a logger instance."""
    logger = get_logger("test_module")
    assert logger is not None
    
    # Test logging methods exist
    assert hasattr(logger, "debug")
    assert hasattr(logger, "info")
    assert hasattr(logger, "warning")
    assert hasattr(logger, "error")
    assert hasattr(logger, "exception")
    assert hasattr(logger, "critical")


def test_setup_logger_basic():
    """Test basic logger setup."""
    setup_logger({"level": "DEBUG"})
    logger = get_logger("test_setup")
    
    # Should not raise any errors
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")


def test_setup_logger_with_config():
    """Test logger setup with custom configuration."""
    config = {
        "level": "INFO",
        "format": "<green>{time}</green> | <level>{level}</level> | {message}"
    }
    setup_logger(config)
    logger = get_logger("test_config")
    
    logger.info("Testing custom configuration")


def test_exception_logging():
    """Test exception logging."""
    logger = get_logger("test_exception")
    
    try:
        raise ValueError("Test exception")
    except ValueError:
        # Should not raise any errors
        logger.exception("Caught an exception")


def test_multiple_loggers():
    """Test creating multiple logger instances."""
    logger1 = get_logger("module1")
    logger2 = get_logger("module2")
    logger3 = get_logger("module1")  # Same name as logger1
    
    assert logger1 is not None
    assert logger2 is not None
    assert logger3 is not None


if __name__ == "__main__":
    print("Running logger tests...")
    
    test_get_logger()
    print("✓ test_get_logger passed")
    
    test_setup_logger_basic()
    print("✓ test_setup_logger_basic passed")
    
    test_setup_logger_with_config()
    print("✓ test_setup_logger_with_config passed")
    
    test_exception_logging()
    print("✓ test_exception_logging passed")
    
    test_multiple_loggers()
    print("✓ test_multiple_loggers passed")
    
    print("\nAll tests passed! ✨")

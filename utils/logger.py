"""
Centralized logging configuration for IND Money Review Analyzer
"""
import logging
import sys
from datetime import datetime
import os

def setup_logger(name: str, log_file: str = None, level=logging.INFO):
    """
    Set up a logger with console and optional file output
    
    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str):
    """Get or create a logger"""
    return logging.getLogger(name)

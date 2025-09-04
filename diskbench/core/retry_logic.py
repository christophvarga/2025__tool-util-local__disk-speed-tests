"""
Retry logic with exponential backoff for handling transient failures.

Provides configurable retry strategies for FIO execution and other
potentially unreliable operations with proper logging and context.
"""
import time
import logging
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps

from .exceptions import DiskBenchError


def exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_multiplier: float = 2.0,
    jitter: bool = True
):
    """
    Decorator for exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        backoff_multiplier: Multiplier for delay on each retry
        jitter: Add random jitter to prevent thundering herd
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Don't retry on the last attempt
                    if attempt >= max_retries:
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(initial_delay * (backoff_multiplier ** attempt), max_delay)
                    
                    # Add jitter to prevent synchronized retries
                    if jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    
                    time.sleep(delay)
            
            # All retries exhausted, re-raise the last exception
            logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            raise last_exception
            
        return wrapper
    return decorator


class RetryableOperation:
    """Context manager for retryable operations with detailed logging."""
    
    def __init__(
        self, 
        operation_name: str,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        retriable_exceptions: Optional[Tuple[Type[Exception], ...]] = None
    ):
        """
        Initialize retryable operation context.
        
        Args:
            operation_name: Name of the operation for logging
            max_retries: Maximum retry attempts
            initial_delay: Initial delay between retries
            retriable_exceptions: Tuple of exception types that should trigger retries
        """
        self.operation_name = operation_name
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.retriable_exceptions = retriable_exceptions or (Exception,)
        self.logger = logging.getLogger(__name__)
        self.attempt = 0
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.attempt += 1
        self.logger.info(f"Starting {self.operation_name} (attempt {self.attempt})")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        if exc_type is None:
            # Success
            self.logger.info(f"{self.operation_name} completed successfully in {elapsed:.2f}s")
            return True
        
        # Check if exception is retriable
        if not issubclass(exc_type, self.retriable_exceptions):
            self.logger.error(f"{self.operation_name} failed with non-retriable error: {exc_val}")
            return False  # Don't suppress exception
        
        if self.attempt <= self.max_retries:
            delay = self.initial_delay * (2 ** (self.attempt - 1))
            self.logger.warning(
                f"{self.operation_name} attempt {self.attempt} failed: {exc_val}. "
                f"Retrying in {delay:.2f}s"
            )
            time.sleep(delay)
            return True  # Suppress exception to allow retry
        else:
            self.logger.error(f"{self.operation_name} failed after {self.attempt} attempts: {exc_val}")
            return False  # Don't suppress exception
    
    def should_retry(self, exception: Exception) -> bool:
        """
        Determine if an operation should be retried based on the exception.
        
        Args:
            exception: The exception that occurred
            
        Returns:
            True if the operation should be retried, False otherwise
        """
        # Don't retry if we've exceeded max attempts
        if self.attempt > self.max_retries:
            return False
        
        # Check if exception type is retriable
        if not isinstance(exception, self.retriable_exceptions):
            self.logger.info(f"Not retrying due to non-retriable exception: {type(exception)}")
            return False
        
        # Add specific logic for different types of failures
        error_message = str(exception).lower()
        
        # Don't retry for certain permanent failures
        permanent_failures = [
            'permission denied',
            'file not found',
            'disk not available',
            'insufficient space',
            'invalid configuration'
        ]
        
        if any(failure in error_message for failure in permanent_failures):
            self.logger.info(f"Not retrying due to permanent failure: {exception}")
            return False
        
        # Retry for transient failures
        transient_failures = [
            'timeout',
            'connection',
            'temporary',
            'busy',
            'locked',
            'unavailable'
        ]
        
        if any(failure in error_message for failure in transient_failures):
            self.logger.info(f"Retrying due to transient failure: {exception}")
            return True
        
        # Default to retry for other exceptions
        return True


def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    retriable_exceptions: Optional[Tuple[Type[Exception], ...]] = None
):
    """
    Simple retry decorator without exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        delay: Fixed delay between retries
        retriable_exceptions: Exception types that should trigger retries
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            retriable = retriable_exceptions or (Exception,)
            logger = logging.getLogger(func.__module__)
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retriable as e:
                    if attempt < max_retries:
                        logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}. Retrying...")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries + 1} attempts")
                        raise
                        
        return wrapper
    return decorator

"""
Remote control module - DISABLED for security.

This module previously allowed remote control of the application via a Pastebin URL,
which was a critical security vulnerability. It has been disabled.

If remote control is needed in the future, implement with:
- HMAC signature verification
- Fail-closed design (deny by default)
- Environment variable configuration
- Proper authentication

See the code review plan for a secure implementation example.
"""
import logging
from typing import Tuple, Optional

def check_remote_status(url: str) -> Tuple[bool, Optional[str], str]:
    """
    DISABLED: Remote control check removed for security.
    
    This function is kept for backward compatibility but always returns
    (True, None, "info") to allow the application to run.
    
    Args:
        url: Remote URL (ignored)
        
    Returns:
        (is_allowed: bool, message: str, level: str) - Always (True, None, "info")
    """
    logging.info("Remote control check disabled for security")
    return True, None, "info"
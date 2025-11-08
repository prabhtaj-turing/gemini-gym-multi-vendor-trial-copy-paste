"""
Shared Session Manager for Terminal-like APIs

This module provides a centralized session management system that allows
cursor, gemini_cli, and terminal APIs to share the same sandbox directory.
This prevents duplicate dehydration and ensures all APIs work on the same
physical files when switching between them.

Key Features:
- Single source of truth for sandbox location
- Prevents duplicate dehydration when switching APIs
- Tracks which API created the session
- Thread-safe access to shared state
"""

import os
import tempfile
import logging
from typing import Optional, Dict, Any

# --- Logger Setup ---
logger = logging.getLogger(__name__)

# --- Shared Session State ---
# These variables are shared across all terminal-like APIs (cursor, gemini_cli, terminal)
SHARED_SANDBOX_DIR: Optional[str] = None
SHARED_SESSION_INITIALIZED: bool = False
SHARED_ACTIVE_API: Optional[str] = None  # Tracks which API created the sandbox
_SHARED_SANDBOX_TEMP_DIR_OBJ: Optional[tempfile.TemporaryDirectory] = None


def get_shared_session_info() -> Dict[str, Any]:
    """
    Returns information about the current shared session.
    
    Returns:
        Dict[str, Any]: Dictionary containing:
            - initialized (bool): Whether a session is active
            - sandbox_dir (Optional[str]): Path to the shared sandbox directory
            - active_api (Optional[str]): Name of the API that created the session
            - exists (bool): Whether the sandbox directory physically exists
    """
    return {
        "initialized": SHARED_SESSION_INITIALIZED,
        "sandbox_dir": SHARED_SANDBOX_DIR,
        "active_api": SHARED_ACTIVE_API,
        "exists": SHARED_SANDBOX_DIR is not None and os.path.exists(SHARED_SANDBOX_DIR)
    }


def initialize_shared_session(api_name: str, workspace_root: str, db_instance, dehydrate_func) -> str:
    """
    Initializes or retrieves the shared sandbox session.
    
    This function checks if a shared session already exists. If it does, it reuses
    the existing sandbox directory. If not, it creates a new sandbox and dehydrates
    the workspace to it.
    
    Args:
        api_name (str): Name of the API requesting the session ('cursor', 'gemini_cli', or 'terminal')
        workspace_root (str): Path to the workspace root directory
        db_instance: The DB instance from the calling API
        dehydrate_func (callable): Function to dehydrate DB to directory, signature: dehydrate_func(db, target_dir)
    
    Returns:
        str: Path to the shared sandbox directory
        
    Raises:
        RuntimeError: If sandbox creation or dehydration fails
    """
    global SHARED_SANDBOX_DIR, SHARED_SESSION_INITIALIZED, SHARED_ACTIVE_API, _SHARED_SANDBOX_TEMP_DIR_OBJ
    
    # Check if we can reuse an existing session
    if SHARED_SESSION_INITIALIZED and SHARED_SANDBOX_DIR and os.path.exists(SHARED_SANDBOX_DIR):
        logger.info(
            f"[{api_name}] Reusing existing sandbox session created by '{SHARED_ACTIVE_API}': {SHARED_SANDBOX_DIR}"
        )
        return SHARED_SANDBOX_DIR
    
    # Need to create a new session
    try:
        logger.info(f"[{api_name}] Creating new shared sandbox session...")
        
        # Create temporary directory
        temp_dir_obj = tempfile.TemporaryDirectory(prefix=f"shared_sandbox_{api_name}_")
        sandbox_path = temp_dir_obj.name
        
        logger.info(f"[{api_name}] Created sandbox at: {sandbox_path}")
        
        # Dehydrate workspace to sandbox using the provided DB instance
        logger.info(f"[{api_name}] Dehydrating workspace to sandbox...")
        dehydrate_func(db_instance, sandbox_path)
        logger.info(f"[{api_name}] Workspace dehydrated successfully")
        
        # Update shared state
        SHARED_SANDBOX_DIR = sandbox_path
        SHARED_SESSION_INITIALIZED = True
        SHARED_ACTIVE_API = api_name
        _SHARED_SANDBOX_TEMP_DIR_OBJ = temp_dir_obj
        
        logger.info(f"[{api_name}] Shared session initialized successfully")
        return sandbox_path
        
    except Exception as e:
        logger.error(f"[{api_name}] Failed to initialize shared session: {e}", exc_info=True)
        raise RuntimeError(f"Failed to initialize shared sandbox session: {e}") from e


def end_shared_session(api_name: str, db_instance, update_func, normalize_path_func) -> Dict[str, Any]:
    """
    Ends the shared session and cleans up the sandbox.
    
    This function syncs changes from the sandbox back to the database and removes
    the temporary sandbox directory. Any API can call this, but it will affect
    all APIs using the shared session.
    
    Args:
        api_name (str): Name of the API requesting the session end
        db_instance: The DB instance from the calling API
        update_func (callable): Function to update DB from temp directory, 
                               signature: update_func(temp_root, original_state, workspace_root, command)
        normalize_path_func (callable): Function to normalize paths, signature: normalize_path_func(path)
    
    Returns:
        Dict[str, Any]: Dictionary containing:
            - success (bool): Whether the cleanup was successful
            - message (str): Description of the outcome
    """
    global SHARED_SANDBOX_DIR, SHARED_SESSION_INITIALIZED, SHARED_ACTIVE_API, _SHARED_SANDBOX_TEMP_DIR_OBJ
    
    if not SHARED_SESSION_INITIALIZED or not SHARED_SANDBOX_DIR:
        logger.info(f"[{api_name}] No active session to end")
        return {'success': True, 'message': "No active session to end."}
    
    logger.info(f"[{api_name}] Ending shared session (created by '{SHARED_ACTIVE_API}')...")
    
    try:
        # Get workspace root from the provided DB instance
        workspace_root = normalize_path_func(db_instance.get("workspace_root", ""))
        
        # Sync changes from sandbox back to DB
        if workspace_root:
            logger.info(f"[{api_name}] Syncing filesystem from sandbox to DB...")
            update_func(
                SHARED_SANDBOX_DIR,
                {},  # original_filesystem_state (empty for full sync)
                workspace_root,
                command="end_session"
            )
            logger.info(f"[{api_name}] Filesystem sync complete")
        else:
            logger.warning(f"[{api_name}] Workspace root not set. Skipping filesystem sync.")
        
        # Clean up the sandbox directory
        if _SHARED_SANDBOX_TEMP_DIR_OBJ:
            _SHARED_SANDBOX_TEMP_DIR_OBJ.cleanup()
            logger.info(f"[{api_name}] Sandbox directory '{SHARED_SANDBOX_DIR}' removed")
            _SHARED_SANDBOX_TEMP_DIR_OBJ = None
        elif os.path.exists(SHARED_SANDBOX_DIR):
            import shutil
            shutil.rmtree(SHARED_SANDBOX_DIR)
            logger.info(f"[{api_name}] Sandbox directory '{SHARED_SANDBOX_DIR}' removed (fallback)")
        
        # Reset shared state
        SHARED_SANDBOX_DIR = None
        SHARED_SESSION_INITIALIZED = False
        SHARED_ACTIVE_API = None
        
        logger.info(f"[{api_name}] Shared session ended successfully")
        return {'success': True, 'message': "Shared session ended and sandbox cleaned up successfully."}
        
    except Exception as e:
        logger.error(f"[{api_name}] Error during shared session cleanup: {e}", exc_info=True)
        
        # Attempt to reset state even if cleanup fails
        SHARED_SANDBOX_DIR = None
        SHARED_SESSION_INITIALIZED = False
        SHARED_ACTIVE_API = None
        _SHARED_SANDBOX_TEMP_DIR_OBJ = None
        
        return {'success': False, 'message': f"Error during shared session cleanup: {e}"}


def reset_shared_session() -> None:
    """
    Forcefully resets the shared session state with cleanup.
    
    This is primarily for testing purposes. In production code, use end_shared_session()
    to properly sync changes before cleanup.
    
    This function will attempt to clean up the temporary directory if it exists.
    """
    global SHARED_SANDBOX_DIR, SHARED_SESSION_INITIALIZED, SHARED_ACTIVE_API, _SHARED_SANDBOX_TEMP_DIR_OBJ
    
    logger.info("Forcefully resetting shared session state with cleanup")
    
    # Try to clean up the sandbox if it exists
    try:
        if _SHARED_SANDBOX_TEMP_DIR_OBJ:
            _SHARED_SANDBOX_TEMP_DIR_OBJ.cleanup()
            logger.info(f"Cleaned up shared sandbox temp directory")
        elif SHARED_SANDBOX_DIR and os.path.exists(SHARED_SANDBOX_DIR):
            import shutil
            shutil.rmtree(SHARED_SANDBOX_DIR, ignore_errors=True)
            logger.info(f"Cleaned up shared sandbox directory: {SHARED_SANDBOX_DIR}")
    except Exception as e:
        logger.warning(f"Failed to clean up shared sandbox during reset: {e}")
    
    SHARED_SANDBOX_DIR = None
    SHARED_SESSION_INITIALIZED = False
    SHARED_ACTIVE_API = None
    _SHARED_SANDBOX_TEMP_DIR_OBJ = None

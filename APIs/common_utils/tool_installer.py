"""
Tool installer utilities for development tools.

Provides functions to detect and install common development tools
(Java, Maven, Node, etc.) in various environments (Colab, local, etc.)
without requiring OOP patterns.
"""

import os
import subprocess
import shutil
import json
import urllib.request
from typing import Dict, List, Optional, Any


# Tool installation configurations
TOOL_INSTALL_MAP = {
    'java': {
        'apt': 'openjdk-11-jdk-headless',
        'check_cmd': 'java --version',
        'aliases': ['javac', 'jar']
    },
    'javac': {
        'apt': 'openjdk-11-jdk-headless',
        'check_cmd': 'javac --version',
        'primary_tool': 'java'
    },
    'maven': {
        'apt': 'maven',
        'check_cmd': 'mvn --version',
        'aliases': ['mvn'],
        'binary_url_pattern': 'https://dlcdn.apache.org/maven/maven-3/{version}/binaries/apache-maven-{version}-bin.tar.gz',
        'github_repo': 'apache/maven',  # For getting latest release
        'sdkman_name': 'maven',
    },
    'mvn': {
        'apt': 'maven',
        'check_cmd': 'mvn --version',
        'primary_tool': 'maven'
    },
    'node': {
        'apt': 'nodejs',
        'check_cmd': 'node --version',
        'aliases': ['nodejs']
    },
    'npm': {
        'apt': 'npm',
        'check_cmd': 'npm --version',
    },
    'go': {
        'apt': 'golang',
        'check_cmd': 'go version',
    },
    'gradle': {
        'apt': None,  # Not available in apt
        'check_cmd': 'gradle --version',
        'binary_url_pattern': 'https://services.gradle.org/distributions/gradle-{version}-bin.zip',
        'latest_version_url': 'https://services.gradle.org/versions/current',
        'sdkman_name': 'gradle',
    },
}


def detect_environment() -> str:
    """
    Detect the execution environment.
    
    Returns:
        str: Environment type - 'colab', 'kaggle', 'docker', or 'local'
    """
    if 'COLAB_GPU' in os.environ or 'COLAB_TPU_ADDR' in os.environ:
        return 'colab'
    elif 'KAGGLE_KERNEL_RUN_TYPE' in os.environ:
        return 'kaggle'
    elif os.path.exists('/.dockerenv'):
        return 'docker'
    else:
        return 'local'


def can_use_apt_without_password() -> bool:
    """
    Check if apt-get can be used without password (e.g., in Colab).
    
    Returns:
        bool: True if apt-get works without password
    """
    try:
        result = subprocess.run(
            ['apt-get', '--version'],
            capture_output=True,
            timeout=2,
            text=True
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_tool_installed(tool_name: str) -> bool:
    """
    Check if a tool is already installed and available.
    
    Args:
        tool_name: Name of the tool to check
        
    Returns:
        bool: True if tool is installed and accessible
    """
    # First try simple which check
    if shutil.which(tool_name):
        return True
    
    # Try using the check command from config
    config = TOOL_INSTALL_MAP.get(tool_name)
    if config and 'check_cmd' in config:
        try:
            result = subprocess.run(
                config['check_cmd'].split(),
                capture_output=True,
                timeout=2,
                check=True
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    return False


def get_apt_package_name(tool_name: str) -> Optional[str]:
    """
    Get the apt package name for a given tool.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        str: Apt package name, or None if not available via apt
    """
    config = TOOL_INSTALL_MAP.get(tool_name)
    if config:
        return config.get('apt')
    return None


def get_latest_version(tool_name: str) -> Optional[str]:
    """
    Get the latest version of a tool from its official source.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        str: Latest version string, or None if unable to fetch
    """
    config = TOOL_INSTALL_MAP.get(tool_name)
    if not config:
        return None
    
    # Need at least one source for version info
    if 'latest_version_url' not in config and 'github_repo' not in config:
        return None
    
    try:
        # Try direct version URL if available
        if 'latest_version_url' in config:
            with urllib.request.urlopen(config['latest_version_url'], timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    # Tool-specific version extraction
                    if tool_name == 'gradle':
                        return data.get('version')
                    
                    return data.get('version') or data.get('tag_name', '').lstrip('v')
        
        # Try GitHub releases API if repo is specified
        if 'github_repo' in config:
            github_url = f"https://api.github.com/repos/{config['github_repo']}/releases/latest"
            req = urllib.request.Request(
                github_url,
                headers={'Accept': 'application/vnd.github.v3+json'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    tag_name = data.get('tag_name', '')
                    
                    # Tool-specific version extraction from GitHub tags
                    if tool_name == 'maven':
                        # Maven tags look like: maven-3.9.6 or apache-maven-3.9.6
                        parts = tag_name.split('-')
                        # Get the last part which should be the version
                        for part in reversed(parts):
                            if part and part[0].isdigit():
                                return part
                    
                    # Default: remove 'v' prefix and extract version
                    return tag_name.lstrip('v').split('-')[0] if tag_name else None
    
    except Exception:
        # Fallback to a stable known version if fetch fails
        pass
    
    return None


def get_download_url(tool_name: str, version: str = 'latest') -> Optional[str]:
    """
    Get the download URL for a tool, optionally with version.
    
    Args:
        tool_name: Name of the tool
        version: Version to download ('latest' for latest version)
        
    Returns:
        str: Download URL, or None if not available
    """
    config = TOOL_INSTALL_MAP.get(tool_name)
    if not config:
        return None
    
    # If version is 'latest', try to fetch it
    if version == 'latest':
        version = get_latest_version(tool_name)
        if not version:
            # Fallback to known stable versions
            fallback_versions = {
                'gradle': '8.5',
                'maven': '3.9.6',
            }
            version = fallback_versions.get(tool_name)
    
    # If there's a URL pattern, format it with version
    if 'binary_url_pattern' in config and version:
        return config['binary_url_pattern'].format(version=version)
    
    # Otherwise return static URL if available
    return config.get('binary_url')


def get_install_command(tool_name: str, environment: str = None) -> Dict[str, str]:
    """
    Get installation commands for a tool in different environments.
    
    Args:
        tool_name: Name of the tool to install
        environment: Target environment (auto-detected if None)
        
    Returns:
        dict: Installation commands for different methods
    """
    if environment is None:
        environment = detect_environment()
    
    config = TOOL_INSTALL_MAP.get(tool_name)
    if not config:
        return {'error': f'Unknown tool: {tool_name}'}
    
    commands = {}
    
    # Apt-based installation (Colab, Ubuntu)
    if config.get('apt'):
        commands['apt'] = f"apt-get install -y -qq {config['apt']}"
    
    # Binary download (if available)
    download_url = get_download_url(tool_name, version='latest')
    if download_url:
        commands['binary'] = f"wget {download_url} && extract to ~/.local/bin"
    
    # SDKMAN installation (for JVM tools)
    if config.get('sdkman_name'):
        commands['sdkman'] = f"sdk install {config['sdkman_name']}"
    
    return commands


def install_tool_via_apt(tool_name: str, quiet: bool = True) -> Dict[str, Any]:
    """
    Install a tool using apt-get.
    
    Args:
        tool_name: Name of the tool to install
        quiet: If True, suppress output
        
    Returns:
        dict: Installation result with success status and details
    """
    package = get_apt_package_name(tool_name)
    if not package:
        return {
            'success': False,
            'tool': tool_name,
            'error': 'Not available via apt',
            'method': 'apt'
        }
    
    try:
        # Update package list
        update_cmd = ['apt-get', 'update']
        if quiet:
            update_cmd.append('-qq')
        
        subprocess.run(update_cmd, check=True, capture_output=quiet)
        
        # Install package
        install_cmd = ['apt-get', 'install', '-y']
        if quiet:
            install_cmd.append('-qq')
        install_cmd.append(package)
        
        subprocess.run(install_cmd, check=True, capture_output=quiet)
        
        return {
            'success': True,
            'tool': tool_name,
            'package': package,
            'method': 'apt'
        }
        
    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'tool': tool_name,
            'error': str(e),
            'method': 'apt'
        }


def install_multiple_tools(tool_names: List[str], quiet: bool = True) -> Dict[str, Any]:
    """
    Install multiple tools efficiently (batch apt installs when possible).
    
    Args:
        tool_names: List of tool names to install
        quiet: If True, suppress output
        
    Returns:
        dict: Results for each tool
    """
    results = {}
    apt_packages = {}  # package_name -> [tool_names]
    
    # Group tools by package name
    for tool in tool_names:
        # Check if already installed
        if check_tool_installed(tool):
            results[tool] = {
                'success': True,
                'status': 'already_installed',
                'tool': tool
            }
            continue
        
        # Get apt package
        package = get_apt_package_name(tool)
        if package:
            if package not in apt_packages:
                apt_packages[package] = []
            apt_packages[package].append(tool)
        else:
            results[tool] = {
                'success': False,
                'error': 'Installation method not available',
                'tool': tool
            }
    
    # Install all apt packages in one batch
    if apt_packages:
        try:
            # Update package list once
            update_cmd = ['apt-get', 'update']
            if quiet:
                update_cmd.append('-qq')
            subprocess.run(update_cmd, check=True, capture_output=quiet)
            
            # Install all packages at once
            install_cmd = ['apt-get', 'install', '-y']
            if quiet:
                install_cmd.append('-qq')
            install_cmd.extend(apt_packages.keys())
            
            subprocess.run(install_cmd, check=True, capture_output=quiet)
            
            # Mark all as successful
            for package, tools in apt_packages.items():
                for tool in tools:
                    results[tool] = {
                        'success': True,
                        'tool': tool,
                        'package': package,
                        'method': 'apt'
                    }
                    
        except subprocess.CalledProcessError as e:
            # Mark all as failed
            for package, tools in apt_packages.items():
                for tool in tools:
                    results[tool] = {
                        'success': False,
                        'tool': tool,
                        'error': str(e),
                        'method': 'apt'
                    }
    
    return results


def install_common_devtools(quiet: bool = True) -> Dict[str, Any]:
    """
    Install a common set of development tools (Java, Maven, Node, npm).
    
    Args:
        quiet: If True, suppress output
        
    Returns:
        dict: Installation results for each tool
    """
    common_tools = ['java', 'maven', 'node', 'npm']
    return install_multiple_tools(common_tools, quiet=quiet)


def ensure_tool_available(tool_name: str, auto_install: bool = False) -> Dict[str, Any]:
    """
    Ensure a tool is available, optionally installing it.
    
    Args:
        tool_name: Name of the tool
        auto_install: If True, attempt to install if missing
        
    Returns:
        dict: Status and information about the tool
    """
    # Check if already available
    if check_tool_installed(tool_name):
        return {
            'available': True,
            'tool': tool_name,
            'path': shutil.which(tool_name)
        }
    
    # Not available
    if auto_install:
        env = detect_environment()
        
        # Only auto-install in safe environments
        if env in ['colab', 'kaggle'] and can_use_apt_without_password():
            result = install_tool_via_apt(tool_name, quiet=True)
            
            if result['success']:
                return {
                    'available': True,
                    'tool': tool_name,
                    'installed': True,
                    'method': result['method']
                }
        
        # Can't auto-install
        return {
            'available': False,
            'tool': tool_name,
            'error': 'Auto-install not available in this environment',
            'install_commands': get_install_command(tool_name, env)
        }
    
    # Not available and no auto-install
    return {
        'available': False,
        'tool': tool_name,
        'install_commands': get_install_command(tool_name)
    }


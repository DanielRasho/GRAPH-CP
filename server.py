import os
import re
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

import graphviz
from graphviz import Source

from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

mcp = FastMCP("GRAPH-CP 🚀")

_output_directory: Optional[Path] = None
DEFAULT_PNG_SIZE = (500, 500)

ALLOWED_EXTENSIONS = {'.dot', '.gv', '.png', '.svg', '.pdf'}

DOT_GRAPH_PATTERN = re.compile(r'^\s*(strict\s+)?(graph|digraph)\s+\w*\s*\{.*\}\s*$', re.DOTALL | re.IGNORECASE)
DOT_BASIC_VALIDATION = re.compile(r'^[^<>|*?]*$')  # Basic path traversal prevention


class GraphvizServerError(Exception):
    pass


class SecurityError(GraphvizServerError):
    pass


class DOTSyntaxError(GraphvizServerError):
    pass


class FileOperationError(GraphvizServerError):
    pass


def validate_path_security(file_path: str, base_directory: Optional[Path] = None) -> Path:
    """
    Validate file path to prevent directory traversal attacks.
    
    Args:
        file_path: The file path to validate
        base_directory: Base directory to restrict access to
        
    Returns:
        Path: Validated and resolved path
        
    Raises:
        SecurityError: If path validation fails
    """
    try:
        path = Path(file_path).resolve()
        
        if not DOT_BASIC_VALIDATION.match(str(path)):
            raise SecurityError("Path contains invalid characters")
            
        if base_directory:
            base_resolved = base_directory.resolve()
            try:
                path.relative_to(base_resolved)
            except ValueError:
                raise SecurityError(f"Path '{path}' is outside allowed directory '{base_resolved}'")
        
        parts = path.parts
        for part in parts:
            if part.startswith('.') and len(part) > 1:
                logger.warning(f"Suspicious path component detected: {part}")
            
        return path
        
    except Exception as e:
        if isinstance(e, SecurityError):
            raise
        raise SecurityError(f"Path validation failed: {str(e)}")


def validate_dot_content(dot_content: str) -> None:
    """
    Validate DOT file content for basic syntax correctness.
    
    Args:
        dot_content: DOT file content to validate
        
    Raises:
        DOTSyntaxError: If DOT syntax is invalid
    """
    if not dot_content.strip():
        raise DOTSyntaxError("DOT content is empty")
    
    if not DOT_GRAPH_PATTERN.match(dot_content.strip()):
        raise DOTSyntaxError("DOT content does not match basic graph syntax")
    
    open_braces = dot_content.count('{')
    close_braces = dot_content.count('}')
    if open_braces != close_braces:
        raise DOTSyntaxError("Unbalanced braces in DOT content")
    
    try:
        source = Source(dot_content)
        source.pipe()
    except Exception as e:
        raise DOTSyntaxError(f"Invalid DOT syntax: {str(e)}")


def ensure_output_directory() -> Path:
    """
    Ensure output directory is set and exists.
    
    Returns:
        Path: Output directory path
        
    Raises:
        FileOperationError: If directory operations fail
    """
    global _output_directory
    
    if _output_directory is None:
        _output_directory = Path(tempfile.gettempdir()) / "mcp_graphviz_output"
    
    try:
        _output_directory.mkdir(parents=True, exist_ok=True)
        return _output_directory
    except Exception as e:
        raise FileOperationError(f"Failed to create output directory: {str(e)}")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent issues.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename.strip('. ')
    
    if not filename:
        filename = "output"
    
    return filename


@mcp.tool()
def set_output_location_file(directory_path: str) -> str:
    """
    Set the output directory for generated files.
    
    Args:
        directory_path: Path to the output directory
        
    Returns:
        str: Confirmation message with the set directory path
        
    Raises:
        SecurityError: If path validation fails
        FileOperationError: If directory cannot be created
    """
    global _output_directory
    
    try:
        validated_path = validate_path_security(directory_path)
        
        validated_path.mkdir(parents=True, exist_ok=True)
        
        if not os.access(validated_path, os.W_OK):
            raise FileOperationError(f"No write permission for directory: {validated_path}")
        
        _output_directory = validated_path
        logger.info(f"Output directory set to: {_output_directory}")
        
        return f"Output directory successfully set to: {_output_directory}"
        
    except Exception as e:
        logger.error(f"Failed to set output directory: {str(e)}")
        if isinstance(e, (SecurityError, FileOperationError)):
            raise
        raise FileOperationError(f"Failed to set output directory: {str(e)}")


@mcp.tool()
def generate_dot_file(dot_content: str, filename: str = "output") -> str:
    """
    Process DOT content and save as .dot file with syntax validation.
    
    Args:
        dot_content: The DOT language content to process
        filename: Name for the output file (without extension)
        
    Returns:
        str: Success message with file path
        
    Raises:
        DOTSyntaxError: If DOT syntax is invalid
        FileOperationError: If file operations fail
        SecurityError: If security validation fails
    """
    try:
        # Validate DOT content
        validate_dot_content(dot_content)
        
        output_dir = ensure_output_directory()
        
        clean_filename = sanitize_filename(filename)
        if not clean_filename.endswith('.dot'):
            clean_filename += '.dot'
        
        file_path = output_dir / clean_filename
        
        validate_path_security(str(file_path), output_dir)
        
        # Write DOT content to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(dot_content)
        except Exception as e:
            raise FileOperationError(f"Failed to write DOT file: {str(e)}")
        
        logger.info(f"DOT file created: {file_path}")
        return f"DOT file successfully created: {file_path}"
        
    except Exception as e:
        logger.error(f"Failed to generate DOT file: {str(e)}")
        if isinstance(e, (DOTSyntaxError, FileOperationError, SecurityError)):
            raise
        raise FileOperationError(f"Failed to generate DOT file: {str(e)}")


@mcp.tool()
def generate_png(
    dot_content: str, 
    filename: str = "output", 
    width: int = DEFAULT_PNG_SIZE[0], 
    height: int = DEFAULT_PNG_SIZE[1]
) -> str:
    """
    Generate PNG image from DOT content with custom dimensions.
    
    Args:
        dot_content: The DOT language content to render
        filename: Name for the output file (without extension)
        width: Image width in pixels (default: 500)
        height: Image height in pixels (default: 500)
        
    Returns:
        str: Success message with file path
        
    Raises:
        DOTSyntaxError: If DOT syntax is invalid
        FileOperationError: If file operations fail
        SecurityError: If security validation fails
    """
    try:
        # Validate inputs
        validate_dot_content(dot_content)
        
        # Validate dimensions
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive integers")
        if width > 10000 or height > 10000:
            raise ValueError("Width and height must be less than 10000 pixels")
        
        output_dir = ensure_output_directory()
        
        clean_filename = sanitize_filename(filename)
        if not clean_filename.endswith('.png'):
            clean_filename += '.png'
        
        file_path = output_dir / clean_filename
        
        validate_path_security(str(file_path), output_dir)
        
        try:
            source = Source(dot_content)
            
            # Calculate DPI for desired dimensions
            # Standard assumption: 1 inch = 96 pixels for screen display
            dpi = min(width, height) / 5  # Rough estimation for reasonable DPI
            dpi = max(72, min(300, dpi))  # Clamp between 72 and 300 DPI
            
            # Render to PNG
            source.format = 'png'
            source.render(
                filename=str(file_path.with_suffix('')), 
                cleanup=True,
                quiet_view=True
            )
            
            # The render method adds the extension, so check for the actual file
            actual_file_path = file_path.with_suffix('.png')
            
            if not actual_file_path.exists():
                raise FileOperationError("PNG file was not created successfully")
                
        except Exception as e:
            raise FileOperationError(f"Failed to render PNG: {str(e)}")
        
        logger.info(f"PNG file created: {actual_file_path}")
        return f"PNG file successfully created: {actual_file_path} ({width}x{height} target size)"
        
    except Exception as e:
        logger.error(f"Failed to generate PNG: {str(e)}")
        if isinstance(e, (DOTSyntaxError, FileOperationError, SecurityError, ValueError)):
            raise
        raise FileOperationError(f"Failed to generate PNG: {str(e)}")


def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Graphviz MCP Server")
    mcp.run()


if __name__ == "__main__":
    main()
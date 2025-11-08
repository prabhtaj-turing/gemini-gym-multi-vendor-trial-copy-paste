#!/usr/bin/env python3
"""
Main script to convert files or folders to JSON representations
that can be handled by simulated APIs.

Usage:
    python preprocessor.py <input_path> [--output-folder <output_folder>] [--log-level <level>] [--workers <num_workers>]

Example:
    python preprocessor.py files
    python preprocessor.py "files/subfolder with spaces"
    python preprocessor.py /absolute/path/to/files
    python preprocessor.py ../other-folder --output-folder converted_files --log-level DEBUG --workers 4
"""

import os
import sys
import argparse
import json
import logging
import traceback
import shutil
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

# Import the conversion modules
from gdocs_converter import convert_doc_to_gdoc_format
from gsheets_converter import convert_excel_to_gsheets_format
from gslides_converter import convert_pptx_to_gslides_format


def setup_logging(log_level='INFO', log_file=None):
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Default log file with timestamp if not provided
    if log_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'conversion_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")
    return logger, log_file


def get_converter_for_file(file_path):
    """Determine which converter to use based on file extension."""
    file_extension = os.path.splitext(file_path)[1].lower()
    
    # Excel files -> Google Sheets format
    if file_extension in ['.xlsx', '.xls', '.xlt']:
        return convert_excel_to_gsheets_format, "gsheets"
    
    # PowerPoint files -> Google Slides format
    elif file_extension in ['.pptx', '.ppt']:
        return convert_pptx_to_gslides_format, "gslides"
    
    # Word documents -> Google Docs format (handled by gdrive converter for now)
    elif file_extension in ['.docx', '.doc']:
        return convert_doc_to_gdoc_format, "gdocs"
    
    # Files that should be processed only during hydration (no JSON conversion)
    elif file_extension in ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico']:
        return None, "hydrate_only"
    
    # All other files -> Google Drive format
    else:
        return convert_doc_to_gdoc_format, "gdrive"


def count_files_to_process(input_path):
    """Count total number of files to process for progress tracking."""
    total_files = 0
    if os.path.isfile(input_path):
        total_files = 1
    else:
        for root, dirs, files in os.walk(input_path):
            total_files += len(files)
    return total_files


def process_file(input_file_path, output_dir, base_name, logger, pbar=None):
    """Process a single file and save the JSON representation."""
    logger.debug(f"Starting processing: {input_file_path}")
    
    try:
        # Get the appropriate converter
        converter_func, converter_type = get_converter_for_file(input_file_path)
        
        file_name = os.path.basename(input_file_path)
        original_file_output_path = os.path.join(output_dir, file_name)
        
        # Copy the original file to the output directory
        shutil.copy2(input_file_path, original_file_output_path)
        
        # Handle files that should only be processed during hydration
        if converter_type == "hydrate_only":
            logger.info(f"SUCCESS: {input_file_path} -> {converter_type} (original file only): {original_file_output_path}")
            logger.debug(f"Skipping JSON creation for {converter_type} file: {file_name}")
            
            if pbar:
                pbar.set_postfix_str(f"✓ {os.path.basename(input_file_path)} (hydrate_only)")
            
            return True, None
        
        # Convert the file to JSON
        json_data = converter_func(input_file_path)
        
        # Create output filename preserving original extension
        output_filename = f"{file_name}.json"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save the JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"SUCCESS: {input_file_path} -> {converter_type} format: {output_path}")
        logger.debug(f"Original file copied to: {original_file_output_path}")
        
        if pbar:
            pbar.set_postfix_str(f"✓ {os.path.basename(input_file_path)}")
        
        return True, None
        
    except Exception as e:
        error_msg = f"ERROR: {input_file_path} - {str(e)}"
        logger.error(error_msg)
        logger.debug(f"Full traceback for {input_file_path}:\n{traceback.format_exc()}")
        
        if pbar:
            pbar.set_postfix_str(f"✗ {os.path.basename(input_file_path)}")
        
        return False, str(e)


def worker_process_file(task_data):
    """Worker function for parallel processing of files.
    
    Args:
        task_data: Tuple containing (input_file_path, output_dir, base_name, log_level)
    
    Returns:
        Tuple of (success, error_msg, input_file_path, output_dir)
    """
    input_file_path, output_dir, base_name, log_level = task_data
    
    # Import conversion modules here to ensure they're available in worker processes
    try:
        from gdocs_converter import convert_doc_to_gdoc_format
        from gsheets_converter import convert_excel_to_gsheets_format
        from gslides_converter import convert_pptx_to_gslides_format
    except ImportError as e:
        return False, f"Failed to import conversion modules: {e}", input_file_path, output_dir
    
    # Set up logging for this worker process
    worker_logger = logging.getLogger(f"worker_{os.getpid()}")
    if not worker_logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(getattr(logging, log_level.upper()))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        worker_logger.addHandler(handler)
        worker_logger.setLevel(getattr(logging, log_level.upper()))
    
    try:
        # Get the appropriate converter
        converter_func, converter_type = get_converter_for_file(input_file_path)
        
        file_name = os.path.basename(input_file_path)
        original_file_output_path = os.path.join(output_dir, file_name)
        
        # Copy the original file to the output directory
        shutil.copy2(input_file_path, original_file_output_path)
        
        # Handle files that should only be processed during hydration
        if converter_type == "hydrate_only":
            worker_logger.info(f"SUCCESS: {input_file_path} -> {converter_type} (original file only): {original_file_output_path}")
            return True, None, input_file_path, output_dir
        
        # Convert the file to JSON
        json_data = converter_func(input_file_path)
        
        # Create output filename preserving original extension
        output_filename = f"{file_name}.json"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save the JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        worker_logger.info(f"SUCCESS: {input_file_path} -> {converter_type} format: {output_path}")
        
        return True, None, input_file_path, output_dir
        
    except Exception as e:
        error_msg = f"ERROR: {input_file_path} - {str(e)}"
        worker_logger.error(error_msg)
        
        return False, str(e), input_file_path, output_dir


def process_path(input_path, output_folder, logger, num_workers=1, log_level='INFO'):
    """Process a file or folder and save to output folder using parallel processing."""
    logger.info(f"Starting processing: {input_path} -> {output_folder}")
    logger.info(f"Using {num_workers} worker processes")
    
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Collect all files to process
    files_to_process = []
    
    if os.path.isfile(input_path):
        # Single file processing
        logger.info(f"Processing single file: {input_path}")
        input_file_path = input_path
        output_subdir = output_folder
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        files_to_process.append((input_file_path, output_subdir, base_name, log_level))
    else:
        # Folder processing
        logger.info(f"Processing folder: {input_path}")
        for root, dirs, files in os.walk(input_path):
            for file in files:
                input_file_path = os.path.join(root, file)
                
                # Create relative path structure in output
                rel_path = os.path.relpath(root, input_path)
                if rel_path == ".":
                    output_subdir = output_folder
                else:
                    output_subdir = os.path.join(output_folder, rel_path)
                    os.makedirs(output_subdir, exist_ok=True)
                
                base_name = os.path.splitext(file)[0]
                files_to_process.append((input_file_path, output_subdir, base_name, log_level))
    
    total_files = len(files_to_process)
    logger.info(f"Found {total_files} files to process")
    
    if total_files == 0:
        logger.warning("No files found to process")
        return 0, 0, []
    
    # Initialize counters and error tracking
    processed_count = 0
    error_count = 0
    errors = []
    
    # Process files in parallel
    start_time = time.time()
    
    if num_workers == 1:
        # Single-threaded processing (original behavior)
        logger.info("Using single-threaded processing")
        with tqdm(total=total_files, desc="Converting files", unit="file") as pbar:
            for task_data in files_to_process:
                input_file_path, output_subdir, base_name, _ = task_data
                success, error_msg = process_file(input_file_path, output_subdir, base_name, logger, pbar)
                
                if success:
                    processed_count += 1
                else:
                    error_count += 1
                    errors.append({
                        'file': input_file_path,
                        'error': error_msg
                    })
                
                pbar.update(1)
                pbar.set_description(f"Converting files (✓{processed_count} ✗{error_count})")
    else:
        # Parallel processing
        logger.info(f"Using parallel processing with {num_workers} workers")
        
        # Create progress bar
        with tqdm(total=total_files, desc="Converting files", unit="file") as pbar:
            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                # Submit all tasks
                future_to_task = {
                    executor.submit(worker_process_file, task_data): task_data 
                    for task_data in files_to_process
                }
                
                # Process completed tasks
                for future in as_completed(future_to_task):
                    try:
                        success, error_msg, input_file_path, output_dir = future.result()
                        
                        if success:
                            processed_count += 1
                            pbar.set_postfix_str(f"✓ {os.path.basename(input_file_path)}")
                        else:
                            error_count += 1
                            errors.append({
                                'file': input_file_path,
                                'error': error_msg
                            })
                            pbar.set_postfix_str(f"✗ {os.path.basename(input_file_path)}")
                        
                        pbar.update(1)
                        pbar.set_description(f"Converting files (✓{processed_count} ✗{error_count})")
                        
                    except Exception as e:
                        # Handle any exceptions from the worker processes
                        error_count += 1
                        task_data = future_to_task[future]
                        input_file_path = task_data[0]
                        error_msg = f"Worker process error: {str(e)}"
                        errors.append({
                            'file': input_file_path,
                            'error': error_msg
                        })
                        logger.error(f"Worker process failed for {input_file_path}: {e}")
                        
                        pbar.update(1)
                        pbar.set_description(f"Converting files (✓{processed_count} ✗{error_count})")
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    # Log final summary
    logger.info("=" * 60)
    logger.info("PROCESSING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total files found: {total_files}")
    logger.info(f"Files processed successfully: {processed_count}")
    logger.info(f"Files with errors: {error_count}")
    logger.info(f"Success rate: {(processed_count/total_files)*100:.1f}%")
    logger.info(f"Processing time: {processing_time:.2f} seconds")
    logger.info(f"Average time per file: {processing_time/total_files:.2f} seconds")
    
    # Log error summary if there were errors
    if errors:
        logger.warning(f"\nERROR SUMMARY ({len(errors)} files failed):")
        logger.warning("-" * 40)
        for i, error in enumerate(errors, 1):
            logger.warning(f"{i:3d}. {error['file']}")
            logger.warning(f"     Error: {error['error']}")
    
    # Print summary to console
    print(f"\n{'='*60}")
    print("PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Total files found: {total_files}")
    print(f"Files processed successfully: {processed_count}")
    print(f"Files with errors: {error_count}")
    print(f"Success rate: {(processed_count/total_files)*100:.1f}%")
    print(f"Processing time: {processing_time:.2f} seconds")
    print(f"Average time per file: {processing_time/total_files:.2f} seconds")
    
    if errors:
        print(f"\n⚠️  {len(errors)} files failed to process. Check the log file for details.")
    
    return processed_count, error_count, errors


def get_optimal_worker_count():
    """Get the optimal number of worker processes based on system resources."""
    cpu_count = mp.cpu_count()
    
    # For I/O intensive operations (file processing), we can use more workers than CPU cores
    # A good rule of thumb is 2-4x the number of CPU cores for I/O bound tasks
    optimal_workers = min(cpu_count * 2, 8)  # Cap at 8 to avoid overwhelming the system
    
    return optimal_workers, cpu_count


def normalize_input_path(input_arg, script_dir):
    """Normalize the input path argument to handle various input formats."""
    # If it's an absolute path, use it as is
    if os.path.isabs(input_arg):
        return input_arg
    
    # If it's a relative path, make it relative to the script directory
    return os.path.join(script_dir, input_arg)


def main():
    parser = argparse.ArgumentParser(
        description="Convert files to JSON representations for simulated APIs with parallel processing support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python preprocessor.py files
  python preprocessor.py "files/subfolder with spaces"
  python preprocessor.py /absolute/path/to/files
  python preprocessor.py ../other-folder --output-folder converted_files --log-level DEBUG --workers 4
  
File type conversions:
  .xlsx, .xls    -> Google Sheets format
  .pptx, .ppt    -> Google Slides format  
  .docx, .doc    -> Google Docs format (via Google Drive)
  Other files    -> Google Drive format

Performance tips:
  - Use --workers 4 (or number of CPU cores) for faster processing
  - More workers = faster processing but higher memory usage
  - For I/O intensive operations, more workers help significantly
  - For CPU intensive operations, match workers to CPU cores

Note: Input path can be relative to script location or absolute path.
      Spaces in folder names should be quoted.
      Log files are saved to logs/ directory with timestamps.
        """
    )
    
    parser.add_argument(
        'input_path',
        help='Path to file or folder to process (relative to script location or absolute path)'
    )
    
    parser.add_argument(
        '--output-folder',
        default=None,
        help='Output folder name within output-data/ (default: derived from input path)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set the logging level (default: INFO)'
    )
    
    # Get optimal worker count for default
    optimal_workers, cpu_count = get_optimal_worker_count()
    
    parser.add_argument(
        '--workers',
        type=int,
        default=optimal_workers,
        help=f'Number of worker processes to use for parallel processing (default: {optimal_workers}, system has {cpu_count} CPU cores)'
    )
    
    args = parser.parse_args()
    
    # Validate workers argument
    if args.workers < 1:
        print("Error: Number of workers must be at least 1")
        sys.exit(1)
    
    # Get CPU count for reference
    cpu_count = mp.cpu_count()
    optimal_workers, _ = get_optimal_worker_count()
    
    if args.workers > cpu_count * 4:
        print(f"Warning: Using {args.workers} workers but system has only {cpu_count} CPU cores.")
        print(f"Recommended: Use {optimal_workers} workers for optimal performance.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # Set up logging
    logger, log_file = setup_logging(args.log_level)
    
    # Log system information
    logger.info(f"System CPU count: {cpu_count}")
    logger.info(f"Optimal worker count: {optimal_workers}")
    logger.info(f"Using {args.workers} worker processes")
    
    # Estimate performance improvement
    if args.workers > 1:
        estimated_speedup = min(args.workers, cpu_count * 2)  # Realistic speedup estimate
        logger.info(f"Estimated speedup: ~{estimated_speedup:.1f}x faster than single-threaded")
        print(f"Estimated speedup: ~{estimated_speedup:.1f}x faster than single-threaded")
    
    # Set up paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_base = os.path.join(script_dir, 'output-data')
    
    # Normalize input path
    input_path = normalize_input_path(args.input_path, script_dir)
    
    # Determine output folder name
    if args.output_folder:
        output_folder_name = args.output_folder
    else:
        # Use the last part of the input path as output folder name
        output_folder_name = os.path.basename(os.path.normpath(args.input_path))
        if not output_folder_name or output_folder_name == '.':
            output_folder_name = 'converted'
    
    output_folder = os.path.join(output_base, output_folder_name)
    
    # Validate input path exists
    if not os.path.exists(input_path):
        error_msg = f"Input path does not exist: {input_path}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        print(f"\nTip: Input path can be relative to script location or absolute path")
        print(f"     For example: 'files', '../other-folder', or '/absolute/path'")
        print(f"\nAvailable files/folders in script directory ({script_dir}):")
        try:
            for item in os.listdir(script_dir):
                item_path = os.path.join(script_dir, item)
                if os.path.isdir(item_path):
                    print(f"  📁 {item}/")
                else:
                    print(f"  📄 {item}")
        except PermissionError:
            print(f"  Cannot list contents of {script_dir} (permission denied)")
        sys.exit(1)
    
    # Log configuration
    logger.info("=" * 60)
    logger.info("FILE CONVERSION STARTED")
    logger.info("=" * 60)
    logger.info(f"Input path: {input_path}")
    logger.info(f"Output folder: {output_folder}")
    logger.info(f"Log level: {args.log_level}")
    logger.info(f"Log file: {log_file}")
    
    print(f"Input path: {input_path}")
    print(f"Output folder: {output_folder}")
    print(f"Log file: {log_file}")
    print("=" * 50)
    
    # Process the path (file or folder)
    try:
        processed_count, error_count, errors = process_path(input_path, output_folder, logger, args.workers, args.log_level)
        
        # Exit with appropriate code
        if error_count == 0:
            logger.info("All files processed successfully!")
            sys.exit(0)
        else:
            logger.warning(f"Processing completed with {error_count} errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        print("\n⚠️  Processing interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error during processing: {e}")
        logger.debug(f"Full traceback:\n{traceback.format_exc()}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Set multiprocessing start method for better compatibility
    if sys.platform.startswith('win'):
        # On Windows, use 'spawn' method for better compatibility
        mp.set_start_method('spawn', force=True)
    else:
        # On Unix-like systems, use 'fork' method for better performance
        try:
            mp.set_start_method('fork', force=True)
        except RuntimeError:
            # If fork is not available, use spawn
            mp.set_start_method('spawn', force=True)
    
    main() 
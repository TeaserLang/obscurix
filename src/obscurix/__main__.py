# This file handles the CLI entry point using argparse.
# It accepts a filename and an optional --debug flag.

import sys
import argparse
from obscurix.interpreter import ObscurixRuntime # Import the main runtime

def main():
    """ Main CLI entry point for the Obscurix interpreter. """
    
    parser = argparse.ArgumentParser(
        description="Obscurix Language Interpreter.",
        epilog="Enjoy this wonderfully obscure language!"
    )
    
    parser.add_argument(
        'filename',
        type=str,
        help="The .obx file to execute."
    )
    
    parser.add_argument(
        '--debug',
        action='store_true', # This makes it a boolean flag
        help="Enable debug logging to trace execution steps."
    )
    
    try:
        args = parser.parse_args()
        
        # Pass the debug flag to the runtime
        runtime = ObscurixRuntime(args.filename, debug=args.debug)
        runtime.run()
        
    except FileNotFoundError as e:
        print(f"!!! FILE ERROR !!!\n{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # General runtime errors
        print(f"!!! PYTHON RUNTIME ERROR !!!\n{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()


import sys
import argparse
from python_module.component.pipeline import run_pipeline

def parse_args():

    parser = argparse.ArgumentParser(prog="pipeline_yolo.py",
                    description="pipeline_yolo multi stream, multi model inference reference app")
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output",
        choices=["display", "file", "rtsp", "silent"],
    )
    # Check input arguments
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    print(vars(args))
    return args

if __name__ == '__main__':
    args = parse_args()
    sys.exit(run_pipeline(args))

import os
import argparse
from converter import NWAConverter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="path to file or directory")
    parser.add_argument("-o", "--output", help="output directory", default=".")
    args = parser.parse_args()
    path = args.path
    output = args.output

    if os.path.isfile(path):
        converter = NWAConverter(path, output)
        converter.convert()
    elif os.path.isdir(path):
        for file in os.listdir(path):
            if file.endswith(".nwa") or file.endswith(".nwk") or file.endswith(".ovk"):
                converter = NWAConverter(os.path.join(path, file), output)
                converter.convert()

if __name__ == "__main__":
    main()

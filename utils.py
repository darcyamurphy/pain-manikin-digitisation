import os
from pathlib import Path
import re
import pandas as pd

def get_files_matching_string(reg_ex: str, search_dirs: list[str]) -> list[str]:
    files = []
    p = re.compile(reg_ex)
    for source_dir in search_dirs:
        for f in os.listdir(source_dir):
            if p.search(Path(f).stem):
                files.append(os.path.join(source_dir, f))

    return files

def write_file_list(files: list[str], filename: str):
    with open(filename, 'w') as file_out:
        for f in files:
            file_out.write(f'{f}\n')

def csv_to_boolean(source_path: str, output_path: str):
    """
    Takes a csv file with cell values of 1 or blank and converts 1 to True and blank/nan to False
    Assumes filename as index column
    :param source_path: file to read
    :param output_path: file to write
    :return:
    """
    df = pd.read_csv(source_path)
    not_na = df.notna()
    not_na['filename'] = df['filename']
    not_na.to_csv(output_path, index=False)

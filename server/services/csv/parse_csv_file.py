import csv
import pandas as pd

def parse_csv_files(files):
    parsed_files_and_statuses = []
    for file_id, file in files.items():
        try:
            # Read the file content and decode it
            file_content = file.read().decode('utf-8')
            
            # Try to detect the delimiter
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(file_content)  # Use first 1024 characters to detect
            delimiter = dialect.delimiter
            
            # If delimiter is not detected or results in only one column, try common delimiters
            common_delimiters = [',', ';', '\t', '|']
            
            # Seek to the beginning of the file
            file.seek(0)
            
            df = pd.read_csv(
                file,
                sep=delimiter,
                encoding='utf-8',
                engine='python',
                on_bad_lines='skip',
                quoting=csv.QUOTE_NONE,  # Don't expect quotes
                skipinitialspace=True,   # Skip spaces after delimiter
            )
            
            # If only one column is detected, try common delimiters
            if len(df.columns) == 1:
                for sep in common_delimiters:
                    file.seek(0)  # Reset file pointer
                    df = pd.read_csv(
                        file,
                        sep=sep,
                        encoding='utf-8',
                        engine='python',
                        on_bad_lines='skip',
                        quoting=csv.QUOTE_NONE,
                        skipinitialspace=True,
                    )
                    if len(df.columns) > 1:
                        delimiter = sep
                        break  # Found a working delimiter
            elif len(df.columns) == 0:
                for sep in common_delimiters:
                    file.seek(0)  # Reset file pointer
                    df = pd.read_csv(
                        file,
                        sep=sep,
                        encoding='utf-8',
                        engine='python',
                        on_bad_lines='skip',
                        quoting=csv.QUOTE_NONE,
                        skipinitialspace=True,
                    )
                    if len(df.columns) > 0:
                        delimiter = sep
                        break  # Found a working delimiter
            
            file = {
                "parsedColumns" : [col.strip("'\"") for col in df.columns.tolist()],
                "fileId" : file_id,
                "delimiter" : delimiter
            }
            parsed_files_and_statuses.append(file)
        except pd.errors.ParserError as e:
            print(f"Error parsing file {file_id}: {e}")

    return parsed_files_and_statuses
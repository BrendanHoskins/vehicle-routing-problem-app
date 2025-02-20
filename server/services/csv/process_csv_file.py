import io
import pandas as pd
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed


def process_selected_columns(file_data):
    """
    Optimized function to process selected columns from provided CSV files.
    Returns data formatted for VRP solving.
    """
    processed_data = {
        'addresses': [],
        'depot_indices': [],
        'identifiers': []
    }
    
    try:
        file_content = file_data['content']
        selected_columns = file_data['selectedColumns']
        column_mappings = file_data['columnMappings']  # e.g., {'address': 'Address Col', 'identifier': 'ID Col', 'depot': 'Is Depot Col'}
        delimiter = file_data['delimiter']

        # Use StringIO to create a file-like object from the string
        csv_file = io.StringIO(file_content)
        
        # Read the CSV in chunks to handle large files efficiently
        chunk_size = 100  # Adjust based on memory capacity
        chunk_iter = pd.read_csv(
            csv_file,
            usecols=selected_columns,
            skipinitialspace=True,
            encoding='utf-8',
            engine='python',
            on_bad_lines='skip',
            sep=delimiter,
            quoting=csv.QUOTE_MINIMAL,
            chunksize=chunk_size,
            skip_blank_lines=True
        )

        # Use ThreadPoolExecutor for concurrent chunk processing
        with ThreadPoolExecutor(max_workers=5) as executor:
            chunk_futures = []
            
            for df_chunk in chunk_iter:
                future = executor.submit(process_chunk, df_chunk, column_mappings)
                chunk_futures.append(future)
                
            # Collect results from all chunks
            for future in as_completed(chunk_futures):
                chunk_result = future.result()
                if chunk_result:
                    processed_data['addresses'].extend(chunk_result['addresses'])
                    processed_data['depot_indices'].extend(chunk_result['depot_indices'])
                    processed_data['identifiers'].extend(chunk_result['identifiers'])

        return processed_data

    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        return None

def process_chunk(df_chunk, column_mappings):
    """
    Process a chunk of the CSV data and return formatted results.
    """
    chunk_results = {
        'addresses': [],
        'depot_indices': [],
        'identifiers': []
    }
    
    df_chunk.dropna(how="all", axis=0, inplace=True)
    
    for _, row in df_chunk.iterrows():
        # Extract address
        if 'address' in column_mappings:
            address_col = column_mappings['address']
            # Use iloc or direct column access instead of get()
            address = str(row[address_col]).strip()
            if address and address.lower() != 'nan':
                chunk_results['addresses'].append(address)
            else:
                chunk_results['addresses'].append("Unknown Address")
            
        # Check if this location is a depot
        if 'depot' in column_mappings:
            depot_col = column_mappings['depot']
            # Use pandas.notna() and direct column access
            is_depot = row[depot_col] == 1
            if is_depot:
                chunk_results['depot_indices'].append(len(chunk_results['addresses']) - 1)
                
        # Extract identifier if present
        if 'identifier' in column_mappings:
            identifier_col = column_mappings['identifier']
            # Use direct column access
            identifier = str(row[identifier_col]).strip()
            chunk_results['identifiers'].append(identifier if identifier and identifier.lower() != 'nan' else str(len(chunk_results['identifiers']) + 1))
        else:
            chunk_results['identifiers'].append(str(len(chunk_results['identifiers']) + 1))

    return chunk_results
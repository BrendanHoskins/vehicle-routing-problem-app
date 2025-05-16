import io
import pandas as pd
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed


class CSVProcessor:
    """
    Generic CSV processor that can handle different types of CSV processing based on mapping configurations.
    """
    def __init__(self):
        """Initialize CSVProcessor with mapping configurations."""
        self.mapping_configs = {
            'deliveries': self._get_delivery_mapping_config(),
            'trucks': self._get_truck_mapping_config(),
            'depots': self._get_depot_mapping_config(),
            'pickups': self._get_pickup_mapping_config()
        }

    @staticmethod
    def _get_delivery_mapping_config():
        return {
            'output_format': [],
            'field_processors': {
                'uid': lambda row, col, results: results.append({
                    'identifier': str(row[col]).strip() if str(row[col]).strip().lower() != 'nan' 
                        else str(len(results) + 1),
                    'current_location': '',
                    'destination': '',
                    'volume': 0.0,
                    'weight': 0.0
                }),
                'current_location': lambda row, col, results: results[-1].update({
                    'current_location': str(row[col]).strip() if str(row[col]).strip().lower() != 'nan' 
                        else "Unknown Location"
                }),
                'destination': lambda row, col, results: results[-1].update({
                    'destination': str(row[col]).strip() if str(row[col]).strip().lower() != 'nan' 
                        else "Unknown Destination"
                }),
                'volume': lambda row, col, results: results[-1].update({
                    'volume': float(row[col]) if pd.notna(row[col]) else 0.0
                }),
                'weight': lambda row, col, results: results[-1].update({
                    'weight': float(row[col]) if pd.notna(row[col]) else 0.0
                })
            },
            'default_handlers': {}
        }

    @staticmethod
    def _get_truck_mapping_config():
        return {
            'output_format': [],
            'field_processors': {
                'uid': lambda row, col, results: results.append({
                    'truck_identifier': str(row[col]).strip(),
                    'max_volume': 0.0,
                    'max_weight': 0.0,
                    'current_location': '',
                    'end_location': '',
                    'range': 0.0
                }),
                'max_volume': lambda row, col, results: results[-1].update({
                    'max_volume': float(row[col]) if pd.notna(row[col]) else 0.0
                }),
                'max_weight': lambda row, col, results: results[-1].update({
                    'max_weight': float(row[col]) if pd.notna(row[col]) else 0.0
                }),
                'current_location': lambda row, col, results: results[-1].update({
                    'current_location': str(row[col]).strip() if str(row[col]).strip().lower() != 'nan' 
                        else "Unknown Location"
                }),
                'end_location': lambda row, col, results: results[-1].update({
                    'end_location': str(row[col]).strip() if str(row[col]).strip().lower() != 'nan' 
                        else "Unknown Location"
                }),
                'range': lambda row, col, results: results[-1].update({
                    'range': float(row[col]) if pd.notna(row[col]) else 0.0
                })
            },
            'default_handlers': {}
        }

    @staticmethod
    def _get_depot_mapping_config():
        return {
            'output_format': [],
            'field_processors': {
                'uid': lambda row, col, results: results.append({
                    'identifier': str(row[col]).strip() if str(row[col]).strip().lower() != 'nan' 
                        else str(len(results) + 1),
                    'location': ''
                }),
                'location': lambda row, col, results: results[-1].update({
                    'location': str(row[col]).strip() if str(row[col]).strip().lower() != 'nan' 
                        else "Unknown Location"
                })
            },
            'default_handlers': {}
        }

    @staticmethod
    def _get_pickup_mapping_config():
        return {
            'output_format': [],
            'field_processors': {
                'uid': lambda row, col, results: results.append({
                    'identifier': str(row[col]).strip() if str(row[col]).strip().lower() != 'nan' 
                        else str(len(results) + 1),
                    'current_location': '',
                    'destination': '',
                    'volume': 0.0,
                    'weight': 0.0
                }),
                'current_location': lambda row, col, results: results[-1].update({
                    'current_location': str(row[col]).strip() if str(row[col]).strip().lower() != 'nan' 
                        else "Unknown Location"
                }),
                'destination': lambda row, col, results: results[-1].update({
                    'destination': str(row[col]).strip() if str(row[col]).strip().lower() != 'nan' 
                        else "Unknown Destination"
                }),
                'volume': lambda row, col, results: results[-1].update({
                    'volume': float(row[col]) if pd.notna(row[col]) else 0.0
                }),
                'weight': lambda row, col, results: results[-1].update({
                    'weight': float(row[col]) if pd.notna(row[col]) else 0.0
                })
            },
            'default_handlers': {}
        }

    def process_files(self, file_data):
        """
        Generic function to process CSV files based on file type.
        Handles multiple file types (addresses and trucks) and processes them in chunks.
        """
        try:
            results = {}
            for file_type, file_info in file_data.items():
                # Get the appropriate mapping config based on file type
                mapping_config = self.mapping_configs.get(file_type)
                if not mapping_config:
                    print(f"No mapping configuration found for file type: {file_type}")
                    continue

                # Initialize results structure for this file type
                results[file_type] = mapping_config['output_format'].copy()
                
                file_content = file_info['content']
                selected_columns = file_info['selectedColumns']
                column_mappings = file_info['columnMappings']
                delimiter = file_info['delimiter']

                csv_file = io.StringIO(file_content)
                
                # Process file in chunks
                chunk_results = self._process_in_chunks(
                    csv_file, 
                    selected_columns, 
                    column_mappings, 
                    delimiter, 
                    mapping_config
                )
                
                results[file_type] = chunk_results

            return results

        except Exception as e:
            print(f"Error processing CSV: {str(e)}")
            return None

    @staticmethod
    def _process_chunk(df_chunk, column_mappings, mapping_config, results):
        """Process a chunk of data using the provided mapping configuration."""
        field_processors = mapping_config['field_processors']
        default_handlers = mapping_config['default_handlers']
        
        for _, row in df_chunk.iterrows():
            # Process each mapped field
            for field, col in column_mappings.items():
                if field in field_processors:
                    field_processors[field](row, col, results)
            
            # Handle any default processing
            for field, handler in default_handlers.items():
                if field not in column_mappings:
                    handler(results)
                    
        return results

    @staticmethod
    def _process_in_chunks(csv_file, selected_columns, column_mappings, delimiter, mapping_config):
        """Process large files in chunks using ThreadPoolExecutor."""
        chunk_size = 100
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

        # Create a single results dictionary that will be shared across all chunks
        results = mapping_config['output_format'].copy()
        
        # Process chunks sequentially to maintain order and prevent duplicates
        for df_chunk in chunk_iter:
            CSVProcessor._process_chunk(
                df_chunk,
                column_mappings,
                mapping_config,
                results  # Pass the same results dictionary to each chunk
            )

        return results

    @staticmethod
    def parse_csv_files(files):
        """
        Parse multiple CSV files and detect their delimiters.
        Returns a list of dictionaries containing parsed column information.
        """
        parsed_files_and_statuses = []
        for file_id, file in files.items():
            try:
                # Read the file content and decode it
                file_content = file.read().decode('utf-8')
                
                # Try to detect the delimiter
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(file_content)
                delimiter = dialect.delimiter
                
                # Common delimiters to try if automatic detection fails
                common_delimiters = [',', ';', '\t', '|']
                
                # Reset file pointer
                file.seek(0)
                
                df = pd.read_csv(
                    file,
                    sep=delimiter,
                    encoding='utf-8',
                    engine='python',
                    on_bad_lines='skip',
                    quoting=csv.QUOTE_NONE,
                    skipinitialspace=True,
                )
                
                # Try common delimiters if only one or no columns detected
                if len(df.columns) <= 1:
                    for sep in common_delimiters:
                        file.seek(0)
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
                            break
                
                parsed_file = {
                    "parsedColumns": [col.strip("'\"") for col in df.columns.tolist()],
                    "fileId": file_id,
                    "delimiter": delimiter
                }
                parsed_files_and_statuses.append(parsed_file)
            except pd.errors.ParserError as e:
                print(f"Error parsing file {file_id}: {e}")

        return parsed_files_and_statuses
import io
import pandas as pd
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, time

class ExcelFileProcessor:
    def __init__(self):
        self.mapping_configs = {
            'deliveries': self._get_delivery_mapping_config(),
            'trucks': self._get_truck_mapping_config(),
            'depots': self._get_depot_mapping_config(),
            'pickups': self._get_pickup_mapping_config(),
            'employees': self._get_employee_mapping_config()
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
                    'range': 0.0,
                    'mpg': 0.0
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
                }),
                'mpg': lambda row, col, results: results[-1].update({
                    'mpg': float(row[col]) if pd.notna(row[col]) and float(row[col]) > 0 else 1.0
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

    @staticmethod
    def _get_employee_mapping_config():
        return {
            'output_format': [],
            'field_processors': {
                'uid': lambda row, col, results: results.append({
                    'employee_uid': str(row[col]).strip() if str(row[col]).strip().lower() != 'nan' 
                        else f"emp_{len(results) + 1}",
                    'total_hours_available': 0.0,
                    'hourly_pay_rate': 0.0,
                    'truck_uid': ''
                }),
                'total_hours_available': lambda row, col, results: results[-1].update({
                    'total_hours_available': float(row[col]) if pd.notna(row[col]) else 0.0
                }),
                'hourly_pay_rate': lambda row, col, results: results[-1].update({
                    'hourly_pay_rate': float(row[col]) if pd.notna(row[col]) else 0.0
                }),
                'truck_uid': lambda row, col, results: results[-1].update({
                    'truck_uid': str(row[col]).strip() if str(row[col]).strip().lower() != 'nan' else "N/A"
                })
            },
            'default_handlers': {}
        }

    def process_file(self, file_data):
        try:
            results = {}
            for file_type, file_info in file_data.items():

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
    def parse_excel_file_and_return_sheets_and_columns(file):
        try:
            df = pd.read_excel(io=file.stream, sheet_name=None, engine=None)
            mappings = {}
            for sheet_name, data in df.items():
                mappings[sheet_name] = data.columns.tolist()
            return mappings
        except Exception as error:
            print('Error in parse_excel_file_and_return_sheets_and_columns:', error)
            raise Exception('Failed to parse Excel file in parse_excel_file_and_return_sheets_and_columns')

# Modified functions to load rank data directly from CSV files

import csv
import os

def load_rank_limits_from_file(file_path='rank_limit_100.csv'):
    """
    Load rank limits directly from CSV file
    
    Parameters:
    file_path (str): Path to the rank limits CSV file
    
    Returns:
    list: List of rank limits
    """
    try:
        if not os.path.exists(file_path):
            print(f"Rank limits file not found: {file_path}, using defaults")
            return [1, 1, 2, 3, 2, 3, 1, 1]  # Default fallback
        
        with open(file_path, 'r') as f:
            csv_reader = csv.reader(f)
            # Skip header row if present
            headers = next(csv_reader)
            # Read data row
            limit_data = next(csv_reader)
            
            # Convert to integers
            rank_limits = [int(limit) for limit in limit_data]
            print(f"Loaded {len(rank_limits)} rank limits from {file_path}")
            return rank_limits
            
    except Exception as e:
        print(f"Error loading rank limits from file: {e}")
        # Return default fallback values
        return [1, 1, 2, 3, 2, 3, 1, 1]

def load_rank_counts_from_file(file_path='rank_count_100.csv'):
    """
    Load rank counts directly from CSV file
    
    Parameters:
    file_path (str): Path to the rank counts CSV file
    
    Returns:
    list: List of rank counts
    """
    try:
        if not os.path.exists(file_path):
            print(f"Rank counts file not found: {file_path}, using defaults")
            return [5, 5, 2, 1, 3, 5, 3, 5, 5, 5, 5, 4, 2, 5, 5, 3, 5, 4, 0, 4, 5, 2, 4, 5, 3, 5, 5, 0, 4, 3, 2, 1, 4, 5, 3, 5, 1, 4, 3, 3, 2, 5]
        
        with open(file_path, 'r') as f:
            csv_reader = csv.reader(f)
            # Skip header row if present
            headers = next(csv_reader)
            # Read data row
            count_data = next(csv_reader)
            
            # Convert to integers
            rank_counts = [int(count) for count in count_data]
            print(f"Loaded {len(rank_counts)} rank counts from {file_path}")
            return rank_counts
            
    except Exception as e:
        print(f"Error loading rank counts from file: {e}")
        # Return default fallback values
        return [5, 5, 2, 1, 3, 5, 3, 5, 5, 5, 5, 4, 2, 5, 5, 3, 5, 4, 0, 4, 5, 2, 4, 5, 3, 5, 5, 0, 4, 3, 2, 1, 4, 5, 3, 5, 1, 4, 3, 3, 2, 5]

# Modified GeorgiaFantasy5Predictor class initialization
class GeorgiaFantasy5Predictor:
    def __init__(self, config, rank_limits_file='rank_limit_100.csv', rank_counts_file='rank_count_100.csv'):
        """
        Initialize the Georgia Fantasy 5 Predictor
        
        Parameters:
        config (dict): MySQL database connection parameters
        rank_limits_file (str): Path to rank limits CSV file
        rank_counts_file (str): Path to rank counts CSV file
        """
        try:
            self.conn = mysql.connector.connect(**config)
            self.cursor = self.conn.cursor(dictionary=True)
            
            # Georgia Fantasy 5 specifics
            self.num_range = range(1, 43)  # Numbers 1-39
            self.nums_per_draw = 5
            
            # Filter settings (can be adjusted via web interface)
            self.max_seq2 = 1
            self.max_seq3 = 0
            self.max_mod_tot = 1
            self.sum_range = (70, 139)
            
            # Load rank data directly from CSV files
            self.rank_limits = load_rank_limits_from_file(rank_limits_file)
            self.rank_counts = load_rank_counts_from_file(rank_counts_file)
            
            # Load column 1 distribution data
            self.col1_data = self.load_col1_data()
            
            # Create cyclers for round-robin col1 selection
            self.col1_cyclers = {}
            for key, values in self.col1_data.items():
                if values:  # Only create cyclers for non-empty lists
                    self.col1_cyclers[key] = cycle(values)
            
            # Load historical data
            self.load_historical_data()
        except mysql.connector.Error as e:
            print(f"Database connection error: {e}")
            # Create empty dataframe for historical draws if DB connection fails
            self.historical_draws = pd.DataFrame(columns=['date', 'b1', 'b2', 'b3', 'b4', 'b5', 'sum'])
            self.conn = None
            self.cursor = None
            
            # Still load rank data from files even if DB fails
            self.rank_limits = load_rank_limits_from_file(rank_limits_file)
            self.rank_counts = load_rank_counts_from_file(rank_counts_file)

# Alternative: Simple file check function
def check_rank_files():
    """
    Check if rank files exist and display their contents
    """
    files_to_check = ['rank_limit_100.csv', 'rank_count_100.csv']
    
    for file_path in files_to_check:
        print(f"\n=== Checking {file_path} ===")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    csv_reader = csv.reader(f)
                    headers = next(csv_reader)
                    data = next(csv_reader)
                    print(f"Headers: {headers}")
                    print(f"Data: {data[:10]}...")  # Show first 10 values
                    print(f"Total values: {len(data)}")
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        else:
            print(f"File not found: {file_path}")

# Usage example:
if __name__ == "__main__":
    # Check what rank files exist
    check_rank_files()
    
    # Test loading from files
    limits = load_rank_limits_from_file()
    counts = load_rank_counts_from_file()
    
    print(f"\nLoaded {len(limits)} rank limits: {limits}")
    print(f"Loaded {len(counts)} rank counts: {counts[:10]}...")  # Show first 10
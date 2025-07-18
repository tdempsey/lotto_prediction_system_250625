import mysql.connector
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from itertools import combinations
import time

class GeorgiaFantasy5Predictor:
    def __init__(self, config):
        """
        Initialize the Georgia Fantasy 5 Predictor
        
        Parameters:
        config (dict): MySQL database connection parameters
        """
        self.conn = mysql.connector.connect(**config)
        self.cursor = self.conn.cursor(dictionary=True)
        
        # Georgia Fantasy 5 specifics
        self.num_range = range(1, 43)  # Numbers 1-39
        self.nums_per_draw = 5
        
        # Load historical data
        self.load_historical_data()
        
    def load_historical_data(self):
        """Load historical draws from MySQL database"""
        query = "SELECT * FROM ga_f5_draws ORDER BY date DESC"
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        
        # Convert to DataFrame for easier manipulation
        self.historical_draws = pd.DataFrame(results)
        print(f"Loaded {len(self.historical_draws)} historical draws")
    
    def get_last_n_draws(self, n=10):
        """Get the last n draws"""
        return self.historical_draws.head(n)
    
    def count_sequential_numbers(self, numbers):
        """Count sequences of 2 and 3 consecutive numbers"""
        seq2 = 0
        seq3 = 0
        
        # Sort the numbers
        sorted_nums = sorted(numbers)
        
        # Check for sequences of 2
        for i in range(len(sorted_nums)-1):
            if sorted_nums[i+1] - sorted_nums[i] == 1:
                seq2 += 1
                
        # Check for sequences of 3
        for i in range(len(sorted_nums)-2):
            if sorted_nums[i+1] - sorted_nums[i] == 1 and sorted_nums[i+2] - sorted_nums[i+1] == 1:
                seq3 += 1
                
        return seq2, seq3
    
    def calculate_modular_total(self, numbers):
        """Calculate modular total - counts how many numbers share the same remainder when divided by 10"""
        mod_counts = [0] * 10
        
        for num in numbers:
            mod_counts[num % 10] += 1
        
        # Sum the count of duplicates
        mod_total = sum(max(0, count-1) for count in mod_counts)
        
        # Count moduli with more than 2 numbers (used in filtering)
        mod_x = sum(1 for count in mod_counts if count > 2)
        
        return mod_total, mod_x
    
    def calculate_decade_distribution(self, numbers):
        """Calculate how many numbers fall in each decade (1-9, 10-19, 20-29, 30-39, 40-42)"""
        d0, d1, d2, d3, d4 = 0, 0, 0, 0, 0
        
        for num in numbers:
            if 1 <= num <= 9:
                d0 += 1
            elif 10 <= num <= 19:
                d1 += 1
            elif 20 <= num <= 29:
                d2 += 1
            elif 30 <= num <= 39:
                d3 += 1
            else:
                d4 += 1
        
        return d0, d1, d2, d3, d4
    
    def calculate_duplicates_from_previous(self, numbers, max_draws=10):
        """
        Calculate duplicates from previous draws
        
        Parameters:
        numbers (list): The combination to check
        max_draws (int): Number of previous draws to check
        
        Returns:
        list: Count of duplicates for each of the previous draws
        """
        dup_counts = []
        
        last_draws = self.get_last_n_draws(max_draws)
        
        # Individual draw duplicate counts
        for i, row in last_draws.iterrows():
            previous_draw = [row['b1'], row['b2'], row['b3'], row['b4'], row['b5']]
            dup_count = len(set(numbers).intersection(set(previous_draw)))
            dup_counts.append(dup_count)
        
        # Calculate cumulative duplicates
        cumulative_dups = []
        for i in range(1, max_draws + 1):
            # All numbers from the last i draws
            all_previous_nums = []
            for j in range(i):
                if j < len(last_draws):
                    row = last_draws.iloc[j]
                    all_previous_nums.extend([row['b1'], row['b2'], row['b3'], row['b4'], row['b5']])
            
            # Count unique duplicates
            unique_prevs = set(all_previous_nums)
            dup_count = len(set(numbers).intersection(unique_prevs))
            cumulative_dups.append(dup_count)
        
        return dup_counts, cumulative_dups
    
    def calculate_stats(self, numbers):
        """Calculate various statistical measures for a combination"""
        numbers_array = np.array(numbers)
        
        # Basic stats
        mean = np.mean(numbers_array)
        median = np.median(numbers_array)
        
        # Advanced stats (if available)
        try:
            harmean = len(numbers_array) / np.sum(1.0 / numbers_array)
        except:
            harmean = 0
            
        try:
            geomean = np.exp(np.mean(np.log(numbers_array)))
        except:
            geomean = 0
        
        # Quartiles
        sorted_nums = sorted(numbers)
        if len(sorted_nums) >= 4:
            quart1 = (sorted_nums[0] + sorted_nums[1]) / 2
            quart2 = (sorted_nums[1] + sorted_nums[2]) / 2
            quart3 = (sorted_nums[2] + sorted_nums[3]) / 2
        else:
            quart1, quart2, quart3 = 0, 0, 0
            
        # Variance stats
        stdev = np.std(numbers_array)
        variance = np.var(numbers_array)
        
        # Absolute deviation
        avedev = np.mean(np.abs(numbers_array - mean))
        
        # Advanced stats if available
        try:
            skew = 0  # Placeholder, implement if needed
            kurt = 0  # Placeholder, implement if needed
        except:
            skew, kurt = 0, 0
            
        return {
            'mean': mean,
            'median': median,
            'harmean': harmean,
            'geomean': geomean,
            'quart1': quart1,
            'quart2': quart2,
            'quart3': quart3,
            'stdev': stdev,
            'variance': variance,
            'avedev': avedev,
            'skew': skew,
            'kurt': kurt
        }
    
    def get_rank_frequency(self, days=30):
        """
        Calculate frequency distribution of numbers in the last n days
        
        Parameters:
        days (int): Number of days to analyze
        
        Returns:
        dict: Frequency count for each number 1-39
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Format date for SQL query
        date_str = cutoff_date.strftime('%Y-%m-%d')
        
        # Query to get draws in the last n days
        query = f"SELECT * FROM ga_f5_draws WHERE date >= '{date_str}' ORDER BY date DESC"
        self.cursor.execute(query)
        recent_draws = self.cursor.fetchall()
        
        # Count frequency of each number
        freq = {num: 0 for num in range(1, 43)}
        
        for draw in recent_draws:
            for i in range(1, 6):
                ball = draw[f'b{i}']
                if ball in freq:
                    freq[ball] += 1
        
        return freq
    
    def rank_numbers(self, frequency_dict):
        """
        Rank numbers based on frequency (0=highest, 6=lowest)
        
        Parameters:
        frequency_dict (dict): Frequency count for each number
        
        Returns:
        dict: Rank for each number (0-6)
        """
        # Sort numbers by frequency
        sorted_nums = sorted(frequency_dict.items(), key=lambda x: x[1], reverse=True)
        
        # Create 7 rank groups (0-6)
        group_size = len(sorted_nums) // 7
        
        # Assign ranks
        ranks = {}
        for i, (num, _) in enumerate(sorted_nums):
            rank = min(i // group_size, 6)  # Ensure max rank is 6
            ranks[num] = rank
            
        return ranks
    
    def filter_combination(self, combination):
        """
        Apply all filters to a combination
        
        Parameters:
        combination (list): The 5-number combination to filter
        
        Returns:
        bool: True if combination passes all filters, False otherwise
        """
        # Basic checks
        if len(combination) != self.nums_per_draw:
            return False
            
        # Get statistics
        stats = {}
        
        # Even/Odd distribution
        even_count = sum(1 for num in combination if num % 2 == 0)
        odd_count = self.nums_per_draw - even_count
        
        if not (2 <= even_count <= 3 and 2 <= odd_count <= 3):
            return False
            
        # Sequential numbers check
        seq2, seq3 = self.count_sequential_numbers(combination)
        if seq2 > 1 or seq3 > 0:
            return False
            
        # Modular totals check
        mod_total, mod_x = self.calculate_modular_total(combination)
        if mod_total > 2 or mod_x > 0:
            return False
            
        # Decade distribution check
        d0, d1, d2, d3, d4 = self.calculate_decade_distribution(combination)
        if d0 > 2 or d1 > 2 or d2 > 2 or d3 > 2 or d4 > 2:
            return False
            
        # Duplicate check from previous draws
        dup_counts, cumulative_dups = self.calculate_duplicates_from_previous(combination)
        
        # Your filtering rules:
        # - No more than 1 number from most recent draw
        if dup_counts[0] > 1:
            return False
            
        # - No more than 2 numbers from cumulative 2 most recent draws
        if cumulative_dups[1] > 2:
            return False
            
        # - No more than 3 numbers from cumulative 3 most recent draws
        if cumulative_dups[2] > 3:
            return False
            
        # Sum range check
        total_sum = sum(combination)
        if not (80 <= total_sum <= 120):  # Adjust this range based on your analysis
            return False
            
        # All filters passed
        return True
    
    def generate_predictions(self, count=10):
        """
        Generate top predictions
        
        Parameters:
        count (int): Number of predictions to generate
        
        Returns:
        list: List of prediction dictionaries with combinations and scores
        """
        print(f"Generating {count} predictions for Georgia Fantasy 5...")
        
        # Get frequency ranks
        frequency = self.get_rank_frequency(days=30)
        ranks = self.rank_numbers(frequency)
        
        # Track all filtered combinations
        filtered_combinations = []
        
        # Get the latest draw date for tracking
        latest_date = self.historical_draws.iloc[0]['date'] if not self.historical_draws.empty else None
        
        # Approach 1: Start with most frequent numbers and build combinations
        most_frequent_nums = sorted(ranks.items(), key=lambda x: x[1])[:15]
        most_frequent_nums = [num for num, _ in most_frequent_nums]
        
        print(f"Analyzing combinations from most frequent numbers...")
        for combo in combinations(most_frequent_nums, self.nums_per_draw):
            combo = sorted(combo)
            if self.filter_combination(combo):
                # Calculate stats for scoring
                stats = self.calculate_stats(combo)
                
                # Calculate a composite score based on multiple factors
                score = self._calculate_score(combo, stats, ranks)
                
                filtered_combinations.append({
                    'combination': combo,
                    'score': score,
                    'sum': sum(combo),
                    'stats': stats
                })
                
                if len(filtered_combinations) >= count * 2:
                    break
        
        # Approach 2: Add combinations from low-frequency numbers
        if len(filtered_combinations) < count:
            print(f"Adding combinations from broader number range...")
            
            # Sample from all numbers, weighted by inverse frequency
            weights = {num: 1/(freq+1) for num, freq in frequency.items()}
            weighted_nums = []
            
            for num, weight in weights.items():
                weighted_nums.extend([num] * int(weight * 10))
                
            # Generate random combinations
            checked_combos = set(tuple(combo['combination']) for combo in filtered_combinations)
            attempts = 0
            
            while len(filtered_combinations) < count * 2 and attempts < 10000:
                attempts += 1
                
                # Select 5 random numbers from the weighted pool
                combo = sorted(np.random.choice(weighted_nums, self.nums_per_draw, replace=False))
                combo_tuple = tuple(combo)
                
                if combo_tuple not in checked_combos and self.filter_combination(combo):
                    checked_combos.add(combo_tuple)
                    
                    # Calculate stats for scoring
                    stats = self.calculate_stats(combo)
                    
                    # Calculate a composite score
                    score = self._calculate_score(combo, stats, ranks)
                    
                    filtered_combinations.append({
                        'combination': combo,
                        'score': score,
                        'sum': sum(combo),
                        'stats': stats
                    })
        
        # Sort by score and return top combinations
        sorted_combinations = sorted(filtered_combinations, key=lambda x: x['score'], reverse=True)
        return sorted_combinations[:count]
    
    def _calculate_score(self, combination, stats, ranks):
        """
        Calculate a composite score for a combination
        
        Parameters:
        combination (list): The 5-number combination
        stats (dict): Statistical measures for the combination
        ranks (dict): Frequency ranks for numbers
        
        Returns:
        float: A score between 0-100
        """
        # Sum rank score (lower is better)
        rank_score = sum(ranks[num] for num in combination)
        norm_rank_score = 100 - (rank_score / (6 * self.nums_per_draw) * 100)
        
        # Statistical score (based on historical analysis)
        stats_score = 0
        
        # Sum score - prefer combinations with sums close to average winning sum
        avg_sum = 100  # Placeholder - calculate from historical data
        sum_score = 100 - min(abs(sum(combination) - avg_sum), 30) * 3.33
        
        # Even/Odd balance score
        even_count = sum(1 for num in combination if num % 2 == 0)
        eo_balance_score = 100 - abs(even_count - (self.nums_per_draw/2)) * 20
        
        # Decade distribution score
        d0, d1, d2, d3, d4 = self.calculate_decade_distribution(combination)
        decade_score = 80
        if d0 > 3 or d1 > 3 or d2 > 3 or d3 > 3 or d4 > 3:
            decade_score -= 20
        if d0 == 0 or d1 == 0 or d2 == 0 or d3 == 0 or d4 == 0:
            decade_score -= 20
            
        # Composite score (weighted average)
        weights = {
            'rank': 0.35,
            'sum': 0.25,
            'eo': 0.15,
            'decade': 0.25
        }
        
        composite_score = (
            norm_rank_score * weights['rank'] + 
            sum_score * weights['sum'] + 
            eo_balance_score * weights['eo'] + 
            decade_score * weights['decade']
        )
        
        return composite_score
        
    def display_predictions(self, predictions):
        """
        Display predictions in a user-friendly format
        
        Parameters:
        predictions (list): List of prediction dictionaries
        """
        print("\n============== GEORGIA FANTASY 5 PREDICTIONS ==============")
        print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("==========================================================\n")
        
        for i, pred in enumerate(predictions, 1):
            combo = pred['combination']
            score = pred['score']
            total = pred['sum']
            
            print(f"Prediction #{i}: {combo[0]}-{combo[1]}-{combo[2]}-{combo[3]}-{combo[4]}")
            print(f"Sum: {total} | Score: {score:.2f}%")
            print("----------------------------------------------------------")
    
    def save_predictions(self, predictions, filename=None):
        """
        Save predictions to a CSV file
        
        Parameters:
        predictions (list): List of prediction dictionaries
        filename (str): Optional filename, defaults to date-based name
        
        Returns:
        str: Path to the saved file
        """
        if filename is None:
            filename = f"ga_f5_predictions_{datetime.now().strftime('%Y%m%d')}.csv"
            
        # Create DataFrame
        rows = []
        for i, pred in enumerate(predictions, 1):
            combo = pred['combination']
            row = {
                'Prediction': i,
                'Ball1': combo[0],
                'Ball2': combo[1],
                'Ball3': combo[2],
                'Ball4': combo[3],
                'Ball5': combo[4],
                'Sum': pred['sum'],
                'Score': pred['score'],
                'Generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            rows.append(row)
            
        df = pd.DataFrame(rows)
        df.to_csv(filename, index=False)
        
        print(f"\nPredictions saved to {filename}")
        return filename
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# Example usage
if __name__ == "__main__":
    # Database configuration
    db_config = {
        'host': 'localhost',
        'user': 'your_username',
        'password': 'your_password',
        'database': 'ga_f5_lotto'
    }
    
    try:
        # Initialize predictor
        predictor = GeorgiaFantasy5Predictor(db_config)
        
        # Generate predictions
        predictions = predictor.generate_predictions(count=10)
        
        # Display predictions
        predictor.display_predictions(predictions)
        
        # Save predictions
        predictor.save_predictions(predictions)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        if 'predictor' in locals():
            predictor.close()import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import os
from datetime import datetime
import pandas as pd
import webbrowser
import json

# Import the predictor class
from ga_fantasy5_predictor import GeorgiaFantasy5Predictor

class Fantasy5PredictionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Georgia Fantasy 5 Prediction System")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Set app icon if available
        try:
            self.root.iconbitmap("lottery_icon.ico")
        except:
            pass
            
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create title label
        title_label = ttk.Label(
            self.main_frame, 
            text="Georgia Fantasy 5 Prediction System", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Create date label
        self.date_label = ttk.Label(
            self.main_frame,
            text=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            font=("Arial", 10)
        )
        self.date_label.pack(pady=5)
        
        # Create settings frame
        settings_frame = ttk.LabelFrame(self.main_frame, text="Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=10)
        
        # Database settings
        db_frame = ttk.Frame(settings_frame)
        db_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(db_frame, text="Database Host:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.db_host = ttk.Entry(db_frame, width=20)
        self.db_host.insert(0, "localhost")
        self.db_host.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(db_frame, text="Database Name:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.db_name = ttk.Entry(db_frame, width=20)
        self.db_name.insert(0, "ga_f5_lotto")
        self.db_name.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(db_frame, text="User:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.db_user = ttk.Entry(db_frame, width=20)
        self.db_user.insert(0, "root")
        self.db_user.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(db_frame, text="Password:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.db_pass = ttk.Entry(db_frame, width=20, show="*")
        self.db_pass.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Filter settings
        filter_frame = ttk.LabelFrame(self.main_frame, text="Filter Settings", padding="10")
        filter_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(filter_frame, text="Max Sequential Pairs:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.max_seq2 = ttk.Spinbox(filter_frame, from_=0, to=5, width=5)
        self.max_seq2.insert(0, "1")
        self.max_seq2.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(filter_frame, text="Max Sequential Triplets:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.max_seq3 = ttk.Spinbox(filter_frame, from_=0, to=5, width=5)
        self.max_seq3.insert(0, "0")
        self.max_seq3.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(filter_frame, text="Max Mod Total:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.max_mod_tot = ttk.Spinbox(filter_frame, from_=0, to=5, width=5)
        self.max_mod_tot.insert(0, "2")
        self.max_mod_tot.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(filter_frame, text="Number of Predictions:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.num_predictions = ttk.Spinbox(filter_frame, from_=1, to=100, width=5)
        self.num_predictions.insert(0, "10")
        self.num_predictions.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Sum range filter
        ttk.Label(filter_frame, text="Sum Range:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        sum_frame = ttk.Frame(filter_frame)
        sum_frame.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        self.min_sum = ttk.Spinbox(sum_frame, from_=5, to=195, width=5)
        self.min_sum.insert(0, "80")
        self.min_sum.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(sum_frame, text="to").pack(side=tk.LEFT, padx=5)
        
        self.max_sum = ttk.Spinbox(sum_frame, from_=5, to=195, width=5)
        self.max_sum.insert(0, "120")
        self.max_sum.pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.generate_btn = ttk.Button(
            button_frame, 
            text="Generate Predictions", 
            command=self.generate_predictions
        )
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(
            button_frame, 
            text="Save Predictions", 
            command=self.save_predictions,
            state=tk.DISABLED
        )
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.load_settings_btn = ttk.Button(
            button_frame, 
            text="Load Settings", 
            command=self.load_settings
        )
        self.load_settings_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_settings_btn = ttk.Button(
            button_frame, 
            text="Save Settings", 
            command=self.save_settings
        )
        self.save_settings_btn.pack(side=tk.LEFT, padx=5)
        
        # Results area
        results_frame = ttk.LabelFrame(self.main_frame, text="Prediction Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, height=15)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(
            self.main_frame, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        # Store predictions
        self.predictions = None
        
        # Load settings if available
        self.try_load_settings()
    
    def generate_predictions(self):
        """Generate predictions based on current settings"""
        try:
            # Get database settings
            db_config = {
                'host': self.db_host.get(),
                'user': self.db_user.get(),
                'password': self.db_pass.get(),
                'database': self.db_name.get()
            }
            
            # Update status
            self.status_var.set("Connecting to database...")
            self.root.update_idletasks()
            
            # Initialize predictor
            predictor = GeorgiaFantasy5Predictor(db_config)
            
            # Update status
            self.status_var.set("Generating predictions...")
            self.root.update_idletasks()
            
            # Override filter settings
            predictor.max_seq2 = int(self.max_seq2.get())
            predictor.max_seq3 = int(self.max_seq3.get())
            predictor.max_mod_tot = int(self.max_mod_tot.get())
            predictor.sum_range = (int(self.min_sum.get()), int(self.max_sum.get()))
            
            # Generate predictions
            count = int(self.num_predictions.get())
            self.predictions = predictor.generate_predictions(count=count)
            
            # Display predictions
            self.display_predictions()
            
            # Enable save button
            self.save_btn.config(state=tk.NORMAL)
            
            # Update status
            self.status_var.set(f"Generated {len(self.predictions)} predictions")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_var.set("Error generating predictions")
    
    def display_predictions(self):
        """Display predictions in the results text area"""
        if not self.predictions:
            return
            
        # Clear results area
        self.results_text.delete(1.0, tk.END)
        
        # Add header
        self.results_text.insert(tk.END, "============== GEORGIA FANTASY 5 PREDICTIONS ==============\n")
        self.results_text.insert(tk.END, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.results_text.insert(tk.END, "==========================================================\n\n")
        
        # Add predictions
        for i, pred in enumerate(self.predictions, 1):
            combo = pred['combination']
            score = pred['score']
            total = pred['sum']
            
            line = f"Prediction #{i}: {combo[0]}-{combo[1]}-{combo[2]}-{combo[3]}-{combo[4]}\n"
            self.results_text.insert(tk.END, line)
            
            line = f"Sum: {total} | Score: {score:.2f}%\n"
            self.results_text.insert(tk.END, line)
            
            self.results_text.insert(tk.END, "----------------------------------------------------------\n")
    
    def save_predictions(self):
        """Save predictions to a CSV file"""
        if not self.predictions:
            messagebox.showinfo("Info", "No predictions to save")
            return
            
        try:
            from tkinter import filedialog
            
            # Get save path
            filename = filedialog.asksaveasfilename(
                initialdir="./",
                title="Save Predictions",
                filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
                defaultextension=".csv"
            )
            
            if not filename:
                return
                
            # Create DataFrame
            rows = []
            for i, pred in enumerate(self.predictions, 1):
                combo = pred['combination']
                row = {
                    'Prediction': i,
                    'Ball1': combo[0],
                    'Ball2': combo[1],
                    'Ball3': combo[2],
                    'Ball4': combo[3],
                    'Ball5': combo[4],
                    'Sum': pred['sum'],
                    'Score': pred['score'],
                    'Generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                rows.append(row)
                
            df = pd.DataFrame(rows)
            df.to_csv(filename, index=False)
            
            self.status_var.set(f"Predictions saved to {filename}")
            messagebox.showinfo("Success", f"Predictions saved to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_var.set("Error saving predictions")
    
    def save_settings(self):
        """Save current settings to a file"""
        try:
            settings = {
                'database': {
                    'host': self.db_host.get(),
                    'name': self.db_name.get(),
                    'user': self.db_user.get(),
                    'password': self.db_pass.get()
                },
                'filters': {
                    'max_seq2': self.max_seq2.get(),
                    'max_seq3': self.max_seq3.get(),
                    'max_mod_tot': self.max_mod_tot.get(),
                    'min_sum': self.min_sum.get(),
                    'max_sum': self.max_sum.get(),
                    'num_predictions': self.num_predictions.get()
                }
            }
            
            with open('ga_f5_settings.json', 'w') as f:
                json.dump(settings, f, indent=4)
                
            self.status_var.set("Settings saved")
            messagebox.showinfo("Success", "Settings saved successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error saving settings: {str(e)}")
    
    def load_settings(self):
        """Load settings from a file"""
        try:
            from tkinter import filedialog
            
            # Get file path
            filename = filedialog.askopenfilename(
                initialdir="./",
                title="Load Settings",
                filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
            )
            
            if not filename:
                return
                
            with open(filename, 'r') as f:
                settings = json.load(f)
                
            # Apply settings
            self.apply_settings(settings)
            
            self.status_var.set("Settings loaded")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error loading settings: {str(e)}")
    
    def try_load_settings(self):
        """Try to load settings from default file"""
        try:
            if os.path.exists('ga_f5_settings.json'):
                with open('ga_f5_settings.json', 'r') as f:
                    settings = json.load(f)
                    
                # Apply settings
                self.apply_settings(settings)
                
                self.status_var.set("Default settings loaded")
        except:
            # Silently fail - use defaults
            pass
    
    def apply_settings(self, settings):
        """Apply loaded settings to UI elements"""
        # Database settings
        if 'database' in settings:
            db = settings['database']
            if 'host' in db:
                self.db_host.delete(0, tk.END)
                self.db_host.insert(0, db['host'])
            if 'name' in db:
                self.db_name.delete(0, tk.END)
                self.db_name.insert(0, db['name'])
            if 'user' in db:
                self.db_user.delete(0, tk.END)
                self.db_user.insert(0, db['user'])
            if 'password' in db:
                self.db_pass.delete(0, tk.END)
                self.db_pass.insert(0, db['password'])
                
        # Filter settings
        if 'filters' in settings:
            filters = settings['filters']
            if 'max_seq2' in filters:
                self.max_seq2.delete(0, tk.END)
                self.max_seq2.insert(0, filters['max_seq2'])
            if 'max_seq3' in filters:
                self.max_seq3.delete(0, tk.END)
                self.max_seq3.insert(0, filters['max_seq3'])
            if 'max_mod_tot' in filters:
                self.max_mod_tot.delete(0, tk.END)
                self.max_mod_tot.insert(0, filters['max_mod_tot'])
            if 'min_sum' in filters:
                self.min_sum.delete(0, tk.END)
                self.min_sum.insert(0, filters['min_sum'])
            if 'max_sum' in filters:
                self.max_sum.delete(0, tk.END)
                self.max_sum.insert(0, filters['max_sum'])
            if 'num_predictions' in filters:
                self.num_predictions.delete(0, tk.END)
                self.num_predictions.insert(0, filters['num_predictions'])

# Main application entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = Fantasy5PredictionApp(root)
    root.mainloop()

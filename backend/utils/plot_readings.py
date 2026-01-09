import json
import pandas as pd
import matplotlib.pyplot as plt
import os

def main():
    # Define file paths
    # Assuming script is run from project root or utils/ directory, handle both if possible or just stick to relative from utils/
    # Best practice: use absolute path based on script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, '../data/readings.json')
    
    print(f"Loading data from {data_path}...")
    
    try:
        with open(data_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {data_path}")
        return

    if not data:
        print("No data found in JSON.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Convert timestamp to datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Ensure numeric columns are floats
    numeric_cols = ['wind_speed', 'rpm', 'lift_force']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    print("Data loaded successfully. Generating plots...")
    
    # Define plots to generate
    # Tuples of (x_col, y_col, filename, title, x_label, y_label)
    plots = [
        ('timestamp', 'rpm', 'rpm_vs_time.png', 'RPM vs Time', 'Time', 'RPM'),
        ('timestamp', 'lift_force', 'lift_force_vs_time.png', 'Lift Force vs Time', 'Time', 'Lift Force'),
        ('wind_speed', 'rpm', 'rpm_vs_wind_speed.png', 'RPM vs Wind Speed', 'Wind Speed', 'RPM'),
        ('wind_speed', 'lift_force', 'lift_force_vs_wind_speed.png', 'Lift Force vs Wind Speed', 'Wind Speed', 'Lift Force'),
        ('lift_force', 'rpm', 'rpm_vs_lift_force.png', 'RPM vs Lift Force', 'Lift Force', 'RPM') # User requested rpm vs lift_force, assuming rpm is y? "rpm vs lift_force usually implies Y vs X". I'll put RPM on Y.
    ]

    for x_col, y_col, filename, title, x_label, y_label in plots:
        if x_col not in df.columns or y_col not in df.columns:
            print(f"Skipping {filename}: Missing columns {x_col} or {y_col}")
            continue
            
        plt.figure(figsize=(10, 6))
        plt.plot(df[x_col], df[y_col], marker='o', linestyle='-')
        
        plt.title(title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.grid(True)
        plt.tight_layout()
        
        # Save to the same directory as the script
        output_path = os.path.join(script_dir, filename)
        plt.savefig(output_path)
        plt.close()
        print(f"Saved {filename}")

if __name__ == "__main__":
    main()

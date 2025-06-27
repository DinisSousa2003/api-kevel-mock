import json
import matplotlib.pyplot as plt
import subprocess
import numpy as np
import datetime
from collections import defaultdict
import pandas as pd
from sortedcontainers import SortedList

def analyse_jsonl(file_path, output_path="analysis/analyse.png"):
    total_updates = 0
    user_updates = defaultdict(int)
    attribute_updates = defaultdict(int)
    attribute_keys_count = []
    timestamps = SortedList()
    user_timestamps = defaultdict(SortedList)
    
    with open(file_path, 'r') as file:
        for line in file:
            data = json.loads(line)
            total_updates += 1
            user_updates[data["userId"]] += 1
            
            attributes = data.get("attributes", {})
            for attr in attributes.keys():
                attribute_updates[attr] += 1
            
            attribute_keys_count.append(len(attributes))
            
            timestamp = datetime.datetime.fromtimestamp(data["timestamp"] / 1000)  # Convert ms to seconds
            timestamps.add(timestamp)
            user_timestamps[data["userId"]].add(timestamp)

            if total_updates % 10000 == 0:
                print(total_updates, "...")

    # Find max and min timestamps and calculate time differences and rate
    min_timestamp = timestamps[0]
    max_timestamp = timestamps[-1]
    time_diff = (max_timestamp - min_timestamp).total_seconds()
    update_rate = total_updates / time_diff if time_diff > 0 else 0

    total_users = len(user_updates)
    total_attributes = len(attribute_updates)
    total_attributes_updates = sum(attribute_updates.values())
    avg_updates_per_user = total_updates / total_users if total_users else 0
    avg_keys_per_update = total_attributes_updates / total_updates if total_updates else 0
    
    median_updates_per_user = np.median(list(user_updates.values())) if user_updates else 0
    median_keys_per_update = np.median(attribute_keys_count) if attribute_keys_count else 0

    # Call function to plot timestamp distribution
    plot_timestamp_distribution(timestamps)
    

    plt.figure(figsize=(21, 14))

    # 1. Distribution of updates per user
    plt.subplot(2, 3, 4)
    data = list(user_updates.values())
    hist, bins, _ = plt.hist(data, bins=40)
    plt.tick_params(labelsize=16)
    plt.yscale("log")
    plt.xlabel('Updates per User', fontsize=18)
    plt.ylabel('Density', fontsize=18)
    plt.title('Distribution of Updates per User', fontsize=20)

    plt.subplot(2, 3, 1)
    logbins = np.logspace(np.log10(bins[0]),np.log10(bins[-1]),len(bins))
    plt.hist(data, bins=logbins, color="blue")
    plt.xscale("log")
    plt.yscale("log")
    plt.tick_params(labelsize=16)
    plt.xlabel('Updates per User', fontsize=18)
    plt.ylabel('Density', fontsize=18)
    plt.title('Distribution of Updates per User', fontsize=20)

    # 2. Distribution of updates per attribute
    plt.subplot(2, 3, 5)
    data = list(attribute_updates.values())
    hist, bins, _ = plt.hist(data, bins=40)
    plt.tick_params(labelsize=16)
    plt.yscale("log")
    plt.xlabel('Updates per Attribute', fontsize=18)
    plt.ylabel('Density', fontsize=18)
    plt.title('Distribution of Updates per Attribute', fontsize=20)
    
    plt.subplot(2, 3, 2)
    logbins = np.logspace(np.log10(bins[0]),np.log10(bins[-1]),len(bins))
    plt.hist(data, bins=logbins, color="green")
    plt.tick_params(labelsize=16)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel('Updates per Attribute', fontsize=18)
    plt.ylabel('Density', fontsize=18)
    plt.title('Distribution of Updates per Attribute', fontsize=20)

    # 3. Distribution of number of attribute keys per update
    plt.subplot(2, 3, 6)
    data = attribute_keys_count
    hist, bins, _ = plt.hist(data, bins=40)
    plt.tick_params(labelsize=16)
    plt.yscale("log")
    plt.xlabel('Number of Keys per Update', fontsize=18)
    plt.ylabel('Density', fontsize=18)
    plt.title('Distribution of Attribute Keys per Update', fontsize=20)
    
    plt.subplot(2, 3, 3)
    logbins = np.logspace(np.log10(bins[0]),np.log10(bins[-1]),len(bins))
    plt.hist(data, bins=logbins, color="red")
    plt.tick_params(labelsize=16)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel('Number of Keys per Update', fontsize=18)
    plt.ylabel('Density', fontsize=18)
    plt.title('Distribution of Attribute Keys per Update', fontsize=20)

    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Visualization saved to {output_path}")
    plt.close()

    plt.close()
    return {
        "Total Number of Updates": total_updates,
        "Total Number of User IDs": total_users,
        "Average Number of Updates per ID": avg_updates_per_user,
        "Median Number of Updates per ID": median_updates_per_user,
        "Average Number of Keys per Attribute Dict": avg_keys_per_update,
        "Median Number of Keys per Attribute Dict": median_keys_per_update,
        "Total Number of Different Keys": total_attributes,
        "Update rate (updates/second)": update_rate,
    }

def plot_timestamp_distribution(timestamps: SortedList):
    """
    Plots the distribution of timestamps over 1-hour blocks.

    Args:
        timestamps: A SortedList of datetime objects.
    """
    if not timestamps:
        print("The SortedList of timestamps is empty. Nothing to plot.")
        return

    s = pd.Series(timestamps)

    # Determine the start and end of the entire time range
    min_time = s.min().floor('D') # Floor to the nearest day
    max_time = s.max().ceil('D')  # Ceil to the nearest day

    # Create daily bins
    # We add an extra day to max_time to ensure the last day block is included
    bins = pd.date_range(start=min_time, end=max_time + pd.Timedelta(days=1), freq="D")

    # Plotting the histogram
    plt.figure(figsize=(12, 6))
    s.hist(bins=bins, edgecolor='black', alpha=0.7)

    plt.title('Daily distribution of requests', fontsize=16)
    plt.xlabel('Day', fontsize=14)
    plt.ylabel('Number of Updates', fontsize=14)
    plt.yscale('log')  # Use logarithmic scale for better visibility
    plt.xticks(rotation=45, fontsize=12) # Rotate x-axis labels for better readability
    plt.grid(axis='y', alpha=0.75)
    plt.tight_layout() # Adjust layout to prevent labels from overlapping
    plt.savefig("analysis/time-distribution.png")
    plt.close()

# Example usage:
file_path = "../dataset/updates-0.jsonl"  # Replace with your actual file path
stats = analyse_jsonl(file_path, "analysis/analyse_log_all4.png")
print(stats)

with open("analysis/stats.txt", "w") as file:
    for k, v in stats.items():
        file.write(f"{k}: {v}\n")
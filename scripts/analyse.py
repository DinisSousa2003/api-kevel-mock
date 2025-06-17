import json
import matplotlib.pyplot as plt
import subprocess
import numpy as np
import datetime
from collections import defaultdict
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
            
            # timestamp = datetime.datetime.fromtimestamp(data["timestamp"] / 1000)  # Convert ms to seconds
            # timestamps.add(timestamp)
            # user_timestamps[data["userId"]].add(timestamp)

            if total_updates % 10000 == 0:
                print(total_updates, "...")
    
    # total_users = len(user_updates)
    # total_attributes = len(attribute_updates)
    # total_attributes_updates = sum(attribute_updates.values())
    # avg_updates_per_user = total_updates / total_users if total_users else 0
    # avg_keys_per_update = total_attributes_updates / total_updates if total_updates else 0
    
    # median_updates_per_user = np.median(list(user_updates.values())) if user_updates else 0
    # median_keys_per_update = np.median(attribute_keys_count) if attribute_keys_count else 0
    
    # # Time-based Analysis
    # avg_time_between_updates = np.mean([
    #     (times[-1] - times[0]).total_seconds() / max(1, len(times) - 1)
    #     for times in user_timestamps.values() if len(times) > 1
    # ]) if user_timestamps else 0

    plt.figure(figsize=(18, 18))

    # 1. Distribution of updates per user
    plt.subplot(3, 3, 7)
    data = list(user_updates.values())
    hist, bins, _ = plt.hist(data, bins=40)
    plt.xlabel('Updates per User')
    plt.ylabel('Density')
    plt.title('Distribution of Updates per User')
    
    plt.subplot(3, 3, 4)
    logbins = np.logspace(np.log10(bins[0]),np.log10(bins[-1]),len(bins))
    plt.hist(data, bins=logbins, color="blue")
    plt.xscale("log")
    plt.xlabel('Updates per User')
    plt.ylabel('Density')
    plt.title('Distribution of Updates per User')

    # 2. Distribution of updates per attribute
    plt.subplot(3, 3, 8)
    data = list(attribute_updates.values())
    hist, bins, _ = plt.hist(data, bins=40)
    plt.xlabel('Updates per Attribute')
    plt.ylabel('Density')
    plt.title('Distribution of Updates per Attribute')
    
    plt.subplot(3, 3, 5)
    logbins = np.logspace(np.log10(bins[0]),np.log10(bins[-1]),len(bins))
    plt.hist(data, bins=logbins, color="green")
    plt.xscale("log")
    plt.xlabel('Updates per Attribute')
    plt.ylabel('Density')
    plt.title('Distribution of Updates per Attribute')

    # 3. Distribution of number of attribute keys per update
    plt.subplot(3, 3, 9)
    data = attribute_keys_count
    hist, bins, _ = plt.hist(data, bins=40)
    plt.xlabel('Number of Keys per Update')
    plt.ylabel('Density')
    plt.title('Distribution of Attribute Keys per Update')
    
    plt.subplot(3, 3, 6)
    logbins = np.logspace(np.log10(bins[0]),np.log10(bins[-1]),len(bins))
    plt.hist(data, bins=logbins, color="red")
    plt.xscale("log")
    plt.xlabel('Number of Keys per Update')
    plt.ylabel('Density')
    plt.title('Distribution of Attribute Keys per Update')

    # Boxplot of updates per user (horizontal, log-scale)
    plt.subplot(3, 3, 1)
    plt.boxplot(list(user_updates.values()), vert=False)
    plt.xscale('log')
    plt.xlabel('Updates per User')
    plt.title('Boxplot of Updates per User')
    plt.grid(True, axis='x')

    # Boxplot of updates per attribute
    plt.subplot(3, 3, 2)
    plt.boxplot(list(attribute_updates.values()), vert=False)
    plt.xscale('log')
    plt.xlabel('Updates per Attribute')
    plt.title('Boxplot of Updates per Attribute')
    plt.grid(True, axis='x')

    # Boxplot of number of attribute keys per update
    plt.subplot(3, 3, 3)
    plt.boxplot(attribute_keys_count, vert=False)
    plt.xscale('log')
    plt.xlabel('Number of Keys per Update')
    plt.title('Boxplot of Attribute Keys per Update')
    plt.grid(True, axis='x')

    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Visualization saved to {output_path}")
    plt.close()

    plt.close()
        # return {
    #     "Total Number of Updates": total_updates,
    #     "Total Number of User IDs": total_users,
    #     "Average Number of Updates per ID": avg_updates_per_user,
    #     "Median Number of Updates per ID": median_updates_per_user,
    #     "Average Number of Keys per Attribute Dict": avg_keys_per_update,
    #     "Median Number of Keys per Attribute Dict": median_keys_per_update,
    #     "Total Number of Different Keys": total_attributes,
    #     "Average Time Between Updates (hours)": avg_time_between_updates / (60*60)
    # }

# Example usage:
file_path = "../dataset/updates-0.jsonl"  # Replace with your actual file path
stats = analyse_jsonl(file_path, "analysis/analyse_log_all.png")
# print(stats)

# with open("analysis/stats.txt", "w") as file:
#     for k, v in stats.items():
#         file.write(f"{k}: {v}\n")
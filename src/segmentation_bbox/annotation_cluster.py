"""In order to improve results, species with less than a threshold number of annotations
 will be grouped into a single class called "rare_species"."""


import os
from collections import defaultdict, Counter


# Paths
annotations_dir = r"annotation_dir"  # Folder containing YOLO annotation files
classes_path = r"classes.txt"  # Original classes file (id: 'species')
output_classes_path = r"classes_final.txt"  # Output updated classes file
rare_threshold = 10  # Threshold for the minimum number of annotations required to keep a species
RARE_SPECIES_NAME = 'rare_species'  # Name for the new merged class

# Step 1: Build mapping of class_id -> species_name from classes.txt
id_to_species = {}
with open(classes_path, 'r', encoding='utf-8') as f:
    for line in f:
        if ':' in line:
            parts = line.strip().split(':')
            old_id = int(parts[0].strip())  # Class ID
            species_name = parts[1].strip().strip("'").strip('"')  # Clean species name
            id_to_species[old_id] = species_name

# Step 2: Count the number of annotations per species across all YOLO .txt files
annotation_counts = Counter()
for fname in os.listdir(annotations_dir):
    if fname.endswith('.txt'):
        with open(os.path.join(annotations_dir, fname), 'r') as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    old_id = int(parts[0])  # Extract class ID from annotation line
                    annotation_counts[old_id] += 1

# Step 3: Identify rare species (those below the annotation threshold)
rare_ids = {cls_id for cls_id, count in annotation_counts.items() if count < rare_threshold}
print(f"Rare species (with less than {rare_threshold} annotations): {rare_ids}")

# Step 4: Build new mapping old_id -> new_id
old_to_new = {}
new_id_to_species = {}
new_id = 0

# Keep non-rare species by reindexing them
for old_id in sorted(id_to_species.keys()):
    if old_id not in rare_ids and annotation_counts[old_id] >= rare_threshold:
        old_to_new[old_id] = new_id
        new_id_to_species[new_id] = id_to_species[old_id]
        new_id += 1

# Add the new merged rare_species class
rare_species_id = new_id
new_id_to_species[rare_species_id] = RARE_SPECIES_NAME
for rid in rare_ids:
    old_to_new[rid] = rare_species_id

print(f"\nNew mapping generated with rare_species -> ID {rare_species_id}")

# Step 5: Write the final updated classes.txt file
with open(output_classes_path, 'w', encoding='utf-8') as f:
    for nid in range(len(new_id_to_species)):
        f.write(f"{nid}: '{new_id_to_species[nid]}'\n")
print(f"New classes.txt written at: {output_classes_path}")

# Step 6: Update all annotation files with the new class IDs
for fname in os.listdir(annotations_dir):
    if fname.endswith('.txt'):
        full_path = os.path.join(annotations_dir, fname)
        new_lines = []
        with open(full_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    old_id = int(parts[0])
                    new_class = old_to_new.get(old_id)
                    if new_class is not None:
                        parts[0] = str(new_class)  # Replace old class ID with new class ID
                        new_lines.append(" ".join(parts))
        # Rewrite the label file with updated class IDs
        with open(full_path, 'w', encoding='utf-8') as fw:
            fw.write("\n".join(new_lines) + "\n")

print("All annotation files have been updated with the new indexing.")

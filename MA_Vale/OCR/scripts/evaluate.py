import os
import glob
import numpy as np
import pandas as pd

def load_files(gt_file_path, pred_file_path, i):
    def process_files(files):
        processed_lines = []

        for file in files:
            with open(file, 'r') as f:
                for line in f:
                    parts = line.strip().split()  
                    if len(parts) > 1: 
                        processed_line = ' '.join(parts[1:]).replace('"', '')
                        processed_lines.append(processed_line)
        return processed_lines

    # Stellen Sie sicher, dass die Pfade in einer Liste übergeben werden
    gt_file = [f"{gt_file_path}/{i}.txt"]
    pred_file = [f"{pred_file_path}/{i}.txt"]

    gt_processed = process_files(gt_file)
    pred_processed = process_files(pred_file)

    return gt_processed, pred_processed

def calculate_polygon(gt_processed):
    polygons = []
    poly_only_text = []
    for line in gt_processed:
        parts = line.split() 

        coordinates = parts[:8]
        text = ' '.join(parts[8:])  

        polygon = [(float(coordinates[i]), float(coordinates[i+1])) for i in range(0, len(coordinates), 2)]

        polygons.append(polygon)
        poly_only_text.append(text)

    return polygons, poly_only_text

def calculate_midpoint(input_lines):
    midpoints = []
    midpoints_w_t = []
    for line in input_lines:
        parts = line.split()  
        coordinates = parts[:8]  
        text = ' '.join(parts[8:])  

        polygon = [(float(coordinates[i]), float(coordinates[i+1])) for i in range(0, len(coordinates), 2)]

        x_values = [p[0] for p in polygon]
        y_values = [p[1] for p in polygon]
        midpoint = (np.mean(x_values), np.mean(y_values))

        midpoints.append(midpoint)
        
        midpoints_w_t.append((midpoint, text))

    return midpoints, midpoints_w_t

def point_in_polygon(points, polygon):
    all_inside_status = []

    for point in points:
        x, y = point
        inside = False
        n = len(polygon)

        for i in range(n):
            j = (i + 1) % n
            try:
                xi, yi = polygon[i]
                xj, yj = polygon[j]
            except TypeError:
                print(f"Fehler beim Entpacken der Koordinaten in Polygon: {polygon[i]} oder {polygon[j]}")
                return []

            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside

        all_inside_status.append(inside)

    return all_inside_status

def link_polygons_to_midpoints(polygons, poly_only_text, midpoint, midpoints_w_t):
    linked_data = []
    df_data = []

    for polygon, poly_text in zip(polygons, poly_only_text):
        for midpoint, mid_text in midpoints_w_t:
            if point_in_polygon([midpoint], polygon)[0]:

                linked_data.append(((polygon, poly_text), midpoint, mid_text))
                df_data.append([str(polygon), poly_text, midpoint[0], midpoint[1], mid_text])

    return linked_data

def sort_linked_data_by_polygon_and_midpoint_x(linked_data):
    def sort_key(entry):
        polygon, (midpoint_x, midpoint_y), _ = entry[0], entry[1], entry[2]
        return (polygon, midpoint_x, -midpoint_y)  

    sorted_data = sorted(linked_data, key=sort_key)

    def custom_sort(sorted_data):
        result = []
        i = 0
        while i < len(sorted_data):
            group = [sorted_data[i]]
            while i + 1 < len(sorted_data) and sorted_data[i][0] == sorted_data[i + 1][0] and abs(sorted_data[i][1][0] - sorted_data[i + 1][1][0]) / sorted_data[i][1][0] < 0.01:
                group.append(sorted_data[i + 1])
                i += 1
            if len(group) > 1:
                group.sort(key=lambda x: x[1][1], reverse=True)
            result.extend(group)
            i += 1
        return result

    sorted_data = custom_sort(sorted_data)

    return sorted_data

def sum_sentences(sorted_data, i):
    sum_data = []
    
    current_first_part_of_polygon = None
    collected_text = ""

    for item in sorted_data:
        first_part_of_polygon, text = item[0][1], item[2] 

        if first_part_of_polygon == current_first_part_of_polygon:
            collected_text += " " + text
        else:
            if current_first_part_of_polygon is not None:
                sum_data.append((current_first_part_of_polygon, collected_text.strip()))

            current_first_part_of_polygon = first_part_of_polygon
            collected_text = text

    if current_first_part_of_polygon is not None:
        sum_data.append((current_first_part_of_polygon, collected_text.strip()))

    csv_file_path = f'../results/sum_data_{i}.csv'
    df = pd.DataFrame(sum_data, columns=['label', 'predict'])
    df.to_csv(csv_file_path, index=False)

    return sum_data
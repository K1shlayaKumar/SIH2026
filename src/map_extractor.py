# ============================================================
# EXACT ROAD-MAP COORDINATE EXTRACTOR
# Image: 1000003032.jpeg
# ============================================================

import cv2
import json
import math
import numpy as np
import matplotlib.pyplot as plt

from PIL import Image
from pathlib import Path
from skimage.morphology import skeletonize

# ============================================================
# 1. LOAD IMAGE
# ============================================================
IMAGE_PATH = Path("1000003032.jpeg")
if not IMAGE_PATH.exists():
    IMAGE_PATH = Path("../1000003032.jpeg")

if not IMAGE_PATH.exists():
    raise FileNotFoundError("Could not find '1000003032.jpeg'. Make sure it is in the project folder.")

original = np.array(Image.open(IMAGE_PATH).convert("RGB"))
original_h, original_w = original.shape[:2]
print(f"Original image: {original_w} x {original_h}")

# ============================================================
# 2. REMOVE THE APP UI / KEEP THE WHITE MAP PAGE
# ============================================================
gray_original = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
white = gray_original > 235

num_labels, labels, stats, centers = cv2.connectedComponentsWithStats(white.astype(np.uint8), 8)

best = None
best_area = 0

for i in range(1, num_labels):
    x = stats[i, cv2.CC_STAT_LEFT]
    y = stats[i, cv2.CC_STAT_TOP]
    w = stats[i, cv2.CC_STAT_WIDTH]
    h = stats[i, cv2.CC_STAT_HEIGHT]
    area = stats[i, cv2.CC_STAT_AREA]

    # Large white page heuristic
    if w > original_w * 0.5 and h > original_h * 0.6 and area > best_area:
        best = (x, y, w, h)
        best_area = area

if best is not None:
    page_x, page_y, page_w, page_h = best
else:
    # Fallback for this screenshot
    page_x = 350
    page_y = 140
    page_w = original_w - page_x
    page_h = original_h - page_y

map_img = original[page_y:page_y + page_h, page_x:page_x + page_w]
H, W = map_img.shape[:2]
print(f"Detected map page: {W} x {H}")

# ============================================================
# 3. DETECT RED DESTINATIONS
# ============================================================
r = map_img[:, :, 0].astype(np.int16)
g = map_img[:, :, 1].astype(np.int16)
b = map_img[:, :, 2].astype(np.int16)

red_mask = (r > 170) & (r > g + 70) & (r > b + 70)
red_mask = cv2.morphologyEx(red_mask.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

def get_centers(mask, min_area=8, max_area=1000):
    n, labels, stats, centers = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    points = []
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if min_area <= area <= max_area:
            x, y = centers[i]
            points.append((float(x), float(y)))
    return points

destinations = get_centers(red_mask, min_area=8, max_area=1000)

# ============================================================
# 4. DETECT CYAN / LIGHT-BLUE TRAFFIC LIGHTS
# ============================================================
cyan_mask = (g > 130) & (b > 130) & (g > r + 50) & (b > r + 50)
cyan_mask = cv2.morphologyEx(cyan_mask.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
traffic_lights = get_centers(cyan_mask, min_area=3, max_area=1000)

# ============================================================
# 5. DETECT BLACK ROADS & SKELETONIZE
# ============================================================
gray = cv2.cvtColor(map_img, cv2.COLOR_RGB2GRAY)
black = gray < 100
black = cv2.morphologyEx(black.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))

skeleton = skeletonize(black > 0)
ys, xs = np.nonzero(skeleton)
road_pixels = set(zip(xs.tolist(), ys.tolist()))

# ============================================================
# 6. FIND JUNCTIONS AND ROAD ENDS
# ============================================================
kernel = np.ones((3, 3), np.uint8)
kernel[1, 1] = 0
degree = cv2.filter2D(skeleton.astype(np.uint8), -1, kernel)
special = skeleton & (degree != 2)

dilated = cv2.dilate(special.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
num_nodes, node_labels = cv2.connectedComponents(dilated, 8)

nodes = {}
for node_id in range(1, num_nodes):
    yy, xx = np.where(special & (node_labels == node_id))
    if len(xx) == 0:
        continue
    pixels = set(zip(xx.astype(int), yy.astype(int)))
    nodes[node_id] = {
        "pixels": pixels,
        "center": (float(np.mean(xx)), float(np.mean(yy)))
    }

pixel_to_node = {}
for node_id, node in nodes.items():
    for pixel in node["pixels"]:
        pixel_to_node[pixel] = node_id

# ============================================================
# 7. CREATE ROAD PIXEL GRAPH
# ============================================================
adjacency = {}
for x, y in road_pixels:
    neighbors = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            p = (x + dx, y + dy)
            if p in road_pixels:
                neighbors.append(p)
    adjacency[(x, y)] = neighbors

# ============================================================
# 8. TRACE EVERY ROAD BETWEEN JUNCTIONS
# ============================================================
visited_edges = set()
routes = []

for start_node, node in nodes.items():
    for start_pixel in node["pixels"]:
        for next_pixel in adjacency[start_pixel]:
            if pixel_to_node.get(next_pixel) == start_node:
                continue
            
            edge = tuple(sorted([start_pixel, next_pixel]))
            if edge in visited_edges:
                continue
            
            visited_edges.add(edge)
            path = [start_pixel, next_pixel]
            
            previous = start_pixel
            current = next_pixel
            
            # Follow road until another junction
            while current not in pixel_to_node:
                candidates = [p for p in adjacency[current] if p != previous]
                if not candidates:
                    break
                nxt = candidates[0]
                edge = tuple(sorted([current, nxt]))
                if edge in visited_edges:
                    break
                
                visited_edges.add(edge)
                path.append(nxt)
                previous = current
                current = nxt
                
            end_node = pixel_to_node.get(current)
            if end_node is not None and end_node != start_node:
                routes.append({
                    "start_node": start_node,
                    "end_node": end_node,
                    "points": path
                })

# ============================================================
# 9. SIMPLIFY GEOMETRY AND EXPORT TO JSON
# ============================================================
def simplify_route(points, epsilon=2.0):
    points_arr = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
    if len(points_arr) <= 2:
        return points_arr.reshape(-1, 2).tolist()
    simplified = cv2.approxPolyDP(points_arr, epsilon, False)
    return simplified.reshape(-1, 2).tolist()

def route_length(points):
    return sum(math.hypot(points[i+1][0]-points[i][0], points[i+1][1]-points[i][1]) for i in range(len(points)-1))

road_routes = []
for i, route in enumerate(routes):
    true_length = route_length(route["points"])
    simplified_points = simplify_route(route["points"])
    road_routes.append({
        "route_id": f"R{i + 1:03d}",
        "start_node": route["start_node"],
        "end_node": route["end_node"],
        "length": round(true_length, 2),
        "coordinates": [[round(float(x), 2), round(float(y), 2)] for x, y in simplified_points]
    })

destination_data = [{"id": f"D{i:02d}", "x": round(x, 2), "y": round(y, 2), "coordinate": [round(x, 2), round(y, 2)]} for i, (x, y) in enumerate(destinations, start=1)]
traffic_data = [{"id": f"TL{i:02d}", "x": round(x, 2), "y": round(y, 2), "coordinate": [round(x, 2), round(y, 2)]} for i, (x, y) in enumerate(traffic_lights, start=1)]

data = {
    "image_size": {"width": W, "height": H}, # Uses cropped UI dimensions for correct scale
    "coordinate_system": {"origin": "top-left", "x_direction": "right", "y_direction": "down"},
    "destinations": destination_data,
    "traffic_lights": traffic_data,
    "road_routes": road_routes
}

with open("map_coordinates.json", "w") as f:
    json.dump(data, f, indent=2)

print("================================")
print("MAP EXTRACTION COMPLETE")
print("================================")
print(f"Destinations: {len(destination_data)}")
print(f"Traffic Lights: {len(traffic_data)}")
print(f"Road Routes Traced: {len(road_routes)}")
print("Coordinates saved to: map_coordinates.json")

# ============================================================
# 10. VISUALIZE OUTPUT
# ============================================================
plt.figure(figsize=(10, 8))
plt.imshow(map_img)

for route in road_routes:
    pts = np.array(route["coordinates"])
    if len(pts) > 1:
        plt.plot(pts[:, 0], pts[:, 1], linewidth=2, color="yellow", alpha=0.7)

for d in destination_data:
    plt.scatter(d["x"], d["y"], s=50, color="red", zorder=10)

for t in traffic_data:
    plt.scatter(t["x"], t["y"], s=50, color="cyan", zorder=10)

plt.title("Extracted Map Data")
plt.axis('off')
plt.tight_layout()
plt.show()
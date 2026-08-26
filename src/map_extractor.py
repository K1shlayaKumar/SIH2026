import json
import math
from pathlib import Path
import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from skimage.morphology import skeletonize

from pathlib import Path

# Search in current script directory, project root, and parent folders
possible_locations = [
    Path("1000003005.jpg"),
    Path(__file__).resolve().parent / "1000003005.jpg",
    Path(__file__).resolve().parent.parent / "1000003005.jpg",
    Path(r"C:\python_proj\SIH2026\1000003005.jpg"),
    Path(r"C:\python_proj\SIH2026\src\1000003005.jpg"),
]

IMAGE_PATH = None
for loc in possible_locations:
    if loc.exists():
        IMAGE_PATH = loc
        break

if IMAGE_PATH is None:
    searched = "\n - ".join(str(p) for p in possible_locations)
    raise FileNotFoundError(f"Image not found. Searched locations:\n - {searched}")

print(f"Found image at: {IMAGE_PATH.resolve()}")

# Look for image in the project root folder or current directory
IMAGE_PATH = Path("1000003005.jpg")
if not IMAGE_PATH.exists():
    IMAGE_PATH = Path("../1000003005.jpg")

if not IMAGE_PATH.exists():
    raise FileNotFoundError(
        "Could not find '1000003005.jpg'. Make sure the image is in the project folder!"
    )

img = Image.open(IMAGE_PATH).convert("RGB")
arr = np.array(img)
W, H = img.size

# ------------------------------------------------------------
# 1. Detect red destinations and cyan traffic lights
# ------------------------------------------------------------
red = (arr[:, :, 0] > 200) & (arr[:, :, 1] < 100) & (arr[:, :, 2] < 100)
cyan = (arr[:, :, 0] < 100) & (arr[:, :, 1] > 150) & (arr[:, :, 2] > 150)


def get_centers(mask, min_area=100):
    n, labels, stats, centers = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8), 8
    )
    result = []
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_area:
            x, y = centers[i]
            result.append((float(x), float(y)))
    return result


destinations = get_centers(red)
traffic_lights = get_centers(cyan)

# ------------------------------------------------------------
# 2. Extract black road lines
# ------------------------------------------------------------
gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
black = gray < 100

skeleton = skeletonize(black)
ys, xs = np.nonzero(skeleton)
road_pixels = set(zip(xs.tolist(), ys.tolist()))

# ------------------------------------------------------------
# 3. Find road junction/end nodes
# ------------------------------------------------------------
kernel = np.ones((3, 3), np.uint8)
kernel[1, 1] = 0

degree = cv2.filter2D(skeleton.astype(np.uint8), -1, kernel)
special = skeleton & (degree != 2)

dilation = cv2.dilate(
    special.astype(np.uint8),
    cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
)

num_labels, labels = cv2.connectedComponents(dilation, 8)
nodes = {}

for label in range(1, num_labels):
    pixels = []
    for y, x in zip(*np.where(special)):
        if labels[y, x] == label:
            pixels.append((int(x), int(y)))
    if pixels:
        nodes[label] = {
            "pixels": set(pixels),
            "center": (
                np.mean([p[0] for p in pixels]),
                np.mean([p[1] for p in pixels]),
            ),
        }

pixel_to_node = {}
for node_id, node in nodes.items():
    for p in node["pixels"]:
        pixel_to_node[p] = node_id

# ------------------------------------------------------------
# 4. Road pixel adjacency
# ------------------------------------------------------------
adjacency = {}
for x, y in road_pixels:
    neighbors = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            q = (x + dx, y + dy)
            if q in road_pixels:
                neighbors.append(q)
    adjacency[(x, y)] = neighbors

# ------------------------------------------------------------
# 5. Trace every road route between junctions
# ------------------------------------------------------------
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

            path = [start_pixel, next_pixel]
            visited_edges.add(edge)

            previous = start_pixel
            current = next_pixel

            while current not in pixel_to_node:
                candidates = [
                    p for p in adjacency[current] if p != previous
                ]
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
                    "points": path,
                })

# ------------------------------------------------------------
# 6. Simplify route coordinates
# ------------------------------------------------------------
def simplify_route(points, epsilon=1.5):
    points_arr = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
    if len(points_arr) <= 2:
        return points_arr.reshape(-1, 2).tolist()
    simplified = cv2.approxPolyDP(points_arr, epsilon, False)
    return simplified.reshape(-1, 2).tolist()


def route_length(points):
    length = 0
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        length += math.hypot(x2 - x1, y2 - y1)
    return length


road_routes = []
for i, route in enumerate(routes):
    true_length = route_length(route["points"])
    simplified_points = simplify_route(route["points"])

    road_routes.append({
        "route_id": f"R{i + 1:03d}",
        "start_node": route["start_node"],
        "end_node": route["end_node"],
        "length": round(true_length, 2),
        "coordinates": [
            [round(float(x), 2), round(float(y), 2)]
            for x, y in simplified_points
        ],
    })

# ------------------------------------------------------------
# 7. Create destination & traffic light data
# ------------------------------------------------------------
destination_data = [
    {
        "id": f"D{i:02d}",
        "x": round(x, 2),
        "y": round(y, 2),
        "coordinate": [round(x, 2), round(y, 2)],
    }
    for i, (x, y) in enumerate(destinations, start=1)
]

traffic_data = [
    {
        "id": f"TL{i:02d}",
        "x": round(x, 2),
        "y": round(y, 2),
        "coordinate": [round(x, 2), round(y, 2)],
    }
    for i, (x, y) in enumerate(traffic_lights, start=1)
]

# ------------------------------------------------------------
# 8. Save output JSON
# ------------------------------------------------------------
data = {
    "image_size": {"width": W, "height": H},
    "coordinate_system": {
        "origin": "top-left",
        "x_direction": "right",
        "y_direction": "down",
    },
    "destinations": destination_data,
    "traffic_lights": traffic_data,
    "road_routes": road_routes,
}

output_path = Path("map_coordinates.json")
with open(output_path, "w") as f:
    json.dump(data, f, indent=2)

print("================================")
print("MAP EXTRACTION COMPLETE")
print("================================")
print("Destinations found:", len(destination_data))
print("Traffic lights found:", len(traffic_data))
print("Road routes found:", len(road_routes))
print(f"Saved to: {output_path.resolve()}")
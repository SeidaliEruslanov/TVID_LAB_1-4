import cv2
import numpy as np
import os

# создание папки для маркеров
output_dir = "aruco_markers_6x6"
os.makedirs(output_dir, exist_ok=True)

# выбор более сложного словаря (6x6, 250 маркеров)
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)

# генерация маркеров
for marker_id in range(50):  # можно 0–249
    marker = np.zeros((400, 400), dtype=np.uint8)
    cv2.aruco.generateImageMarker(aruco_dict, marker_id, 400, marker, 1)

    text = f"id {marker_id}"
    cv2.putText(marker, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    filename = os.path.join(output_dir, f"marker_{marker_id}.png")
    cv2.imwrite(filename, marker)
    print(f"маркер {marker_id} сохранён как {filename}")

print("генерация 6x6 маркеров завершена")

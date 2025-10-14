import cv2
import numpy as np
import pygame
import webbrowser
import time
import os

# Инициализация Pygame для звуков
pygame.mixer.init()

# Словарь маркеров ArUco
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)  # Новый API

# Таймеры для маркеров
marker_last_seen_time = {}
TIME_THRESHOLD = 5  # Уменьшено до 5 секунд для тестирования

# Специальные маркеры
special_markers = {
    15: "https://www.stankin.ru",
    16: "https://vk.com/msut_stankin",
    # ... остальные ссылки
    30: "станкин.mp3"  # Убедитесь, что файл существует
}


def overlay_image_on_marker(image, overlay_path, corners):
    """Накладывает изображение на область маркера"""
    if not os.path.exists(overlay_path):
        print(f"Файл не найден: {overlay_path}")
        return image

    try:
        # Читаем изображение для наложения
        overlay_img = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
        if overlay_img is None:
            return image

        # Получаем координаты маркера
        pts = corners.reshape((4, 2))

        # Вычисляем перспективную трансформацию
        width, height = 200, 200  # Размер накладываемого изображения

        # Целевые точки для трансформации
        dst_pts = np.array([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ], dtype="float32")

        # Вычисляем матрицу преобразования
        M = cv2.getPerspectiveTransform(dst_pts, pts.astype("float32"))

        # Применяем перспективную трансформацию
        warped = cv2.warpPerspective(overlay_img, M, (image.shape[1], image.shape[0]))

        # Накладываем изображение
        if warped.shape[2] == 4:  # С альфа-каналом
            alpha = warped[:, :, 3] / 255.0
            for c in range(3):
                image[:, :, c] = (1 - alpha) * image[:, :, c] + alpha * warped[:, :, c]
        else:
            image = cv2.addWeighted(image, 0.7, warped, 0.3, 0)

    except Exception as e:
        print(f"Ошибка при наложении изображения: {e}")

    return image


def play_sound(sound_path):
    """Воспроизводит звук"""
    try:
        if os.path.exists(sound_path):
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play()
        else:
            print(f"Звуковой файл не найден: {sound_path}")
    except Exception as e:
        print(f"Ошибка воспроизведения звука: {e}")


def handle_special_marker(marker_id):
    """Обрабатывает специальные маркеры с проверкой времени"""
    current_time = time.time()

    if marker_id in marker_last_seen_time:
        time_since_last_seen = current_time - marker_last_seen_time[marker_id]
        if time_since_last_seen < TIME_THRESHOLD:
            return False

    marker_last_seen_time[marker_id] = current_time

    if marker_id in special_markers:
        action = special_markers[marker_id]
        if action.endswith(".mp3"):
            play_sound(action)
        else:
            webbrowser.open(action)
        return True

    return False


# Основной цикл обработки видео
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Ошибка: не удалось открыть камеру")
    exit()

print("Запуск системы распознавания маркеров. Нажмите 'q' для выхода.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Ошибка: не удалось получить кадр")
        break

    # Конвертируем в grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Обнаруживаем маркеры
    corners, ids, rejected = detector.detectMarkers(gray)

    if ids is not None:
        for i in range(len(ids)):
            marker_id = ids[i][0]

            # Рисуем контур маркера
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)

            # Обрабатываем специальные маркеры
            if marker_id >= 15:
                handle_special_marker(marker_id)
            else:
                # Накладываем изображения на обычные маркеры
                overlay_paths = {
                    0: "image/1.jpg", 1: "image/2.jpg", 2: "image/3.jpg",
                    3: "image/4.jpg", 4: "image/5.jpg", 5: "image/6.jpg",
                    6: "image/7.jpg", 7: "image/8.jpg", 8: "image/9.jpg",
                    9: "image/10.jpg", 10: "image/11.jpg", 11: "image/12.jpg",
                    12: "image/13.jpg", 13: "image/14.jpg", 14: "image/15.jpg"
                }

                if marker_id in overlay_paths:
                    frame = overlay_image_on_marker(frame, overlay_paths[marker_id], corners[i])

    # Отображаем информацию
    cv2.putText(frame, "Press 'q' to quit", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("ArUco Marker Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
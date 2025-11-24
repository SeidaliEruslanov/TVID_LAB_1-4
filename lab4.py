import cv2
import numpy as np
import pygame
import webbrowser
import time
from PIL import Image, ImageDraw, ImageFont

# инициализируем pygame для воспроизведения звуков
pygame.mixer.init()

# определяем словарь маркеров aruco
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
parameters = cv2.aruco.DetectorParameters()

# таймеры для каждого специального маркера
marker_last_seen_time = {}

# время в секундах между обработкой одного и того же special_marker
TIME_THRESHOLD = 10

# список специальных маркеров для открытия ссылок или воспроизведения звука
special_markers = {
    15: "https://artplaymedia.ru/exhibitions/multimedia-exhibition-i-aivazovsky",
    16: "https://ru.wikipedia.org/wiki/Айвазовский,_Иван_Константинович",
    17: "https://ru.ruwiki.ru/wiki/Айвазовский,_Иван_Константинович",
    18: "https://skillbox.ru/media/design/10-kartin-ivana-ayvazovskogo-kotorye-stoit-znat/",
    19: "https://crimea.mk.ru/culture/2025/04/06/uvlekatelnye-fakty-iz-zhizni-znamenitogo-marinista-ivana-ayvazovskogo.html",
    20: "https://www.miloserdie.ru/article/genij-mesta-vstrechaya-na-ulicze-ivana-ajvazovskogo-malchiki-snimali-kartuzy-i-klanyalis-a-devochki-delali-kniksen/",
    21: "https://artplaymedia.ru/blog/morskie-shedevry-ayvazovskogo",
    22: "https://histrf.ru/read/articles/car-morya-pyat-istoriy-iz-zhizni-ivana-ayvazovskogo",
    23: "https://ananasposter.ru/blog/samye-izvestnye-kartiny-aivazovskogo-more-i-stihiya-v-zhivopisi",
    24: "https://www.vokrugsveta.ru/articles/more-eto-moya-zhizn-kak-ivan-aivazovskii-stal-marinistom-vseya-rusi-id912915/",
    25: "https://artchive.ru/ivanaivazovsky",
    26: "https://rgo.ru/activity/redaction/articles/khudozhnik-russkogo-morya-puteshestviya-i-tvorchestvo-ivana-ayvazovskogo/",
    27: "https://taler-travel.ru/countries/krym-ajvazovskij",
    28: "https://crimea.ria.ru/20250729/1111327136.html",
    29: "https://muzei-mira.com/biografia_hudojnikov/703-ayvazovskiy-ivan-konstantinovich-biografiya.html",
    30: "audio/М. Равель (Марсель Мейер - рояль) - Отражения_ Лодка в океане.mp3"
}

# словарь с путями к изображениям для обычных маркеров
overlay_paths = {
    0: "image/1.jpg", 1: "image/2.jpg", 2: "image/3.jpg", 3: "image/4.jpg",
    4: "image/5.jpg", 5: "image/6.jpg", 6: "image/7.jpg", 7: "image/8.jpg",
    8: "image/9.jpg", 9: "image/10.jpg", 10: "image/11.jpg", 11: "image/12.jpg",
    12: "image/13.jpg", 13: "image/14.jpg", 14: "image/15.jpg"
}

# коэффициент увеличения изображения относительно размера маркера
IMAGE_SCALE_FACTOR = 2.5  # Увеличиваем изображение в 2.5 раза относительно маркера

# переменные для управления размером окна
window_width = 1280
window_height = 720
aspect_ratio = window_width / window_height
original_width = 1920
original_height = 1080
frame_aspect_ratio = original_width / original_height


# функция для наложения изображения на маркер с высоким качеством
def overlay_image_on_marker(image, overlay_path, corners):
    # загружаем изображение для наложения с высоким качеством
    overlay_img = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
    if overlay_img is None:
        print(f"Не удалось загрузить изображение: {overlay_path}")
        return image

    # если изображение не имеет альфа-канала, добавляем его
    if overlay_img.shape[2] == 3:
        overlay_img = cv2.cvtColor(overlay_img, cv2.COLOR_BGR2BGRA)

    # преобразуем corners в удобный формат
    corners = corners.reshape(4, 2)

    # вычисляем центр маркера
    c_x = int((corners[0][0] + corners[1][0] + corners[2][0] + corners[3][0]) / 4)
    c_y = int((corners[0][1] + corners[1][1] + corners[2][1] + corners[3][1]) / 4)

    # вычисляем размер маркера (средняя длина сторон)
    side1 = np.linalg.norm(corners[0] - corners[1])
    side2 = np.linalg.norm(corners[1] - corners[2])
    marker_size = (side1 + side2) / 2

    # определяем размер для overlay изображения (увеличиваем относительно маркера)
    overlay_size = int(marker_size * IMAGE_SCALE_FACTOR)

    # получаем размеры исходного overlay изображения
    h, w = overlay_img.shape[:2]

    # вычисляем коэффициенты масштабирования
    scale = overlay_size / max(h, w)
    new_w = int(w * scale)
    new_h = int(h * scale)

    # масштабируем изображение с высоким качеством
    resized_overlay = cv2.resize(overlay_img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    # вычисляем координаты для вставки (центрирование)
    x_start = c_x - new_w // 2
    y_start = c_y - new_h // 2
    x_end = x_start + new_w
    y_end = y_start + new_h

    # проверяем границы и обрезаем если нужно
    if x_start < 0:
        crop_left = -x_start
        resized_overlay = resized_overlay[:, crop_left:]
        x_start = 0
    if y_start < 0:
        crop_top = -y_start
        resized_overlay = resized_overlay[crop_top:, :]
        y_start = 0
    if x_end > image.shape[1]:
        crop_right = x_end - image.shape[1]
        resized_overlay = resized_overlay[:, :-crop_right]
        x_end = image.shape[1]
    if y_end > image.shape[0]:
        crop_bottom = y_end - image.shape[0]
        resized_overlay = resized_overlay[:-crop_bottom, :]
        y_end = image.shape[0]

    # если после обрезки изображение не пустое, накладываем его
    if (x_end > x_start and y_end > y_start and
            resized_overlay.shape[0] > 0 and resized_overlay.shape[1] > 0):

        # извлекаем область для наложения
        target_region = image[y_start:y_end, x_start:x_end]

        # если размеры не совпадают, пропускаем
        if (resized_overlay.shape[0] != target_region.shape[0] or
                resized_overlay.shape[1] != target_region.shape[1]):
            return image

        # накладываем изображение с учетом альфа-канала
        if resized_overlay.shape[2] == 4:  # если есть альфа-канал
            alpha = resized_overlay[:, :, 3] / 255.0
            for c in range(0, 3):
                target_region[:, :, c] = (
                        (1 - alpha) * target_region[:, :, c] +
                        alpha * resized_overlay[:, :, c]
                )
        else:  # если нет альфа-канала
            image[y_start:y_end, x_start:x_end] = resized_overlay

    return image


# функция для воспроизведения звука
def play_sound(sound_path):
    try:
        # загружаем и воспроизводим звуковой файл
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play()
    except pygame.error as e:
        print(f"ошибка при воспроизведении звука: {e}")


# функция для обработки специальных маркеров
def display_info_on_marker(image, corners, marker_id):
    global marker_last_seen_time
    current_time = time.time()

    # проверяем, является ли маркер специальным
    if marker_id in special_markers:
        # проверяем, когда маркер был обработан в последний раз
        if marker_id in marker_last_seen_time:
            time_since_last_seen = current_time - marker_last_seen_time[marker_id]
            # если маркер был обработан недавно, пропускаем обработку
            if time_since_last_seen < TIME_THRESHOLD:
                print(f"маркер {marker_id} недавно был обработан ({time_since_last_seen:.2f} сек назад), пропускаем.")
                return image

        # обновляем время последней обработки маркера
        marker_last_seen_time[marker_id] = current_time
        print(f"обработка специального маркера {marker_id}.")

        # проверяем тип содержимого маркера (звук или ссылка)
        if special_markers[marker_id].endswith(".mp3"):
            # воспроизводим звук
            play_sound(special_markers[marker_id])
        else:
            # открываем ссылку в браузере
            webbrowser.open(special_markers[marker_id])
    else:
        # если маркер есть в словаре overlay_paths, накладываем изображение
        if marker_id in overlay_paths:
            # накладываем изображение на маркер
            image = overlay_image_on_marker(image, overlay_paths[marker_id], corners)

    return image


# функция для изменения размера изображения с сохранением пропорций
def resize_with_aspect_ratio(image, width=None, height=None):
    h, w = image.shape[:2]

    if width is None and height is None:
        return image

    if width is None:
        ratio = height / float(h)
        dim = (int(w * ratio), height)
    else:
        ratio = width / float(w)
        dim = (width, int(h * ratio))

    return cv2.resize(image, dim, interpolation=cv2.INTER_AREA)


# функция для принудительного сохранения пропорций окна
def maintain_window_aspect_ratio():
    global window_width, window_height
    # Получаем текущий размер окна
    try:
        # В OpenCV нет прямой функции для получения размера окна, поэтому мы будем использовать системные вызовы
        # Вместо этого мы будем отслеживать размер в наших переменных и принудительно устанавливать его
        cv2.resizeWindow("aruco marker detection", window_width, window_height)
    except:
        pass


# захватываем видео с камеры
cap = cv2.VideoCapture(0)

# устанавливаем максимальное разрешение для лучшего качества
cap.set(cv2.CAP_PROP_FRAME_WIDTH, original_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, original_height)

# создаем окно с возможностью изменения размера
cv2.namedWindow("aruco marker detection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("aruco marker detection", window_width, window_height)

# основной цикл обработки видео
while True:
    # читаем кадр с камеры
    ret, frame = cap.read()
    if not ret:
        break

    # преобразуем кадр в оттенки серого для детектирования маркеров
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # детектируем маркеры на кадре
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    # если маркеры найдены
    if ids is not None and len(ids) > 0:
        # обрабатываем каждый обнаруженный маркер
        for i in range(len(ids)):
            # рисуем контуры маркеров на кадре
            cv2.aruco.drawDetectedMarkers(frame, corners)
            marker_id = ids[i][0]
            # обрабатываем маркер (накладываем изображение или открываем ссылку/звук)
            frame = display_info_on_marker(frame, corners[i], marker_id)

    # изменяем размер кадра для отображения с сохранением пропорций исходного видео
    display_frame = resize_with_aspect_ratio(frame, width=window_width)

    # Принудительно сохраняем пропорции окна
    maintain_window_aspect_ratio()

    # отображаем кадр с обнаруженными маркерами
    cv2.imshow("aruco marker detection", display_frame)

    # обработка событий изменения размера окна
    key = cv2.waitKey(1) & 0xFF

    # проверяем нажатие клавиши 'q' для выхода
    if key == ord('q'):
        break
    # проверяем нажатие клавиши '+' для увеличения окна
    elif key == ord('+') or key == ord('='):
        window_width = min(1920, window_width + 100)
        window_height = int(window_width / aspect_ratio)
        cv2.resizeWindow("aruco marker detection", window_width, window_height)
    # проверяем нажатие клавиши '-' для уменьшения окна
    elif key == ord('-') or key == ord('_'):
        window_width = max(640, window_width - 100)
        window_height = int(window_width / aspect_ratio)
        cv2.resizeWindow("aruco marker detection", window_width, window_height)
    # проверяем изменение размера окна мышью
    else:
        # Пытаемся получить текущий размер окна (это приблизительный метод)
        # В OpenCV нет прямого способа получить размер окна, поэтому мы полагаемся на наши переменные
        pass

# освобождаем ресурсы камеры и закрываем окна
cap.release()
cv2.destroyAllWindows()
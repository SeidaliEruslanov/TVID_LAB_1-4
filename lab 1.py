# Вход 'input.bmp'.
# Если 'input.bmp' не найден — градиент.
# Выход: yiq_Y.bmp, yiq_I.bmp, yiq_Q.bmp
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import os

input_path = "input.bmp"


if not os.path.exists(input_path):
    w, h = 512, 384
    demo = np.zeros((h, w, 3), dtype=np.uint8)
    # фон - горизонтальный градиент
    for x in range(w):
        demo[:, x, 0] = int(255 * x / (w-1))   # R gradient
        demo[:, x, 1] = int(255 * (w-1-x) / (w-1))  # G inverse gradient
        demo[:, x, 2] = int(128 + 127 * np.sin(2*np.pi*x/w))  # B sinusoid
    # добавим цветные полосы сверху
    demo[:60, :170] = [255, 0, 0]
    demo[:60, 170:340] = [0, 255, 0]
    demo[:60, 340:] = [0, 0, 255]
    Image.fromarray(demo).save(input_path, format='BMP')        # Генерация градиента




img = Image.open(input_path).convert('RGB') # открыть BMP в RGB
arr = np.asarray(img).astype(np.float32) / 255.0  # PIL-изображение в NumPy-массив формы (h, w, 3) и нормализация 0 - 1.0 для матричных операция

# Матрица преобразования RGB -> YIQ
M = np.array([[0.299,  0.587,  0.114],
              [0.596, -0.274, -0.322],
              [0.211, -0.523,  0.312]], dtype=np.float32)

# и обратная матрица YIQ -> RGB
Minv = np.array([[1.0,  0.956,  0.621],
                 [1.0, -0.272, -0.647],
                 [1.0, -1.106,  1.703]], dtype=np.float32)

# вычисляем YIQ
h, w, _ = arr.shape # извлекаем высоту h и ширину w
flat = arr.reshape(-1, 3) # преобразуем 3D массив в 2D (каждый пиксель становится строкой из 3 значений RGB)
yiq = flat @ M.T #  транспонированная матрица M
yiq = yiq.reshape(h, w, 3) # преобразуем обратно в 3D массив (изображение)

# извлекаем отдельные каналы Y, I, Q из преобразованного изображения
Y = yiq[:, :, 0]
I = yiq[:, :, 1]
Q = yiq[:, :, 2]


# функция для создания RGB-изображения, в котором оставлен только один канал Y/I/Q
def channel_to_rgb(channel_index):
    # создаем массив YIQ такого же размера, заполненный нулями
    yiq_zero = np.zeros_like(yiq)
    # копируем только выбранный канал (Y, I или Q) в нулевой массив
    yiq_zero[:, :, channel_index] = yiq[:, :, channel_index]
    # преобразуем обратно в RGB пространство, используя обратную матрицу
    rgb = yiq_zero.reshape(-1, 3) @ Minv.T  # Матричное умножение
    rgb = rgb.reshape(h, w, 3)  # Возвращаем к форме изображения
    # ограничиваем значения пикселей диапазоном [0, 1] (на случай выхода за границы)
    rgb_clipped = np.clip(rgb, 0.0, 1.0)
    # преобразуем нормализованные значения обратно в 8-битные [0, 255]
    rgb_uint8 = (rgb_clipped * 255).astype(np.uint8)
    return rgb_uint8

rgb_Y = channel_to_rgb(0)
rgb_I = channel_to_rgb(1)
rgb_Q = channel_to_rgb(2)

# Сохраняем результаты
out_Y = 'yiq_Y.bmp'
out_I = 'yiq_I.bmp'
out_Q = 'yiq_Q.bmp'
Image.fromarray(rgb_Y).save(out_Y, format='BMP')
Image.fromarray(rgb_I).save(out_I, format='BMP')
Image.fromarray(rgb_Q).save(out_Q, format='BMP')

# Выводим исходное и три канала рядом
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
axes[0].imshow(rgb_Y)
axes[0].set_title('Y-channel (I=Q=0)')
axes[1].imshow(rgb_I)
axes[1].set_title('I-channel (Y=Q=0)')
axes[2].imshow(rgb_Q)
axes[2].set_title('Q-channel (Y=I=0)')
for ax in axes:
    ax.axis('off')

fig2, ax2 = plt.subplots(1, 1, figsize=(5, 5))
ax2.imshow(img)
ax2.set_title('Original (RGB)')
ax2.axis('off')

plt.tight_layout()
plt.show()


out_paths = {
    'Y_channel': out_Y,
    'I_channel': out_I,
    'Q_channel': out_Q,
    'input_used': input_path
}
out_paths


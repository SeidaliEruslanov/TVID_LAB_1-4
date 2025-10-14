import sys
import random
import heapq
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QSpinBox, QLabel, QFileDialog, QTableWidget, QTableWidgetItem
)

# ---------- Оптимизированное RLE ----------
def rle_encode_optimized(data_input):
    if not data_input:
        return ''

    parts = []  # собираем части результата в список, чтобы потом соединить одной строкой
    i = 0
    n = len(data_input)

    while i < n:
        count = 1  # считаем, сколько раз подряд повторяется один и тот же элемент
        while i + count < n and data_input[i + count] == data_input[i]:
            count += 1

        if count > 1:
            # если подряд идут одинаковые элементы — записываем их в виде "число*значение"
            parts.append(f"{count}*{data_input[i]}")
            i += count  # переходим к следующему отличающемуся элементу
        else:
            # если элементы разные, собираем подряд идущие неповторяющиеся символы
            start = i
            while i < n and (i + 1 == n or data_input[i + 1] != data_input[i]):
                i += 1
                # ограничиваем длину сегмента до 255, чтобы не переполнить
                if i - start >= 255:
                    break
            # объединяем элементы сегмента в строку
            segment = ''.join(map(str, data_input[start:i]))
            # сохраняем как "-длина(сегмент)", где длина указывает количество элементов
            parts.append(f"-{len(segment)}({segment})")

    # возвращаем строку, где сегменты разделены запятыми
    return ', '.join(parts)


# ---------- Хаффман ----------
class Node:
    def __init__(self, char, freq):
        self.char = char        # символ
        self.freq = freq        # частота появления символа
        self.left = None        # левый потомок
        self.right = None       # правый потомок

    def __lt__(self, other):
        # сравнение узлов по частоте (для правильной работы очереди с приоритетом)
        return self.freq < other.freq


def huffman_encode(data):
    if not data:
        return "", {}

    freq = {}  # создаем словарь для подсчета частоты появления каждого символа
    for char in data:
        freq[char] = freq.get(char, 0) + 1

    # создаем приоритетную очередь (кучу) из узлов дерева
    heap = [Node(char, fr) for char, fr in freq.items()]
    heapq.heapify(heap)

    # объединяем узлы, пока не останется один корневой
    while len(heap) > 1:
        left = heapq.heappop(heap)   # достаем узел с наименьшей частотой
        right = heapq.heappop(heap)  # второй по редкости
        merged = Node(None, left.freq + right.freq)  # создаем новый объединяющий узел
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)  # добавляем объединенный узел обратно в кучу

    root = heap[0]  # получаем корень дерева
    codes = {}      # сюда будут записаны коды для каждого символа

    # рекурсивная функция для обхода дерева и построения кодов
    def generate_codes(node, current_code=""):
        if node is None:
            return
        if node.char is not None:
            # если достигнут лист — сохраняем код для символа
            codes[node.char] = current_code
            return
        # рекурсивно идем влево (0) и вправо (1)
        generate_codes(node.left, current_code + "0")
        generate_codes(node.right, current_code + "1")

    generate_codes(root)

    # формируем итоговую закодированную строку
    encoded = "".join(codes[ch] for ch in data)
    return encoded, codes


# ---------- Рекурсивное преобразование ----------
def recursive_flatten(matrix):
    n = len(matrix)
    # проверяем, что матрица квадратная и имеет четный размер
    if n % 2 != 0 or any(len(row) != n for row in matrix):
        raise ValueError("Матрица должна быть квадратной и иметь чётный размер")

    result = []  # сюда будем складывать элементы в правильном порядке

    # вспомогательная рекурсивная функция для обработки блоков
    def process_block(i0, j0, size):
        # базовый случай — блок 2x2, упорядочиваем его по шаблону
        if size == 2:
            result.extend([
                matrix[i0][j0],
                matrix[i0][j0 + 1],
                matrix[i0 + 1][j0 + 1],
                matrix[i0 + 1][j0]
            ])
            return

        half = size // 2
        # рекурсивно обрабатываем подматрицы в порядке:
        # верхний левый, верхний правый, нижний правый, нижний левый
        process_block(i0, j0, half)
        if size - half >= 2:
            process_block(i0, j0 + half, size - half)
            process_block(i0 + half, j0 + half, size - half)
            process_block(i0 + half, j0, half)

    process_block(0, 0, n)  # запускаем обработку с верхнего левого угла
    return result


# ---------- Основное окно приложения ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сжатие массива (RLE и Хаффман)")

        # создаем главный вертикальный layout
        layout = QVBoxLayout()

        # панель управления с кнопками и настройками
        control_layout = QHBoxLayout()
        self.size_label = QLabel("Размер массива:")  # подпись к спинбоксу
        self.size_spin = QSpinBox()  # поле для выбора размера матрицы
        self.size_spin.setMinimum(2)
        self.size_spin.setMaximum(20)
        self.size_spin.setValue(4)

        # кнопки управления
        self.load_btn = QPushButton("Загрузить из файла")
        self.generate_btn = QPushButton("Сгенерировать")
        self.run_btn = QPushButton("Выполнить сжатие")
        self.save_btn = QPushButton("Сохранить результат")

        # добавляем элементы управления на панель
        control_layout.addWidget(self.size_label)
        control_layout.addWidget(self.size_spin)
        control_layout.addWidget(self.load_btn)
        control_layout.addWidget(self.generate_btn)
        control_layout.addWidget(self.run_btn)
        control_layout.addWidget(self.save_btn)

        # таблица для отображения матрицы
        self.table = QTableWidget()

        # текстовое поле для вывода результатов
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)  # делаем поле только для чтения

        # добавляем элементы на главный layout
        layout.addLayout(control_layout)
        layout.addWidget(self.table)
        layout.addWidget(self.text_edit)

        # создаем контейнер для layout и ставим его в окно
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # переменные для хранения данных
        self.last_result = ""  # последний результат для сохранения
        self.matrix = []       # текущая матрица

        # подключаем кнопки к методам
        self.load_btn.clicked.connect(self.load_matrix)
        self.generate_btn.clicked.connect(self.generate_matrix)
        self.run_btn.clicked.connect(self.process)
        self.save_btn.clicked.connect(self.save_result)

    # ---------- получение матрицы из таблицы ----------
    def get_matrix_from_table(self):
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        if rows == 0 or cols == 0:
            return []

        matrix = []
        for i in range(rows):
            row = []
            for j in range(cols):
                item = self.table.item(i, j)
                # если ячейка содержит число — преобразуем в int, иначе 0
                if item is not None and item.text().strip().isdigit():
                    row.append(int(item.text()))
                else:
                    row.append(0)
            matrix.append(row)
        return matrix

    # ---------- загрузка матрицы из файла ----------
    def load_matrix(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите файл с матрицей", "", "Text Files (*.txt)")
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                matrix = []
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        matrix.append([int(x) for x in parts])
                n = len(matrix)
                for row in matrix:
                    if len(row) != n:
                        raise ValueError("Матрица не квадратная")

                # сохраняем и отображаем матрицу
                self.matrix = matrix
                self.display_matrix()
                self.text_edit.setPlainText(f"Матрица {n}x{n} успешно загружена.")

        except Exception as e:
            self.text_edit.setPlainText(f"Ошибка при чтении файла: {e}")

    # ---------- генерация случайной матрицы ----------
    def generate_matrix(self):
        size = self.size_spin.value()  # читаем выбранный размер
        # создаем матрицу случайных чисел от 0 до 9
        self.matrix = [[random.randint(0, 9) for _ in range(size)] for _ in range(size)]
        self.display_matrix()
        self.text_edit.setPlainText(f"Матрица {size}x{size} успешно сгенерирована.")

    # ---------- отображение матрицы в таблице ----------
    def display_matrix(self):
        if not self.matrix:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        n = len(self.matrix)
        self.table.setRowCount(n)
        self.table.setColumnCount(n)

        # заполняем таблицу значениями из матрицы
        for i in range(n):
            for j in range(n):
                item = QTableWidgetItem(str(self.matrix[i][j]))
                self.table.setItem(i, j, item)

    # ---------- выполнение алгоритмов сжатия ----------
    def process(self):
        matrix = self.get_matrix_from_table()
        if not matrix:
            self.text_edit.setPlainText("Сначала загрузите или сгенерируйте матрицу!")
            return

        self.matrix = matrix

        # преобразуем матрицу в одномерный массив рекурсивно
        flattened = recursive_flatten(self.matrix)
        flattened_str = list(map(str, flattened))  # переводим в строки

        # применяем RLE и Хаффман
        rle = rle_encode_optimized(flattened_str)
        huff_encoded, codes = huffman_encode(flattened_str)

        # формируем текстовый вывод
        text = "Исходная матрица:\n"
        text += "\n".join(" ".join(map(str, row)) for row in self.matrix)
        text += "\n\nОдномерный массив:\n" + " ".join(map(str, flattened))
        text += "\n\nОптимизированный RLE:\n" + rle
        text += "\n\nХаффман (закодированная строка):\n" + huff_encoded
        text += "\n\nКоды Хаффмана:\n" + str(codes)

        self.text_edit.setPlainText(text)
        self.last_result = text  # сохраняем результат для последующего сохранения

    # ---------- сохранение результата в файл ----------
    def save_result(self):
        if not self.last_result:
            self.text_edit.setPlainText("Нет данных для сохранения, сначала выполните сжатие")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить результат", "", "Text Files (*.txt)")
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.last_result)
            # добавляем уведомление в поле вывода
            self.text_edit.append(f"\n\nРезультат сохранен в файл: {filename}")


# ---------- Запуск программы ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)  # задаем размер окна
    window.show()            # отображаем интерфейс
    sys.exit(app.exec_())    # запускаем цикл обработки событий

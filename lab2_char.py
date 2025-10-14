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

    encoding = ''
    i = 0
    n = len(data_input)

    while i < n:
        count = 1
        while i + count < n and data_input[i + count] == data_input[i]:
            count += 1
        if count > 1:
            encoding += str(count) + data_input[i]
            i += count
        else:
            start = i
            while i < n and (i + 1 == n or data_input[i + 1] != data_input[i]):
                i += 1
                if i - start >= 255:
                    break
            segment = ''.join(data_input[start:i])
            encoding += f'-{len(segment)}{segment}'
    return encoding


# ---------- Хаффман ----------
class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


def huffman_encode(data):
    if not data:
        return "", {}

    freq = {}
    for char in data:
        freq[char] = freq.get(char, 0) + 1

    heap = [Node(char, fr) for char, fr in freq.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = Node(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)

    root = heap[0]
    codes = {}

    def generate_codes(node, current_code=""):
        if node is None:
            return
        if node.char is not None:
            codes[node.char] = current_code
            return
        generate_codes(node.left, current_code + "0")
        generate_codes(node.right, current_code + "1")

    generate_codes(root)
    encoded = "".join(codes[ch] for ch in data)
    return encoded, codes


# ---------- Рекурсивное преобразование ----------
def recursive_flatten(matrix):
    n = len(matrix)

    # Базовый случай — матрица 2×2
    if n == 2:
        # два возможных шаблона без разрывов (из лекции)
        # вариант 1:
        return [matrix[0][0], matrix[0][1], matrix[1][1], matrix[1][0]]
        # если нужен альтернативный порядок:
        # return [matrix[0][0], matrix[1][0], matrix[1][1], matrix[0][1]]

    # Разбиваем матрицу на 4 квадранта
    mid = n // 2
    a11 = [row[:mid] for row in matrix[:mid]]      # верхний левый
    a12 = [row[mid:] for row in matrix[:mid]]      # верхний правый
    a21 = [row[:mid] for row in matrix[mid:]]      # нижний левый
    a22 = [row[mid:] for row in matrix[mid:]]      # нижний правый

    # Рекурсивный обход — шаблон из лекции:
    # сначала верхний левый, затем верхний правый, потом нижний правый и нижний левый
    return (
        recursive_flatten(a11) +
        recursive_flatten(a12) +
        recursive_flatten(a22) +
        recursive_flatten(a21)
    )


# ---------- Основное окно ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сжатие массива (RLE и Хаффман)")

        layout = QVBoxLayout()

        # Панель управления
        control_layout = QHBoxLayout()
        self.size_label = QLabel("Размер массива:")
        self.size_spin = QSpinBox()
        self.size_spin.setMinimum(2)
        self.size_spin.setMaximum(20)
        self.size_spin.setValue(4)

        self.load_btn = QPushButton("Загрузить из файла")
        self.generate_btn = QPushButton("Сгенерировать")
        self.run_btn = QPushButton("Выполнить сжатие")
        self.save_btn = QPushButton("Сохранить результат")

        control_layout.addWidget(self.size_label)
        control_layout.addWidget(self.size_spin)
        control_layout.addWidget(self.load_btn)
        control_layout.addWidget(self.generate_btn)
        control_layout.addWidget(self.run_btn)
        control_layout.addWidget(self.save_btn)

        self.table = QTableWidget()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)

        layout.addLayout(control_layout)
        layout.addWidget(self.table)
        layout.addWidget(self.text_edit)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.last_result = ""
        self.matrix = []

        self.load_btn.clicked.connect(self.load_matrix)
        self.generate_btn.clicked.connect(self.generate_matrix)
        self.run_btn.clicked.connect(self.process)
        self.save_btn.clicked.connect(self.save_result)

    def get_matrix_from_table(self):
        """Считывает матрицу из таблицы интерфейса"""
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        if rows == 0 or cols == 0:
            return []

        matrix = []
        for i in range(rows):
            row = []
            for j in range(cols):
                item = self.table.item(i, j)
                if item is not None and item.text().strip():
                    row.append(item.text()[0])  # берем только первый символ
                else:
                    row.append(' ')  # пустой символ
            matrix.append(row)
        return matrix

    def load_matrix(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите файл с матрицей", "", "Text Files (*.txt)")
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                matrix = []
                for line in f:
                    line = line.strip()
                    if line:
                        row = list(line.replace(" ", ""))  # убираем пробелы, оставляем символы
                        matrix.append(row)

                # Проверяем, что матрица квадратная
                n = len(matrix)
                for row in matrix:
                    if len(row) != n:
                        raise ValueError("Матрица не квадратная")

                self.matrix = matrix
                self.display_matrix()
                self.text_edit.setPlainText(f"Матрица {n}x{n} успешно загружена.")

        except Exception as e:
            self.text_edit.setPlainText(f"Ошибка при чтении файла: {e}")

    def generate_matrix(self):
        size = self.size_spin.value()
        # Генерация случайных букв A-Z
        self.matrix = [[random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(size)] for _ in range(size)]
        self.display_matrix()
        self.text_edit.setPlainText(f"Матрица {size}x{size} успешно сгенерирована.")

    def display_matrix(self):
        """Отображает текущую матрицу в таблице"""
        if not self.matrix:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        n = len(self.matrix)
        self.table.setRowCount(n)
        self.table.setColumnCount(n)

        for i in range(n):
            for j in range(n):
                item = QTableWidgetItem(self.matrix[i][j])
                self.table.setItem(i, j, item)

    def process(self):
        # Считываем данные из таблицы
        matrix = self.get_matrix_from_table()
        if not matrix:
            self.text_edit.setPlainText("Сначала загрузите или сгенерируйте матрицу!")
            return

        # Обновляем внутреннюю матрицу
        self.matrix = matrix

        flattened = recursive_flatten(self.matrix)
        rle = rle_encode_optimized(flattened)
        huff_encoded, codes = huffman_encode(flattened)

        text = "Исходная матрица:\n"
        text += "\n".join(" ".join(map(str, row)) for row in self.matrix)
        text += "\n\nОдномерный массив:\n" + "".join(flattened)
        text += "\n\nОптимизированный RLE:\n" + rle
        text += "\n\nХаффман (закодированная строка):\n" + huff_encoded
        text += "\n\nКоды Хаффмана:\n" + str(codes)

        self.text_edit.setPlainText(text)
        self.last_result = text

    def save_result(self):
        if not self.last_result:
            self.text_edit.setPlainText("Нет данных для сохранения, сначала выполните сжатие")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить результат", "", "Text Files (*.txt)")
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.last_result)
            self.text_edit.append(f"\n\nРезультат сохранен в файл: {filename}")


# ---------- Запуск ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())

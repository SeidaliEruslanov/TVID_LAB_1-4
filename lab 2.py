import sys
import random
import heapq  # для построения кучи в алгоритме хаффмана
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QSpinBox, QLabel, QFileDialog, QTableWidget, QTableWidgetItem
)

# ---------- утилиты ----------
# проверка, что число является степенью двойки (n = 1,2,4,8,...)
def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0

# ---------- оптимизированное rle ----------
# алгоритм run-length encoding с оптимизацией для смешанных данных:
# 1) повторяющиеся символы кодируются как "количество*символ"
# 2) неповторяющиеся сегменты кодируются как "-длина(содержимое)"
# это позволяет эффективно сжимать как повторяющиеся, так и уникальные последовательности
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
            # это стандартный rle для повторяющихся символов
            parts.append(f"{count}*{data_input[i]}")
            i += count  # переходим к следующему отличающемуся элементу
        else:
            # если элементы разные, собираем подряд идущие неповторяющиеся символы
            # это оптимизация для не-повторяющихся данных
            start = i
            while i < n and (i + 1 == n or data_input[i + 1] != data_input[i]):
                i += 1
                # ограничиваем длину сегмента до 255, чтобы не переполнить однобайтовое поле
                if i - start >= 255:
                    break
            # объединяем элементы сегмента в строку
            segment = ''.join(map(str, data_input[start:i]))
            # сохраняем как "-длина(сегмент)", где длина указывает количество элементов
            # знак минус отличает от повторяющихся сегментов
            parts.append(f"-{len(segment)}({segment})")

    # возвращаем строку, где сегменты разделены запятыми для читаемости
    return ', '.join(parts)


# ---------- хаффман ----------
# алгоритм хаффмана строит оптимальное префиксное дерево кодирования:
# 1) подсчитываем частоты символов
# 2) строим дерево, объединяя узлы с наименьшими частотами
# 3) коды получаются обходом дерева (0=левый, 1=правый)
# технически используем кучу (heap) для эффективного поиска минимумов
class Node:
    def __init__(self, char, freq):
        self.char = char        # символ (None для внутренних узлов)
        self.freq = freq        # частота появления символа
        self.left = None        # левый потомок
        self.right = None       # правый потомок

    def __lt__(self, other):
        # сравнение узлов по частоте (для правильной работы очереди с приоритетом)
        # heapq использует это для сортировки узлов в куче
        return self.freq < other.freq


def huffman_encode(data):
    if not data:
        return "", {}

    # подсчитываем частоты символов для построения дерева
    freq = {}  # создаем словарь для подсчета частоты появления каждого символа
    for char in data:
        freq[char] = freq.get(char, 0) + 1

    # создаем приоритетную очередь (кучу) из узлов дерева
    # каждый символ становится листом дерева с соответствующей частотой
    heap = [Node(char, fr) for char, fr in freq.items()]
    heapq.heapify(heap)  # превращаем список в кучу за O(n)

    # объединяем узлы, пока не останется один корневой (алгоритм хаффмана)
    while len(heap) > 1:
        left = heapq.heappop(heap)   # достаем узел с наименьшей частотой
        right = heapq.heappop(heap)  # второй по редкости
        # создаем внутренний узел с суммой частот дочерних узлов
        merged = Node(None, left.freq + right.freq)  # создаем новый объединяющий узел
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)  # добавляем объединенный узел обратно в кучу

    root = heap[0]  # получаем корень дерева (единственный оставшийся узел)
    codes = {}      # сюда будут записаны коды для каждого символа

    # рекурсивная функция для обхода дерева и построения кодов
    # обход в глубину: 0=левый, 1=правый
    def generate_codes(node, current_code=""):
        if node is None:
            return
        if node.char is not None:
            # если достигнут лист — сохраняем код для символа
            # частые символы получают короткие коды
            codes[node.char] = current_code
            return
        # рекурсивно идем влево (0) и вправо (1)
        generate_codes(node.left, current_code + "0")
        generate_codes(node.right, current_code + "1")

    generate_codes(root)

    # формируем итоговую закодированную строку, заменяя символы на их коды
    encoded = "".join(codes[ch] for ch in data)
    return encoded, codes


# ---------- рекурсивное преобразование ----------
# алгоритм зигзагообразного обхода матрицы с рекурсивным разбиением:
# 1) разбиваем матрицу на 4 квадранта
# 2) обрабатываем их в порядке: верх-левый, верх-правый, низ-правый, низ-левый
# 3) для блока 2x2 применяем фиксированный шаблон обхода
# это создает зигзагообразную последовательность элементов
def recursive_flatten(matrix):
    n = len(matrix)
    # проверяем, что матрица квадратная и имеет четный размер
    # рекурсивный алгоритм требует четных размеров для корректного разбиения
    if n % 2 != 0 or any(len(row) != n for row in matrix):
        raise ValueError("Матрица должна быть квадратной и иметь чётный размер")

    result = []  # сюда будем складывать элементы в правильном порядке

    # вспомогательная рекурсивная функция для обработки блоков
    def process_block(i0, j0, size):
        # базовый случай — блок 2x2, упорядочиваем его по шаблону
        # это создает зигзагообразный обход для маленьких блоков
        if size == 2:
            result.extend([
                matrix[i0][j0],         # верх-левый
                matrix[i0][j0 + 1],     # верх-правый
                matrix[i0 + 1][j0 + 1], # низ-правый
                matrix[i0 + 1][j0]      # низ-левый
            ])
            return

        half = size // 2
        # рекурсивно обрабатываем подматрицы в порядке:
        # верхний левый, верхний правый, нижний правый, нижний левый
        # это создает зигзагообразный обход для больших матриц
        process_block(i0, j0, half)  # верх-левый квадрант
        if size - half >= 2:
            process_block(i0, j0 + half, size - half)      # верх-правый
            process_block(i0 + half, j0 + half, size - half)  # низ-правый
            process_block(i0 + half, j0, half)            # низ-левый

    process_block(0, 0, n)  # запускаем обработку с верхнего левого угла всей матрицы
    return result


# ---------- основное окно приложения ----------
# gui для демонстрации алгоритмов сжатия данных:
# 1) загрузка/генерация матриц через интерфейс
# 2) рекурсивное преобразование в одномерный массив
# 3) применение rle и хаффмана для сжатия
# 4) сохранение результатов в файл
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сжатие массива (RLE и Хаффман)")

        # создаем главный вертикальный layout для размещения элементов
        layout = QVBoxLayout()

        # панель управления с кнопками и настройками
        control_layout = QHBoxLayout()
        self.size_label = QLabel("Размер массива:")  # подпись к спинбоксу
        self.size_spin = QSpinBox()  # поле для выбора размера матрицы
        self.size_spin.setMinimum(2)  # минимальный размер 2x2
        self.size_spin.setMaximum(20)  # максимальный размер 20x20
        self.size_spin.setValue(4)  # размер по умолчанию

        # кнопки управления для различных операций
        self.load_btn = QPushButton("Загрузить из файла")  # загрузка матрицы из файла
        self.generate_btn = QPushButton("Сгенерировать")  # генерация случайной матрицы
        self.run_btn = QPushButton("Выполнить сжатие")  # запуск алгоритмов сжатия
        self.save_btn = QPushButton("Сохранить результат")  # сохранение результатов

        # добавляем элементы управления на панель
        control_layout.addWidget(self.size_label)
        control_layout.addWidget(self.size_spin)
        control_layout.addWidget(self.load_btn)
        control_layout.addWidget(self.generate_btn)
        control_layout.addWidget(self.run_btn)
        control_layout.addWidget(self.save_btn)

        # таблица для отображения матрицы (редактируемая)
        self.table = QTableWidget()

        # текстовое поле для вывода результатов сжатия
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

        # переменные для хранения данных между операциями
        self.last_result = ""  # последний результат для сохранения
        self.matrix = []       # текущая матрица

        # подключаем кнопки к соответствующим методам обработки
        self.load_btn.clicked.connect(self.load_matrix)
        self.generate_btn.clicked.connect(self.generate_matrix)
        self.run_btn.clicked.connect(self.process)
        self.save_btn.clicked.connect(self.save_result)

    # ---------- получение матрицы из таблицы ----------
    # извлекаем данные из gui-таблицы для дальнейшей обработки
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
                # это обеспечивает корректную работу с пустыми ячейками
                if item is not None and item.text().strip().isdigit():
                    row.append(int(item.text()))
                else:
                    row.append(0)  # значение по умолчанию для некорректных данных
            matrix.append(row)
        return matrix

    # ---------- загрузка матрицы из файла ----------
    # загружаем матрицу из текстового файла с проверкой корректности
    def load_matrix(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите файл с матрицей", "", "Text Files (*.txt)")
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                matrix = []
                for line in f:
                    parts = line.strip().split()  # разбиваем строку на числа
                    if parts:
                        matrix.append([int(x) for x in parts])
                n = len(matrix)
                # проверяем, что матрица квадратная
                for row in matrix:
                    if len(row) != n:
                        raise ValueError("Матрица не квадратная")
                # проверяем, что размер — степень двойки (2,4,8,...)
                if not is_power_of_two(n):
                    raise ValueError("Размер матрицы должен быть степенью двойки (2^k)")

                # сохраняем и отображаем матрицу в gui
                self.matrix = matrix
                self.display_matrix()
                self.text_edit.setPlainText(f"Матрица {n}x{n} успешно загружена.")

        except Exception as e:
            self.text_edit.setPlainText(f"Ошибка при чтении файла: {e}")

    # ---------- генерация случайной матрицы ----------
    # создаем матрицу случайных чисел для тестирования алгоритмов
    def generate_matrix(self):
        size = self.size_spin.value()  # читаем выбранный размер
        # создаем матрицу случайных чисел от 0 до 9
        # диапазон 0-9 выбран для удобства отображения и тестирования
        self.matrix = [[random.randint(0, 9) for _ in range(size)] for _ in range(size)]
        self.display_matrix()
        self.text_edit.setPlainText(f"Матрица {size}x{size} успешно сгенерирована.")

    # ---------- отображение матрицы в таблице ----------
    # обновляем gui-таблицу для отображения текущей матрицы
    def display_matrix(self):
        if not self.matrix:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        n = len(self.matrix)
        self.table.setRowCount(n)
        self.table.setColumnCount(n)

        # заполняем таблицу значениями из матрицы
        # каждый элемент матрицы становится ячейкой в gui-таблице
        for i in range(n):
            for j in range(n):
                item = QTableWidgetItem(str(self.matrix[i][j]))
                self.table.setItem(i, j, item)

    # ---------- выполнение алгоритмов сжатия ----------
    # основной метод: применяем все алгоритмы сжатия к матрице
    def process(self):
        matrix = self.get_matrix_from_table()
        if not matrix:
            self.text_edit.setPlainText("Сначала загрузите или сгенерируйте матрицу!")
            return

        # валидируем матрицу из таблицы: квадратность и чётность размера
        rows = len(matrix)
        cols = len(matrix[0]) if rows > 0 else 0
        if any(len(row) != cols for row in matrix) or rows != cols:
            self.text_edit.setPlainText("Ошибка: матрица должна быть квадратной")
            return
        if not is_power_of_two(rows):
            self.text_edit.setPlainText("Ошибка: размер матрицы должен быть степенью двойки (2^k)")
            return

        self.matrix = matrix

        # преобразуем матрицу в одномерный массив рекурсивно
        # это создает зигзагообразную последовательность элементов
        try:
            flattened = recursive_flatten(self.matrix)
        except Exception as e:
            self.text_edit.setPlainText(f"Ошибка при преобразовании матрицы: {e}")
            return
        flattened_str = list(map(str, flattened))  # переводим в строки для алгоритмов

        # применяем RLE и Хаффман к полученному массиву
        rle = rle_encode_optimized(flattened_str)  # run-length encoding
        huff_encoded, codes = huffman_encode(flattened_str)  # кодирование хаффмана

        # формируем текстовый вывод с результатами всех этапов
        text = "Исходная матрица:\n"
        text += "\n".join(" ".join(map(str, row)) for row in self.matrix)
        text += "\n\nОдномерный массив:\n" + " ".join(map(str, flattened))
        text += "\n\nОптимизированный RLE:\n" + rle
        text += "\n\nХаффман (закодированная строка):\n" + huff_encoded
        text += "\n\nКоды Хаффмана:\n" + str(codes)

        self.text_edit.setPlainText(text)
        self.last_result = text  # сохраняем результат для последующего сохранения

    # ---------- сохранение результата в файл ----------
    # сохраняем результаты сжатия в текстовый файл
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


# ---------- запуск программы ----------
# точка входа в приложение с созданием главного окна
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)  # задаем размер окна
    window.show()            # отображаем интерфейс
    sys.exit(app.exec_())    # запускаем цикл обработки событий

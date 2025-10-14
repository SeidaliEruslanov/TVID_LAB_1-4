# -*- coding: utf-8 -*-
import sys
from collections import defaultdict, deque
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QDialog,
    QTextEdit, QLineEdit
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


# --- Функции кодирования (без изменений) ---

def arithmetic_encode(text):
    frequencies = defaultdict(int)
    for char in text:
        frequencies[char] += 1

    total_symbols = len(text)
    probabilities = {char: freq / total_symbols for char, freq in frequencies.items()}

    cumulative_prob = 0.0
    intervals = {}
    interval_log = []
    for char, prob in sorted(probabilities.items()):
        intervals[char] = (cumulative_prob, cumulative_prob + prob)
        interval_log.append((char, cumulative_prob, cumulative_prob + prob))
        cumulative_prob += prob

    low, high = 0.0, 1.0
    calculation_steps = []
    for char in text:
        char_low, char_high = intervals[char]
        range_width = high - low
        high = low + range_width * char_high
        low = low + range_width * char_low
        calculation_steps.append((char, low, high))

    encoded_value = (low + high) / 2
    final_interval = f"[{low}, {high}]"

    with open("encoding_results.txt", "a", encoding="utf-8") as file:
        file.write("--- Арифметическое кодирование ---\n")
        file.write(f"Исходный текст: {text}\n\n")
        file.write(f"Частоты символов: {dict(frequencies)}\n")
        file.write(f"Вероятности символов: {probabilities}\n\n")
        file.write("Интервалы для каждого символа:\n")
        for char, low_int, high_int in interval_log:
            file.write(f"  {char}: [{low_int}, {high_int}]\n")
        file.write("\nПошаговые вычисления:\n")
        for char, low_step, high_step in calculation_steps:
            file.write(f"  Символ '{char}': Интервал после сжатия [{low_step}, {high_step}]\n")
        file.write("\nФИНАЛЬНЫЙ РЕЗУЛЬТАТ:\n")
        file.write(f"  Интервал: {final_interval}\n")
        file.write(f"  Закодированное значение: {encoded_value}\n\n")

    return final_interval, encoded_value


def bwt_transform(s):
    rotations = sorted([s[i:] + s[:i] for i in range(len(s))])
    bwt_result = ''.join(rotation[-1] for rotation in rotations)

    with open("encoding_results.txt", "a", encoding="utf-8") as file:
        file.write("--- Преобразование BWT ---\n")
        file.write(f"Исходный текст: {s}\n")
        file.write("Отсортированные циклические сдвиги:\n")
        for r in rotations:
            file.write(f"  {r}\n")
        file.write(f"Результат BWT: {bwt_result}\n\n")

    return bwt_result


def mtf_encode(bwt_result):
    alphabet = deque(sorted(set(bwt_result)))
    mtf_result = []

    with open("encoding_results.txt", "a", encoding="utf-8") as file:
        file.write("--- Преобразование MTF ---\n")
        file.write(f"Входная строка (результат BWT): {bwt_result}\n")

        for char in bwt_result:
            index = alphabet.index(char)
            mtf_result.append(index)
            file.write(f"Символ '{char}': Индекс {index}, Алфавит: {list(alphabet)}\n")
            alphabet.remove(char)
            alphabet.appendleft(char)

        file.write(f"\nРезультат MTF: {mtf_result}\n\n")

    return mtf_result


# --- Диалоговые окна с увеличенным шрифтом ---

class ArithmeticDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Арифметическое кодирование")
        self.setGeometry(200, 200, 700, 500)
        self.default_text = (
            "Винни шагал мимо сосен и елок, шагал по склонам,заросшим можжевельником и репейником, шагал по крутым берегам ручьев и речек, шагал среди груд камней и снова среди зарослей, и вот наконец, усталый и голодный, он вошел в Дремучий Лес, потому что именно там, в Дремучем Лесу, жила Сова "

        )
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        font = QFont("Arial", 14)

        info_label = QLabel("Текст для кодирования (можно редактировать):", self)
        info_label.setFont(font)
        layout.addWidget(info_label)

        self.text_display = QTextEdit(self)
        self.text_display.setFont(font)
        self.text_display.setText(self.default_text)
        layout.addWidget(self.text_display)

        self.result_label = QLabel("Результат будет показан здесь.", self)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setFont(font)
        layout.addWidget(self.result_label)

        show_result_button = QPushButton("Показать результат", self)
        show_result_button.setFont(QFont("Arial", 16, QFont.Bold))
        show_result_button.clicked.connect(self.show_result)
        layout.addWidget(show_result_button)

    def show_result(self):
        text_to_encode = self.text_display.toPlainText()
        if not text_to_encode:
            self.result_label.setText("Ошибка: Поле ввода не может быть пустым.")
            return
        interval, value = arithmetic_encode(text_to_encode)
        result_text = f"ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:\nИнтервал: {interval}\nЗакодированное значение: {value}"
        self.result_label.setText(result_text)


class BwtDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Преобразование BWT")
        self.setGeometry(250, 250, 600, 400)
        self.default_text = "ИИККЕКВАУЦСРННН"
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        font = QFont("Arial", 14)

        info_label = QLabel("Входная строка для BWT (можно редактировать):", self)
        info_label.setFont(font)
        layout.addWidget(info_label)

        self.input_field = QLineEdit(self)
        self.input_field.setFont(font)
        self.input_field.setText(self.default_text)
        layout.addWidget(self.input_field)

        self.result_label = QLabel("Результат будет показан здесь.", self)
        self.result_label.setFont(font)
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        show_result_button = QPushButton("Показать результат", self)
        show_result_button.setFont(QFont("Arial", 16, QFont.Bold))
        show_result_button.clicked.connect(self.show_result)
        layout.addWidget(show_result_button)

    def show_result(self):
        text_to_transform = self.input_field.text()
        if not text_to_transform:
            self.result_label.setText("Ошибка: Поле ввода не может быть пустым.")
            return
        result = bwt_transform(text_to_transform)
        self.result_label.setText(f"Результат BWT: {result}")


class MtfDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MTF Преобразование")
        self.setGeometry(300, 300, 600, 400)
        bwt_input_default = "ИИККЕКВАУЦСРННН"
        self.default_text = bwt_transform(bwt_input_default)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        font = QFont("Arial", 14)

        info_label = QLabel("Входная строка для MTF (можно редактировать):", self)
        info_label.setFont(font)
        layout.addWidget(info_label)

        self.input_field = QLineEdit(self)
        self.input_field.setFont(font)
        self.input_field.setText(self.default_text)
        layout.addWidget(self.input_field)

        self.result_label = QLabel("Результат будет показан здесь.", self)
        self.result_label.setFont(font)
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        show_result_button = QPushButton("Показать результат", self)
        show_result_button.setFont(QFont("Arial", 16, QFont.Bold))
        show_result_button.clicked.connect(self.show_result)
        layout.addWidget(show_result_button)

    def show_result(self):
        text_to_encode = self.input_field.text()
        if not text_to_encode:
            self.result_label.setText("Ошибка: Поле ввода не может быть пустым.")
            return
        result = mtf_encode(text_to_encode)
        self.result_label.setText(f"Результат MTF: {result}")


# --- Главное окно приложения ---

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        with open("encoding_results.txt", "w", encoding="utf-8") as f:
            f.write("Результаты выполнения лабораторной работы №3\n\n")

    def initUI(self):
        self.setWindowTitle("Кодирование текста (PyQt5)")
        self.setGeometry(100, 100, 600, 400)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        title_label = QLabel("Выберите тип кодирования:", self)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        font_button = QFont("Arial", 16)

        btn_arithmetic = QPushButton("Арифметическое кодирование", self)
        btn_arithmetic.setFont(font_button)
        btn_arithmetic.clicked.connect(self.open_arithmetic_dialog)
        main_layout.addWidget(btn_arithmetic)

        btn_bwt = QPushButton("Преобразование Барроуза-Уилера (BWT)", self)
        btn_bwt.setFont(font_button)
        btn_bwt.clicked.connect(self.open_bwt_dialog)
        main_layout.addWidget(btn_bwt)

        btn_mtf = QPushButton("Move-to-Front (MTF)", self)
        btn_mtf.setFont(font_button)
        btn_mtf.clicked.connect(self.open_mtf_dialog)
        main_layout.addWidget(btn_mtf)

        main_layout.addStretch()

    def open_arithmetic_dialog(self):
        dialog = ArithmeticDialog(self)
        dialog.exec_()

    def open_bwt_dialog(self):
        dialog = BwtDialog(self)
        dialog.exec_()

    def open_mtf_dialog(self):
        dialog = MtfDialog(self)
        dialog.exec_()


# --- Точка входа ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

# -*- coding: utf-8 -*-
import sys
from collections import defaultdict, deque
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QDialog,
    QTextEdit, QLineEdit
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from decimal import Decimal, getcontext  # decimal даёт управляемую точность вместо float


# --- функции кодирования ---
# ниже реализованы три классических алгоритма: арифметическое кодирование, bwt и mtf.
# комментарии поясняют как идею алгоритмов, так и технические детали реализации.
# замечание про точность: для арифметического кодирования важно избегать накопления ошибок,
# поэтому вместо float используется decimal с повышением precision относительно длины входа.

def arithmetic_encode(text):
    # арифметическое кодирование на интервале [0,1):
    # 1) считаем частоты символов во входе и превращаем их в вероятности
    # 2) строим кумулятивные интервалы для символов (префиксные суммы вероятностей)
    # 3) для каждого символа последовательно сужаем рабочий интервал [low, high)
    #    в пропорции к интервалу соответствующего символа
    # 4) любой номер внутри финального интервала является кодом сообщения
    # технически используем Decimal для высокой точности на длинных строках
    # (устанавливаем precision пропорционально длине текста)
    getcontext().prec = max(50, len(text) * 2)  # эмпирически достаточная точность для учебных примеров

    frequencies = defaultdict(int)
    for char in text:
        frequencies[char] += 1

    # общее число символов и вероятности (как Decimal)
    total_symbols = Decimal(len(text))
    probabilities = {char: Decimal(freq) / total_symbols for char, freq in frequencies.items()}  # p(x)

    # строим кумулятивные интервалы для каждого символа в порядке сортировки
    cumulative_prob = Decimal(0)
    intervals = {}
    interval_log = []
    for char, prob in sorted(probabilities.items()):
        intervals[char] = (cumulative_prob, cumulative_prob + prob)  # полуинтервал [low, high)
        interval_log.append((char, cumulative_prob, cumulative_prob + prob))
        cumulative_prob += prob

    # последовательно сужаем интервал [low, high)
    low, high = Decimal(0), Decimal(1)
    calculation_steps = []
    for char in text:
        char_low, char_high = intervals[char]
        range_width = high - low  # ширина текущего рабочего интервала
        high = low + range_width * char_high
        low = low + range_width * char_low
        calculation_steps.append((char, low, high))

    # берём середину финального интервала как представительный код
    encoded_value = (low + high) / 2
    final_interval = f"[{low}, {high}]"

    # лог пишется в отдельный файл; файл очищается перед каждой записью
    with open("arithmetic_results.txt", "w", encoding="utf-8") as file:  # отдельный файл на каждую операцию
        file.write("--- Арифметическое кодирование ---\n")
        file.write(f"Исходный текст: {text}\n\n")
        file.write(f"Частоты символов: {dict(frequencies)}\n")  # словарь символ→частота
        file.write(f"Вероятности символов: {probabilities}\n\n")  # словарь символ→вероятность
        file.write("Интервалы для каждого символа:\n")
        for char, low_int, high_int in interval_log:
            file.write(f"  {char}: [{low_int}, {high_int}]\n")  # кумулятивный интервал символа
        file.write("\nПошаговые вычисления:\n")
        for char, low_step, high_step in calculation_steps:
            # после обработки каждого символа сохраняем текущий рабочий интервал;
            # из-за использования decimal шаги воспроизводимы и не зависят от платформы
            file.write(f"  Символ '{char}': Интервал после сжатия [{low_step}, {high_step}]\n")
        file.write("\nФИНАЛЬНЫЙ РЕЗУЛЬТАТ:\n")
        file.write(f"  Интервал: {final_interval}\n")  # итоговый интервал сообщения
        file.write(f"  Закодированное значение: {encoded_value}\n\n")  # представительный код

    return final_interval, encoded_value


def bwt_transform(s):
    # преобразование барроуза–уилера (bwt):
    # 1) строим все циклические сдвиги строки
    # 2) сортируем их лексикографически
    # 3) берём последний столбец отсортированной матрицы сдвигов — это и есть bwt-строка
    rotations = sorted([s[i:] + s[:i] for i in range(len(s))])  # матрица всех циклических сдвигов
    bwt_result = ''.join(rotation[-1] for rotation in rotations)

    # логируем в отдельный файл (очистка при каждом запуске)
    with open("bwt_results.txt", "w", encoding="utf-8") as file:  # отдельный лог для bwt
        file.write("--- Преобразование BWT ---\n")
        file.write(f"Исходный текст: {s}\n")
        file.write("Отсортированные циклические сдвиги:\n")
        for r in rotations:
            file.write(f"  {r}\n")  # каждая строка — один циклический сдвиг
        file.write(f"Результат BWT: {bwt_result}\n\n")

    return bwt_result


def mtf_encode(bwt_result):
    # преобразование move-to-front (mtf):
    # 1) поддерживаем упорядоченный алфавит (очередь)
    # 2) для каждого символа записываем его индекс в текущем алфавите
    # 3) перемещаем встретившийся символ в начало (front)
    alphabet = deque(sorted(set(bwt_result)))  # уникальные символы, отсортированные (стартовый алфавит)
    mtf_result = []

    # логируем вход и шаги mtf в отдельный файл
    with open("mtf_results.txt", "w", encoding="utf-8") as file:  # отдельный лог для mtf
        file.write("--- Преобразование MTF ---\n")
        file.write(f"Входная строка (результат BWT): {bwt_result}\n")

        for char in bwt_result:
            index = alphabet.index(char)  # находим индекс символа в текущем алфавите
            mtf_result.append(index)
            file.write(f"Символ '{char}': Индекс {index}, Алфавит: {list(alphabet)}\n")
            # переносим символ в начало, чтобы учесть локальность в дальнейших шагах
            alphabet.remove(char)
            alphabet.appendleft(char)

        file.write(f"\nРезультат MTF: {mtf_result}\n\n")  # последовательность индексов

    return mtf_result


# --- диалоговые окна с увеличенным шрифтом ---
# окна ui предназначены для демонстрации работы алгоритмов на примерах.
# ввод можно редактировать, результат отображается внизу диалога.

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

        self.text_display = QTextEdit(self)  # поле редактируемого текста; многострочный ввод
        self.text_display.setFont(font)
        self.text_display.setText(self.default_text)
        layout.addWidget(self.text_display)

        self.result_label = QLabel("Результат будет показан здесь.", self)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setFont(font)
        layout.addWidget(self.result_label)

        show_result_button = QPushButton("Показать результат", self)  # запуск кодирования
        show_result_button.setFont(QFont("Arial", 16, QFont.Bold))
        show_result_button.clicked.connect(self.show_result)
        layout.addWidget(show_result_button)

    def show_result(self):
        text_to_encode = self.text_display.toPlainText()
        if not text_to_encode:
            self.result_label.setText("Ошибка: Поле ввода не может быть пустым.")
            return
        interval, value = arithmetic_encode(text_to_encode)  # лог пишется внутри функции (в свой файл)

        # отображаем округление до 9 знаков (не влияет на запись в файл). округление нужно лишь для удобочитаемости
        try:
            interval_body = interval.strip()[1:-1]
            low_s, high_s = interval_body.split(',')
            low_d = Decimal(low_s.strip())
            high_d = Decimal(high_s.strip())
            q9 = Decimal('0.000000000')
            low_r = str(low_d.quantize(q9))
            high_r = str(high_d.quantize(q9))
            interval_disp = f"[{low_r}, {high_r}]"
        except Exception:
            interval_disp = interval

        try:
            value_d = Decimal(str(value))  # приводим к строке, чтобы не потерять точность при конвертации
            value_disp = str(value_d.quantize(Decimal('0.000000000')))
        except Exception:
            try:
                value_disp = f"{float(value):.9f}"  # запасной путь, если decimal не сработал
            except Exception:
                value_disp = str(value)

        result_text = f"ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:\nИнтервал: {interval_disp}\nЗакодированное значение: {value_disp}"
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

        self.input_field = QLineEdit(self)  # однострочное поле ввода
        self.input_field.setFont(font)
        self.input_field.setText(self.default_text)
        layout.addWidget(self.input_field)

        self.result_label = QLabel("Результат будет показан здесь.", self)
        self.result_label.setFont(font)
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        show_result_button = QPushButton("Показать результат", self)  # запуск bwt
        show_result_button.setFont(QFont("Arial", 16, QFont.Bold))
        show_result_button.clicked.connect(self.show_result)
        layout.addWidget(show_result_button)

    def show_result(self):
        text_to_transform = self.input_field.text()
        if not text_to_transform:
            self.result_label.setText("Ошибка: Поле ввода не может быть пустым.")
            return
        result = bwt_transform(text_to_transform)  # лог пишется внутри функции
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

        self.input_field = QLineEdit(self)  # однострочное поле ввода
        self.input_field.setFont(font)
        self.input_field.setText(self.default_text)
        layout.addWidget(self.input_field)

        self.result_label = QLabel("Результат будет показан здесь.", self)
        self.result_label.setFont(font)
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        show_result_button = QPushButton("Показать результат", self)  # запуск mtf
        show_result_button.setFont(QFont("Arial", 16, QFont.Bold))
        show_result_button.clicked.connect(self.show_result)
        layout.addWidget(show_result_button)

    def show_result(self):
        text_to_encode = self.input_field.text()
        if not text_to_encode:
            self.result_label.setText("Ошибка: Поле ввода не может быть пустым.")
            return
        result = mtf_encode(text_to_encode)  # лог пишется внутри функции
        self.result_label.setText(f"Результат MTF: {result}")


# --- Главное окно приложения ---

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

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

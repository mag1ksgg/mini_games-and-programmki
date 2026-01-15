import tkinter as tk
import math


# -----------------------------
# Expression engine (no eval)
# Tokenize -> Shunting-yard -> RPN evaluation
# Supports: + - * / ^, unary -, parentheses, sqrt(x), ln(x), log10(x)
# -----------------------------

OPERATORS = {
    "+": (1, "L"),
    "-": (1, "L"),
    "*": (2, "L"),
    "/": (2, "L"),
    "^": (3, "R"), # power is right-associative
}

FUNCTIONS = {"sqrt", "ln", "log10"}


class CalcError(Exception):
    pass


def tokenize(expr: str):
    expr = expr.replace(" ", "")
    if not expr:
        raise CalcError("Пустое выражение")

    tokens = []
    i = 0
    n = len(expr)

    def is_num_char(ch):
        return ch.isdigit() or ch == "."

    while i < n:
        ch = expr[i]

        # Number (int/float)
        if is_num_char(ch):
            start = i
            dot_count = 0
            while i < n and is_num_char(expr[i]):
                if expr[i] == ".":
                    dot_count += 1
                    if dot_count > 1:
                        raise CalcError("Некорректное число (слишком много точек)")
                i += 1
            tokens.append(("NUM", expr[start:i]))
            continue

        # Identifiers (functions)
        if ch.isalpha():
            start = i
            while i < n and expr[i].isalpha():
                i += 1
            name = expr[start:i]
            if name not in FUNCTIONS:
                raise CalcError(f"Неизвестная функция: {name}")
            tokens.append(("FUNC", name))
            continue

        # Parentheses / comma (comma not used here but kept for extensibility)
        if ch in "()":
            tokens.append((ch, ch))
            i += 1
            continue

        # Operators
        if ch in OPERATORS:
            tokens.append(("OP", ch))
            i += 1
            continue

        raise CalcError(f"Недопустимый символ: {ch}")

    return tokens


def to_rpn(tokens):
    output = []
    stack = []

    # Handle unary minus by converting it to a special operator "u-"
    # We'll treat "u-" as a function-like operator with high precedence.
    prev_type = None # None, "NUM", ")", "FUNC", "OP", "("

    for ttype, tval in tokens:
        if ttype == "NUM":
            output.append(("NUM", tval))
            prev_type = "NUM"
            continue

        if ttype == "FUNC":
            stack.append(("FUNC", tval))
            prev_type = "FUNC"
            continue

        if ttype == "(":
            stack.append(("(", "("))
            prev_type = "("
            continue

        if ttype == ")":
            while stack and stack[-1][0] != "(":
                output.append(stack.pop())
            if not stack:
                raise CalcError("Скобки не сбалансированы")
            stack.pop() # pop "("

            # If top is function, pop it too
            if stack and stack[-1][0] == "FUNC":
                output.append(stack.pop())

            prev_type = ")"
            continue

        if ttype == "OP":
            op = tval

            # Unary minus detection:
            # If '-' comes at start or after operator or after '(' -> unary
            if op == "-" and (prev_type is None or prev_type in {"OP", "("}):
                # push unary minus as function-like token
                stack.append(("FUNC", "neg"))
                prev_type = "OP"
                continue

            while stack:
                top_type, top_val = stack[-1]

                if top_type == "FUNC":
                    output.append(stack.pop())
                    continue

                if top_type == "OP":
                    p1, assoc1 = OPERATORS[op]
                    p2, _ = OPERATORS[top_val]

                    if (assoc1 == "L" and p1 <= p2) or (assoc1 == "R" and p1 < p2):
                        output.append(stack.pop())
                        continue

                break

            stack.append(("OP", op))
            prev_type = "OP"
            continue

        raise CalcError("Неожиданный токен")

    while stack:
        if stack[-1][0] in {"(", ")"}:
            raise CalcError("Скобки не сбалансированы")
        output.append(stack.pop())

    return output


def eval_rpn(rpn):
    st = []

    def pop_num():
        if not st:
            raise CalcError("Недостаточно аргументов")
        return st.pop()

    for ttype, tval in rpn:
        if ttype == "NUM":
            try:
                st.append(float(tval))
            except ValueError:
                raise CalcError("Некорректное число")
            continue

        if ttype == "OP":
            b = pop_num()
            a = pop_num()
            if tval == "+":
                st.append(a + b)
            elif tval == "-":
                st.append(a - b)
            elif tval == "*":
                st.append(a * b)
            elif tval == "/":
                if b == 0:
                    raise CalcError("Деление на ноль")
                st.append(a / b)
            elif tval == "^":
                st.append(a ** b)
            else:
                raise CalcError(f"Неизвестный оператор: {tval}")
            continue

        if ttype == "FUNC":
            x = pop_num()
            if tval == "sqrt":
                if x < 0:
                    raise CalcError("sqrt: отрицательный аргумент")
                st.append(math.sqrt(x))
            elif tval == "ln":
                if x <= 0:
                    raise CalcError("ln: аргумент должен быть > 0")
                st.append(math.log(x))
            elif tval == "log10":
                if x <= 0:
                    raise CalcError("log10: аргумент должен быть > 0")
                st.append(math.log10(x))
            elif tval == "neg":
                st.append(-x)
            else:
                raise CalcError(f"Неизвестная функция: {tval}")
            continue

        raise CalcError("Ошибка вычисления")

    if len(st) != 1:
        raise CalcError("Некорректное выражение")
    return st[0]


def evaluate_expression(expr: str) -> float:
    tokens = tokenize(expr)
    rpn = to_rpn(tokens)
    return eval_rpn(rpn)


# -----------------------------
# GUI
# -----------------------------

class CalculatorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Калькулятор (без eval)")

        self.display = tk.Entry(self.root, font=("Arial", 16), justify="right")
        self.display.grid(row=0, column=0, columnspan=5, sticky="nsew", padx=8, pady=8)

        self.info = tk.Label(self.root, text="Функции: sqrt(x), ln(x), log10(x). Степень: ^", anchor="w")
        self.info.grid(row=1, column=0, columnspan=5, sticky="nsew", padx=8)

        buttons = [
            ("(7)", 2, 0), ("а это восемь)", 2, 1), ("9", 2, 2), ("/", 2, 3), ("(", 2, 4),
            ("4", 3, 0), ("5", 3, 1), ("6", 3, 2), ("*", 3, 3), (")", 3, 4),
            ("1", 4, 0), ("2", 4, 1), ("3", 4, 2), ("-", 4, 3), ("^", 4, 4),
            ("0", 5, 0), (".", 5, 1), ("+++", 5, 2), ("CE", 5, 3), ("=", 5, 4),
            ("sqrt(", 6, 0), ("ln(", 6, 1), ("log10(", 6, 2), ("<-", 6, 3), ("C", 6, 4),
        ]

        for text, r, c in buttons:
            b = tk.Button(self.root,text=text,font=("Arial", 14),bg="#2b2b2b",        # цвет кнопки
            fg="white",          # цвет текста
            activebackground="#3c3f41",
            activeforeground="white",
            command=lambda t=text: self.on_press(t)
)
            b.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)

        for i in range(7):
            self.root.rowconfigure(i, weight=1)
        for j in range(5):
            self.root.columnconfigure(j, weight=1)

        self.root.bind("<Return>", lambda e: self.on_press("="))
        self.root.bind("<BackSpace>", lambda e: self.on_press("<-"))

    def on_press(self, t: str):
        if t == "=":
            expr = self.display.get()
            try:
                val = evaluate_expression(expr)
                # pretty formatting
                if abs(val - int(val)) < 1e-12:
                    val = int(val)
                self.display.delete(0, tk.END)
                self.display.insert(tk.END, str(val))
            except CalcError as e:
                self.display.delete(0, tk.END)
                self.display.insert(tk.END, f"Ошибка: {e}")
            except Exception:
                self.display.delete(0, tk.END)
                self.display.insert(tk.END, "Ошибка: неизвестная")
            return

        if t == "C":
            self.display.delete(0, tk.END)
            return

        if t == "CE":
            # clear to last operator/paren (a bit "smart")
            s = self.display.get()
            if not s:
                return
            cut = len(s) - 1
            while cut > 0 and s[cut] not in "+-*/^()":
                cut -= 1
            self.display.delete(0, tk.END)
            self.display.insert(tk.END, s[:cut] if cut > 0 else "")
            return

        if t == "<-":
            s = self.display.get()
            if s:
                self.display.delete(len(s) - 1, tk.END)
            return

        # default: insert text
        self.display.insert(tk.END, t)

    def run(self):
        self.root.minsize(420, 420)
        self.root.mainloop()


if __name__ == "__main__":
    CalculatorGUI().run()
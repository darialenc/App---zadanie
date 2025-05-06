from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

class Manager:
    def __init__(self):
        self.saldo = 0.0
        self.historia = []
        self.magazyn = {}
        self.saldo_file = ""
        self.magazyn_file = ""
        self.historia_file = ""

    def file_exists(self, filepath):
        return os.path.isfile(filepath)

    def load_data(self):
        self.saldo = self.load_saldo_from_file(self.saldo_file)
        self.magazyn = self.load_magazyn_from_file(self.magazyn_file)
        self.historia = self.load_historia_from_file(self.historia_file)

    def assign(self, saldo_file, magazyn_file, historia_file):
        self.saldo_file = saldo_file
        self.magazyn_file = magazyn_file
        self.historia_file = historia_file
        self.load_data()

    def save_saldo_to_file(self):
        with open(self.saldo_file, "w", encoding="utf-8") as fd:
            fd.write(str(self.saldo))

    def save_magazyn_to_file(self):
        with open(self.magazyn_file, "w", encoding="utf-8") as fd:
            for nazwa, produkt in self.magazyn.items():
                fd.write(f"{nazwa},{produkt['ilosc']},{produkt['cena']}\n")

    def save_historia_to_file(self):
        with open(self.historia_file, "w", encoding="utf-8") as fd:
            for operacja in self.historia:
                fd.write(operacja + "\n")

    def load_saldo_from_file(self, filepath):
        if not self.file_exists(filepath):
            return 0.0
        with open(filepath, "r") as fd:
            content = fd.read().strip()
        return float(content) if content else 0.0

    def load_magazyn_from_file(self, filepath):
        magazyn = {}
        if not self.file_exists(filepath):
            return magazyn
        with open(filepath, "r") as fd:
            for line in fd:
                parts = line.strip().split(",")
                if len(parts) != 3:
                    continue
                nazwa, ilosc, cena = parts
                magazyn[nazwa] = {"ilosc": int(ilosc), "cena": float(cena)}
        return magazyn

    def load_historia_from_file(self, filepath):
        if not self.file_exists(filepath):
            return []
        with open(filepath, "r") as fd:
            return [line.strip() for line in fd.readlines()]

manager = Manager()
manager.assign("Saldo.txt", "Magazyn.txt", "Historia.txt")

@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "saldo":
            wartosc = float(request.form.get("wartosc", 0))
            manager.saldo += wartosc
            manager.historia.append(f"Saldo zmienione: Wartość: {wartosc}")
            manager.save_saldo_to_file()

        elif action == "zakup":
            nazwa = request.form.get("nazwa")
            cena = float(request.form.get("cena"))
            ilosc = int(request.form.get("ilosc"))
            koszt = cena * ilosc
            if koszt <= manager.saldo:
                manager.saldo -= koszt
                if nazwa in manager.magazyn:
                    manager.magazyn[nazwa]["ilosc"] += ilosc
                else:
                    manager.magazyn[nazwa] = {"ilosc": ilosc, "cena": cena}
                manager.historia.append(f"Zakup: {nazwa}, {ilosc} szt., cena {cena}")
            else:
                manager.historia.append(f"Nieudany zakup: {nazwa}, za drogi")
            manager.save_saldo_to_file()

        elif action == "sprzedaz":
            nazwa = request.form.get("nazwa")
            cena = float(request.form.get("cena"))
            ilosc = int(request.form.get("ilosc"))
            if nazwa in manager.magazyn and manager.magazyn[nazwa]["ilosc"] >= ilosc:
                manager.magazyn[nazwa]["ilosc"] -= ilosc
                manager.saldo += cena * ilosc
                if manager.magazyn[nazwa]["ilosc"] == 0:
                    del manager.magazyn[nazwa]
                manager.historia.append(f"Sprzedaż: {nazwa}, {ilosc} szt., cena {cena}")
            else:
                manager.historia.append(f"Nieudana sprzedaż: {nazwa}")
            manager.save_saldo_to_file()

        manager.save_magazyn_to_file()
        manager.save_historia_to_file()
        return redirect(url_for("main"))

    return render_template("main.html", saldo=manager.saldo, magazyn=manager.magazyn)

@app.route("/historia/")
@app.route("/historia/<int:line_from>/<int:line_to>/")
def historia(line_from=0, line_to=None):
    historia = manager.historia
    if line_to is None:
        line_to = len(historia)
    historia_fragment = historia[line_from:line_to]
    return render_template("historia.html", historia=historia_fragment, od=line_from, do=line_to)

if __name__ == "__main__":
    app.run(debug=True)

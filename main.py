#!/usr/bin/env python3
"""
Interface graphique pour le bloc d’alimentation Hanmatek HM310T.
Affiche les valeurs configurées et mesurées en temps réel (0.5s).
"""

import os
import sys
from dotenv import load_dotenv
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget, QApplication, QGridLayout, QFrame
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

load_dotenv()
PORT = os.getenv("PORT") or os.getenv("PORT_USB")

class PowerSupplyUI(QWidget):
    def __init__(self, port):
        super().__init__()
        self.setWindowTitle("HM310T - Bloc d'alimentation")
        self.setFixedSize(400, 250)
        self.setStyleSheet("background-color: #1e1e1e;")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("ALIMENTATION HM310T")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)

        ligne = QFrame()
        ligne.setFrameShape(QFrame.Shape.HLine)
        ligne.setStyleSheet("color: white;")
        layout.addWidget(ligne)

        grid = QGridLayout()
        grid.setContentsMargins(10, 4, 10, 4)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(4)

        self.champs = {
            "ÉTAT": "ÉTAT",
            "Vset": "Voltage Configuré",
            "Iset": "Courant Configuré",
            "Vout": "Voltage Actuel",
            "Iout": "Courant Actuel",
            "Watt": "Watt"
        }
        self.labels = {}

        i = 0
        for cle, etiquette in self.champs.items():
            if cle == "Vout":
                ligne_sep = QFrame()
                ligne_sep.setFrameShape(QFrame.Shape.HLine)
                ligne_sep.setStyleSheet("color: white; margin: 2px 0px; padding: 0px;")
                grid.addWidget(ligne_sep, i, 0, 1, 2)
                i += 1

            lbl_nom = QLabel(etiquette + " :")
            lbl_nom.setStyleSheet("font-size: 20px; color: white;")
            lbl_val = QLabel("-")
            lbl_val.setStyleSheet("font-size: 20px; font-weight: bold; color: #90ee90;")
            grid.addWidget(lbl_nom, i, 0)
            grid.addWidget(lbl_val, i, 1)
            self.labels[cle] = lbl_val
            i += 1

        layout.addLayout(grid)
        self.setLayout(layout)

        self.port = port
        self.client = ModbusClient(
            method='rtu',
            port=self.port,
            baudrate=9600,
            stopbits=1,
            bytesize=8,
            parity='N',
            timeout=1
        )

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_values)
        self.timer.start(500)

    def update_values(self):
        if not self.client.connect():
            for champ in self.champs:
                self.labels[champ].setText("Erreur")
            return

        try:
            def lire_registre(logique):
                return self.client.read_holding_registers(logique - 1, 1, unit=1).registers[0]

            etat = lire_registre(2)
            if etat == 1:
                self.labels["ÉTAT"].setText("🟢")
            else:
                self.labels["ÉTAT"].setText("🔴")

            vset = lire_registre(49) / 100
            self.labels["Vset"].setText(f"{vset:.2f} V")

            iset = lire_registre(50) / 1000
            self.labels["Iset"].setText(f"{iset:.3f} A")

            vout = lire_registre(17) / 100
            self.labels["Vout"].setText(f"{vout:.2f} V")

            raw_iout = lire_registre(18)
            if raw_iout < 1000:
                iout = raw_iout / 100
            else:
                iout = raw_iout / 1000
            self.labels["Iout"].setText(f"{iout:.3f} A")

            watt = lire_registre(20) / 100
            self.labels["Watt"].setText(f"{watt:.2f} W")

        except Exception as e:
            for champ in self.champs:
                self.labels[champ].setText("Erreur")

        finally:
            self.client.close()

    def closeEvent(self, event):
        self.timer.stop()
        self.client.close()
        event.accept()

if __name__ == "__main__":
    if not PORT:
        print("❌ Aucun port spécifié. Utilise --port ou une variable PORT dans un fichier .env")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = PowerSupplyUI(port=PORT)
    window.show()
    sys.exit(app.exec())

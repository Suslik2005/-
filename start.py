import sys
import threading
import time
import os

import PySide6
from PySide6 import QtWidgets, QtGui
from PySide6.QtWidgets import QApplication, QMainWindow
from pymodbus.client.sync import ModbusTcpClient

from main_window import Ui_MainWindow
from main import ModbusServer
DB_NAME = "ip.db"

class Modbus(QMainWindow):
    def __init__(self):
        super(Modbus, self).__init__()
        # создание txt файла с последними ip
        self.FILE_NAME = "ips.txt"
        if not os.path.exists(self.FILE_NAME):
            with open(self.FILE_NAME, "w") as file:
                self.ips = []
                pass  # Просто создаём пустой файл
        else:
            f = open('ips.txt', 'r')
            self.ips = f.read().split('\n')
            print(self.ips)
            f.close()

        # до сюда
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.client = None
        self.control_result = 0
        self.ui.pushButton_2.setEnabled(False)
        self.thread = False
        server = ModbusServer()
        server.run()
        # словарь для отправки значений
        self.main_dict = {"калибролвка отключена": 0, 'начать калибровку': 1, "сохранить калибровку": 2,
                          "вернуть заводскую калибровку": 3, "задать термокомпенсацию(-)": 4,
                          "задать термокомпенсацию(+)": 5}
        self.stadiya_colibrovki = {0: "калибровка отключена", 1: "подайте 4мА (1 В)", 2: "подайте 20мА (5 В)",
                                   3: "сохранить калибровку?", 4: "подайте 8мА (2 В)", 5: "подайте 12мА (3 В)",
                                   6: "подайте 16мА (4 В)", 7: "ожидание стабилизации сигнала", 8: "калиброка"}
        self.refresh_ips()
        # кнопка подключения
        self.ui.pushButton.clicked.connect(self.connection)
        # кнопка для передачи значения в "действия при калибровке"
        self.ui.pushButton_2.clicked.connect(self.ask)
        self.ui.pushButton_3.clicked.connect(self.nonconnection)


    # при отправке значения запускается поток
    def nonconnection(self):
        self.ui.pushButton.setEnabled(True)
        self.ui.label.clear()
        self.client.close()
        if self.thread:
            self.monitoring_thread.join()


    def write_ip_to_file(self, ip):
        with open(self.FILE_NAME, "a") as file:
            file.write(f"{ip}\n")
        print(f"IP '{ip}' записан в файл.")


    def potok(self):
        self.monitoring_thread = threading.Thread(target=self.surveillance)
        self.monitoring_thread.daemon = True  # Закрыть поток при завершении программы
        self.monitoring_thread.start()


    def surveillance(self):
        self.thread = True
        while True:
            result = self.client.read_holding_registers(0, 10)

            print(result.registers)
            if self.control_result != self.stadiya_colibrovki[int(result.registers[0])]:
                self.control_result = self.stadiya_colibrovki[int(result.registers[0])]
                self.ui.label.clear()  # Очищаем текст в QLabel
                self.ui.label.setText(self.control_result)
                time.sleep(1)


    # Функция для чтения IP из файла в обратном порядке
    def read_ips_from_file(self):
        with open(self.FILE_NAME, "r") as file:
            lines = file.readlines()
        return [line.strip() for line in reversed(lines)]  # Удаляем лишние символы


    # функция для отправки значения в 10030 индекс
    def ask(self):
        vaalue = self.ui.comboBox_2.currentText()
        print(vaalue)
        print(self.main_dict[vaalue])
        # отправка выбранной команды
        self.client.write_register(1, self.main_dict[vaalue])
        self.potok()


    def refresh_ips(self):
        self.ui.comboBox.clear()
        ips = self.read_ips_from_file()
        self.ui.comboBox.addItems(ips)
        print("IP-адреса обновлены в comboBox.")


    # подключение к ModbusTcp
    def connection(self):
        text = self.ui.comboBox.currentText()
        self.client = ModbusTcpClient(text)
        # значение при подключении (True/False)
        a = self.client.connect()
        # есть подключение - кнопка зеленая, нет подключения - кнопка красная
        if a:
            print("все ок")
            self.ui.pushButton.setEnabled(False)
            self.ui.pushButton.setDisabled(True)
            self.ui.pushButton_2.setEnabled(True)
            if text not in self.ips:
                self.write_ip_to_file(text)
                self.refresh_ips()

        else:
            self.ui.pushButton.setStyleSheet(
                'QPushButton {background-color: rgba(255,0,0,30); color: white;}')
            print("ошибка подключения")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Modbus()
    window.show()
    sys.exit(app.exec())
# отработать адгоритм перехода по точкам через slave
# кнопка шаманит

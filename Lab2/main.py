import tkinter as tk
import serial
import threading
import time
import sys
import tkinter.messagebox

pack_flag = "01110011"    #symbol 's'
dest_addr = "0000"
src_addr = "0000"
fcs = "0"


class Ports:
    def __init__(self):
        self.status = None
        try:
            self.sender = serial.Serial(port='COM1')
            self.sender_info = 'Sender - COM1'
            self.receiver = serial.Serial(port='COM2')
            self.receiver_info = 'Receiver - COM2'
        except serial.SerialException:
            try:
                self.sender = serial.Serial(port='COM3')
                self.sender_info = 'Sender - COM3'
                self.receiver = serial.Serial(port='COM4')
                self.receiver_info = 'Receiver - COM4'
            except serial.SerialException:
                tkinter.messagebox.showerror("Error.",
                                             "There is a problem with ports.")
                self.status = 'Error'

    def write_str_in_port(self, text) -> None:
        for i in range(0, len(text)):
            self.sender.write(data=text[i].encode())

    def read_from_port(self) -> str:
        byte = self.receiver.read(size=1)
        return byte.decode()


ports = Ports()
if ports.status == 'Error':
    sys.exit()

gui = tk.Tk()
gui.title('COM-ports transmitter')
gui.geometry('620x400')
gui.resizable(width=False, height=False)
gui.configure(background="#C0C0C0")


class Window:
    def __init__(self, text, r, c, dflt_txt=''):
        self.sent_bytes = 0
        self.received_bytes = 0

        self.pack = ""
        self.packs = ""

        self.dflt_txt = dflt_txt
        self.text = self.dflt_txt
        self.str = self.dflt_txt
        self.enter_flag = False
        self.label = tk.Label(gui, text=text, font=("Times New Roman", 12), background="#C0C0C0")
        self.label.grid(row=r, column=c, sticky='w')
        self.frame = tk.Frame(gui, width=300, height=150, highlightbackground="#808080")
        self.frame.grid(row=r + 1, column=c)
        self.listbox = tkinter.Listbox(self.frame, bg='#E0E0E0', font=("Courier New", 8), fg='black',
                                       highlightcolor='#A0A0A0', highlightthickness=3,
                                       selectbackground='#404040', activestyle=tkinter.NONE, width=40)
        self.scrollbar = tk.Scrollbar(self.frame, width=20)
        self.scrollbar.grid(row=r + 1, column=c + 1, sticky='ns')
        self.scrollbar.grid_propagate(False)
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        self.listbox.grid(row=r + 1, column=c)

    def length_former(self, length_int):
        length_str = ""
        while(length_int > 0):
            length_str = str(length_int % 2) + length_str
            length_int = length_int // 2
        while(len(length_str) < 4):
            length_str = "0" + length_str
        return length_str

    def pack_creator(self, length_str, pack):
        pack = pack_flag + dest_addr + src_addr + length_str + pack + fcs
        self.packs = self.packs + pack

    def add_symbol(self, symbol):
        self.listbox.delete(tk.END)
        self.text = self.text + symbol
        self.str = self.str + symbol
        self.listbox.insert(tk.END, self.text)
        self.listbox.yview_moveto(1)

    def enter_pushed(self):
        self.text = ""
        self.listbox.insert(tk.END, self.text)
        self.listbox.yview_moveto(1)

    def input_symbol(self, symbol): # тут происходит отправление данных в порт
        global flag
        flag = 0
        if symbol:
            self.add_symbol(symbol)
            if symbol != '\n':
                self.pack = self.pack + symbol
                self.sent_bytes += 1
        if self.sent_bytes % 15 == 0 and self.sent_bytes != 0:  # это отвечает за то, когда будет перенос на следующую строку в окне ввода
            self.enter_pushed()

            length_str = self.length_former(self.sent_bytes)
            self.pack_creator(length_str, self.pack)
            self.pack = ""

            self.sent_bytes = 0
            self.str = ""

        if symbol == '\n':
            length_str = self.length_former(self.sent_bytes)
            self.pack_creator(length_str, self.pack)
            self.pack = ""

            self.sent_bytes = 0
            self.packs = self.packs + '\n'
            ports.write_str_in_port(self.packs)
            self.packs = ""
            self.str = ""
            self.enter_pushed()

    def output_symbol(self, symbol):
        if symbol == '\n':
            self.enter_pushed()
        self.add_symbol(symbol)

    def status_text(self, text):
        self.add_symbol(text)
        self.enter_pushed()


input_window = Window(text='Input:', r=0, c=0)
output_window = Window(text='Output:', r=0, c=3)
status_window = Window(text='Status:', r=2, c=0)
status_window.status_text(ports.sender_info)
status_window.status_text(ports.receiver_info)

parity_change_label = tk.Label(gui, text='Parity:', font=("Times New Roman", 12), background="#C0C0C0")
parity_change_label.grid(row=2, column=3, sticky='w')

List = ['PARITY_NONE', 'PARITY_EVEN', 'PARITY_ODD', 'PARITY_MARK', 'PARITY_SPACE']
option = tk.StringVar(gui)
option.set('PARITY_NONE')
parity_menu = tk.OptionMenu(gui, option, *List)
parity_menu.grid(row=3, column=3)


def output_cycle_read():    # это всё отвечает чисто за окно вывода
    output_str = ""
    pause = False
    index = 0
    pack = ""
    while True:
        while not pause:
            read_byte = ports.read_from_port()
            output_str = output_str + read_byte
            if read_byte == '\n':
                pause = True
        print("Output_str = ", output_str)
        while len(output_str) > len(pack):
            index = output_str.find(pack_flag, 1)
            print("Index = ", index)
            if index != 0 and index != -1:
                pack = output_str[0:index]
                output_str = output_str[index:]
                for i in range(0, len(pack)):
                    output_window.output_symbol(pack[i])
                output_window.enter_pushed()
            else:
                pack = output_str
        pack = output_str
        for i in range(0, len(pack)):
            output_window.output_symbol(pack[i])
        output_str = ""
        pause = False


output_cycle_read_thread = threading.Thread(target=output_cycle_read)
output_cycle_read_thread.daemon = True
output_cycle_read_thread.start()


def cycle_check_bytes_count():
    while True:
        time.sleep(0.5)
        status_window.listbox.delete(tkinter.END)
        status_window.listbox.insert(tkinter.END, f'Bytes received = {output_window.received_bytes}')


check_count_thread = threading.Thread(target=cycle_check_bytes_count)
check_count_thread.daemon = True
check_count_thread.start()

input_window.listbox.bind('<Return>', lambda x: input_window.input_symbol('\n'))

input_window.listbox.bind('1', lambda x: input_window.input_symbol('1'))
input_window.listbox.bind('0', lambda x: input_window.input_symbol('0'))

gui.mainloop()
ports.sender.close()
ports.receiver.close()

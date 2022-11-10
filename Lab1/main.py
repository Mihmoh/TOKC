import tkinter as tk
import serial
import threading
import time
import sys
import tkinter.messagebox


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
                                             "Problem with ports.")
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

    def input_symbol(self, symbol):
        global flag
        flag = 0
        if symbol:
            self.sent_bytes += 1
            self.add_symbol(symbol)
        if self.sent_bytes % 40 == 0 and self.sent_bytes != 0:
            self.enter_pushed()
        if symbol == '\n':
            self.sent_bytes = 0
            ports.write_str_in_port(self.str)
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


def output_cycle_read():
    while True:
        read_byte = ports.read_from_port()
        if read_byte:
            if output_window.enter_flag == True:
                output_window.received_bytes = 0
                output_window.enter_flag = False
        output_window.received_bytes += 1
        output_window.output_symbol(read_byte)
        if output_window.received_bytes % 40 == 0 and output_window.received_bytes != 0:
            output_window.enter_pushed()
        if read_byte == '\n':
            output_window.enter_flag = True


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
input_window.listbox.bind('<slash>', lambda x: input_window.input_symbol('/'))
input_window.listbox.bind('<backslash>', lambda x: input_window.input_symbol('\\'))
input_window.listbox.bind('<space>', lambda x: input_window.input_symbol(' '))

input_window.listbox.bind('a', lambda x: input_window.input_symbol('a'))
input_window.listbox.bind('b', lambda x: input_window.input_symbol('b'))
input_window.listbox.bind('c', lambda x: input_window.input_symbol('c'))
input_window.listbox.bind('d', lambda x: input_window.input_symbol('d'))
input_window.listbox.bind('e', lambda x: input_window.input_symbol('e'))
input_window.listbox.bind('f', lambda x: input_window.input_symbol('f'))
input_window.listbox.bind('g', lambda x: input_window.input_symbol('g'))
input_window.listbox.bind('h', lambda x: input_window.input_symbol('h'))
input_window.listbox.bind('i', lambda x: input_window.input_symbol('i'))
input_window.listbox.bind('j', lambda x: input_window.input_symbol('j'))
input_window.listbox.bind('k', lambda x: input_window.input_symbol('k'))
input_window.listbox.bind('l', lambda x: input_window.input_symbol('l'))
input_window.listbox.bind('m', lambda x: input_window.input_symbol('m'))
input_window.listbox.bind('n', lambda x: input_window.input_symbol('n'))
input_window.listbox.bind('o', lambda x: input_window.input_symbol('o'))
input_window.listbox.bind('p', lambda x: input_window.input_symbol('p'))
input_window.listbox.bind('q', lambda x: input_window.input_symbol('q'))
input_window.listbox.bind('r', lambda x: input_window.input_symbol('r'))
input_window.listbox.bind('s', lambda x: input_window.input_symbol('s'))
input_window.listbox.bind('t', lambda x: input_window.input_symbol('t'))
input_window.listbox.bind('u', lambda x: input_window.input_symbol('u'))
input_window.listbox.bind('v', lambda x: input_window.input_symbol('v'))
input_window.listbox.bind('w', lambda x: input_window.input_symbol('w'))
input_window.listbox.bind('x', lambda x: input_window.input_symbol('x'))
input_window.listbox.bind('y', lambda x: input_window.input_symbol('y'))
input_window.listbox.bind('z', lambda x: input_window.input_symbol('z'))
input_window.listbox.bind('A', lambda x: input_window.input_symbol('A'))
input_window.listbox.bind('B', lambda x: input_window.input_symbol('B'))
input_window.listbox.bind('C', lambda x: input_window.input_symbol('C'))
input_window.listbox.bind('D', lambda x: input_window.input_symbol('D'))
input_window.listbox.bind('E', lambda x: input_window.input_symbol('E'))
input_window.listbox.bind('F', lambda x: input_window.input_symbol('F'))
input_window.listbox.bind('G', lambda x: input_window.input_symbol('G'))
input_window.listbox.bind('H', lambda x: input_window.input_symbol('H'))
input_window.listbox.bind('I', lambda x: input_window.input_symbol('I'))
input_window.listbox.bind('J', lambda x: input_window.input_symbol('J'))
input_window.listbox.bind('K', lambda x: input_window.input_symbol('K'))
input_window.listbox.bind('L', lambda x: input_window.input_symbol('L'))
input_window.listbox.bind('M', lambda x: input_window.input_symbol('M'))
input_window.listbox.bind('N', lambda x: input_window.input_symbol('N'))
input_window.listbox.bind('O', lambda x: input_window.input_symbol('O'))
input_window.listbox.bind('P', lambda x: input_window.input_symbol('P'))
input_window.listbox.bind('Q', lambda x: input_window.input_symbol('Q'))
input_window.listbox.bind('R', lambda x: input_window.input_symbol('R'))
input_window.listbox.bind('S', lambda x: input_window.input_symbol('S'))
input_window.listbox.bind('T', lambda x: input_window.input_symbol('T'))
input_window.listbox.bind('U', lambda x: input_window.input_symbol('U'))
input_window.listbox.bind('V', lambda x: input_window.input_symbol('V'))
input_window.listbox.bind('W', lambda x: input_window.input_symbol('W'))
input_window.listbox.bind('X', lambda x: input_window.input_symbol('X'))
input_window.listbox.bind('Y', lambda x: input_window.input_symbol('Y'))
input_window.listbox.bind('Z', lambda x: input_window.input_symbol('Z'))
input_window.listbox.bind('1', lambda x: input_window.input_symbol('1'))
input_window.listbox.bind('2', lambda x: input_window.input_symbol('2'))
input_window.listbox.bind('3', lambda x: input_window.input_symbol('3'))
input_window.listbox.bind('4', lambda x: input_window.input_symbol('4'))
input_window.listbox.bind('5', lambda x: input_window.input_symbol('5'))
input_window.listbox.bind('6', lambda x: input_window.input_symbol('6'))
input_window.listbox.bind('7', lambda x: input_window.input_symbol('7'))
input_window.listbox.bind('8', lambda x: input_window.input_symbol('8'))
input_window.listbox.bind('9', lambda x: input_window.input_symbol('9'))
input_window.listbox.bind('0', lambda x: input_window.input_symbol('0'))
input_window.listbox.bind('.', lambda x: input_window.input_symbol('.'))
input_window.listbox.bind(',', lambda x: input_window.input_symbol(','))
input_window.listbox.bind(';', lambda x: input_window.input_symbol(';'))
input_window.listbox.bind(':', lambda x: input_window.input_symbol(':'))
input_window.listbox.bind('!', lambda x: input_window.input_symbol('!'))
input_window.listbox.bind('-', lambda x: input_window.input_symbol('-'))
input_window.listbox.bind('+', lambda x: input_window.input_symbol('+'))
input_window.listbox.bind('_', lambda x: input_window.input_symbol('_'))
input_window.listbox.bind('?', lambda x: input_window.input_symbol('?'))
input_window.listbox.bind('=', lambda x: input_window.input_symbol('='))
input_window.listbox.bind('@', lambda x: input_window.input_symbol('@'))
input_window.listbox.bind('$', lambda x: input_window.input_symbol('$'))
input_window.listbox.bind('%', lambda x: input_window.input_symbol('%'))
input_window.listbox.bind('^', lambda x: input_window.input_symbol('^'))
input_window.listbox.bind('&', lambda x: input_window.input_symbol('&'))
input_window.listbox.bind('*', lambda x: input_window.input_symbol('*'))
input_window.listbox.bind('/', lambda x: input_window.input_symbol('/'))
input_window.listbox.bind('(', lambda x: input_window.input_symbol('('))
input_window.listbox.bind(')', lambda x: input_window.input_symbol(')'))
input_window.listbox.bind('#', lambda x: input_window.input_symbol('#'))
input_window.listbox.bind('|', lambda x: input_window.input_symbol('|'))
input_window.listbox.bind('[', lambda x: input_window.input_symbol('['))
input_window.listbox.bind(']', lambda x: input_window.input_symbol(']'))
input_window.listbox.bind('{', lambda x: input_window.input_symbol('{'))
input_window.listbox.bind('}', lambda x: input_window.input_symbol('}'))
input_window.listbox.bind('~', lambda x: input_window.input_symbol('~'))

gui.mainloop()
ports.sender.close()
ports.receiver.close()

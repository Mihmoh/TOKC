import tkinter as tk
import serial
import threading
import random
import sys
import time
import tkinter.messagebox

pack_flag = "01110011"    #symbol 's'
dest_addr = "0000"
src_addr = "0000"


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


class Status_Window:
    def __init__(self, text, r, c, dflt_txt=''):
        self.dflt_txt = dflt_txt
        self.text = self.dflt_txt
        self.str = self.dflt_txt
        self.enter_flag = False
        self.label = tk.Label(gui, text=text, font=("Times New Roman", 12), background="#C0C0C0")
        self.label.grid(row=r, column=c, sticky='w')
        self.frame = tk.Frame(gui, width=300, height=150, highlightbackground="#808080")
        self.frame.grid(row=r + 1, column=c)
        self.textbox = tkinter.Text(self.frame, bg='#E0E0E0', font=("Courier New", 7), fg='black',
                                       highlightcolor='#A0A0A0', highlightthickness=3, height=12,
                                       selectbackground='#404040', width=55, state="disabled")
        self.scrollbar = tk.Scrollbar(self.frame, width=20)
        self.scrollbar.grid(row=r + 1, column=c + 1, sticky='ns')
        self.scrollbar.grid_propagate(False)
        self.textbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.textbox.yview)
        self.textbox.grid(row=r + 1, column=c)
        self.textbox.tag_configure("RED", foreground="red")
        self.textbox.tag_configure("BLUE", foreground="blue")

    def add_symbol(self, symbol):
        self.textbox.delete(tk.END)
        self.text = self.text + symbol
        self.str = self.str + symbol
        self.textbox.insert(tk.END, self.text)
        self.textbox.yview_moveto(1)

    def enter_pushed(self):
        self.text = ""
        self.textbox.insert(tk.END, self.text)
        self.textbox.yview_moveto(1)

    def output_symbol(self, symbol):
        if symbol == '\n':
            self.enter_pushed()
        self.add_symbol(symbol)

    def status_text(self, text):
        self.add_symbol(text)
        self.enter_pushed()


status_window = Status_Window(text='Status:', r=2, c=0)


class Window:
    def __init__(self, text, r, c, dflt_txt=''):
        self.sent_bytes = 0
        self.received_bytes = 0
        self.pack_length = 0
        self.fcs = ""
        self.fcs_length = 0
        self.parity_bit = "0"
        self.isSendPortBusy = False

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

    def collision(self, data):
        self.isSendPortBusy = True
        status_window.textbox.config(state="normal")
        status_window.textbox.delete("1.0", tkinter.END)
        status_window.status_text(ports.sender_info)
        status_window.textbox.insert(tk.END, "\n")
        status_window.status_text(ports.receiver_info)
        status_window.textbox.insert(tk.END, "\n")
        status_window.textbox.config(state="disabled")
        for bit in data:
            attempt_count = 0
            while attempt_count < 10:
                while True:
                    chance = random.randint(1, 100)
                    print("Chance: ", chance)
                    if 1 <= chance <= 50:
                        pass
                    else:
                        break
                ports.write_str_in_port(bit)
                time.sleep(0.5)
                chance = random.randint(1, 100)
                #print("Chance: ", chance)
                if 1 <= chance <= 25:
                    attempt_count += 1
                    isCollisionAppeared(True)
                    time.sleep(500 * 2 ** min(attempt_count, 10) / 1000)
                    continue
                isCollisionAppeared(False)
                break
            else:
                collisionError()
        ports.write_str_in_port("\n")
        self.isSendPortBusy = False

    def parity_bitter(self, pack):
        sum = 0
        i = 0
        while i < len(pack):
            if pack[i] == "1":
                sum += 1
            i += 1
        if sum % 2 == 0:
            self.parity_bit = "0"
        else:
            self.parity_bit = "1"

    def fcs_former(self, length_int, pack):     #формирователь fcs
        r0 = 0
        r1 = 0
        r2 = 0
        r3 = 0
        r4 = 0
        print("Pack before: ", pack)
        #_________________________________________________________________________________________
        if length_int == 1:
            self.fcs_length = 2
            pack = str(r0) + str(r1) + pack
            print("Pack coding: ", pack)
            if int(pack[2]) % 2 == 0:
                r0 = 0
                r1 = 0
            else:
                r0 = 1
                r1 = 1
            self.fcs = str(r0) + str(r1)
            pack = str(r0) + str(r1) + pack[2:]
            return pack
        #_________________________________________________________________________________________
        if 2 <= length_int <= 4:
            self.fcs_length = 3
            pack = str(r0) + str(r1) + pack[:1] + str(r2) + pack[1:]
            print("Pack coding: ", pack)

            i = 0
            j = 0
            s = 0
            while(i < len(pack)):
                s = s + int(pack[i])
                i = i + 2
            if s % 2 == 0:
                r0 = 0
            else:
                r0 = 1

            i = 1
            j = 0
            s = 0
            while (i < len(pack)):
                s = s + int(pack[i])
                j = j + 1
                if j == 2:
                    j = 0
                    i = i + 3
                else:
                    i = i + 1
            if s % 2 == 0:
                r1 = 0
            else:
                r1 = 1

            i = 3
            j = 0
            s = 0
            while (i < len(pack)):
                s = s + int(pack[i])
                j = j + 1
                if j == 4:
                    j = 0
                    i = i + 3
                else:
                    i = i + 1
            if s % 2 == 0:
                r2 = 0
            else:
                r2 = 1

            self.fcs = str(r0) + str(r1) + str(r2)
            pack = str(r0) + str(r1) + pack[2] + str(r2) + pack[4:]
            return pack
        #_________________________________________________________________________________________
        if 5 <= length_int <= 11:
            self.fcs_length = 4
            pack = str(r0) + str(r1) + pack[:1] + str(r2) + pack[1:4] + str(r3) + pack[4:]
            print("Pack coding: ", pack)

            i = 0
            j = 0
            s = 0
            while (i < len(pack)):
                s = s + int(pack[i])
                i = i + 2
            if s % 2 == 0:
                r0 = 0
            else:
                r0 = 1

            i = 1
            j = 0
            s = 0
            while (i < len(pack)):
                s = s + int(pack[i])
                j = j + 1
                if j == 2:
                    j = 0
                    i = i + 3
                else:
                    i = i + 1
            if s % 2 == 0:
                r1 = 0
            else:
                r1 = 1

            i = 3
            j = 0
            s = 0
            while (i < len(pack)):
                s = s + int(pack[i])
                j = j + 1
                if j == 4:
                    j = 0
                    i = i + 5
                else:
                    i = i + 1
            if s % 2 == 0:
                r2 = 0
            else:
                r2 = 1

            i = 7
            j = 0
            s = 0
            while (i < len(pack)):
                s = s + int(pack[i])
                j = j + 1
                if j == 8:
                    j = 0
                    i = i + 9
                else:
                    i = i + 1
            if s % 2 == 0:
                r3 = 0
            else:
                r3 = 1

            self.fcs = str(r0) + str(r1) + str(r2) + str(r3)
            pack = str(r0) + str(r1) + pack[2] + str(r2) + pack[4:7] + str(r3) + pack[8:]
            return pack
        # _________________________________________________________________________________________
        if length_int >= 12:
            self.fcs_length = 5
            pack = str(r0) + str(r1) + pack[:1] + str(r2) + pack[1:4] + str(r3) + pack[4:11] + str(r4) + pack[11:]
            print("Pack coding: ", pack)

            i = 0
            j = 0
            s = 0
            while (i < len(pack)):
                s = s + int(pack[i])
                i = i + 2
            if s % 2 == 0:
                r0 = 0
            else:
                r0 = 1

            i = 1
            j = 0
            s = 0
            while (i < len(pack)):
                s = s + int(pack[i])
                j = j + 1
                if j == 2:
                    j = 0
                    i = i + 3
                else:
                    i = i + 1
            if s % 2 == 0:
                r1 = 0
            else:
                r1 = 1

            i = 3
            j = 0
            s = 0
            while (i < len(pack)):
                s = s + int(pack[i])
                j = j + 1
                if j == 4:
                    j = 0
                    i = i + 5
                else:
                    i = i + 1
            if s % 2 == 0:
                r2 = 0
            else:
                r2 = 1

            i = 7
            j = 0
            s = 0
            while (i < len(pack)):
                s = s + int(pack[i])
                j = j + 1
                if j == 8:
                    j = 0
                    i = i + 9
                else:
                    i = i + 1
            if s % 2 == 0:
                r3 = 0
            else:
                r3 = 1

            i = 15
            j = 0
            s = 0
            while (i < len(pack)):
                s = s + int(pack[i])
                j = j + 1
                if j == 16:
                    j = 0
                    i = i + 17
                else:
                    i = i + 1
            if s % 2 == 0:
                r4 = 0
            else:
                r4 = 1

            self.fcs = str(r0) + str(r1) + str(r2) + str(r3) + str(r4)
            pack = str(r0) + str(r1) + pack[2] + str(r2) + pack[4:7] + str(r3) + pack[8:15] + str(r4) + pack[16:]
            return pack

    def length_former(self, length_int):
        length_str = ""
        while length_int > 0:
            length_str = str(length_int % 2) + length_str
            length_int = length_int // 2
        while len(length_str) < 4:
            length_str = "0" + length_str
        return length_str

    def bit_stuffing(self, data):
        start_find = 9
        while True:
            print("start_find = ", start_find)
            index = data.find("011100", start_find)
            if index == -1:
                return data
            data1 = data[0: index + 6]
            data2 = data[index + 6:]
            data = data1 + "0" + data2
            start_find = index + 4
        #return data

    def pack_creator(self, length_str, pack):
        pack = pack_flag + dest_addr + src_addr + length_str + pack + self.fcs
        pack = self.bit_stuffing(pack)
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

    def input_symbol(self, symbol):
        global flag
        flag = 0
        if symbol:
            if symbol != '\n':
                self.sent_bytes += 1
                self.add_symbol(symbol)
        if self.sent_bytes % 40 == 0 and self.sent_bytes != 0:
            self.enter_pushed()
        if symbol == '\n':
            self.sent_bytes = 0
            #self.collision(self.str)
            self.col_thread = threading.Thread(target=self.collision, args=(self.str,))
            self.col_thread.start()
            #ports.write_str_in_port(self.str)
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

parity_change_label = tk.Label(gui, text='Parity:', font=("Times New Roman", 12), background="#C0C0C0")
parity_change_label.grid(row=2, column=3, sticky='w')

List = ['PARITY_NONE', 'PARITY_EVEN', 'PARITY_ODD', 'PARITY_MARK', 'PARITY_SPACE']
option = tk.StringVar(gui)
option.set('PARITY_NONE')
parity_menu = tk.OptionMenu(gui, option, *List)
parity_menu.grid(row=3, column=3)


def isCollisionAppeared(fl: bool):
    status_window.textbox.configure(state='normal')
    #status_window.textbox.delete("3.0", tkinter.END)
    status_window.textbox.insert('end', 'c' if fl else '\n')
    status_window.textbox.yview('end')
    status_window.textbox.configure(state='disabled')


def collisionError():
    status_window.textbox.configure(state='normal')
    #status_window.textbox.delete("3.0", tkinter.END)
    status_window.textbox.insert('end', ' Sending error...' + '\n')
    status_window.textbox.yview('end')
    status_window.textbox.configure(state='disabled')


def debit_stuffing(pack, row):
    start_find = 9
    indexs = []
    j = 0
    while True:
        indexs.append(pack.find("0111000", start_find))
        if indexs[j] == -1:
            j -= 1
            # status_window.textbox.config(state="normal")
            # status_window.textbox.insert(tk.END, pack)
            # while j >= 0 and indexs[j] != -1:
            #     status_window.textbox.insert("%d.%d" % (row, indexs[j] + 6), "0", "RED")
            #     j -= 1
            # if len(pack[20:len(pack)]) == 5:
            #     status_window.textbox.delete("%d.%d" % (row, 23), "%d.%d" % (row, 25))
            #     status_window.textbox.insert("%d.%d" % (row, 25), pack[23] + pack[24], "BLUE")
            # status_window.textbox.insert(tk.END, "\n")
            # status_window.textbox.config(state="disabled")
            return pack
        pack1 = pack[0: indexs[j] + 6]
        pack2 = pack[indexs[j] + 7:]
        pack = pack1 + pack2
        start_find = indexs[j] + 4
        j += 1
    #return pack


def inverter(number):
    if number == 0:
        return 1
    else:
        return 0


def fcs_comparator(old_fcs, new_fcs):
    i = len(old_fcs) - 2
    index = 0
    st = len(old_fcs) - 2
    while i >= 0:
        if int(old_fcs[i]) != int(new_fcs[i]):
            index = index + 2 ** st
        #print("i: ", index)
        #print("st: ", st)
        i -= 1
        st -= 1
    # if index == 0:
        # status_window.textbox.config(state="normal")
        # status_window.textbox.delete("1.13", "1.56")
        # status_window.textbox.insert("1.13", "                          Errors found: 0")
        # status_window.textbox.config(state="disabled")
    if old_fcs[-1] == new_fcs[-1] and index > 0:
        index = 0
        # status_window.textbox.config(state="normal")
        # status_window.textbox.delete("1.13", "1.56")
        # status_window.textbox.insert("1.13", "                          Errors found: 2")
        # status_window.textbox.config(state="disabled")
    # if index > 0:
    #     status_window.textbox.config(state="normal")
    #     status_window.textbox.delete("1.13", "1.56")
    #     status_window.textbox.insert("1.13", "                          Errors found: 1")
    #     status_window.textbox.config(state="disabled")
    return index


def errorer(pack, fcs_length):
    chance = random.randint(1, 100)
    print("Chance: ", chance)

    if chance > 50:
        i = random.randint(1, len(pack))
        print("Error index: ", i)
        pack = pack[:(i - 1)] + str(inverter(int(pack[i - 1]))) + pack[i:]
        #status_window.textbox.config(state="normal")
        #status_window.textbox.delete("1.13", "1.41")
        #status_window.textbox.insert("1.13", "        Generated errors: 1")
        #status_window.textbox.config(state="disabled")
        return pack

    if chance <= 25 and len(pack) > 1:
        i1 = random.randint(1, len(pack))
        print("Error index 1: ", i1)
        i2 = random.randint(1, len(pack))
        while i2 == i1:
            i2 = random.randint(1, len(pack))
        print("Error index 2: ", i2)
        pack = pack[:(i1 - 1)] + str(inverter(int(pack[i1 - 1]))) + pack[i1:]
        pack = pack[:(i2 - 1)] + str(inverter(int(pack[i2 - 1]))) + pack[i2:]
        #status_window.textbox.config(state="normal")
        #status_window.textbox.delete("1.13", "1.41")
        #status_window.textbox.insert("1.13", "        Generated errors: 2")
        #status_window.textbox.config(state="disabled")
        return pack
    else:
        #status_window.textbox.config(state="normal")
        #status_window.textbox.delete("1.13", "1.41")
        #status_window.textbox.insert("1.13", "        Generated errors: 0")
        #status_window.textbox.config(state="disabled")
        return pack


def statuser(header, pack, fcs_length, row):
    pack = header + pack
    # status_window.textbox.config(state="normal")
    # status_window.textbox.insert(tk.END, pack)
    # status_window.textbox.delete("%d.%d" % (row, len(pack) - fcs_length), "%d.%d" % (row, len(pack)))
    # status_window.textbox.insert("%d.%d" % (row, len(pack) - fcs_length), pack[(len(pack) - fcs_length):(len(pack))], "BLUE")
    # status_window.textbox.insert(tk.END, "\n")
    # status_window.textbox.config(state="disabled")


def new_parity_bitter(pack):
    sum = 0
    i = 0
    while i < len(pack):
        if pack[i] == "1":
            sum += 1
        i += 1
    if sum % 2 == 0:
        return "0"
    else:
        return "1"


def fcs_deformer(header, pack, row):
    r0 = 0
    r1 = 0
    r2 = 0
    r3 = 0
    r4 = 0
    if len(pack) == 6:
        fcs_length = 3
        old_fcs = pack[3:]
        pack = pack[2]
        print("Data: ", pack)
        pack = errorer(pack, fcs_length)
        pack = pack + old_fcs
        statuser(header, pack, fcs_length, row)

        pack = pack[0]
        print("Data after errorer: ", pack)
        print("Old FCS: ", old_fcs)
        parity_bit = new_parity_bitter(pack)

        pack = str(r0) + str(r1) + pack
        print("Pack coding: ", pack)

        i = 0
        j = 0
        s = 0
        while (i < len(pack)):
            s = s + int(pack[i])
            i = i + 2
        if s % 2 == 0:
            r0 = 0
        else:
            r0 = 1

        i = 1
        j = 0
        s = 0
        while (i < len(pack)):
            s = s + int(pack[i])
            j = j + 1
            if j == 2:
                j = 0
                i = i + 3
            else:
                i = i + 1
        if s % 2 == 0:
            r1 = 0
        else:
            r1 = 1
        new_fcs = str(r0) + str(r1)
        print("New FCS: ", new_fcs)
        new_fcs = new_fcs + parity_bit
        print("New FCS with parity bit: ", new_fcs)
        index = fcs_comparator(old_fcs, new_fcs)
        print("Index: ", index)
        if index == 0:
            print("New Data and FCS: ", pack)
            pack = pack[2]
            return pack
        else:
            index -= 1
            if index == 0:
                pack = str(inverter(int(pack[index]))) + pack[(index + 1):]
            else:
                pack = pack[:index] + str(inverter(int(pack[index]))) + pack[index + 1:]
            print("New Data and FCS: ", pack)
            pack = pack[2]
            return pack

    if 9 <= len(pack) <= 11:
        fcs_length = 4
        old_fcs = pack[-4:]
        print("Coded Data: ", pack)
        pack = pack[:-4]
        pack = pack[2] + pack[4:]
        parity_bit = new_parity_bitter(pack)
        old_fcs = old_fcs[:3] + parity_bit
        print("Data: ", pack)
        pack = errorer(pack, fcs_length)
        parity_bit = new_parity_bitter(pack)
        pack = pack + old_fcs
        print("Data and fcs after errorer: ", pack)
        statuser(header, pack, fcs_length, row)
        pack = pack[:-4]
        print("Data after errorer: ", pack)
        print("Old FCS: ", old_fcs)
        pack = str(r0) + str(r1) + pack[:1] + str(r2) + pack[1:]
        print("Pack coding: ", pack)

        i = 0
        j = 0
        s = 0
        while (i < len(pack)):
            s = s + int(pack[i])
            i = i + 2
        if s % 2 == 0:
            r0 = 0
        else:
            r0 = 1

        i = 1
        j = 0
        s = 0
        while (i < len(pack)):
            s = s + int(pack[i])
            j = j + 1
            if j == 2:
                j = 0
                i = i + 3
            else:
                i = i + 1
        if s % 2 == 0:
            r1 = 0
        else:
            r1 = 1

        i = 3
        j = 0
        s = 0
        while (i < len(pack)):
            s = s + int(pack[i])
            j = j + 1
            if j == 4:
                j = 0
                i = i + 5
            else:
                i = i + 1
        if s % 2 == 0:
            r2 = 0
        else:
            r2 = 1

        new_fcs = str(r0) + str(r1) + str(r2)
        pack = str(r0) + str(r1) + pack[2] + str(r2) + pack[4:]

        print("New FCS: ", new_fcs)
        new_fcs = new_fcs + parity_bit
        print("New FCS with parity bit: ", new_fcs)
        index = fcs_comparator(old_fcs, new_fcs)
        print("Index: ", index)
        if index == 0:
            print("New Data and FCS: ", pack)
            pack = pack[2] + pack[4:]
            return pack
        else:
            index -= 1
            if index == 0:
                pack = str(inverter(int(pack[index]))) + pack[(index + 1):]
            else:
                pack = pack[:index] + str(inverter(int(pack[index]))) + pack[index + 1:]
            print("New Data and FCS: ", pack)
            pack = pack[2] + pack[4:]
            return pack

    if 14 <= len(pack) <= 20:
        fcs_length = 5
        old_fcs = pack[-5:]
        print("Coded Data: ", pack)
        pack = pack[:-5]
        pack = pack[2] + pack[4:7] + pack[8:]
        parity_bit = new_parity_bitter(pack)
        old_fcs = old_fcs[:4] + parity_bit
        print("Data: ", pack)
        pack = errorer(pack, fcs_length)
        parity_bit = new_parity_bitter(pack)
        pack = pack + old_fcs
        print("Data and fcs after errorer: ", pack)
        statuser(header, pack, fcs_length, row)
        pack = pack[:-5]
        print("Data after errorer: ", pack)
        print("Old FCS: ", old_fcs)
        pack = str(r0) + str(r1) + pack[:1] + str(r2) + pack[1:4] + str(r3) + pack[4:]
        print("Pack coding: ", pack)

        i = 0
        j = 0
        s = 0
        while (i < len(pack)):
            s = s + int(pack[i])
            i = i + 2
        if s % 2 == 0:
            r0 = 0
        else:
            r0 = 1

        i = 1
        j = 0
        s = 0
        while (i < len(pack)):
            s = s + int(pack[i])
            j = j + 1
            if j == 2:
                j = 0
                i = i + 3
            else:
                i = i + 1
        if s % 2 == 0:
            r1 = 0
        else:
            r1 = 1

        i = 3
        j = 0
        s = 0
        while (i < len(pack)):
            s = s + int(pack[i])
            j = j + 1
            if j == 4:
                j = 0
                i = i + 5
            else:
                i = i + 1
        if s % 2 == 0:
            r2 = 0
        else:
            r2 = 1

        i = 7
        j = 0
        s = 0
        while (i < len(pack)):
            s = s + int(pack[i])
            j = j + 1
            if j == 8:
                j = 0
                i = i + 9
            else:
                i = i + 1
        if s % 2 == 0:
            r3 = 0
        else:
            r3 = 1

        new_fcs = str(r0) + str(r1) + str(r2) + str(r3)
        pack = str(r0) + str(r1) + pack[2] + str(r2) + pack[4:7] + str(r3) + pack[8:]

        print("New FCS: ", new_fcs)
        new_fcs = new_fcs + parity_bit
        print("New FCS with parity bit: ", new_fcs)
        index = fcs_comparator(old_fcs, new_fcs)
        print("Index: ", index)
        if index == 0:
            print("New Data and FCS: ", pack)
            pack = pack[2] + pack[4:7] + pack[8:]
            return pack
        else:
            index -= 1
            if index == 0:
                pack = str(inverter(int(pack[index]))) + pack[(index + 1):]
            else:
                pack = pack[:index] + str(inverter(int(pack[index]))) + pack[index + 1:]
            print("New Data and FCS: ", pack)
            pack = pack[2] + pack[4:7] + pack[8:]
            return pack

    if len(pack) >= 23:
        fcs_length = 6
        old_fcs = pack[-6:]
        print("Coded Data: ", pack)
        pack = pack[:-6]
        pack = pack[2] + pack[4:7] + pack[8:15] + pack[16:]
        parity_bit = new_parity_bitter(pack)
        old_fcs = old_fcs[:5] + parity_bit
        print("Data: ", pack)
        pack = errorer(pack, fcs_length)
        parity_bit = new_parity_bitter(pack)
        pack = pack + old_fcs
        print("Data and fcs after errorer: ", pack)
        statuser(header, pack, fcs_length, row)
        pack = pack[:-6]
        print("Data after errorer: ", pack)
        print("Old FCS: ", old_fcs)
        pack = str(r0) + str(r1) + pack[:1] + str(r2) + pack[1:4] + str(r3) + pack[4:11] + str(r4) + pack[11:]
        print("Pack coding: ", pack)

        i = 0
        j = 0
        s = 0
        while (i < len(pack)):
            s = s + int(pack[i])
            i = i + 2
        if s % 2 == 0:
            r0 = 0
        else:
            r0 = 1

        i = 1
        j = 0
        s = 0
        while (i < len(pack)):
            s = s + int(pack[i])
            j = j + 1
            if j == 2:
                j = 0
                i = i + 3
            else:
                i = i + 1
        if s % 2 == 0:
            r1 = 0
        else:
            r1 = 1

        i = 3
        j = 0
        s = 0
        while (i < len(pack)):
            s = s + int(pack[i])
            j = j + 1
            if j == 4:
                j = 0
                i = i + 5
            else:
                i = i + 1
        if s % 2 == 0:
            r2 = 0
        else:
            r2 = 1

        i = 7
        j = 0
        s = 0
        while (i < len(pack)):
            s = s + int(pack[i])
            j = j + 1
            if j == 8:
                j = 0
                i = i + 9
            else:
                i = i + 1
        if s % 2 == 0:
            r3 = 0
        else:
            r3 = 1

        i = 15
        j = 0
        s = 0
        while (i < len(pack)):
            s = s + int(pack[i])
            j = j + 1
            if j == 16:
                j = 0
                i = i + 17
            else:
                i = i + 1
        if s % 2 == 0:
            r4 = 0
        else:
            r4 = 1

        new_fcs = str(r0) + str(r1) + str(r2) + str(r3) + str(r4)
        pack = str(r0) + str(r1) + pack[2] + str(r2) + pack[4:7] + str(r3) + pack[8:15] + str(r4) + pack[16:]

        print("New FCS: ", new_fcs)
        new_fcs = new_fcs + parity_bit
        print("New FCS with parity bit: ", new_fcs)
        index = fcs_comparator(old_fcs, new_fcs)
        print("Index: ", index)
        if index == 0:
            print("New Data and FCS: ", pack)
            pack = pack[2] + pack[4:7] + pack[8:15] + pack[16:]
            return pack
        else:
            index -= 1
            if index == 0:
                pack = str(inverter(int(pack[index]))) + pack[(index + 1):]
            else:
                pack = pack[:index] + str(inverter(int(pack[index]))) + pack[index + 1:]
            print("New Data and FCS: ", pack)
            pack = pack[2] + pack[4:7] + pack[8:15] + pack[16:]
            return pack


status_window.textbox.config(state="normal")
status_window.textbox.delete("1.0", tkinter.END)
status_window.status_text(ports.sender_info)
status_window.textbox.insert(tk.END, "\n")
status_window.status_text(ports.receiver_info)
status_window.textbox.insert(tk.END, "\n")
status_window.textbox.config(state="disabled")


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

input_window.listbox.bind('<Return>', lambda x: input_window.input_symbol('\n'))

input_window.listbox.bind('1', lambda x: input_window.input_symbol('1'))
input_window.listbox.bind('0', lambda x: input_window.input_symbol('0'))

gui.mainloop()
ports.sender.close()
ports.receiver.close()
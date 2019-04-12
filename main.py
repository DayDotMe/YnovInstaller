import json
import os
import subprocess
import time
import uuid
import webbrowser
from threading import Thread
from tkinter import Tk, Frame, RAISED, Button, messagebox, Label, Canvas
from urllib import request
from urllib.error import HTTPError
import platform
from PIL import Image, ImageTk

green = Image.open("green.ico")
green.thumbnail((16, 16))
yellow = Image.open("yellow.svg")
yellow.thumbnail((16, 16))
red = Image.open("red.png")
red.thumbnail((16, 16))


class App:
    def __init__(self):
        self.root = Tk()
        # self.root.overrideredirect(1)
        w = 300
        h = 40
        ws = self.root.winfo_screenwidth()  # width of the screen
        hs = self.root.winfo_screenheight()
        x = ws - w
        y = hs - h
        self.root.geometry('%dx%d+%d+%d' % (w, h, x, y - 70))
        self.root.resizable(False, False)
        self.root.iconbitmap(r'favicon.ico')

        self.frame = Frame(self.root, width=w, height=h,
                           borderwidth=2, relief="flat")

        self.frame.pack_propagate(False)
        self.frame.pack()

        self.bConnect = Button(self.frame, text="Connexion", command=self.connect)

        self.bConnect.grid(column=0, row=0, pady=5)

        self.lDisplay = Label(self.frame, text="Connexion en cours ...", relief="flat", borderwidth=2)

        self.canvas = Canvas(self.frame, width=80, height=32, relief="flat", borderwidth="2")
        self.canvas.grid(column=1, row=0)
        self.green = ImageTk.PhotoImage(green)
        self.yellow = ImageTk.PhotoImage(yellow)
        self.red = ImageTk.PhotoImage(red)

        self.canvas.create_image(70, 20, image=self.red, tags="red")
        self.canvas.create_image(70, 20, image=self.yellow, tags="yellow", state="hidden")
        self.canvas.create_image(70, 20, image=self.green, tags="green", state="hidden")

    def connect(self):
        self.bConnect.destroy()
        self.lDisplay.grid(column=0, row=0, pady=5)
        self.canvas.itemconfigure("red", state="hidden")
        self.canvas.itemconfigure("yellow", state="normal")

        Thread(target=connect_vpn, daemon=True).start()


app = App()


def connect_vpn():
    """
    Renvoi un processus qui execute le client openVPN
    :return:
    """
    vpn = subprocess.Popen(
        ["OpenVPN\\bin\\openvpn", "--config", "OpenVPN\\config\\ynovlyonFirewall-udp-11942-config.ovpn"],
        shell=True, stdin=None, stdout=subprocess.PIPE, stderr=None
    )
    while "Connexion pas encore établie":
        try:
            line = vpn.stdout.readline().decode("utf-8")
            print(line)
        except UnicodeDecodeError:
            line = ""
        if "End ipconfig" in line:
            break

    app.canvas.itemconfigure("yellow", state="hidden")
    app.canvas.itemconfigure("green", state="normal")
    app.lDisplay.config(text="Connexion établie, ne fermez pas.")
    init_ansible()


def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower() == 'windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    return subprocess.call(command) == 0


def init_ansible():
    """
    Autorise les connections WINRM ou SSH
    :return:
    """
    if "Linux" in platform.platform():
        subprocess.Popen(["service", "sshd", "start"])
    elif "Darwin" in platform.platform():
        subprocess.Popen(["systemsetup", "-setremotelogin", "on"])
    elif "Windows" in platform.platform():
        subprocess.Popen(["C:\Windows\SysWOW64\cmd.exe", "powershell", "Set-ExecutionPolicy", "RemoteSigned"])
        subprocess.Popen(['powershell', "lib\\winAnsible.ps1"])
        get_certificate()
        if os.path.exists("cert.pem"):
            subprocess.check_output(['powershell.exe', "-ExecutionPolicy", "ByPass", "lib\\winCertAnsible.ps1"])
            time.sleep(2)
            os.remove("cert.pem")
            print("clean")
        return "Fini"


def check_ansible_enabled():
    """
    :return:
    """
    if "Linux" in platform.platform():
        pass
    elif "Darwin" in platform.platform():
        cmd = subprocess.Popen(["systemsetup", "getremotelogin"])
        if "On" in cmd:
            return True
    elif "Windows" in platform.platform():
        subprocess.Popen(['powershell.exe', "-ExecutionPolicy", "ByPass", "lib\\winAnsible.ps1"])


def get_certificate():
    uname = os.environ.get('USERNAME')
    session = uuid.uuid4()
    try:
        res = request.urlopen("https://apps.ydayslyon.fr/client/?username=%s&session=%s" % (uname, session)).read()
    except HTTPError:
        print("Error")
        return
    res = json.loads(res.decode("utf8"))
    if res.get("cert") and res.get("session"):
        webbrowser.open('https://apps.ydayslyon.fr/&session=%s' % res.get("session"), new=2)  # nouvel onglet
        with open("cert.pem", "w") as f:
            f.write(res.get("cert"))
            os.environ["session"] = res.get("session")
            return


if __name__ == "__main__":
    app.root.mainloop()

    #     time.sleep(1)
    #
    # session = init_ansible()
    # session = init_ansible()

import json
import os
import subprocess
import time
import uuid
import webbrowser
from threading import Thread
import platform
from tkinter import Tk, Frame, RAISED, Button, messagebox
from urllib import request
from urllib.error import HTTPError


def connect_vpn():
    subprocess.Popen(["OpenVPN\\bin\\openvpn", "--config", "OpenVPN\\config\\ynovlyonFirewall-udp-11942-config.ovpn"],
                     shell=True,
                     stdin=None, stdout=None, stderr=None, close_fds=True)


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
        res = request.urlopen("http://localhost:8000/client/?username=%s&session=%s" % (uname, session)).read()
    except HTTPError:
        return
    res = json.loads(res.decode("utf8"))
    if res.get("cert") and res.get("session"):
        webbrowser.open('https://apps.ydayslyon.fr/&session=%s' % res.get("session"), new=2)  # nouvel onglet
        with open("cert.pem", "w") as f:
            f.write(res.get("cert"))
            os.environ["session"] = res.get("session")
            return


class App():
    def __init__(self):
        self.root = Tk()
        self.root.overrideredirect(1)
        w = 200
        h = 100
        ws = self.root.winfo_screenwidth()  # width of the screen
        hs = self.root.winfo_screenheight()
        x = ws - w
        y = hs - h
        self.root.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.frame = Frame(self.root, width=w, height=h,
                           borderwidth=2, relief=RAISED)
        self.frame.pack_propagate(False)
        self.frame.pack()
        self.bQuit = Button(self.frame, text="Quit",
                            command=self.root.quit)
        self.bQuit.pack()
        self.bHello = Button(self.frame, text="Hello",
                             command=self.hello)
        self.bHello.pack()

    def hello(self):
        messagebox.showinfo("Popup", "Hello!")


if __name__ == "__main__":
    # connection = Thread(connect_vpn())
    # connection.start()
    # connection.join()
    session = init_ansible()
    print(os.environ["session"])
    app = App()
    app.bQuit.config(text="OK")
    app.root.mainloop()

    print("Fin de la connection")

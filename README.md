# net-dl

Download web pages and files from the internet. Can be used as a standalone
CLI command, or as a python module.

[Usage & Documentation](https://sil-car.github.io/net-dl/)

## Installation

**End Users (with pipx)**
```
python3 -m pip install pipx
pipx install net-dl
```

**Dev Users (with pip)**
```
python3 -m pip install net-dl
```

## External progress bar example
`demo/tkapp.py`:
```python
from net_dl import Download
from queue import Queue
from threading import Thread
from tkinter import IntVar
from tkinter import StringVar
from tkinter import Tk
from tkinter import ttk


class Win(ttk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.root.title("net-dl demo")

        self.urlv = StringVar()
        self.urlw = ttk.Entry(self, textvariable=self.urlv)
        self.getw = ttk.Button(self, text="Get", command=self.get)
        self.progq = Queue()
        self.progv = IntVar()
        self.proge = '<<UpdateProgress>>'
        self.root.bind(self.proge, self.update_progress)
        self.progw = ttk.Progressbar(
            self,
            mode='determinate',
            variable=self.progv,
            )

        self.grid(column=0, row=0, sticky='nesw')
        self.urlw.grid(column=0, row=0, columnspan=4, sticky='we')
        self.getw.grid(column=4, row=0)
        self.progw.grid(column=0, row=1, columnspan=5, sticky='we')

    def get(self):
        dl = Download(
            self.urlv.get(),
            progress_queue=self.progq,
            callback=self.root.event_generate,
            callback_args=[self.proge],
            )
        self.get_thread = Thread(target=dl.get, daemon=True)
        self.get_thread.start()

    def update_progress(self, evt):
        self.progv.set(self.progq.get())


def run():
    root = Tk()
    Win(root)
    root.mainloop()
```
Run code:
```
demo$ python -c 'import tkapp; tkapp.run()'
```

https://github.com/user-attachments/assets/a33d7752-3167-4224-a7ce-4fb56f69fe5d

## Releasing on PyPI

- Create new tag in repo that matches package version; e.g. if version is "0.1.0", tag will be "v0.1.0".
- CI will auto build and upload package to TestPyPI and PyPI.

import tkinter as tk
from PIL import ImageTk, Image
import threading

import image_queue

class ImagePopup:
    def __init__(self, parent, img_queue: image_queue.ImageQueue):
        """
        To resume from a previous point, pass the full list of source files in same order, the filename pairs that have
         been already processed, and a resume index matching the last processed file.
        :param parent:
        :param img_queue:
        """
        self.parent = parent

        self._load_lock = threading.Lock()
        self._loading = False
        self.img_queue = img_queue

        self.cropped_image = None
        self.full_image = None

        self.window = tk.Toplevel(self.parent)

        self.img = ImageTk.PhotoImage(Image.new('RGB', (800,350)))
        self.panel = tk.Label(self.window, image=self.img)
        self.panel.pack(side='top', fill='both', expand='yes')

        frame = tk.Frame(self.window)
        frame.pack()

        label = tk.Label(frame, text='Enter participant ID')
        self.filename_var = tk.StringVar()
        filename_box = tk.Entry(frame, textvariable=self.filename_var)
        filename_box.bind('<Return>', self.filename_enter)
        save_and_next_button = tk.Button(frame, text='Save and next', command=self.save_and_next_clicked)
        skip_button = tk.Button(frame, text='Skip', command=self.skip_clicked)
        label.grid(column=0, row=0)
        filename_box.grid(column=1, row=0)
        save_and_next_button.grid(column=2, row=0)
        skip_button.grid(column=3, row=0)

        self.window.wait_visibility()
        self.window.grab_set()
        self.window.transient(self.parent)

        self.show_next_img()

    def show_next_img(self):
        full_image, cropped_image, display_image = self.img_queue.get_next_img()

        if full_image is None:
            # reached end of files
            self.window.destroy()
        else:
            self.full_image = full_image
            # clip manikin area and ID
            self.cropped_image = cropped_image
            self.img = ImageTk.PhotoImage(display_image)
            # show ID on screen and get user to transcribe
            self.panel.configure(image=self.img)
            self.panel.image = self.img

        with self._load_lock:
            self._loading = False

    def filename_enter(self, event):
        self.save_and_next_clicked()

    def skip_clicked(self):
        with self._load_lock:
            if self._loading:
                return
            self._loading = True

        self.img_queue.log_skipped_img()
        thread = threading.Thread(target=self.show_next_img)
        thread.start()

    def save_and_next_clicked(self):
        with self._load_lock:
            if self._loading:
                return
            self._loading = True

        save_thread = threading.Thread(target=self.img_queue.save_current_img, args=(self.filename_var.get(),))
        save_thread.start()
        load_thread = threading.Thread(target=self.show_next_img)
        load_thread.start()



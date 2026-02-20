import tkinter.filedialog
from tkinter import ttk
import tkinter as tk

from digitisation import data_io
import image_queue, image_popup

def directory_button_clicked(text_var):
    selected_dir = tk.filedialog.askdirectory()
    text_var.set(selected_dir)

def file_button_clicked(text_var):
    selected_file = tk.filedialog.askopenfilename()
    text_var.set(selected_file)

class MainWindow:
    def __init__(self, pdf_dir: str, img_dir: str, alignment_template: str, cropped_template: str, pixel_template: str,
                 filenames_log_path: str, resume_index_file: str, manikin_coords: image_queue.ImageCoords,
                 display_coords: image_queue.ImageCoords, source_filesnames: str):
        self.root = tk.Tk()
        self.root.title('Pain Manikin Digitisation')
        self.root.minsize(650, 300)
        self.root.geometry('650x300')

        notebook = ttk.Notebook(self.root)
        notebook.pack(pady=10, expand=True)

        config_tab = ttk.Frame(notebook)
        operations_tab = ttk.Frame(notebook)
        config_tab.pack()
        operations_tab.pack()
        notebook.add(operations_tab, text='Operations')
        notebook.add(config_tab, text='Config')

        # Config tab
        current_row = 0
        pdf_dir_label = ttk.Label(config_tab, text="PDF directory:")
        self.pdf_dir_var = tk.StringVar()
        pdf_dir_box = ttk.Entry(config_tab, textvariable=self.pdf_dir_var, width=50)
        pdf_dir_button = ttk.Button(config_tab, text="Select", command=lambda: directory_button_clicked(self.pdf_dir_var))

        pdf_dir_label.grid(column=0, row=current_row)
        pdf_dir_box.grid(column=1, row=current_row)
        pdf_dir_button.grid(column=2, row=current_row)
        current_row += 1

        img_dir_label = ttk.Label(config_tab, text="Image directory:")
        self.img_dir_var = tk.StringVar()
        img_dir_box = ttk.Entry(config_tab, textvariable=self.img_dir_var, width=50)
        img_dir_button = ttk.Button(config_tab, text="Select", command=lambda: directory_button_clicked(self.img_dir_var))

        img_dir_label.grid(column=0, row=current_row)
        img_dir_box.grid(column=1, row=current_row)
        img_dir_button.grid(column=2, row=current_row)
        current_row += 1

        json_dir_label = ttk.Label(config_tab, text="Json directory:")
        self.json_dir_var = tk.StringVar()
        json_dir_box = ttk.Entry(config_tab, textvariable=self.json_dir_var, width=50)
        json_dir_button = ttk.Button(config_tab, text="Select", command=lambda: directory_button_clicked(self.json_dir_var))

        json_dir_label.grid(column=0, row=current_row)
        json_dir_box.grid(column=1, row=current_row)
        json_dir_button.grid(column=2, row=current_row)
        current_row += 1

        filenames_log_label = ttk.Label(config_tab, text="Filenames log:")
        self.filenames_log_path_var = tk.StringVar()
        filenames_log_box = ttk.Entry(config_tab, textvariable=self.filenames_log_path_var, width=50)
        filenames_log_button = ttk.Button(config_tab, text="Select", command=lambda: file_button_clicked(self.filenames_log_path_var))

        filenames_log_label.grid(column=0, row=current_row)
        filenames_log_box.grid(column=1, row=current_row)
        filenames_log_button.grid(column=2, row=current_row)
        current_row += 1

        alignment_template_label = ttk.Label(config_tab, text="PDF Template file:")
        self.alignment_template_var = tk.StringVar()
        alignment_template_box = ttk.Entry(config_tab, textvariable=self.alignment_template_var, width=50)
        alignment_template_button = ttk.Button(config_tab, text="Select", command=lambda: file_button_clicked(self.alignment_template_var))

        alignment_template_label.grid(column=0, row=current_row)
        alignment_template_box.grid(column=1, row=current_row)
        alignment_template_button.grid(column=2, row=current_row)
        current_row += 1

        pixel_template_label = ttk.Label(config_tab, text="Pixel Template file:")
        self.pixel_template_var = tk.StringVar()
        pixel_template_box = ttk.Entry(config_tab, textvariable=self.pixel_template_var, width=50)
        pixel_template_button = ttk.Button(config_tab, text="Select", command=lambda: file_button_clicked(self.pixel_template_var))

        pixel_template_label.grid(column=0, row=current_row)
        pixel_template_box.grid(column=1, row=current_row)
        pixel_template_button.grid(column=2, row=current_row)
        current_row += 1

        resume_index_label = ttk.Label(config_tab, text="Resume index file:")
        self.resume_index_text_var = tk.StringVar()
        resume_index_box = ttk.Entry(config_tab, textvariable=self.resume_index_text_var, width=50)
        resume_index_button = ttk.Button(config_tab, text="Select", command=lambda: file_button_clicked(self.resume_index_text_var))

        resume_index_label.grid(column=0, row=current_row)
        resume_index_box.grid(column=1, row=current_row)
        resume_index_button.grid(column=2, row=current_row)


        self.pdf_dir_var.set(pdf_dir)
        self.img_dir_var.set(img_dir)
        self.alignment_template_var.set(alignment_template)
        self.pixel_template_var.set(pixel_template)
        self.filenames_log_path_var.set(filenames_log_path)
        self.resume_index_text_var.set(resume_index_file)
        self.manikin_coords = manikin_coords
        self.display_coords = display_coords

        # Operations tab
        align_button = ttk.Button(operations_tab, text="Align and crop PDFs", command=lambda: self.run_alignment(source_filesnames))
        self.resume_check_var = tk.IntVar()
        resume_checkbox = tk.Checkbutton(operations_tab, text='Resume', variable=self.resume_check_var, onvalue=1, offvalue=0)
        align_button.grid(column=0, row=0)
        resume_checkbox.grid(column=1, row=0)

        manikin_pixels_button = ttk.Button(operations_tab, text='Get raw manikin pixel data', command=self.find_raw_manikin_pixels)
        manikin_pixels_button.grid(column=0, row=1)

        realign_button = ttk.Button(operations_tab, text='Realign cropped images', command=lambda: self.realign_cropped(cropped_template))
        realign_button.grid(column=0, row=2)

        self.root.mainloop()

    def realign_cropped(self, template_file):
        source_dir = self.img_dir_var.get()
        output_dir = data_io.create_sub_dir(source_dir, 'aligned')
        data_io.align_directory(source_dir, output_dir, template_file)

    def find_raw_manikin_pixels(self):
        source_dir = self.img_dir_var.get()
        output_dir = self.json_dir_var.get()
        template_file = self.pixel_template_var.get()
        data_io.apply_template_mask(source_dir, output_dir, template_file)

    def run_alignment(self, source_filenames):
        source_dir = self.pdf_dir_var.get()
        output_dir = self.img_dir_var.get()
        template_file = self.alignment_template_var.get()
        resume_index_file = self.resume_index_text_var.get()
        filenames_log_path = self.filenames_log_path_var.get()

        temp_dir = data_io.create_sub_dir(output_dir)
        if self.resume_check_var.get() == 1:
            # load source files from file
            files = data_io.load_source_files_list(source_dir)
            img_queue = image_queue.ImageQueue(files, output_dir, temp_dir, template_file, resume_index_file,
                                               filenames_log_path, self.manikin_coords, self.display_coords,
                                               resume=True)
            popup = image_popup.ImagePopup(self.root, img_queue)
        else:
            files = data_io.get_source_files(source_dir, '.pdf')
            data_io.save_source_files_list(files, temp_dir, source_filenames)
            data_io.create_filenames_log(output_dir, resume_index_file, filenames_log_path)
            img_queue = image_queue.ImageQueue(files, output_dir, temp_dir, template_file, resume_index_file,
                                               filenames_log_path, self.manikin_coords, self.display_coords)
            popup = image_popup.ImagePopup(self.root, img_queue)

        self.root.wait_window(popup.window)


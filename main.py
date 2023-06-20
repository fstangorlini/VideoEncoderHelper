###############################################################################
######################### Author:  Felipe Stangorlini #########################
######################### Date:    Jun-2023           #########################
######################### Version: 0.2                #########################
###############################################################################

###############################################################################
################################## IMPORTS ####################################
###############################################################################

import os   
import os.path
import queue
from tkinter import ttk
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk, ImageOps
from subprocess import call
import tempfile
import threading
from datetime import datetime

###############################################################################
############################# GLOBAL VARIABLES ################################
###############################################################################

queue = queue.Queue()

DATE_FORMAT = '%d-%m-%Y'
MSG_INFO    = -1
MSG_ERROR   =  1
MSG_SUCCESS =  0

SOURCE_PATH   = 'D:/Recordings/Counter-strike  Global Offensive'
TARGET_PATH   = 'E:/My clips/Counter-strike  Global Offensive/'
EXTENSION = '.mp4'

QUALITY_BITRATE = {True:'12M', False:'2M'}

THUMBNAIL_DIMENSIONS = (450,450)

FFMPEG_PATH = 'C:/ffmpeg/bin/ffmpeg.exe'

###############################################################################
########################### START OF ENCODER CLASS ############################
###############################################################################

class Encoder:
    def __init__(self, params:dict, queue:queue, FFMPEG_PATH:str='C:/ffmpeg/bin/ffmpeg.exe'):
        
        #Checks if input file exists
        if not os.path.exists(params['input']):
            queue.put((1, 'Error: input file does not exist'))
            return
        #Overrides output without asking
        if os.path.exists(params['output']):
            os.remove(params['output'])
        #Args array
        args = [FFMPEG_PATH]
        gpu_a = ['-hwaccel', 'cuda','-hwaccel_output_format', 'cuda']
        if params['hardware'] == 1: #1: GPU / 2: CPU
            args.extend(gpu_a)
        args.extend(['-i', params['input'],
            '-b:v', params['bitrate'], #video quality
            '-codec:v', params['codec'],
            '-preset', params['preset'],
            '-codec:a', 'copy', #audio copy - no encoding will be performed
            '-ss', '00:'+params['start_min']+':'+params['start_sec'],
            '-to', '00:'+params['end_min']  +':'+params['end_sec'],
            params['output']])
        before = datetime.now()
        call(args)
        if params['delete']:
            os.remove(params['input'])
        after = datetime.now()
        runtime = after-before
        runtime = runtime.total_seconds()
        msg = 'Encoded successfully in ['+str(runtime)+'] seconds'
        queue.put((0, msg))

class ThreadedTask(threading.Thread):
    def __init__(self, params:dict, queue):
        threading.Thread.__init__(self)
        self.params = params
        self.queue = queue
        
    def run(self):
        Encoder(self.params, self.queue)

###############################################################################
############################ END OF ENCODER CLASS #############################
###############################################################################

###############################################################################
############################# START OF GUI CLASS ##############################
###############################################################################
class main:
    
    def process_queue(self):
        msg = None
        if(queue.empty()==False):
            msg = queue.get(0)
            error_code = msg[0]
            message = msg[1]
            #If not info, unlock controls
            if(error_code>=0):
                self.progress_bar.stop()
                self.unlock_elements()
            self.textfield_status.configure(state='normal')
            self.textfield_status.delete(0, END)
            self.textfield_status.insert(0, message)
            self.textfield_status.configure(state='disabled')
    
    def update_root(self):
        self.root.after(100, self.update_root)
        if(queue.empty()==False):
            self.process_queue()
            
    def lock_elements(self):
        for element in self.elements_control:
            element.configure(state='disabled')

    def unlock_elements(self):
        for element in self.elements_control:
            element.configure(state='normal')
    
    def update_thumbnail(self):
        in_file = self.root.input_file
        if os.path.exists(in_file) and os.path.isfile(in_file):
            temp_thumbnail = os.path.join(tempfile.gettempdir(), 'VideoEncoderTempThumbnail.jpg')
            if os.path.exists(temp_thumbnail) and os.path.isfile(temp_thumbnail):
                os.remove(temp_thumbnail)
            call(['ffmpeg', '-i', in_file, '-ss', '00:00:00.000', '-vframes', '1', temp_thumbnail])
            image = Image.open(temp_thumbnail)
            image = ImageOps.contain(image, THUMBNAIL_DIMENSIONS)
            img = ImageTk.PhotoImage(image)
            self.label_thumbnail.configure(image=img)
            self.label_thumbnail.image = img

    def action_button_in_file(self):
        input_folder = self.textfield_in_file.get()
        self.textfield_in_file.delete(0, END)
        if os.path.exists(input_folder):
            self.root.input_file = filedialog.askopenfilename(initialdir=input_folder)
        else:
            self.root.input_file = filedialog.askopenfilename()
        
        self.update_thumbnail()
            
        self.textfield_in_file.insert(0, self.root.input_file)
        self.textfield_out_file.delete(0, END)
        self.textfield_out_file.insert(0, TARGET_PATH+os.path.basename(self.root.input_file))

        return
    
    def refresh_params(self):
        self.params['codec'] = self.stringvar_codec.get()
        self.params['preset'] = 'slow'
        self.params['input'] = self.textfield_in_file.get()
        self.params['output'] = self.textfield_out_file.get()
        self.params['start_min'] = self.textfield_sm.get()
        self.params['start_sec'] = self.textfield_ss.get()
        self.params['end_min'] = self.textfield_em.get()
        self.params['end_sec'] = self.textfield_es.get()
        self.params['hardware'] = self.intvar_hardware.get()
        self.params['delete'] = self.booleanvar_delete.get()
        self.params['bitrate'] = QUALITY_BITRATE[self.booleanvar_high_quality.get()]

    def action_button_process(self):
        self.refresh_params()

        if not os.path.exists(self.params['input']):
            queue.put((MSG_INFO, 'Error while processing'))
            return
    
        queue.put((MSG_INFO, self.MSG_INFO_WORKING))
        self.progress_bar.start()
        self.lock_elements()
        ThreadedTask(self.params, queue).start()
        return
    
    def refresh_output_file(self):
        f = self.stringvar_text_in_file.get()
        if os.path.exists(f) and os.path.isfile(f):
            if self.booleanvar_high_quality.get():
                self.textfield_out_file.delete(0, END)
                self.textfield_out_file.insert(0, TARGET_PATH+os.path.basename(f))
            else:
                o = self.textfield_out_file.get()
                index = o.find(EXTENSION)
                o = o[:index] + '[low]' + o[index:]
                self.stringvar_text_out_file.set(o)
        else:
            self.textfield_out_file.delete(0, END)

    def update_quality(self):
        if self.booleanvar_high_quality.get():
            self.stringvar_codec.set('hevc_nvenc')
        else:
            self.stringvar_codec.set('h264_nvenc')
        self.refresh_output_file()

    def __ui_elements_init__(self):
        ###############################
        # Define root window properties
        ###############################
        self.root.title(self.TITLE)
        self.root.geometry(self.GEOMETRY)
        self.root.resizable(False, False)
        
        ###############################
        # Create Elements
        ###############################
        self.frameParams = Frame(master=self.root)
        self.frameTime = Frame(master=self.frameParams)
        self.frameHardware = Frame(master=self.frameParams)
        self.stringvar_text_status      = StringVar()
        self.stringvar_text_in_file     = StringVar()
        self.stringvar_text_out_file    = StringVar()
        self.label_subtitle             = Label(self.root,text=self.SUBTITLE,font=(self.FONT_CALIBRI, 14))
        self.label_status               = Label(self.root,text=self.LABEL_STATUS,font=(self.FONT_CALIBRI, 10))
        self.label_out_file             = Label(self.root,text=self.LABEL_OUTPUT,font=(self.FONT_CALIBRI, 10))
        self.label_parameters           = Label(self.root,text='Parameters',font=(self.FONT_CALIBRI, 10))
        self.textfield_status           = Entry(self.root,width=110,textvariable=self.stringvar_text_status)
        self.progress_label             = Label(self.root,text=self.LABEL_PROGRESS,font=(self.FONT_CALIBRI, 10))
        self.progress_bar               = ttk.Progressbar(orient="horizontal",length=664, mode="determinate")
        self.textfield_in_file          = Entry(self.root, width=110, textvariable=self.stringvar_text_in_file)
        self.textfield_out_file         = Entry(self.root, width=110, textvariable=self.stringvar_text_out_file)
        
        self.button_in_file  = Button(self.root, text=self.BUTTONTEXT1, command=self.action_button_in_file, width=16)
        self.button_process  = Button(self.root, text=self.BUTTONTEXT2, command=self.action_button_process, width=16)
        
        self.stringvar_sm     = StringVar()
        self.stringvar_ss     = StringVar()
        self.stringvar_em     = StringVar()
        self.stringvar_es     = StringVar()
        
        self.label_start      = Label(self.frameTime,text='Time start',font=(self.FONT_CALIBRI, 8))
        self.label_separator1 = Label(self.frameTime,text=':',font=(self.FONT_CALIBRI, 8))
        self.label_separator2 = Label(self.frameTime,text=':',font=(self.FONT_CALIBRI, 8))
        self.label_end        = Label(self.frameTime,text='Time end',  font=(self.FONT_CALIBRI, 8))
        self.textfield_sm     = Entry(self.frameTime, width=2, textvariable=self.stringvar_sm)
        self.textfield_ss     = Entry(self.frameTime, width=2, textvariable=self.stringvar_ss)
        self.textfield_em     = Entry(self.frameTime, width=2, textvariable=self.stringvar_em)
        self.textfield_es     = Entry(self.frameTime, width=2, textvariable=self.stringvar_es)
        
        self.label_hardware = Label(self.frameParams,text='Hardware',font=(self.FONT_CALIBRI, 8))
        self.intvar_hardware = IntVar()
        self.dropdown_use_gpu = Radiobutton(self.frameHardware, text="GPU", variable=self.intvar_hardware, value=1)
        self.dropdown_use_cpu = Radiobutton(self.frameHardware, text="CPU", variable=self.intvar_hardware, value=2)
        #self.checkbox_use_gpu = Checkbutton(self.frameParams, text='GPU',variable=self.intvar_use_gpu, onvalue=1, offvalue=0)
        self.label_codec = Label(self.frameParams,text='Codec',font=(self.FONT_CALIBRI, 8))
        self.stringvar_codec = StringVar()
        self.textfield_codec = Entry(self.frameParams, width=15, textvariable=self.stringvar_codec)
        
        self.label_high_quality = Label(self.frameParams,text='Quality',font=(self.FONT_CALIBRI, 8))
        self.booleanvar_high_quality = BooleanVar()
        self.checkbox_high_quality = Checkbutton(self.frameParams, text='High Quality',variable=self.booleanvar_high_quality, onvalue=True, offvalue=False, command=self.update_quality)

        self.label_delete = Label(self.frameParams,text='Input file',font=(self.FONT_CALIBRI, 8))
        self.booleanvar_delete = BooleanVar()
        self.checkbox_delete = Checkbutton(self.frameParams, text='Delete input file after encoding',variable=self.booleanvar_delete, onvalue=True, offvalue=False)

        self.label_thumbnail = Label(self.root)
        
        ###############################
        # Align elements to grid
        ###############################
        #root frame
        self.button_in_file.grid(column=0, row=1, sticky='W')
        self.textfield_in_file.grid(column=1, row=1, sticky='W')
        self.label_out_file.grid(column=0, row=2, sticky='W')
        self.textfield_out_file.grid(column=1, row=2, sticky='W')
        self.label_parameters.grid(column=0, row=3, sticky='W')
        self.frameParams.grid(column=1, row=3, sticky='W')
        self.frameTime.grid(column=0, row=0, sticky='W')
        self.button_process.grid(column=0, row=8, sticky='W')
        self.label_status.grid(column=0, row=9, sticky='W')
        self.progress_label.grid(column=0, row=10, sticky='W')
        self.label_subtitle.grid(column=1, row=0, sticky='NSWE')
        self.textfield_status.grid(column=1, row=9, sticky='W')
        self.progress_bar.grid(column=1, row=10, sticky='W')

        # Parameters sub frame
        self.label_start.grid(column=0, row=0, sticky='W')
        self.textfield_sm.grid(column=1, row=0, sticky='W')
        self.label_separator1.grid(column=2, row=0, sticky='W')
        self.textfield_ss.grid(column=3, row=0, sticky='W')
        self.label_end.grid(column=0, row=1, sticky='W')
        self.textfield_em.grid(column=1, row=1, sticky='W')
        self.label_separator2.grid(column=2, row=1, sticky='W')
        self.textfield_es.grid(column=3, row=1, sticky='W')
        
        self.label_hardware.grid(column=0, row=2, sticky='W')
        self.frameHardware.grid(column=1,row=2, sticky = 'W')
        self.dropdown_use_gpu.grid(column=0, row=0, sticky='W')
        self.dropdown_use_cpu.grid(column=0, row=1, sticky='W')
        self.label_codec.grid(column=0, row=3, sticky='W')
        self.textfield_codec.grid(column=1, row=3, sticky='W')
        self.label_high_quality.grid(column=0, row=5, sticky='W')
        self.checkbox_high_quality.grid(column=1, row=5, sticky='W')
        self.label_delete.grid(column=0, row=6, sticky='W')
        self.checkbox_delete.grid(column=1, row=6, sticky='W')
        
        self.label_thumbnail.grid(column=1,row=11)

    def __pre_open__(self):
        ###############################
        # Pre-open
        ###############################
        self.elements_control = [self.textfield_in_file, self.textfield_out_file, self.button_process, self.button_in_file,
                                 self.textfield_codec, self.textfield_sm, self.textfield_ss, self.textfield_em,
                                 self.textfield_es, self.checkbox_delete, self.checkbox_high_quality, self.dropdown_use_cpu,
                                 self.dropdown_use_gpu]
        self.textfield_status.delete(0, END)
        self.textfield_status.insert(0, self.FILE_DIALOG_TITLE)
        self.textfield_status.configure(state=self.STATE_DISABLED,disabledbackground='white')
        self.textfield_in_file.insert(0,self.INITIAL_DIR)
        self.textfield_sm.insert(0,'04')
        self.textfield_ss.insert(0,'40')
        self.textfield_em.insert(0,'05')
        self.textfield_es.insert(0,'00')
        self.intvar_hardware.set(0)
        self.stringvar_codec.set('hevc_nvenc')
        self.checkbox_high_quality.select()
        self.booleanvar_delete.set(True)
        self.intvar_hardware.set(1)
        self.booleanvar_high_quality.set(True)
        self.textfield_codec.configure(state=self.STATE_DISABLED,disabledbackground='white')

    def __post_close__(self):
        ###############################
        # Post-close
        ###############################
        pass

    def __init__(self):
        self.root = Tk()
        self.GEOMETRY = '800x650'
        self.TITLE = 'Video Encoder Helper - by Felipe S.'
        self.SUBTITLE = 'ffmpeg Python video encoder - by Felipe S.'
        self.INITIAL_DIR = SOURCE_PATH
        self.LABEL_PROGRESS = 'Progress: '
        self.LABEL_STATUS = 'Status:'
        self.STATE_NORMAL   = 'normal'
        self.STATE_DISABLED = 'disabled'
        self.FONT_CALIBRI   = 'Calibri'
        self.BUTTONTEXT1 = 'Select Input file'
        self.LABEL_OUTPUT = 'Output file'
        self.BUTTONTEXT2 = 'Encode'
        self.FILE_DIALOG_TITLE = 'Select a video file to encode'
        self.FILETYPES = (("Videos", "*.mp4"), ("all files", "*.*"))
        self.MSG_INFO_WORKING = 'Working, please wait...'
        self.params = {}
        
        self.__ui_elements_init__()
        self.__pre_open__()
        
        ###############################
        # GUI main loop
        ###############################
        self.root.after(100, self.update_root)
        self.root.mainloop()
        
        self.__post_close__()
        
###############################################################################
############################## END OF GUI CLASS ###############################
###############################################################################

# Initialize
if __name__ == "__main__":
    main()


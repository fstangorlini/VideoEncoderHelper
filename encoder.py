###############################################################################
######################### Author:  Felipe Stangorlini #########################
######################### Date:    Jun-2023           #########################
######################### Version: 0.1                #########################
###############################################################################

from subprocess import call
import os
import threading
import queue
from datetime import datetime

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
        if params['gpu'] == 1:
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

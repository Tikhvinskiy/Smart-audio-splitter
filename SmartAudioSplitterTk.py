import os
import time
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import pydub
from pydub.playback import play
import re
import webbrowser
import multiprocessing
import threading
from SmartAudioSplitter import SmartAudioSplitter


class SmartAudioSplitterTk(SmartAudioSplitter):
    """
    SmartAudioSplitter splits large audio files into sections
    by silence.
    SmartAudioSplitterTk operate with the standard Python interface(tkinter).
    """

    def __init__(self):
        super().__init__(full_filename='')

        # set engine
        self.root = tk.Tk()
        self.root.title('Smart Audio Splitter')
        self.root.geometry("1200x520+300+300")
        self.root.resizable(False, False)

        # set fonts
        self.font = {0: ('Helvetica', 12),
                     1: ('Helvetica', 16),
                     2: ('Helvetica', 18, 'bold')}
        self.root.option_add('*Dialog.msg.font', self.font[0])
        self.root.option_add('*TCombobox*Listbox.font', self.font[1])

        # set variables
        self.in_format = tk.StringVar(value='Format:')
        self.filename = tk.StringVar(value='File:')
        self.full_filename = ''
        self.params_dict = []
        self.duration_label = tk.StringVar(value='Duration:')
        self.duration = 0
        self.ncut = tk.IntVar(value=4)
        self.ncut_calc = tk.StringVar(value='(part is ~)')
        self.add_pause_state = tk.BooleanVar(value=True)
        self.pause_len = tk.IntVar(value=2000)
        self.split_by_silence = tk.BooleanVar(value=True)
        self.silence_len = tk.IntVar(value=500)
        self.out_format = tk.StringVar(value='mp3')
        self.bitrate = tk.StringVar(value='128k')
        self.newfilename = tk.StringVar(value='')
        self.multiprocesses = tk.BooleanVar(value=True)
        self.n_cores = tk.StringVar(value='all cores')
        self.progress_len = tk.IntVar(value=1)

    def start(self):
        self.create_step1()
        self.create_step2()
        self.create_step3()
        self.root.mainloop()

    def open_file_dialog(self):
        filename = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title='Select file',
            filetypes=(('mp3 files', '*.mp3'),
                       ('wav files', '*.wav'),
                       ('audio book files', '*.m4b'),
                       ('aac files', '*.aac'),
                       ('flac files', '*.flac'),
                       ('all files', '*.*')),
        )

        self.full_filename = filename
        self.filename.set(f'File: {os.path.basename(filename)}')
        self.set_input_params()
        self.run_button['state'] = 'normal'

    def set_input_params(self):
        self.params_dict = self.get_parameters(self.full_filename)

        if 'ffprobe_duration' in self.params_dict:
            format_ = '##'
            rate = '##'
            channels = '##'
            bt = '##'
            self.duration = float(self.params_dict['ffprobe_duration'])

        else:
            format_ = self.params_dict['format_name'][:10]
            rate = int(self.params_dict['sample_rate']) // 1000
            channels = self.params_dict['channels']
            bt = int(self.params_dict['bit_rate']) // 1000
            self.duration = float(self.params_dict['duration'])

        self.in_format.set(
            value=f'Format: {format_} {bt}kbit/s {rate}khz {channels} channels')

        m, s = divmod(self.duration, 60)
        h, m = divmod(m, 60)
        self.duration_label.set(
            value=f'Duration: {h:.0f}h : {m:.0f}m : {s:.01f}s')

        self.parts_calc()

        output_name = re.findall(
            r'[a-zA-ZА-яёЁ]+', os.path.basename(self.full_filename))
        output_name = '_'.join(output_name)[:20]
        self.newfilename.set(output_name)

    def parts_calc(self):
        duration = self.duration / self.ncut.get()
        m, s = divmod(duration, 60)
        h, m = divmod(m, 60)
        self.ncut_calc.set(
            value=f'(part is ~{h:.0f}h : {m:.0f}m : {s:.01f}s)')

    def pause_on_off(self):
        if str(self.entry_pause['state']) == 'normal':
            self.entry_pause['state'] = 'disabled'
        else:
            self.entry_pause['state'] = 'normal'

    def by_silence_on_off(self):
        if str(self.entry_silence['state']) == 'normal':
            self.entry_silence['state'] = 'disabled'
        else:
            self.entry_silence['state'] = 'normal'

    def multiprocessing_on_off(self):
        if str(self.menu_out_format['state']) == 'normal':
            self.menu_out_format['state'] = 'disabled'
        else:
            self.menu_out_format['state'] = 'normal'

    def is_mp3(self, entry):
        if entry.get() == 'wav':
            self.entry_bitrate['state'] = 'disabled'
        else:
            self.entry_bitrate['state'] = 'normal'

    def show_params(self):
        if len(self.params_dict):
            params = '\n'.join(
                f"'{k}': {v}" for k, v in self.params_dict.items())
            tk.messagebox.showinfo(title='Parameters',
                                   message=params)

    def play(self):
        audio = pydub.AudioSegment.from_file(self.full_filename,
                                             start_second=0,
                                             duration=10)
        process_play = multiprocessing.Process(
            target=play, args=(audio,), daemon=True)
        process_play.start()

    def create_step1(self):

        step1_frame = tk.LabelFrame(self.root, text='Step 1. Load an audio file',
                                    font=self.font[2])

        step1_frame.columnconfigure(index=1, weight=1)

        file_button = tk.Button(step1_frame,
                                text='Select File',
                                command=self.open_file_dialog,
                                width=20,
                                font=self.font[1])
        file_button.grid(row=0, column=0, padx=4, pady=4, sticky='w')

        prop_button = tk.Button(step1_frame,
                                text='All parameters',
                                command=self.show_params,
                                width=15,
                                font=self.font[1])
        prop_button.grid(row=0, column=2, padx=4, pady=4, sticky='e')

        label_format = tk.Label(step1_frame,
                                textvariable=self.in_format,
                                font=self.font[1])
        label_format.grid(row=0, column=1, padx=10, pady=4, sticky='w')

        label_file = tk.Label(step1_frame,
                              textvariable=self.filename,
                              width=100,
                              anchor='w',
                              font=self.font[1])
        label_file.grid(row=1, column=0, columnspan=3, padx=4,
                        pady=4, sticky='w')

        play_button = tk.Button(step1_frame,
                                text='Play (10 sec)',
                                command=self.play,
                                width=15,
                                font=self.font[1])
        play_button.grid(row=1, column=2, padx=4, pady=4, sticky='e')

        step1_frame.pack(padx=10, pady=10, fill=tk.X)

    def create_step2(self):

        step2_frame = tk.LabelFrame(self.root, text='Step 2. Config',
                                    font=self.font[2])
        step2_frame.columnconfigure(index=2, weight=1)

        label_duration = tk.Label(step2_frame,
                                  textvariable=self.duration_label,
                                  anchor='w',
                                  font=self.font[1])
        label_duration.grid(row=0, column=0, padx=4,
                            pady=4, sticky='w')

        label_ncut = tk.Label(step2_frame,
                              text='How many parts to split:',
                              anchor='w',
                              font=self.font[1])
        label_ncut.grid(row=1, column=0, padx=4,
                        pady=4, sticky='w')

        entry_ncut = tk.Entry(step2_frame,
                              textvariable=self.ncut,
                              width=4,
                              font=self.font[1])
        entry_ncut.bind('<Return>', lambda event: self.parts_calc())
        entry_ncut.grid(row=1, column=1, padx=4,
                        pady=4, sticky='w')

        label_ncut_calc = tk.Label(step2_frame,
                                   textvariable=self.ncut_calc,
                                   anchor='w',
                                   font=self.font[1])
        label_ncut_calc.grid(row=3, column=0, padx=4,
                             pady=4, sticky='w')

        radio_pause = tk.Checkbutton(step2_frame,
                                     text='Split by silence:',
                                     command=self.by_silence_on_off,
                                     anchor='w',
                                     variable=self.split_by_silence,
                                     font=self.font[1])
        radio_pause.grid(row=0, column=3, padx=4,
                         pady=4, sticky='w')

        self.entry_silence = tk.Entry(step2_frame,
                                      textvariable=self.silence_len,
                                      width=8,
                                      state=['disabled', 'normal'][self.add_pause_state.get()],
                                      font=self.font[1])
        self.entry_silence.grid(row=0, column=4, padx=4,
                                pady=4, sticky='w')

        label_silence = tk.Label(step2_frame,
                                 text='ms',
                                 anchor='w',
                                 font=self.font[1])
        label_silence.grid(row=0, column=5, padx=4,
                           pady=4, sticky='w')

        radio_pause = tk.Checkbutton(step2_frame,
                                     text='Add pauses to parts:',
                                     command=self.pause_on_off,
                                     anchor='w',
                                     variable=self.add_pause_state,
                                     font=self.font[1])
        radio_pause.grid(row=1, column=3, padx=4,
                         pady=4, sticky='w')

        self.entry_pause = tk.Entry(step2_frame,
                                    textvariable=self.pause_len,
                                    width=8,
                                    state=['disabled', 'normal'][self.split_by_silence.get()],
                                    font=self.font[1])
        self.entry_pause.grid(row=1, column=4, padx=4,
                              pady=4, sticky='w')

        label_pause = tk.Label(step2_frame,
                               text='ms',
                               anchor='w',
                               font=self.font[1])
        label_pause.grid(row=1, column=5, padx=4,
                         pady=4, sticky='w')

        label_out_format = tk.Label(step2_frame,
                                    text='Select output format:',
                                    anchor='w',
                                    font=self.font[1])
        label_out_format.grid(row=4, column=0, padx=4,
                              pady=4, sticky='w')

        menu_out_format = ttk.Combobox(step2_frame,
                                       textvariable=self.out_format,
                                       width=6,
                                       values=['mp3', 'wav'],
                                       font=self.font[1])
        menu_out_format.bind('<<ComboboxSelected>>',
                             lambda event, entry=menu_out_format: self.is_mp3(entry))
        menu_out_format.grid(row=4, column=1, padx=4,
                             pady=4, sticky='w')

        self.entry_bitrate = ttk.Combobox(step2_frame,
                                          textvariable=self.bitrate,
                                          width=6,
                                          values=['64k', '96k', '128k', '256k', '320k'],
                                          state=['disabled', 'normal'][self.out_format.get() == 'mp3'],
                                          font=self.font[1])
        self.entry_bitrate.grid(row=4, column=2, padx=4,
                                pady=4, sticky='w')

        label_filename = tk.Label(step2_frame,
                                  text='Select output filename:',
                                  anchor='w',
                                  font=self.font[1])
        label_filename.grid(row=4, column=2, padx=4,
                            pady=4, sticky='e')

        self.entry_filename = tk.Entry(step2_frame,
                                       textvariable=self.newfilename,
                                       width=30,
                                       font=self.font[1])
        self.entry_filename.grid(row=4, column=3, columnspan=2, padx=4,
                                 pady=4, sticky='w')

        step2_frame.pack(padx=10, pady=20, fill=tk.X)

    def create_step3(self):

        step3_frame = tk.LabelFrame(self.root, text='Step 3. Processing',
                                    font=self.font[2])
        step3_frame.columnconfigure(2, weight=1)

        self.run_button = tk.Button(step3_frame,
                                    text='Start processing',
                                    command=self.start_processing,
                                    width=50,
                                    state='disabled',
                                    font=self.font[1])
        self.run_button.grid(row=0, column=0, padx=4, pady=4, sticky='w')

        radio_multiprocessing = tk.Checkbutton(step3_frame,
                                               text='Use multiprocessing:',
                                               command=self.multiprocessing_on_off,
                                               anchor='w',
                                               variable=self.multiprocesses,
                                               font=self.font[1])
        radio_multiprocessing.grid(row=0, column=1, padx=4,
                                   pady=4, sticky='w')

        self.menu_out_format = ttk.Combobox(step3_frame,
                                            textvariable=self.n_cores,
                                            width=10,
                                            values=['all cores', '2 cores', '3 cores', '4 cores'],
                                            state=['disabled', 'normal'][self.multiprocesses.get()],
                                            font=self.font[1])
        self.menu_out_format.grid(row=0, column=2, padx=4,
                                  pady=4, sticky='w')

        self.progress = ttk.Progressbar(step3_frame,
                                        orient='horizontal')
        self.progress.grid(row=1, column=0, columnspan=4, padx=10,
                           pady=4, sticky='we')

        self.label_progress = tk.Label(step3_frame,
                                       text='',
                                       anchor='center',
                                       font=self.font[0])
        self.label_progress.grid(row=2, column=0, columnspan=4, padx=4,
                                 pady=4, sticky='we')

        step3_frame.pack(padx=10, pady=10, fill=tk.X)

        self.label_version = tk.Label(self.root,
                                      text=self.version,
                                      cursor='hand1',
                                      fg="blue",
                                      font=self.font[0])
        self.label_version.bind("<Button-1>",
                                lambda event: webbrowser.open(
                                    self.version.split()[-1]))
        self.label_version.pack(side=tk.BOTTOM, anchor='e', pady=2, padx=10)

    def start_processing(self):
        """
        After defining all parameters via the interface,
        we prepare variables for the SmartAudioSplitter and
        start processing.
        """

        def worker(multiprocessing_on):
            """
            We run a multiprocessing mode in a thread as an app.
            Tkinter does not allow multiprocessing from a subclass
            (tkinter cannot be pickled )
            """

            app = SmartAudioSplitter(
                full_filename=self.full_filename,
                add_pause=self.add_pause_state.get(),
                pause_len=self.pause_len.get(),
                silence_len=self.silence_len.get(),
                n_split=self.ncut.get(),
                multiprocessing_on=multiprocessing_on,
                n_jobs=self.n_jobs,
                how=self.how,
                out_filename=self.newfilename.get(),
                format_=self.out_format.get(),
                bitrate=self.bitrate.get(),
                store=self.store)
            app.run()

        def progress_bar():
            """
            Tkinter progress bar with a multiprocessing mode
            """

            maximum = None
            works = ''
            while works != 'Done':
                time.sleep(1)
                if (maximum is None and
                        (progress_len := self.store.get('progress_len', False))):
                    maximum = progress_len
                    self.progress['maximum'] = maximum

                if progress_tick := self.store.get('progress_tick', False):
                    self.progress['value'] = progress_tick

                if progress_message := self.store.get('progress_message', False):
                    self.label_progress['text'] = progress_message
                    works = progress_message

                self.root.update()

            self.progress['value'] = self.progress['maximum']

        # set variables

        self.store.clear()

        if self.n_cores.get() == 'all cores':
            self.n_jobs = multiprocessing.cpu_count()
        else:
            self.n_jobs = int(self.n_cores.get().split()[0])

        if self.split_by_silence.get():
            self.how = 'split_by_silence'
        else:
            self.how = 'raw_split'

        if self.multiprocesses.get():
            self.store = multiprocessing.Manager().dict()
        else:
            self.store = dict()

        # start processing
        if mp := self.multiprocesses.get():
            thread_worker = threading.Thread(target=worker, args=(mp,), daemon=True)
            thread_worker.start()

        else:
            thread_worker = threading.Thread(target=worker, args=(mp,), daemon=True)
            thread_worker.start()

        thread_progress = threading.Thread(target=progress_bar, daemon=True)
        thread_progress.start()


if __name__ == '__main__':
    app = SmartAudioSplitterTk()
    app.start()

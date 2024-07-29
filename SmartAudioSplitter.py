import time
import pydub
import re
import subprocess
import concurrent.futures
import multiprocessing
from typing import List, Dict, Tuple


class SmartAudioSplitter:
    """
    SmartAudioSplitter splits large audio files into sections
    by silence, contains audio processing functions based on
    pydub, ffmpeg, ffprobe. There is a multiprocessing mode.

    """

    def __init__(self,
                 full_filename, add_pause=True, pause_len=2000,
                 silence_len=500, level_dBFS='calc',
                 multiprocessing_on=True,
                 n_split=4, n_jobs=2, how='split_by_silence',
                 out_filename='part', format_='mp3', bitrate='128k',
                 tags=None, log_to_file=False, store=None):

        self.full_filename = full_filename
        self.add_pause = add_pause
        self.pause_len = pause_len
        self.silence_len = silence_len
        self.level_dBFS = level_dBFS
        self.n_split = n_split
        self.multiprocessing_on = multiprocessing_on
        self.n_jobs = n_jobs
        self.how = how
        self.out_filename = out_filename
        self.format_ = format_
        self.bitrate = bitrate
        self.tags = tags
        self.log_to_file = log_to_file
        self.version = 'SmartAudioSplitter v1.0 2024 https://github.com/Tikhvinskiy/Smart-audio-splitter.git'

        if store is None:
            if self.multiprocessing_on:
                self.store = multiprocessing.Manager().dict()
            else:
                self.store = dict()
        else:
            self.store = store

    def run(self) -> None:
        """
        Run splitting with the specified parameters
        """

        if self.multiprocessing_on:
            self.multiprocessing_split_pool(
                input_file=self.full_filename,
                n=self.n_split,
                add_pause=self.add_pause,
                pause_len=self.pause_len,
                silence_len=self.silence_len,
                n_jobs=self.n_jobs,
                how=self.how,
                out_filename=self.out_filename,
                format_=self.format_,
                bitrate=self.bitrate,
                tags=self.tags,
                store=self.store)

        else:
            self.processing_pipeline(
                input_file=self.full_filename,
                n=self.n_split,
                add_pause=self.add_pause,
                pause_len=self.pause_len,
                silence_len=self.silence_len,
                how=self.how,
                out_filename=self.out_filename,
                format_=self.format_,
                bitrate=self.bitrate,
                tags=self.tags,
                store=self.store)

    def get_parameters(self, input_file) -> Dict:
        """
        Trying to get parameters of the audio file.
        If pydub is failed, we use 'ffprobe' directly
        """

        try:
            parameters = pydub.utils.mediainfo(input_file)

        except Exception as err:
            print(f'{err}\nTrying ffprobe')
            try:
                args = ('ffprobe',
                        '-show_entries',
                        'format=duration',
                        '-i',
                        input_file)
                popen = subprocess.Popen(args, stdout=subprocess.PIPE)
                popen.wait()
                output = popen.stdout.read()
                duration = re.findall(
                    r'duration=([\d\.]+)', str(output))[0]
                parameters = {'ffprobe_duration': duration}

            except Exception as err:
                raise err

        return parameters

    def calc_list_of_parts(self, n, duration) -> List:
        """
        Calc time intervals to divide into files

        """
        start_time = 0
        chunkc_times = []
        chunk_len = duration / n

        for i in range(n):
            start = chunk_len * i
            chunkc_times.append((start, start + chunk_len))

        return chunkc_times

    def detect_silence(self, chunk, min_silence_len=500,
                       dBFS='calc', store=None) -> float:
        """
        Detect silence in the end of the chunk(last 80%) and return
        middle of this silence time. This time uses for splitting.

        """
        silence = []
        chunk_len = len(chunk)
        time_calc_silence = len(chunk)

        if dBFS == 'calc':
            silence_thresh = int(chunk.dBFS)
            silence_thresh += silence_thresh // 2

        iteration = 0
        while not len(silence):

            if iteration > 2:
                self.progress(store, warning=True,
                              message=f'Detecting silence is difficult. I increase dBFS.')
                silence_thresh -= 0.1 * silence_thresh
                time_calc_silence = chunk_len
                iteration = 0

            time_calc_silence -= chunk_len // (20 - iteration * 3)
            silence = pydub.silence.detect_silence(
                chunk[time_calc_silence:],
                min_silence_len=min_silence_len,
                silence_thresh=silence_thresh)
            iteration += 1

        end_time_chunk = time_calc_silence + sum(silence[-1]) / 2

        return end_time_chunk

    def save_data(self, chunk, n, file_name,
                  format_='mp3', bitrate='128k',
                  tags=None, store=None) -> None:
        """
        Save audio file with params
        """

        if isinstance(store, multiprocessing.managers.DictProxy):
            chunk = store[n]

        if tags is None:
            tags = {'artist': f'{file_name}', 'track': f'Part {n}'}

        if format_ == 'mp3':
            chunk.export(f'{file_name}_{n}',
                         format=format_,
                         bitrate=bitrate,
                         tags=tags)

        elif format_ == 'wav':
            chunk.export(f'{file_name}_{n}',
                         format=format_)

    def processing_pipeline(self, input_file, n,
                            add_pause, pause_len,
                            silence_len, how,
                            out_filename, format_,
                            bitrate, tags, store) -> None:
        """
        - Get duration
        - Calc time intervals
        - Load data by chunks
        - Detect silence
        - Add pause
        - Save file

        """

        # Get duration of audio data
        parameters = self.get_parameters(input_file)
        if 'duration' in parameters:
            duration = float(parameters['duration'])
        elif 'ffprobe_duration' in parameters:
            duration = float(parameters['ffprobe_duration'])

        # Calc time intervals
        chunks_times = self.calc_list_of_parts(n, duration)

        # Calc the total number of tasks
        len_all_tasks = n + n + n * add_pause + n

        # Save progress
        self.progress(store, set_max=True, maximum=len_all_tasks)

        # Load data by chunks
        to_next_chunk = []
        for i, (start, end) in enumerate(chunks_times, start=1):
            print(m := (f'\rProcessing part {i} '
                        f'(load audio data)'), end=' ' * 20)
            self.progress(store, tick=1, message=m[1:])

            start_second = start - len(to_next_chunk) / 1000

            if i == n:
                duration = end
            else:
                duration = end - start_second

            chunk = pydub.AudioSegment.from_file(
                input_file,
                start_second=start_second,
                duration=duration)

            if how == 'split_by_silence':
                print(m := (f'\rProcessing part {i} '
                            f'(split by silence)'), end=' ' * 20)
                self.progress(store, tick=1, message=m[1:])

                end_time_chunk = self.detect_silence(
                    chunk,
                    min_silence_len=silence_len,
                    dBFS=self.level_dBFS,
                    store=store)

                to_next_chunk = chunk[end_time_chunk:]
                chunk = chunk[:end_time_chunk]

            if add_pause:
                print(m := (f'\rProcessing part {i} '
                            f'(add pause)'), end=' ' * 20)
                self.progress(store, tick=1, message=m[1:])

                silents = pydub.AudioSegment.silent(duration=pause_len)
                chunk = silents.append(chunk)
                chunk = chunk.append(silents)

            print(m := (f'\rProcessing part {i} '
                        f'(save audio data)'), end=' ' * 20)
            self.progress(store, tick=1, message=m[1:])

            self.save_data(chunk, i,
                           file_name=out_filename,
                           format_=format_,
                           bitrate=bitrate,
                           tags=tags)

        self.progress(store, tick=1, message='Done')

    def multiprocessing_task_load_save(self, input_file,
                                       start, end,
                                       i, store) -> None:
        """
        The Task for the multiprocessing pool
        Loads and save data.

        """

        start_second = start
        duration = end - start_second
        chunk = pydub.AudioSegment.from_file(
            input_file,
            start_second=start_second,
            duration=duration)

        store[i] = chunk

    def multiprocessing_task_split_by_silence(self, input_file1,
                                              input_file2,
                                              min_silence_len,
                                              store) -> None:
        """
        The Task for the multiprocessing pool
        Split by silence two parts

        """
        chunk1 = store[input_file1]
        chunk2 = store[input_file2]

        end_time_chunk = self.detect_silence(
            chunk1,
            min_silence_len=min_silence_len,
            dBFS=self.level_dBFS,
            store=store)

        to_next_chunk = chunk1[end_time_chunk:]
        chunk1 = chunk1[:end_time_chunk]
        chunk2 = to_next_chunk.append(chunk2)

        store[input_file1] = chunk1
        store[input_file2] = chunk2

    def multiprocessing_task_add_pauses(self, input_file,
                                        pause, store) -> None:
        """
        The Task for the multiprocessing pool
        Add pauses to the audio data and save
        """

        chunk = store[input_file]
        chunk = pause.append(chunk)
        chunk = chunk.append(pause)
        store[input_file] = chunk

    def calc_tasks_for_pool(self, number_of_files) -> Tuple[List, List]:
        """
        Calculate sequence of tasks for multiprocessing pool.
        We need two consecutive dependent iterations
        """

        if number_of_files == 2:
            iteration1 = [[1, 2]]
            iteration2 = []

            return iteration1, iteration2

        elif number_of_files == 3:
            iteration1 = [[1, 2]]
            iteration2 = [[2, 3]]

            return iteration1, iteration2

        else:
            left = number_of_files % 2
            end = number_of_files - left
            start = 1
            tasks = {'iteration_1': [], 'iteration_2': []}
            for start in [1, 2]:
                for i in range(start, end + 1, 2):
                    tasks[f'iteration_{start}'].append([i, i + 1])
                end -= 1

            if left:
                tasks[f'iteration_2'].append([i + 2, i + 3])

            return tasks['iteration_1'], tasks['iteration_2']

    def progress(self, store, set_max=False, maximum=100,
                 tick=0, message='', warning=False) -> None:
        """
        Progress bar / logger
        """

        if set_max:
            store['progress_len'] = maximum
            store['progress_tick'] = 1

        if not warning and (old_tick := store.get('progress_tick', False)):
            store['progress_tick'] = old_tick + tick

        if warning:
            store['progress_message'] = f'WARNING: {message}'
        else:
            store['progress_message'] = message

        if self.log_to_file:
            with open('info.log', 'a') as f:
                progress_len = store.get('progress_len', None)
                progress_tick = store.get('progress_tick', None)
                progress_message = store.get('progress_message', None)
                f.write(
                    (f'{time.ctime()} {progress_len=}, '
                     f'{progress_tick=}, '
                     f'{progress_message=}\n'))

    def multiprocessing_split_pool(self, input_file,
                                   n, add_pause, pause_len, silence_len,
                                   n_jobs, how, out_filename, format_,
                                   bitrate, tags, store) -> None:
        """
        Processing data with the multiprocessing pools:
        - Get duration
        - Calc time intervals
        - Load data by chunks pool
        - Detect silence pool(2 iteration)
        - Add pause pool
        - Save file pool

        """

        # Get duration of audio data
        parameters = self.get_parameters(input_file)
        if 'duration' in parameters:
            duration = float(parameters['duration'])
        elif 'ffprobe_duration' in parameters:
            duration = float(parameters['ffprobe_duration'])

        # Calc time intervals
        chunks_times = self.calc_list_of_parts(n, duration)

        if how == 'raw_split':
            # calc the total number of tasks
            len_all_tasks = n + n * add_pause + n

            # save progress
            self.progress(store, set_max=True, maximum=len_all_tasks)

            # split audio into N equal parts
            with concurrent.futures.ProcessPoolExecutor(max_workers=n_jobs) as pool:

                futures = {}
                for i, (start, end) in enumerate(chunks_times, start=1):
                    futures[pool.submit(self.multiprocessing_task_load_save,
                                        input_file, start, end, i, store)] = (i, (start, end))

                for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    if (exception := future.exception()) is not None:
                        print(f'{futures[future]}. An error was raised({exception}).\n')
                        self.progress(store, message=exception, warning=True)

                    print(m := (f'\rProcessing task {i} of {len_all_tasks} '
                                f'(pool prepare audio data)'), end=' ' * 20)
                    self.progress(store, tick=1, message=m[1:])
                last_iter = i

        elif how == 'split_by_silence':

            # calc the total number of tasks
            iteration_1, iteration_2 = self.calc_tasks_for_pool(n)
            len_all_tasks = (n + len(iteration_1) +
                             len(iteration_2) + n * add_pause + n)

            # save progress
            self.progress(store, set_max=True, maximum=len_all_tasks)

            # load and split data by chunks
            with concurrent.futures.ProcessPoolExecutor(max_workers=n_jobs) as pool:

                futures = {}
                for i, (start, end) in enumerate(chunks_times, start=1):
                    futures[pool.submit(self.multiprocessing_task_load_save,
                                        input_file,
                                        start, end,
                                        i, store)] = (i, (start, end))

                for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    if (exception := future.exception()) is not None:
                        print(f'{futures[future]}. An error was raised({exception}).\n')
                        self.progress(store, message=exception, warning=True)

                    print(m := (f'\rProcessing task {i} of {len_all_tasks} '
                                f'(pool prepare audio data)'), end=' ' * 20)
                    self.progress(store, tick=1, message=m[1:])
                last_iter = i

            # split by silence
            # do iteration 1 after completing load and split data by chunks
            with concurrent.futures.ProcessPoolExecutor(max_workers=n_jobs) as pool:

                futures = {}
                for task in iteration_1:
                    futures[pool.submit(self.multiprocessing_task_split_by_silence,
                                        task[0], task[1], silence_len, store)] = (task[0], task[1])

                for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    if (exception := future.exception()) is not None:
                        print(f'{futures[future]}. An error was raised({exception}).\n')
                        self.progress(store, message=exception, warning=True)

                    print(m := (f'\rProcessing task {last_iter + i} of {len_all_tasks} '
                                f'(pool split by silence iteration 1)'), end=' ' * 20)
                    self.progress(store, tick=1, message=m[1:])
                last_iter += i

                # do iteration 2 after completing iteration 1
            with concurrent.futures.ProcessPoolExecutor(max_workers=n_jobs) as pool:
                futures = {}
                for task in iteration_2:
                    futures[pool.submit(self.multiprocessing_task_split_by_silence,
                                        task[0], task[1], silence_len, store)] = (task[0], task[1])

                for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    if (exception := future.exception()) is not None:
                        print(f'{futures[future]}. An error was raised({exception}).\n')
                        self.progress(store, message=exception, warning=True)

                    print(m := (f'\rProcessing task {last_iter + i} of {len_all_tasks} '
                                f'(pool split by silence iteration 2)'), end=' ' * 20)
                    self.progress(store, tick=1, message=m[1:])
                last_iter += i

        # add pauses after 'raw_split' or 'split_by_silence'
        if add_pause:

            silents = pydub.AudioSegment.silent(duration=pause_len)
            with concurrent.futures.ProcessPoolExecutor(max_workers=n_jobs) as pool:

                futures = {}
                for i in range(1, n + 1):
                    futures[pool.submit(self.multiprocessing_task_add_pauses,
                                        i, silents, store)] = i

                for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    if (exception := future.exception()) is not None:
                        print(f'{futures[future]}. An error was raised({exception}).\n')
                        self.progress(store, message=exception, warning=True)

                    print(m := (f'\rProcessing task {last_iter + i} of {len_all_tasks} '
                                f'(pool add pause)'), end=' ' * 20)
                    self.progress(store, tick=1, message=m[1:])
                last_iter += i

        # save audio data to files for 'raw_split' or 'split_by_silence'
        with concurrent.futures.ProcessPoolExecutor(max_workers=n_jobs) as pool:
            futures = {}
            for i in range(1, n + 1):
                futures[pool.submit(
                    self.save_data,
                    chunk=None, n=i, file_name=out_filename,
                    format_=format_, bitrate=bitrate, tags=tags,
                    store=store)] = i

            for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                if (exception := future.exception()) is not None:
                    print(f'{futures[future]}. An error was raised({exception}).\n')
                    self.progress(store, message=exception, warning=True)

                print(m := (f'\rProcessing task {last_iter + i} of {len_all_tasks} '
                            f'(pool save audio data)'), end=' ' * 20)
                self.progress(store, tick=1, message=m[1:])

        self.progress(store, message='Done')

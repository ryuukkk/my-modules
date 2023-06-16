import collections
import hashlib
import optparse
import os
import queue
import threading


def parse_options():
    parser = optparse.OptionParser(usage=("usage: %prog [options] word name1 "
                                          "[name2 [... nameN]]\n\n"
                                          "names are filenames or paths; paths only "
                                          "make sense with the -r option set"))
    parser.add_option('-p', '--processes', dest='count', default=7, type='int', help=("the number of child processes "
                                                                                      "to use (1..20)"
                                                                                      "[default %default]"))
    parser.add_option('-r', '--recurse', dest='recurse', default=False, action='store_true', help='recurse into '
                                                                                                  'subdirectories')
    opts, args = parser.parse_args()

    if len(args) == 0:
        parser.error('enter at least one filename')

    if not opts.recurse and not any([os.path.isfile(arg) for arg in args]):
        parser.error('at least one file must be specified')
    if not (1 <= opts.count <= 20):
        parser.error('process count must be between 1 and 20')

    return opts, args

class Worker(threading.Thread):

    Md5_lock = threading.Lock()
    def __init__(self, work_queue, md5_from_filename, result_queue):
        super().__init__()
        self.work_queue = work_queue
        self.md5_from_filename = md5_from_filename
        self.result_queue = result_queue

    def run(self):
        while True:
            try:
                size, names = self.work_queue.get()
                self.process(size,names)
            finally:
                self.work_queue.task_done()

    def process(self, size, names):
        md5s = collections.defaultdict(set)
        for file in names:
            with self.Md5_lock:
                md5 = self.md5_from_filename.get(file, None)
            if md5 is not None:
                md5s[md5].add(file)
            else:
                try:
                    hash = hashlib.md5()
                    with open(file, 'rb') as fh:
                        hash.update(fh.read())
                    md5 = hash.digest()
                    md5s[md5].add(file)
                    with self.Md5_lock:
                        self.md5_from_filename[file] = md5
                except EnvironmentError:
                    continue

        for file in md5s.values():
            if len(file) == 1:
                continue
            self.result_queue.put(file)

def main():
    opts, path = parse_options()
    data = collections.defaultdict(list)
    for root, dirs, files in os.walk(path):
        for file in files:
            fullname = os.path.join(root, file)
            try:
                key = (os.path.getsize(fullname), file)
            except EnvironmentError:
                continue
            if key[0] == 0:
                continue
            data[key].append(fullname)

    work_queue = queue.PriorityQueue()
    result_queue = queue.Queue()
    md5_from_filename = {}
    for i in range(opts.count):
        worker = Worker(work_queue, md5_from_filename, result_queue)
        worker.daemon = True
        worker.start()

    result_thread = threading.Thread(target=lambda: print_results(result_queue))
    result_thread.daemon = True
    result_thread.start()

    def print_results(result_queue):
        results = result_queue.get()
        try:
            if results:
                print(results)
        finally:
            result_queue.task_done()
import optparse
import os
import queue
import threading

BLOCK_SIZE = 8000


def main():
    opts, word, args = parse_options()
    filelist = get_files(args, opts.recurse)
    work_queue = queue.Queue()
    for i in range(opts.count):
        worker = Worker(work_queue, word)
        worker.daemon = True
        worker.start()
    for file in filelist:
        work_queue.put(file)
    work_queue.join()  # waits until all non-daemon threads have finished.


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
        parser.error('enter the word to find')
    elif len(args) == 1:
        parser.error('enter at least one filename')
    if not opts.recurse and not any([os.path.isfile(arg) for arg in args]):
        parser.error('at least one file must be specified')
    if not (1 <= opts.count <= 20):
        parser.error('process count must be between 1 and 20')

    return opts, args[0], args[1:]


def get_files(args, recurse):
    filelist = []
    for path in args:
        if os.path.isfile(path):
            filelist.append(path)
        elif recurse:
            for root, dirs, files in os.walk(path):
                for file in files:
                    filelist.append(os.path.join(root, file))
    return filelist


class Worker(threading.Thread):
    def __init__(self, work_queue, word):
        super().__init__()
        self.work_queue = work_queue
        self.word = word

    def run(self) -> None:
        while True:
            try:
                filename = self.work_queue.get()
                self.process(filename)
            finally:
                self.work_queue.task_done()  # task_done() tells main that the current file has been processed.

    def process(self, filename):
        previous = ""
        try:
            with open(filename, "rb") as fh:
                while True:
                    current = fh.read(BLOCK_SIZE)
                    if not current:
                        break
                    current = current.decode("utf8", "ignore")
                    if (self.word in current or
                            self.word in previous[-len(self.word):] +
                            current[:len(self.word)]):
                        print("{0}".format(filename))
                        break
                    if len(current) != BLOCK_SIZE:
                        break
                    previous = current
        except EnvironmentError as err:
            print("{0}".format(err))

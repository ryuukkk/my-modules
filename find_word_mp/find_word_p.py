import optparse
import os.path
import subprocess
import sys


def main():
    child = os.path.join(os.path.dirname(__file__), 'find_word_c.py')
    opts, word, args = parse_options()
    filelist = get_files(args, opts.recurse)
    file_per_process = len(filelist) // opts.count
    start, end = 0, file_per_process + (len(filelist) % opts.count)

    pipes = []
    while start < len(filelist):
        command = [sys.executable, child]
        pipe = subprocess.Popen(command, stdin=subprocess.PIPE)
        pipes.append(pipe)
        pipe.stdin.write(word.encode('utf-8') + b'\n')
        for file in filelist[start:end]:
            pipe.stdin.write(file.encode('utf-8') + b'\n')
        pipe.stdin.close()
        start, end = end, end + file_per_process

    while pipes:
        pipe = pipes.pop()
        pipe.wait()


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

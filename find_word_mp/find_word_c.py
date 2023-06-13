import sys

BLOCK_SIZE = 8000

stdin = sys.stdin.buffer.read()
lines = stdin.decode('utf-8', 'ignore').splitlines()
word = lines[0].strip()

for filename in lines[1:]:
    filename = filename.rstrip()
    previous = ''
    try:
        with open(filename, 'rb') as fh:
            while True:
                current = fh.read(BLOCK_SIZE)
                if not current:
                    break
                current = current.decode('utf8', 'ignore')
                if word in current or word in previous[-len(word):] + current[:len(word)]:
                    print(filename)
                    break
                if len(current) != BLOCK_SIZE:
                    break
                previous = current
    except EnvironmentError as err:
        print(err, filename)

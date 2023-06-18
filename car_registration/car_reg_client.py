import collections
import pickle
import socket
import struct
import sys

Address = ['localhost', 9653]
CarTuple = collections.namedtuple("CarTuple", "seats mileage owner")


def main():
    if len(sys.argv) > 1:
        Address[0] = sys.argv[1]
    call = dict(c=get_car_details, m=change_mileage, o=change_owner, n=new_registration, s=stop_server, q=quit)
    message = ("(C)ar\n  Edit (M)ileage\n  Edit (O)wner\n  (N)ew car\n  "
               "(S)top server\n  (Q)uit")
    valid = frozenset('cmonsq')
    previous_license = None

    while True:
        action = input(message)
        if action not in valid:
            print('Wrong input')
            continue
        previous_license = call[action](previous_license)


def get_car_details(previous_license):
    license, car = retrieve_car(previous_license)
    if car:
        print("License: {0}\nSeats:   {seats}\nMileage: {mileage}\n"
              "Owner:   {owner}".format(license, **car._asdict()))
    return license


def retrieve_car(previous_license):
    license = input('Enter license number: ')
    if not license:
        return previous_license, None
    license = license.upper()
    ok, *data = handle_request('GET_CAR_DETAILS', license)
    if not ok:
        print(data[0])
        return previous_license, None
    return license, CarTuple(*data)


def change_mileage(previous_license):
    license, car = retrieve_car(previous_license)
    if car is None:
        return previous_license
    mileage = input('Enter Mileage: ')
    if mileage == 0:
        return license
    ok, *data = handle_request('CHANGE_MILEAGE', license, mileage)
    if not ok:
        print(data[0])
    else:
        print('Mileage changed')
    return license


def change_owner(previous_license):
    license, car = retrieve_car(previous_license)
    if car is None:
        return previous_license
    owner = input('Enter owner({0}): '.format(car.owner))
    ok, *data = handle_request('CHANGE_OWNER', license, owner)
    if not ok:
        print(data[0])
    else:
        print('owner changed to {0}'.format(owner))
    return license


def new_registration(previous_license):
    license = input('Enter license: ')
    mileage = input('Enter mileage: ')
    owner = input('Enter owner: ')
    seats = input('Enter seats: ')
    ok, *data = handle_request('NEW_REGISTRATION', license, seats, mileage, owner)
    if not ok:
        print(data[0])
    else:
        print('Registered {0}'.format(license))
    return license


def quit(*ignore):
    sys.exit()


def stop_server(*ignore):
    handle_request('SHUTDOWN', wait_for_reply=False)
    sys.exit()


def handle_request(*items, wait_for_reply=True):
    SizeStruct = struct.Struct('!I')
    data = pickle.dumps(items, 3)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(tuple(Address))
            sock.sendall(SizeStruct.pack(len(data)))
            sock.sendall(data)

            if not wait_for_reply:
                return

            size = SizeStruct.unpack(sock.recv(SizeStruct.size))[0]
            result = bytearray()
            while True:
                data = sock.recv(4000)
                if not data:
                    break
                result.extend(data)
                if len(result) > size:
                    break
                return pickle.loads(result)
    except socket.error as err:
        print(err)
        sys.exit(1)

main()
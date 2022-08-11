from time import sleep
from pyftdi.jtag import JtagEngine, JtagTool
from pyftdi.bits import BitSequence
from pyftdi.ftdi import Ftdi
from os import environ
import argparse

INSTR = {
    'IR_ADDR_16BIT': BitSequence(0x83, msb=False, length=8),
    'IR_ADDR_CAPTURE': BitSequence(0x84, msb=False, length=8),
    'IR_DATA_TO_ADDR': BitSequence(0x85, msb=False, length=8),
    'IR_DATA_16BIT': BitSequence(0x41, msb=False, length=8),
    'IR_DATA_QUICK': BitSequence(0x43, msb=False, length=8),
    'IR_BYPASS': BitSequence(0xFF, msb=False, length=8),
    'IR_CNTRL_SIG_16BIT': BitSequence(0x13, msb=False, length=8),
    'IR_CNTRL_SIG_CAPTURE': BitSequence(0x14, msb=False, length=8),
    'IR_CNTRL_SIG_RELEASE': BitSequence(0x15, msb=False, length=8),
    'IR_DATA_PSA': BitSequence(0x44, msb=False, length=8),
    'IR_SHIFT_OUT_PSA': BitSequence(0x46, msb=False, length=8),
    'IR_JMB_EXCHANGE': BitSequence(0x61, msb=False, length=8),
}


def set_tckl():
    if jtag.state_machine.state() != jtag.state_machine['run_test_idle']:
        jtag.change_state('run_test_idle')
    jtag._ctrl._ftdi.write_data(
        bytearray((Ftdi.SET_BITS_LOW, 0x1, jtag._ctrl.direction)))  # set pin TCK high
    jtag._ctrl._ftdi.write_data(bytearray(
        (Ftdi.SET_BITS_LOW, 0x2 | 0x1, jtag._ctrl.direction)))  # set pin TDI and TCK high
    sleep(0.01)
    jtag._ctrl._ftdi.write_data(bytearray(
        (Ftdi.SET_BITS_LOW, 0x2, jtag._ctrl.direction)))  # set pin 4 TDI high and TCK low
    sleep(0.01)


def clear_tckl():
    if jtag.state_machine.state() != jtag.state_machine['run_test_idle']:
        jtag.change_state('run_test_idle')
    jtag._ctrl._ftdi.write_data(
        bytearray((Ftdi.SET_BITS_LOW, 0x1, jtag._ctrl.direction)))  # set pin TCK high
    sleep(0.01)
    jtag._ctrl._ftdi.write_data(
        bytearray((Ftdi.SET_BITS_LOW, 0, jtag._ctrl.direction)))
    sleep(0.01)


def custom_reset():
    jtag.write_tms(BitSequence('111111'))
    jtag._ctrl._ftdi.write_data(
        bytearray((Ftdi.SET_BITS_LOW, 0x1, jtag._ctrl.direction)))  # set pin TCK high
    sleep(0.1)

    for i in range(0, 2):
        jtag._ctrl._ftdi.write_data(bytearray(
            (Ftdi.SET_BITS_LOW, 0x2 | 0x1, jtag._ctrl.direction)))  # set pin TDI and TCK high
        sleep(0.5)
        jtag._ctrl._ftdi.write_data(bytearray(
            (Ftdi.SET_BITS_LOW, 0x2 | 0x1 | 0x08, jtag._ctrl.direction)))  # set pin TDI, TCK and TMS high
        sleep(0.5)

    jtag._ctrl._ftdi.write_data(bytearray(
        (Ftdi.SET_BITS_LOW, 0x2 | 0x1, jtag._ctrl.direction)))  # set pin TDI and TCK high
    sleep(0.5)
    jtag._ctrl._ftdi.write_data(
        bytearray((Ftdi.SET_BITS_LOW, 0x2, jtag._ctrl.direction)))
    jtag.state_machine._current = jtag.state_machine['run_test_idle']


def get_device():
    jtag.write_ir(INSTR['IR_CNTRL_SIG_16BIT'])  # IR_CNTRL_SIG_16BIT
    jtag.write_dr(BitSequence(0x2401, msb=True, length=16))
    jtag.write_ir(INSTR['IR_CNTRL_SIG_CAPTURE'])  # IR_CNTRL_SIG_CAPTURE

    # loop 1000 times
    for i in range(1000):
        data = jtag.read_dr(16)
        print("Register CNTRL value: " + str(data))
        if data[15-9] == 1:
            if data == BitSequence(0xFFFF, msb=True, length=16):
                raise Exception(
                    'returned invalid register data, reset the device or check the connection')
            print('Found device')
            return

    raise Exception('Cant syncronize with device')


def disconnect():
    jtag.write_ir(INSTR['IR_CNTRL_SIG_16BIT'])
    jtag.write_dr(BitSequence(0x2C01, msb=True, length=16))
    jtag.write_dr(BitSequence(0x2401, msb=True, length=16))
    jtag.write_ir(INSTR['IR_CNTRL_SIG_RELEASE'])
    clear_tckl()
    set_tckl()
    clear_tckl()
    jtag._ctrl._ftdi.write_data(
        bytearray((Ftdi.SET_BITS_LOW, 0x0, jtag._ctrl.direction)))


def set_instruction_fetch():
    jtag.write_ir(INSTR['IR_CNTRL_SIG_CAPTURE'])
    for i in range(7):
        data = jtag.read_dr(16)
        print("Register CNTRL value: " + str(data))
        if data[15-7] == 1:
            print('CPU is in instruction fetch stage')
            return
        clear_tckl()
        set_tckl()
    raise Exception('Cant put CPU in instruction fetch stage')


def set_pc(address):
    set_instruction_fetch()
    jtag.write_ir(INSTR['IR_CNTRL_SIG_16BIT'])
    jtag.write_dr(BitSequence(0x3401, msb=True, length=16))
    jtag.write_ir(INSTR['IR_DATA_16BIT'])
    jtag.write_dr(BitSequence(0x4030, msb=True, length=16))
    clear_tckl()
    set_tckl()
    jtag.write_dr(BitSequence(address, msb=True, length=16))
    clear_tckl()
    set_tckl()
    jtag.write_ir(INSTR['IR_ADDR_CAPTURE'])
    clear_tckl()
    jtag.write_ir(INSTR['IR_CNTRL_SIG_16BIT'])
    jtag.write_dr(BitSequence(0x2401, msb=True, length=16))


def stop_start_cpu(stop=True):
    if stop:
        set_instruction_fetch()
        jtag.write_ir(INSTR['IR_DATA_16BIT'])
        jtag.write_dr(BitSequence(0x3FFF, msb=True, length=16))

    clear_tckl()
    jtag.sync()
    jtag.write_ir(INSTR['IR_CNTRL_SIG_16BIT'])
    jtag.write_dr(BitSequence(0x2409 if stop else 0x2401, msb=True, length=16))
    if not stop:
        jtag.write_ir(INSTR['IR_ADDR_CAPTURE'])
    set_tckl()


def read_words(address, length) -> list:
    clear_tckl()
    jtag.write_ir(INSTR['IR_CNTRL_SIG_16BIT'])
    jtag.write_dr(BitSequence(0x2409, msb=True, length=16))

    result = []
    for i in range(address, address + length, 2):
        jtag.write_ir(INSTR['IR_ADDR_16BIT'])
        jtag.write_dr(BitSequence(i, msb=True, length=16))
        jtag.write_ir(INSTR['IR_DATA_TO_ADDR'])
        set_tckl()
        clear_tckl()
        result.append(jtag.read_dr(16))

    return result


def quick_read_words(length) -> list:
    clear_tckl()
    jtag.write_ir(INSTR['IR_CNTRL_SIG_16BIT'])
    jtag.write_dr(BitSequence(0x2409, msb=True, length=16))
    jtag.write_ir(INSTR['IR_DATA_QUICK'])

    result = []
    for i in range(length):
        set_tckl()
        result.append(jtag.read_dr(16))
        clear_tckl()
    return result

parser = argparse.ArgumentParser(description='Dump a memory region')
parser.add_argument('-d', '--device', help='Device URI (see https://eblot.github.io/pyftdi/urlscheme.html)',
                    default='ftdi://ftdi:2232h/1')
parser.add_argument('addr', help='Address to start dumping', type=int)
parser.add_argument('length', help='Length of memory to dump', type=int)
parser.add_argument('-o', '--output', help='Output file', default='dump.bin')
parser.add_argument('-q', '--quick', help='Use quick read', type=bool, default=False)
args = parser.parse_args()

print("Dumping from 0x{:x} to 0x{:x}".format(args.addr, args.addr+args.length))

url = environ.get('FTDI_DEVICE', args.device)
jtag = JtagEngine(trst=False, frequency=3E6)
jtag.configure(url)


# jtag.reset()
custom_reset()
get_device()

if args.quick:
    set_pc(args.addr -4)
stop_start_cpu(True)

data = quick_read_words(args.length) if args.quick else read_words(args.addr, args.length)

# open file to write data to
print("Writing dump to {}".format(args.output))
with open(args.output, 'w+b') as f:
    for i in data:
        bytes = i.tobytes(True, True)
        f.write(bytes)


stop_start_cpu(False)
disconnect()

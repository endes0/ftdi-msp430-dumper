# MSP430 JTAG DUMPER

This script dumps a MSP430 mcu memory location using the jtag interface with a FTDI adapter.

**Warning: This script should only works with the 1xx, 2xx, 3xx with the 4 jtag pins (no SBW). By the moment, it was only tested with the MSP430F24x.**

## Usage

```bash
$ python3 dumper.py -h
usage: dumper.py [-h] [-d DEVICE] [-o OUTPUT] [-q QUICK] addr length

Dump a memory region

positional arguments:
  addr                  Address to start dumping
  length                Length of memory to dump

options:
  -h, --help            show this help message and exit
  -d DEVICE, --device DEVICE
                        Device URI (see https://eblot.github.io/pyftdi/urlscheme.html)
  -o OUTPUT, --output OUTPUT
                        Output file
  -q QUICK, --quick QUICK
                        Use quick read
```

### Requirements

```bash
$ pip install requirements.txt
```

### Slow dump

```bash
$ python3 dumper.py <start address in decimal> <lenght in decimal>
```

example dumping from **0x8000** to **0x8100**:

```bash
$ python3 dumper.py 32768 256
```

### Quick dumping

**Warning: There is a bug in this dumping that always start at the same address, altrought you specify another address.**

```bash
$ python3 dumper.py -q <start address in decimal> <lenght in decimal>
```

## TODO

- [ ] Better abstraction

- [ ] Add support to MSP430X

- [ ] Add support to the 4xx and 5xx series

- [ ] Add support to SBW



Reference used: https://www.ti.com/lit/ug/slau320aj/slau320aj.pdf

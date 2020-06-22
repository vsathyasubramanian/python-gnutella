# Python Gnutella

A simple Gnutella-like file sharing protocol tool with a command line interface

## Requirements

Python version > 3.6

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the required additional packages. All the required additional packages are available in requirements.txt

PyInquirer
pyfiglet
tabulate

```bash
pip -r /tmp/requirements.txt
```

## Usage

By default this script runs in local host 127.0.0.1. If we choose to change the IP address , we can change the same in /src/variable.py

```bash
python /src/servent.py <<port no>>
```

To connect to another node running in the same network or another network, enter the relevant node ip address and port number through the CLI

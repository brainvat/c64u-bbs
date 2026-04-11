# c64u-bbs

Deploy and manage a Commodore 64 BBS on the C64 Ultimate — over the network, no SD cards.

## Requirements

- Python 3.10+
- Git
- A C64 Ultimate (Ultimate 64 or Ultimate-II+) on your local network

## Setup

```bash
# Clone and install
git clone https://github.com/brainvat/c64u-bbs.git
cd c64u-bbs
bash install.sh          # or: bash install.sh --dev (includes test tools)

# Activate the environment
source venv/bin/activate

# Connect to your C64U
c64u --host <your-c64u-ip> info
```

## Documentation

Full documentation: [brainvat.github.io/c64u-bbs](https://brainvat.github.io/c64u-bbs/)

## Repository

[github.com/brainvat/c64u-bbs](https://github.com/brainvat/c64u-bbs)

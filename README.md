# inventory-keeper

[![Build Status](https://travis-ci.org/makerdao/inventory-keeper.svg?branch=master)](https://travis-ci.org/makerdao/inventory-keeper)
[![codecov](https://codecov.io/gh/makerdao/inventory-keeper/branch/master/graph/badge.svg)](https://codecov.io/gh/makerdao/inventory-keeper)

The _DAI Stablecoin System_ incentivizes external agents, called _keepers_,
to automate certain operations around the Ethereum blockchain.

`inventory-keeper` is a TODO TODO TODO.

<https://chat.makerdao.com/channel/keeper>


## Installation

This project uses *Python 3.6.2*.

In order to clone the project and install required third-party packages please execute:
```
git clone https://github.com/makerdao/inventory-keeper.git
git submodule update --init --recursive
pip3 install -r requirements.txt
```

For some known macOS issues see the [pymaker](https://github.com/makerdao/pymaker) README.

## Configuration

TODO

Sample configuration file:

```json
TODO
```

### Referencing environment variables

TODO


## Usage

```
usage: inventory-keeper [-h] [--rpc-host RPC_HOST] [--rpc-port RPC_PORT]
                        --config CONFIG [--gas-price GAS_PRICE]
                        [--gas-price-increase GAS_PRICE_INCREASE]
                        [--gas-price-increase-every GAS_PRICE_INCREASE_EVERY]
                        [--gas-price-max GAS_PRICE_MAX]
                        [--gas-price-file GAS_PRICE_FILE]
                        [--inventory-dump-file INVENTORY_DUMP_FILE]
                        [--inventory-dump-interval INVENTORY_DUMP_INTERVAL]
                        [--debug]

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
  --config CONFIG       Inventory configuration file
  --gas-price GAS_PRICE
                        Gas price (in Wei)
  --gas-price-increase GAS_PRICE_INCREASE
                        Gas price increase (in Wei) if no confirmation within
                        `--gas-price-increase-every` seconds
  --gas-price-increase-every GAS_PRICE_INCREASE_EVERY
                        Gas price increase frequency (in seconds, default:
                        120)
  --gas-price-max GAS_PRICE_MAX
                        Maximum gas price (in Wei)
  --gas-price-file GAS_PRICE_FILE
                        Gas price configuration file
  --inventory-dump-file INVENTORY_DUMP_FILE
                        File the keeper will periodically write the inventory
                        dump to
  --inventory-dump-interval INVENTORY_DUMP_INTERVAL
                        Frequency of writing the inventory dump file (in
                        seconds, default: 30)
  --debug               Enable debug output
```


## License

See [COPYING](https://github.com/makerdao/inventory-keeper/blob/master/COPYING) file.

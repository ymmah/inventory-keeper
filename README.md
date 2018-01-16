# inventory-keeper

[![Build Status](https://travis-ci.org/makerdao/inventory-keeper.svg?branch=master)](https://travis-ci.org/makerdao/inventory-keeper)
[![codecov](https://codecov.io/gh/makerdao/inventory-keeper/branch/master/graph/badge.svg)](https://codecov.io/gh/makerdao/inventory-keeper)

The _DAI Stablecoin System_ incentivizes external agents, called _keepers_,
to automate certain operations around the Ethereum blockchain.

`inventory-keeper` is a responsible for maintaining appropriate ETH and token balances
across a set of accounts, which will usually belong to token-hungry bots like market makers
(see <https://github.com/makerdao/market-maker-keeper>).

ETH and tokens are being distributed to and from a `base` account. For each bot (`member`)
a list of tokens its provided for which the `inventory-keeper` will be managing balances.
Keeper will aim to keep the balance within the `minAmount` - `maxAmount`, range bringing
it back to `avgAmount` if it goes out of this range. Keeper is also fine if only one side
of the range is defined. If no range is defined, the keeper will only monitor the balance
(include it in the inventory dump file), but will not adjust it.

If the `--inventory-dump-file` argument is present, the keeper will periodically save
a table with all accounts and their token balances to that file. This file may then be
monitored by the `watch` command for example.

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

Sample configuration file:

```json
{
  "tokens": {
    "ETH": "0x0000000000000000000000000000000000000000",
    "WETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    "0WETH": "0x2956356cD2a2bf3202F771F50D3D14A367b48070",
    "DAI": "0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359"
  },
  "base": {
    "name": "Some base account",
    "type": "ethereum-account",
    "address": "0x0012121212001212121200121212120012121212"
  },
  "members": [
    {
      "name": "Some Oasis market maker keeper",
      "type": "oasis-market-maker-keeper",
      "config": {
        "oasisAddress": "0x0034343434003434343400343434340034343434",
        "marketMakerAddress": "0x0034343434003434343400343434340034343434"
      },
      "tokens": {
        "ETH": {
          "minAmount": 1.0,
          "avgAmount": 5.0
        },
        "WETH": {
          "minAmount": 0.5,
          "avgAmount": 3.0,
          "maxAmount": 5.0
        },
        "DAI": {
          "minAmount": 0.5,
          "avgAmount": 3.0,
          "maxAmount": 5.0
        }
      }
    },
    {
      "name": "Some EtherDelta market maker keeper",
      "type": "etherdelta-market-maker-keeper",
      "config": {
        "etherDeltaAddress": "0x0054545345005454534500545453450054545345",
        "marketMakerAddress": "0x0054545345005454534500545453450054545345"
      },
      "tokens": {
        "ETH": {
          "minAmount": 1.0,
          "avgAmount": 5.0,
          "maxAmount": 5.0
        },
        "DAI": {
          "minAmount": 0.5,
          "avgAmount": 3.0,
          "maxAmount": 5.0
        }
      }
    },
    {
      "name": "Some RadarRelay market maker keeper",
      "type": "radarrelay-market-maker-keeper",
      "config": {
        "marketMakerAddress": "0x0002198600021986000219860002198600021986"
      },
      "address": "",
      "tokens": {
        "ETH": {
          "minAmount": 1.0,
          "avgAmount": 5.0
        },
        "0WETH": {
          "minAmount": 0.5,
          "avgAmount": 3.0,
          "maxAmount": 5.0
        },
        "DAI": {
          "minAmount": 0.5,
          "avgAmount": 3.0,
          "maxAmount": 5.0
        }
      }
    },
    {
      "name": "Some Bibox market maker keeper",
      "type": "bibox-market-maker-keeper",
      "config": {
        "apiKey": "$BIBOX_API_KEY",
        "secret": "$BIBOX_SECRET"
      },
      "tokens": {
        "ETH": {
          "minAmount": 1.0,
          "avgAmount": 5.0
        },
        "DAI": {
          "minAmount": 0.5,
          "avgAmount": 3.0,
          "maxAmount": 5.0
        }
      }
    }
  ]
}
```

### Referencing environment variables

Environment variables may be referenced from the `apiKey` and `secret` properties of the
`bibox-market-maker-keeper` member.


## Usage

```
usage: inventory-keeper [-h] [--rpc-host RPC_HOST] [--rpc-port RPC_PORT]
                        --config CONFIG [--gas-price GAS_PRICE]
                        [--gas-price-increase GAS_PRICE_INCREASE]
                        [--gas-price-increase-every GAS_PRICE_INCREASE_EVERY]
                        [--gas-price-max GAS_PRICE_MAX]
                        [--gas-price-file GAS_PRICE_FILE] [--manage-inventory]
                        [--manage-inventory-frequency MANAGE_INVENTORY_FREQUENCY]
                        [--inventory-dump-file INVENTORY_DUMP_FILE]
                        [--inventory-dump-frequency INVENTORY_DUMP_FREQUENCY]
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
  --manage-inventory    If specified, the keeper will actively manage
                        inventory according to the config
  --manage-inventory-frequency MANAGE_INVENTORY_FREQUENCY
                        Frequency of actively managing the inventory (in
                        seconds, default: 60)
  --inventory-dump-file INVENTORY_DUMP_FILE
                        File the keeper will periodically write the inventory
                        dump to
  --inventory-dump-frequency INVENTORY_DUMP_FREQUENCY
                        Frequency of writing the inventory dump file (in
                        seconds, default: 30)
  --debug               Enable debug output
```


## License

See [COPYING](https://github.com/makerdao/inventory-keeper/blob/master/COPYING) file.

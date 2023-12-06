<div align="center">

# **ZkTensor Subnet v1.0.0** <!-- omit in toc -->

[![Discord Chat](https://img.shields.io/discord/308323056592486420.svg)](https://discord.gg/bittensor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

### The Incentivized Internet <!-- omit in toc -->

[Discord](https://discord.gg/bittensor) • [Network](https://taostats.io/) • [Research](https://bittensor.com/whitepaper)

</div>

This repo contains all the necessary files and functions to define zktensor subnet incentive mechanisms. You can run this project in three ways,
on Bittensor's main-network (real TAO, to be released), Bittensor's test-network (fake TAO), or with your own staging-network. This repo includes instructions for doing all three.

# Installation

This repository requires python3.8 or higher. To install, simply clone this repository and install the requirements.

## Install Bittensor

```bash
$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/opentensor/bittensor/master/scripts/install.sh)"
```

## Install Dependencies

```bash
git clone https://github.com/zktensor/zktensor_subnet.git
cd zktensor_subnet
python -m pip install -r requirements.txt
```

# Miner

Miners contribute to the execution layer in the current version.
They receive public inputs of the specified model in the deployment layer, generate output and zk proof and return the result.
Right now, Only a single ZkSqrtRegressionModel is deployed in the deployment layer, miners will be asked to generate proof for the public inputs from the validators. This will not require that much computing power right now.

## Prerequisites

Install pm2

```bash
npm i -g pm2
```

Install make

```bash
sudo apt-get update && sudo apt-get install make
```

```bash
cp Makefile.example Makefile
```

## Running Miner

My personal preference to run is using Makefile.
Visit Makefile in root folder and edit it based on your settings

```bash

.PHONY: run-miner
run-miner:
	cd neurons && \
	pm2 start --name miner miner.py --interpreter python3 -- \
	--netuid {net_uid} \
	--axon.port 8091 \
	--subtensor.network finney \
	--wallet.name {your_miner_key_name} \
	--wallet.hotkey {your_miner_hotkey_name} \
	--subtensor.chain_endpoint wss://entrypoint-finney.opentensor.ai:443 \
	--logging.debug

```

And just run the following in terminal

```
make run-miner
```

Or you can just run this in terminal

```bash
	cd neurons && \
	pm2 start --name miner miner.py --interpreter python3 -- \
	--netuid {net_uid} \
	--axon.port 8091 \
	--subtensor.network finney \
	--wallet.name {your_miner_key_name} \
	--wallet.hotkey {your_miner_hotkey_name} \
	--subtensor.chain_endpoint wss://entrypoint-finney.opentensor.ai:443 \
	--logging.debug
```

# Validator

Validators send public inputs of the specified model(which is deployed in deployment layer) to the miners, and verify the output and proof returned from the miners, update weights based on the verificaton results.

## Running Validator

visit Makefile in root folder and edit based on your settings

```bash
cd neurons
# To run the validator
.PHONY: run-validator
run-validator:
	cd neurons && \
	pm2 start validator.py --name validator --interpreter python3 -- \
	--netuid {net_uid} \
	--subtensor.network finney \
	--wallet.name {validater_key_name} \
	--wallet.hotkey {validator_hot_key_name} \
	--subtensor.chain_endpoint wss://entrypont-finney.opentensor.ai:443 \
	--logging.debug

```

And just run the following in the terminal

```bash
make run-validator
```

You can make your own custom Makefile command and uset it based on your activity

---

## License

This repository is licensed under the MIT License.

```text
# The MIT License (MIT)
# Copyright © 2023 Chris Wilson

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
```

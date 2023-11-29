.PHONY: install

install:
	pip install -r requirements.txt

.PHONY: run-validator
run-validator: 
	cd neurons && \
	python validator.py \
	--netuid 39 \
	--subtensor.network test \
	--wallet.name test_validator \
	--wallet.hotkey test_validator_h1 \
	--subtensor.chain_endpoint wss://test.finney.opentensor.ai:443 \
	--logging.debug 

.PHONY: run-miner
run-miner: 
	cd neurons && \
	python miner.py \
	--netuid 39 \
	--axon.port 8091 \
	--subtensor.network test \
	--wallet.name test_miner \
	--wallet.hotkey test_miner_h1 \
	--subtensor.chain_endpoint wss://test.finney.opentensor.ai:443 \
	--logging.debug 


.PHONY: run-query
run-query: 
	python query.py \
	--netuid 28 \
	--subtensor.network finney \
	--wallet.name test_validator \
	--wallet.hotkey test_validator_h1 \
	--subtensor.chain_endpoint wss://entrypoint-finney.opentensor.ai:443 \
	--logging.debug 

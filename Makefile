.PHONY: install

install:
	python -m pip install -r requirements.txt
	python -m pip install -e .


.PHONY: run-validators
run-validators: 
	make run-validator || make run-validator2 || make run-validator3

.PHONY: run-validator
run-validator: 
	cd neurons && \
	pm2 start validator.py --name validator --interpreter python3 -- \
	--netuid 39 \
	--subtensor.network test \
	--wallet.name test_validator \
	--wallet.hotkey test_validator_h1 \
	--subtensor.chain_endpoint wss://test.finney.opentensor.ai:443 \
	--logging.debug 

run-validator2: 
	cd neurons && \
	python validator.py \
	--netuid 39 \
	--subtensor.network test \
	--wallet.name test_validator \
	--wallet.hotkey test_validator_h2 \
	--subtensor.chain_endpoint wss://test.finney.opentensor.ai:443 \
	--logging.debug 

run-validator3: 
	cd neurons && \
	python validator.py \
	--netuid 39 \
	--subtensor.network test \
	--wallet.name test_validator \
	--wallet.hotkey test_validator_h3 \
	--subtensor.chain_endpoint wss://test.finney.opentensor.ai:443 \
	--logging.debug 


.PHONY: run-miners
run-miners:
	make run-miner
	make run-miner2
	make run-miner3
	make run-miner4

.PHONY: run-miner
run-miner: 
	cd neurons && \
	python miner.py \
	--netuid 39 \
	--axon.port 8092 \
	--subtensor.network test \
	--wallet.name test_miner \
	--wallet.hotkey test_miner_h2 \
	--subtensor.chain_endpoint wss://test.finney.opentensor.ai:443 \
	--logging.debug 

.PHONY: run-miner2
run-miner2: 
	cd neurons && \
	python miner.py \
	--netuid 39 \
	--axon.port 8093 \
	--subtensor.network test \
	--wallet.name test_miner \
	--wallet.hotkey test_miner_h2 \
	--subtensor.chain_endpoint wss://test.finney.opentensor.ai:443 \
	--logging.debug 

.PHONY: run-miner3
run-miner3: 
	cd neurons && \
	python miner.py \
	--netuid 39 \
	--axon.port 8094 \
	--subtensor.network test \
	--wallet.name test_miner \
	--wallet.hotkey test_miner_h3 \
	--subtensor.chain_endpoint wss://test.finney.opentensor.ai:443 \
	--logging.debug 

.PHONY: run-miner4
run-miner4: 
	cd neurons && \
	python miner.py \
	--netuid 39 \
	--axon.port 8095 \
	--subtensor.network test \
	--wallet.name test_miner \
	--wallet.hotkey test_miner_h4 \
	--subtensor.chain_endpoint wss://test.finney.opentensor.ai:443 \
	--logging.debug 



.PHONY: run-query
run-query: 
	python query.py \
	--netuid 4 \
	--subtensor.network finney \
	--wallet.name test_validator \
	--wallet.hotkey test_validator_h1 \
	--subtensor.chain_endpoint wss://entrypoint-finney.opentensor.ai:443 \
	--logging.debug 

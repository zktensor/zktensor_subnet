import os
import time
import torch
import argparse
import traceback
import bittensor as bt
import json
import protocol
from score.model_score import calculateScore
import random
from _validator.validator_session import ValidatorSession

# This function is responsible for setting up and parsing command-line arguments.
def get_config_from_args():
    """
    This function sets up and parses command-line arguments.
    """
    parser = argparse.ArgumentParser()

    # Adds override arguments for network and netuid.
    parser.add_argument( '--netuid', type = int, default = 1, help = "The chain subnet uid." )
    parser.add_argument( '--auto-update', default = True, help = "Auto update." )

    # Adds subtensor specific arguments i.e. --subtensor.chain_endpoint ... --subtensor.network ...
    bt.subtensor.add_args(parser)
    # Adds logging specific arguments i.e. --logging.debug ..., --logging.trace .. or --logging.logging_dir ...
    bt.logging.add_args(parser)
    # Adds wallet specific arguments i.e. --wallet.name ..., --wallet.hotkey ./. or --wallet.path ...
    bt.wallet.add_args(parser)
    # Parse the config (will take command-line arguments if provided)
    # To print help message, run python3 neurons/validator.py --help
    config =  bt.config(parser)

    # Logging is crucial for monitoring and debugging purposes.
    config.full_path = os.path.expanduser(
        "{}/{}/{}/netuid{}/{}".format(
            config.logging.logging_dir,
            config.wallet.name,
            config.wallet.hotkey,
            config.netuid,
            'validator',
        )
    )
    # Ensure the logging directory exists.
    if not os.path.exists(config.full_path): os.makedirs(config.full_path, exist_ok=True)
        
    # Set up logging with the provided configuration and directory.
    bt.logging(config=config, logging_dir=config.full_path)
    
    # Return the parsed config.
    return config


# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    # Parse the configuration.
    config = get_config_from_args()
    # Run the main function.
    with ValidatorSession(config) as validator_session:
        validator_session.run()


"""
The MIT License (MIT)
Copyright © 2023 Chris Wilson

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the “Software”), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of
the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
# dealings in the software.


# Importing necessary libraries and modules
import os
import time
import torch
import argparse
import traceback
import bittensor as bt
import json
from neurons import protocol
from score.model_score import calculateScore
import random


# This function is responsible for setting up and parsing command-line arguments.
def get_config_from_args():
    """
    This function sets up and parses command-line arguments.
    """
    parser = argparse.ArgumentParser()

    # Adds override arguments for network and netuid.
    parser.add_argument( '--netuid', type = int, default = 1, help = "The chain subnet uid." )
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

def get_bt_objects(config):
     # The wallet holds the cryptographic key pairs for the validator.
    wallet = bt.wallet( config = config )
    bt.logging.info(f"Wallet: {wallet}")

    # The subtensor is our connection to the Bittensor blockchain.
    subtensor = bt.subtensor( config = config )
    bt.logging.info(f"Subtensor: {subtensor}")

    # Dendrite is the RPC client; it lets us send messages to other nodes (axons) in the network.
    dendrite = bt.dendrite( wallet = wallet )
    bt.logging.info(f"Dendrite: {dendrite}")
    
    metagraph = subtensor.metagraph( config.netuid )

    return wallet, subtensor, dendrite, metagraph

class ValidatorSession:
    def __init__(self, config):
        self.config = config
        self.configure()
        self.check_register()
        
    def run(self):
        bt.logging.info("Building validation weights.")

        # Restore weights, or initialize weights for each miner to 0.
        scores_file = "scores.pt"
        try:
            scores = torch.load(scores_file)
            bt.logging.info(f"Loaded scores from save file: {scores}")
        except:
            scores = torch.zeros_like(metagraph.S, dtype=torch.float32)
            bt.logging.info(f"Initialized all scores to 0")


        current_block = subtensor.block
        print("🔢 scores", scores)
        # all nodes with more than 1e3 total stake are set to 0 (sets validators weights to 0)
        scores = scores * (metagraph.total_stake < 1.024e3)
        # set all nodes without ips set to 0
        scores = scores * torch.Tensor([metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in metagraph.uids])
        step = 0

        bt.logging.info(f"Initial scores: {scores}")
        bt.logging.info("Starting validator loop.")
        
        total_dendrites_per_query = 25
        minimum_dendrites_per_query = 3
        last_updated_block = current_block - (current_block % 100)
        last_reset_weights_block = current_block

        print("metagraph.total_stake 💻", metagraph.total_stake)

        print("len", len(metagraph.total_stake)) 
        
    def check_register(self):
        if self.wallet.hotkey.ss58_address not in self.metagraph.hotkeys:
            bt.logging.error(f"\nYour validator: {self.wallet} if not registered to chain connection: {subtensor} \nRun btcli register and try again.")
            exit()
        else:
            # Each miner gets a unique identity (UID) in the network for differentiation.
            subnet_uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
            bt.logging.info(f"Running validator on uid: {self.subnet_uid}")
            self.subnet_uid = subnet_uid
        
    def configure(self):
        self.wallet = bt.wallet( config = config )
        bt.logging.info(f"Wallet: {self.wallet}")

        # The subtensor is our connection to the Bittensor blockchain.
        self.subtensor = bt.subtensor( config = config )
        bt.logging.info(f"Subtensor: {self.subtensor}")

        # Dendrite is the RPC client; it lets us send messages to other nodes (axons) in the network.
        self.dendrite = bt.dendrite( wallet = self.wallet )
        bt.logging.info(f"Dendrite: {self.dendrite}")
        
        self.metagraph = self.subtensor.metagraph( config.netuid )
        self.sync_metagraph()

    def sync_metagraph(self):
        self.metagraph.sync(subtensor = self.subtensor)
        bt.logging.info(f"Sync Metagraph: {self.metagraph}")
    
def main( config ):
    bt.logging.info(f"🚀 Running validator  for subnet: {config.netuid} on network: {config.subtensor.chain_endpoint} with config:")
        
    # The metagraph holds the state of the network, letting us know about other miners.
    metagraph.sync(subtensor = subtensor)


    if wallet.hotkey.ss58_address not in metagraph.hotkeys:
        bt.logging.error(f"\nYour validator: {wallet} if not registered to chain connection: {subtensor} \nRun btcli register and try again.")
        exit()
    else:
        # Each miner gets a unique identity (UID) in the network for differentiation.
        my_subnet_uid = metagraph.hotkeys.index(wallet.hotkey.ss58_address)
        bt.logging.info(f"Running validator on uid: {my_subnet_uid}")

    bt.logging.info("Building validation weights.")

    # Restore weights, or initialize weights for each miner to 0.
    scores_file = "scores.pt"
    try:
        scores = torch.load(scores_file)
        bt.logging.info(f"Loaded scores from save file: {scores}")
    except:
        scores = torch.zeros_like(metagraph.S, dtype=torch.float32)
        bt.logging.info(f"Initialized all scores to 0")


    print("🔢 scores", scores)
    # all nodes with more than 1e3 total stake are set to 0 (sets validators weights to 0)
    scores = scores * (metagraph.total_stake < 1.024e3)
    # set all nodes without ips set to 0
    scores = scores * torch.Tensor([metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in metagraph.uids])
    
    step = 0
    current_block = subtensor.block

    bt.logging.info(f"Initial scores: {scores}")
    bt.logging.info("Starting validator loop.")
    
    total_dendrites_per_query = 25
    minimum_dendrites_per_query = 3
    last_updated_block = current_block - (current_block % 100)
    last_reset_weights_block = current_block

    print("metagraph.total_stake 💻", metagraph.total_stake)

    print("len", len(metagraph.total_stake)) 

    # Main loop
    while True:
        # Per 10 blocks, sync the subtensor state with the blockchain.
        if step % 5 == 0:
            metagraph.sync(subtensor = subtensor)
            bt.logging.info(f"🔄 Syncing metagraph with subtensor.")

        # If the metagraph has changed, update the weights.
        # Get the uids of all miners in the network.
        uids = metagraph.uids.tolist()
        print("uids", uids)
        # return
        # If there are more uids than scores, add more weights.
        if len(uids) > len(scores):
            bt.logging.trace("Adding more weights")
            size_difference = len(uids) - len(scores)
            new_scores = torch.zeros(size_difference, dtype=torch.float32)
            scores = torch.cat((scores, new_scores))
            del new_scores
        # If there are less uids than scores, remove some weights.
        queryable_uids = (metagraph.total_stake < 1.024e3)
        bt.logging.info(f"queryable_uids:{queryable_uids}")
        bt.logging.info("ip", torch.Tensor([metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in uids]))

        # Remove the weights of miners that are not queryable.
        queryable_uids = queryable_uids * torch.Tensor([metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in uids])
        active_miners = torch.sum(queryable_uids)
        dendrites_per_query = total_dendrites_per_query

        # if there are no active miners, set active_miners to 1
        if active_miners == 0:
            active_miners = 1
        # if there are less than dendrites_per_query * 3 active miners, set dendrites_per_query to active_miners / 3
        if active_miners < total_dendrites_per_query * 3:
            dendrites_per_query = int(active_miners / 3)
        else:
            dendrites_per_query = total_dendrites_per_query
        
        # less than 3 set to 3
        if dendrites_per_query < minimum_dendrites_per_query:
                dendrites_per_query = minimum_dendrites_per_query
        # zip uids and queryable_uids, filter only the uids that are queryable, unzip, and get the uids
        print("queryable_uids", queryable_uids)
        zipped_uids = list(zip(uids, queryable_uids))
        print("zipped_uids", zipped_uids)
        
        filtered_uids = list(zip(*filter(lambda x: x[1], zipped_uids)))
        if len(filtered_uids) != 0:
            filtered_uids = filtered_uids[0]

        bt.logging.info(f"filtered_uids:{filtered_uids}")

        dendrites_to_query = random.sample( filtered_uids, min( dendrites_per_query, len(filtered_uids) ) )
        bt.logging.info(f"dendrites_to_query:{dendrites_to_query}")
        
        # every 2 minutes, query the miners
        try:
            # Filter metagraph.axons by indices saved in dendrites_to_query list
            filtered_axons = [metagraph.axons[i] for i in dendrites_to_query]
            bt.logging.info(f"filtered_axons: {filtered_axons}")
            # Broadcast a GET_DATA query to filtered miners on the network.

            # * every 10 minutes, query the miners for twitter data
            if step % 4 == 0 | step % 4 == 1 | step % 4 == 2 | step % 4 == 3:
                query_input = {"model_id" : [0], "public_inputs":[2,4,9]}
                bt.logging.info(f"\033[92m 𝕏 ⏩ Sending model_proof query ({query_input}). \033[0m")
                responses = dendrite.query(
                    filtered_axons,
                    # Construct a scraping query.
                    protocol.QueryZkProof(query_input = query_input), # Construct a scraping query.
                    # All responses have the deserialize function called on them before returning.
                    deserialize = True, 
                    timeout = 60
                )
                
                # Update score
                new_scores = []
                try:
                    if(len(responses) > 0 and responses is not None):
                        new_scores = calculateScore(responses = responses)
                        bt.logging.info(f"✅ new_scores: {new_scores}")
                except Exception as e:
                    bt.logging.error(f"❌ Error in twitterScore: {e}")
                # for i, score_i in enumerate(new_scores):
                #     scores[dendrites_to_query[i]] = twitterAlpha * scores[dendrites_to_query[i]] + (1 - twitterAlpha) * score_i
                bt.logging.info(f"\033[92m ✓ Updated Scores: {scores} \033[0m")
                
                # try:
                #     if len(responses) > 0:
                #         indexing_result = storage.store.twitter_store(data = responses, search_keys=[search_key])
                #         bt.logging.info(f"\033[92m saving index info: {indexing_result} \033[0m")
                #     else:
                #         bt.logging.warning("\033[91m ⚠ No twitter data found in responses \033[0m")
                # except Exception as e:
                #     bt.logging.error(f"❌ Error in store_Twitter: {e}")
                    
                        
                current_block = subtensor.block
                if current_block - last_updated_block > 100:
                    
                    weights = scores / torch.sum(scores)
                    bt.logging.info(f"Setting weights: {weights}")
                    # Miners with higher scores (or weights) receive a larger share of TAO rewards on this subnet.
                    (
                        processed_uids,
                        processed_weights,
                    ) = bt.utils.weight_utils.process_weights_for_netuid(
                        uids=metagraph.uids,
                        weights=weights,
                        netuid=config.netuid,
                        subtensor=subtensor
                    )
                    bt.logging.info(f"Processed weights: {processed_weights}")
                    bt.logging.info(f"Processed uids: {processed_uids}")
                    result = subtensor.set_weights(
                        netuid = config.netuid, # Subnet to set weights on.
                        wallet = wallet, # Wallet to sign set weights using hotkey.
                        uids = processed_uids, # Uids of the miners to set weights for.
                        weights = processed_weights, # Weights to set for the miners.
                    )
                    last_updated_block = current_block
                    if result: bt.logging.success('✅ Successfully set weights.')
                    else: bt.logging.error('Failed to set weights.')
                    
            step += 1

            if last_reset_weights_block + 1800 < current_block:
                bt.logging.trace(f"Clearing weights for validators and nodes without IPs")
                last_reset_weights_block = current_block
                # scores = scores * metagraph.last_update > current_block - 600

                # all nodes with more than 1e3 total stake are set to 0 (sets validtors weights to 0)
                scores = scores * (metagraph.total_stake < 1.024e3) 

                # set all nodes without ips set to 0
                scores = scores * torch.Tensor([metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in metagraph.uids])

            # Resync our local state with the latest state from the blockchain.
            metagraph = subtensor.metagraph(config.netuid)
            torch.save(scores, scores_file)
            bt.logging.info(f"Saved weights to \"{scores_file}\"")
            # Sleep for a duration equivalent to the block time (i.e., time between successive blocks).
            time.sleep(bt.__blocktime__ * 10)

        # If we encounter an unexpected error, log it for debugging.
        except RuntimeError as e:
            bt.logging.error(e)
            traceback.print_exc()
        except Exception as e:
            bt.logging.error(e)
            continue
        # If the user interrupts the program, gracefully exit.
        except KeyboardInterrupt:
            bt.logging.success("Keyboard interrupt detected. Exiting validator.")
            exit()
        
# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    # Parse the configuration.
    config = get_config_from_args()
    # Run the main function.
    with ValidatorSession(config) as validator_session:
        validator_session.run()


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

class ValidatorSession:
    def __init__(self, config):
        self.config = config
        self.configure()
        self.check_register()
        
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        None
        return False
    
    def unpack_bt_objects(self):
        wallet = self.wallet
        metagraph = self.metagraph
        subtensor = self.subtensor
        dendrite = self.dendrite
        return wallet, metagraph, subtensor, dendrite
    
    def init_scores(self):
        bt.logging.info("Building validation weights.")
        
        # Restore weights, or initialize weights for each miner to 0.
        scores_file = "scores.pt"
        try:
            scores = torch.load(scores_file)
            bt.logging.info(f"Loaded scores from save file: {scores}")
        except:
            scores = torch.zeros_like(self.metagraph.S, dtype=torch.float32)
            bt.logging.info(f"Initialized all scores to 0")
        print("🔢 scores", scores)
        
        # all nodes with more than 1e3 total stake are set to 0 (sets validators weights to 0)
        scores = scores * (self.metagraph.total_stake < 1.024e3)
        # set all nodes without ips set to 0
        scores = scores * torch.Tensor([self.metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in self.metagraph.uids])
        self.scores = scores
        return self.scores
    
    def sync_scores_uids(self, uids):
        # If the metagraph has changed, update the weights.
        # If there are more uids than scores, add more weights.
        if len(uids) > len(self.scores):
            bt.logging.trace("Adding more weights")
            size_difference = len(uids) - len(self.scores)
            new_scores = torch.zeros(size_difference, dtype=torch.float32)
            self.scores = torch.cat((self.scores, new_scores))
            del new_scores
    
        # If there are less uids than scores, remove some weights.
    def init_loop_params(self):
        self.step = 0
        self.current_block = self.subtensor.block
            
        self.total_dendrites_per_query = 25
        self.minimum_dendrites_per_query = 3
        self.last_updated_block = self.current_block - (self.current_block % 100)
        self.last_reset_weights_block = self.current_block

    def get_querable_axons(self):
        wallet, metagraph, subtensor, dendrite = self.unpack_bt_objects()
        uids = metagraph.uids.tolist()
        
        # If there are less uids than scores, remove some weights.
        queryable_uids = (metagraph.total_stake < 1.024e3)
        bt.logging.info("ip", torch.Tensor([metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in uids]))

        # Remove the weights of miners that are not queryable.
        queryable_uids = queryable_uids * torch.Tensor([metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in uids])
        active_miners = torch.sum(queryable_uids)
        dendrites_per_query = self.total_dendrites_per_query

        # if there are no active miners, set active_miners to 1
        if active_miners == 0:
            active_miners = 1
        # if there are less than dendrites_per_query * 3 active miners, set dendrites_per_query to active_miners / 3
        if active_miners < self.total_dendrites_per_query * 3:
            dendrites_per_query = int(active_miners / 3)
        else:
            dendrites_per_query = self.total_dendrites_per_query
        
        # less than 3 set to 3
        if dendrites_per_query < self.minimum_dendrites_per_query:
                dendrites_per_query = self.minimum_dendrites_per_query
        # zip uids and queryable_uids, filter only the uids that are queryable, unzip, and get the uids
        zipped_uids = list(zip(uids, queryable_uids))
        
        filtered_uids = list(zip(*filter(lambda x: x[1], zipped_uids)))
        if len(filtered_uids) != 0:
            filtered_uids = filtered_uids[0]

        dendrites_to_query = random.sample( filtered_uids, min( dendrites_per_query, len(filtered_uids) ) )
            
        filtered_axons = [metagraph.axons[i] for i in dendrites_to_query]
        bt.logging.info(f"filtered_axons: {filtered_axons}")
        return filtered_axons

    def update_scores(self, responses):
        wallet, metagraph, subtensor, dendrite = self.unpack_bt_objects()
        # Update score
        new_scores = []
        scores = self.scores
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
            
        self.current_block = subtensor.block
        if self.current_block - self.last_updated_block > 100:
            weights = self.scores / torch.sum(scores)
            bt.logging.info(f"Setting weights: {weights}")
            # Miners with higher scores (or weights) receive a larger share of TAO rewards on this subnet.
            (
                processed_uids,
                processed_weights,
            ) = bt.utils.weight_utils.process_weights_for_netuid(
                uids=metagraph.uids,
                weights=weights,
                netuid=self.config.netuid,
                subtensor=subtensor
            )
            bt.logging.info(f"Processed weights: {processed_weights}")
            bt.logging.info(f"Processed uids: {processed_uids}")
            result = subtensor.set_weights(
                netuid = self.config.netuid, # Subnet to set weights on.
                wallet = wallet, # Wallet to sign set weights using hotkey.
                uids = processed_uids, # Uids of the miners to set weights for.
                weights = processed_weights, # Weights to set for the miners.
            )
            self.last_updated_block = self.current_block
            if result: bt.logging.success('✅ Successfully set weights.')
            else: bt.logging.error('Failed to set weights.')
            
        if self.last_reset_weights_block + 1800 < self.current_block:
            bt.logging.trace(f"Clearing weights for validators and nodes without IPs")
            self.last_reset_weights_block = self.current_block
            # scores = scores * metagraph.last_update > current_block - 600

            # all nodes with more than 1e3 total stake are set to 0 (sets validtors weights to 0)
            scores = scores * (metagraph.total_stake < 1.024e3) 

            # set all nodes without ips set to 0
            scores = scores * torch.Tensor([metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in metagraph.uids])

        # Resync our local state with the latest state from the blockchain.
        metagraph = subtensor.metagraph(self.config.netuid)
        # torch.save(scores, scores_file)
        # bt.logging.info(f"Saved weights to \"{self.scores_file}\"")
        
    def run_one_loop(self):
        wallet, metagraph, subtensor, dendrite = self.unpack_bt_objects()
        
        if self.step % 5 == 0:
            metagraph.sync(subtensor = subtensor)
            bt.logging.info(f"🔄 Syncing metagraph with subtensor.")

        # Get the uids of all miners in the network.
        uids = metagraph.uids.tolist()
        self.sync_scores_uids(uids)
        axons = self.get_querable_axons()
        
        query_input = {"model_id" : [0], "public_inputs":[2,4,9]}
        bt.logging.info(f"\033[92m 𝕏 ⏩ Sending model_proof query ({query_input}). \033[0m")
        try:
            responses = dendrite.query(
                axons,
                # Construct a scraping query.
                protocol.QueryZkProof(query_input = query_input), # Construct a scraping query.
                # All responses have the deserialize function called on them before returning.
                deserialize = True, 
                timeout = 60
            )
            print("responses", responses.instances)
            self.update_scores(responses)
            self.step += 1

            # Sleep for a duration equivalent to the block time (i.e., time between successive blocks).
            time.sleep(bt.__blocktime__ * 10)
        except RuntimeError as e:
            bt.logging.error(e)
            traceback.print_exc()
        except Exception as e:
            bt.logging.error(e)
            return
        # If the user interrupts the program, gracefully exit.
        except KeyboardInterrupt:
            bt.logging.success("Keyboard interrupt detected. Exiting validator.")
            exit()
            
    def run(self):
        
        wallet, metagraph, subtensor, dendrite = self.unpack_bt_objects()
    
        self.init_scores()
        self.init_loop_params()

        while True:
            self.run_one_loop()
             # If we encounter an unexpected error, log it for debugging.
            
    def check_register(self):
        if self.wallet.hotkey.ss58_address not in self.metagraph.hotkeys:
            bt.logging.error(f"\nYour validator: {self.wallet} if not registered to chain connection: {self.subtensor} \nRun btcli register and try again.")
            exit()
        else:
            # Each miner gets a unique identity (UID) in the network for differentiation.
            subnet_uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
            bt.logging.info(f"Running validator on uid: {subnet_uid}")
            self.subnet_uid = subnet_uid
        
    def configure(self):
        self.wallet = bt.wallet( config = self.config )
        bt.logging.info(f"Wallet: {self.wallet}")

        # The subtensor is our connection to the Bittensor blockchain.
        self.subtensor = bt.subtensor( config = self.config )
        bt.logging.info(f"Subtensor: {self.subtensor}")

        # Dendrite is the RPC client; it lets us send messages to other nodes (axons) in the network.
        self.dendrite = bt.dendrite( wallet = self.wallet )
        bt.logging.info(f"Dendrite: {self.dendrite}")
        
        self.metagraph = self.subtensor.metagraph( self.config.netuid )
        self.sync_metagraph()

    def sync_metagraph(self):
        self.metagraph.sync(subtensor = self.subtensor)
        bt.logging.info(f"Sync Metagraph: {self.metagraph}")
    
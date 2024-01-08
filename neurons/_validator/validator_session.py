import os
import time
import torch
import argparse
import traceback
import bittensor as bt
import json
import protocol
import random

from rich.table import Table
from rich.console import Console

from execution_layer.ZkSqrtModelSession import ZkSqrtModelSession
from utils import try_update
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
        # scores_file = "scores.pt"
        # try:
        #     scores = torch.load(scores_file)
        #     bt.logging.info(f"Loaded scores from save file: {scores}")
        # except:
        #     scores = torch.zeros_like(self.metagraph.S, dtype=torch.float32)
        #     bt.logging.info(f"Initialized all scores to 0")

        try:
            self.scores = torch.load("scores.pt")
        except Exception as e:
            scores = torch.zeros_like(self.metagraph.S, dtype=torch.float32)

            # set all nodes without ips set to 0
            scores = scores * torch.Tensor([self.metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in self.metagraph.uids])
            self.scores = scores
        
        bt.logging.info("Succesfully init scores")
        
        self.log_scores()
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
    
    def init_running_args(self):
        # Initiate parameters that is used in running the steps

        self.step = 0
        self.current_block = self.subtensor.block
            
        self.last_updated_block = self.current_block - (self.current_block % self.config.blocks_per_epoch)
        self.last_reset_weights_block = self.current_block
        

    def get_querable_uids(self):
        """Returns the uids of the miners that are queryable

        Returns:
            _type_: _description_
        """
        wallet, metagraph, subtensor, dendrite = self.unpack_bt_objects()
        uids = metagraph.uids.tolist()
        
        # If there are less uids than scores, remove some weights.
        queryable_uids = (metagraph.total_stake < 1.024e3)

        # Remove the weights of miners that are not queryable.
        queryable_uids = queryable_uids * torch.Tensor([metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in uids])

        active_miners = torch.sum(queryable_uids)

        # if there are no active miners, set active_miners to 1
        if active_miners == 0:
            active_miners = 1


        # zip uids and queryable_uids, filter only the uids that are queryable, unzip, and get the uids
        zipped_uids = list(zip(uids, queryable_uids))
        
        filtered_uids = list(zip(*filter(lambda x: x[1], zipped_uids)))
        bt.logging.debug(f"filtered_uids: {filtered_uids}")
        
        if len(filtered_uids) != 0:
            filtered_uids = filtered_uids[0]
                        
        return filtered_uids

    def update_scores(self, responses):
        """Updates scores based on the response from the miners

        Args:
            responses (_type_): [(uid, response)] array from the miners


        """
        if(len(responses) == 0 or responses is None):
            return
        
        wallet, metagraph, subtensor, dendrite = self.unpack_bt_objects()
        new_scores = self.scores[:]
        max_score = torch.max(self.scores)
        if max_score == 0:
            max_score = 1
        
        min_score = 0
        recover_rate = 0.2
        decent_rate = 0.8
        
        def update_score(score, value):
            if value == True:
                return score + recover_rate * (max_score - score)
            else:
                return score - decent_rate * (score - min_score)
        
        all_uids = set(range(len(self.scores)))
        response_uids = set(uid for uid, _, _ in responses)
        missing_uids = all_uids - response_uids

        responses.extend((uid, False, 1) for uid in missing_uids)
        
        for uid, response, factor in responses:
            new_scores[uid] = update_score(self.scores[uid], response) * factor
        
        if torch.sum(self.scores).item() != 0:
            self.scores = self.scores / torch.sum(self.scores)

        self.log_scores()
        self.try_store_scores()
        self.current_block = subtensor.block
        if self.current_block - self.last_updated_block > self.config.blocks_per_epoch:
            self.update_weights()            

        
    def update_weights(self):
        wallet, metagraph, subtensor, dendrite = self.unpack_bt_objects()

        if torch.sum(self.scores).item() != 0:
            weights = self.scores / torch.sum(self.scores)
        else:
            weights = self.scores
        
        
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
        
        self.weights = weights
        self.log_weights()
        
        self.last_updated_block = metagraph.block.item()
        
        if result: bt.logging.success('✅ Successfully set weights.')
        else: bt.logging.error('Failed to set weights.')

    def log_scores(self):
        table = Table(title="scores")
        table.add_column("uid", justify="right", style="cyan", no_wrap=True)
        table.add_column("score", justify="right", style="magenta", no_wrap=True)

        for uid, score in enumerate(self.scores):
            table.add_row(str(uid), str(round(score.item(), 4)))
        
        console = Console()
        console.print(table)

    def try_store_scores(self):
        try:
            torch.save(self.scores, "scores.pt")
        except Exception as e:
            bt.logging.info(f"Error at storing scores {e}")
  
            
    def log_verify_result(self, results):
        table = Table(title="proof verification result")
        table.add_column("uid", justify="right", style="cyan", no_wrap=True)
        table.add_column("Verified?", justify="right", style="magenta", no_wrap=True)
        for uid, result in results:
            table.add_row(str(uid), str(result))

        
        console = Console()
        console.print(table)

    def log_weights(self):
        table = Table(title="weights")
        table.add_column("uid", justify="right", style="cyan", no_wrap=True)
        table.add_column("weight", justify="right", style="magenta", no_wrap=True)

        for uid, score in enumerate(self.weights):
            table.add_row(str(uid), str(round(score.item(), 4)))
        
        console = Console()
        console.print(table)
        
    
    def verify_proof_string(self, proof_string: str):
        # if proof_string != None and proof_string.startswith("An error"):
        #     print(proof_string)
            
        if proof_string == None:
            return False
        try:
            sqrt_session = ZkSqrtModelSession()
            res = sqrt_session.verify_proof_string(proof_string)
            sqrt_session.end()
            return res
        except Exception as e:
            bt.logging.error(f"❌error at verifying", e)
            print("proof_string for error", proof_string)

        return False
    
    def run_step(self):
        wallet, metagraph, subtensor, dendrite = self.unpack_bt_objects()

        # Get the uids of all miners in the network.
        uids = metagraph.uids.tolist()
        self.sync_scores_uids(uids)

        filtered_uids = self.get_querable_uids()
        
        # filtered_uids = [134] # for debug
        filtered_axons = [metagraph.axons[i] for i in filtered_uids]
        
        random_values = [random.randint(1, 100) for _ in range(3)]

        # [AxonInfo( /ipv4/61.221.116.28:8092, 5C5JiwUh9GqYR4FGzcH7CyhqYjtTd7c3HAhTMsZjn4Kyyxu1, 
        #           5DMHnegFAW82XBhejpNZE4Xg2vHN3ijCwYPD2NWyEcKZTHvp, 620 )]

        query_input = {"model_id" : [0], "public_inputs":random_values}
        bt.logging.info(f"\033[92m >> Sending model_proof query ({query_input}). \033[0m")

        try:
            responses = dendrite.query(
                filtered_axons,
                protocol.QueryZkProof(query_input = query_input), 
                # All responses have the deserialize function called on them before returning.
                deserialize = True, 
                timeout = 100
            )
            ip_array = [axon.ip for axon in filtered_axons]
            coldkey_array = [axon.coldkey for axon in filtered_axons]
            print("ip_array", ip_array)
            
            ip_distributions = [1 / ip_array.count(ip) for ip in ip_array]
            coldkey_distributions = [1 / (coldkey_array.count(coldkey) - 4 if coldkey_array.count(coldkey) > 4 else 1)  for coldkey in coldkey_array]
            
            weight_factors = [ip_dist * coldkey_dist for ip_dist, coldkey_dist in zip(ip_distributions, coldkey_distributions)]
            
            verif_results = list(map(self.verify_proof_string, responses))

            self.log_verify_result(list(zip(filtered_uids, verif_results)))
            
            self.update_scores(list(zip(filtered_uids, verif_results, weight_factors)))

            self.step += 1

            # Sleep for a duration equivalent to the block time (i.e., time between successive blocks).
            time.sleep(bt.__blocktime__)
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
        bt.logging.debug("Validator started its running loop")
                
        wallet, metagraph, subtensor, dendrite = self.unpack_bt_objects()
        
        self.init_scores()
        self.init_running_args()

        while True:
            try:
                if self.config.auto_update == True:
                    try_update()    
                self.sync_metagraph()
                self.run_step()
                
            except KeyboardInterrupt:
                bt.logging.info("KeyboardInterrupt caught. Exiting validator.")
                exit()

            except Exception as e:
                bt.logging.error(f"Error in validator loop \n {e} \n {traceback.format_exc()}")
                    
            
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
        #=== Configure Bittensor objects ====
        self.wallet = bt.wallet( config = self.config )
        self.subtensor = bt.subtensor( config = self.config )
        self.dendrite = bt.dendrite( wallet = self.wallet )
        self.metagraph = self.subtensor.metagraph( self.config.netuid )
        self.subnet = bt.metagraph(netuid = self.config.netuid, lite = False)
        
        self.sync_metagraph()
        

    def sync_metagraph(self):
        self.metagraph.sync(subtensor = self.subtensor)
    

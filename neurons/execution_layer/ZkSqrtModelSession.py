import os

import onnxruntime
import numpy as np
import torch
import uuid
import json
import ezkl

dir_path = os.path.dirname(os.path.realpath(__file__))

class ZkSqrtModelSession:

    def __init__(self, public_inputs = []):
        self.model_id = 0
        self.session_id = str(uuid.uuid4())
        self.model_path = os.path.join(dir_path, f"../deployment_layer/model_{self.model_id}/network.onnx")
        self.pk_path = os.path.join(dir_path, f"../deployment_layer/model_{self.model_id}/pk.key")
        self.vk_path = os.path.join(dir_path, f"../deployment_layer/model_{self.model_id}/vk.key")
        self.srs_path = os.path.join(dir_path, f"../deployment_layer/model_{self.model_id}/kzg.srs")
        self.circuit_path = os.path.join(dir_path, f"../deployment_layer/model_{self.model_id}/network.ezkl")
        self.settings_path = os.path.join(dir_path, f"../deployment_layer/model_{self.model_id}/settings.json")
        self.sample_input_path = os.path.join(dir_path, f"../deployment_layer/model_{self.model_id}/input.json")
        
        self.witness_path = os.path.join(dir_path, f"./temp/witness_{self.model_id}_{self.session_id}.json")
        self.input_path = os.path.join(dir_path, f"./temp/input_{self.model_id}_{self.session_id}.json")
        self.proof_path = os.path.join(dir_path, f"./temp/model_{self.model_id}_{self.session_id}.proof")

        self.ort_session = onnxruntime.InferenceSession(self.model_path, providers=["CPUExecutionProvider"])

        self.public_inputs = public_inputs

        self.py_run_args=ezkl.PyRunArgs()
        self.py_run_args.input_visibility = "public"
        self.py_run_args.output_visibility = "public"
        self.py_run_args.param_visibility = "fixed"


    # produce the output of the model
    def run_model(self):
        self.input_name = self.ort_session.get_inputs()[0].name
        self.input_shape = self.ort_session.get_inputs()[0].shape
        self.batch_size = 3
        input_data = np.abs(self.public_inputs)

        outputs = self.ort_session.run(None, {self.input_name: [input_data]})
        self.outputs = outputs
        # should generate input.json file

    async def gen_settings(self):
        ezkl.gen_settings(self.model_path, self.settings_path, py_run_args=self.py_run_args)
        await ezkl.calibrate_settings(self.input_path, self.model_path, self.settings.path, "resources")

    def compile_circuit(self):
        ezkl.compile_model(self.model_path, self.circuit_path, self.settings_path)

    def get_srs(self):
        ezkl.get_srs(self.srs_path, self.settings_path)
        ezkl.setup(
            self.circuit_path,
            self.vk_path,
            self.pk_path,
            self.srs_path
        )
        
    async def setup_circuit(self):
        await self.gen_settings()
        self.compile_circuit()
        ezkl.setup(
            self.circuit_path,
            self.vk_path,
            self.pk_path,
            self.srs_path,
            self.settings_path
        )
        
    # generate the input_{model_id}_{session_id}.json file, which is used to generate witness
    def gen_input_file(self):        
        input_data = [self.public_inputs]
        input_shapes = [[self.batch_size]]
        data = {
            "input_data": input_data,
            "input_shapes": input_shapes
        }
        
        # Get the directory name
        dir_name = os.path.dirname(self.input_path)

        # Create the directory if it doesn't exist
        os.makedirs(dir_name, exist_ok=True)

        with open(self.input_path, 'w') as f:
            json.dump(data, f)
    
    def gen_witness(self):
        ezkl.gen_witness(
            self.input_path, 
            self.circuit_path, 
            self.witness_path
            )

    def gen_proof_file(self, proof_string):
        with open(self.proof_path, 'w') as f:
            f.write(proof_string)
        
    # generate the proof of the model
    def gen_proof(self):
  
        try:
            self.run_model()
            self.gen_input_file()
            self.gen_witness()
            
            ezkl.prove(
                self.witness_path,
                self.circuit_path,
                self.pk_path,
                self.proof_path,
                self.srs_path,
                # "evm",
                "single",
                # self.settings_path,
            )
            
            with open(self.proof_path, 'r') as f:
                proof_content = f.read()
            
            return proof_content
        
        except Exception as e:
            print(f"An error occured: {e}")
            return f"An error occured on miner proof: {e}"

    def verify_proof(self):        
        res = ezkl.verify(
            self.proof_path,
            self.settings_path,
            self.vk_path,
            self.srs_path,
        )

        return res
    
    def verify_proof_string(self, proof_string):
        if proof_string == None:
            return False
        self.gen_proof_file(proof_string)
        return self.verify_proof()
        
    def __enter__(self):
        return self
    
    def remove_temp_files(self):
        if os.path.exists(self.input_path):
            os.remove(self.input_path)

        if os.path.exists(self.witness_path):
            os.remove(self.witness_path)

        if os.path.exists(self.proof_path):
            os.remove(self.proof_path)

    def end(self):
        self.remove_temp_files()
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Perform any necessary cleanup or resource release here
        # For example, you can delete the input file generated by the class
        None
        # if os.path.exists(self.input_path):
        #     os.remove(self.input_path)

        # if os.path.exists(self.witness_path):
        #     os.remove(self.input_path)
            
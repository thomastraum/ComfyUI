# This is an example that uses the websockets api to know when a prompt execution is done
# Once the prompt execution is done it downloads the images using the /history endpoint

import websocket  # NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse

import time

server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())


def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode("utf-8")
    req = urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())


def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(
        "http://{}/view?{}".format(server_address, url_values)
    ) as response:
        return response.read()


def get_history(prompt_id):
    with urllib.request.urlopen(
        "http://{}/history/{}".format(server_address, prompt_id)
    ) as response:
        return json.loads(response.read())


def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)["prompt_id"]
    output_images = {}
    start_time = None  # Declare this outside the loop

    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            print(message)

            if message["type"] == "executed":
                data = message["data"]
                end_time = time.time()  # Capture the current time
                execution_duration = (
                    end_time - start_time if start_time else 0
                )  # Calculate the execution time
                print(f"Node {data['node']} in {execution_duration:.2f} seconds")

            if message["type"] == "execution_start":
                data = message["data"]
                print(f"Execution started with prompt {data['prompt_id']}")
                start_time = time.time()  # Start a new timer here

            if message["type"] == "progress":
                data = message["data"]
                print(f"Progress {data['value']} of {data['max']}")

            if message["type"] == "executing":
                data = message["data"]
                print(f"Executing node {data['node']} with prompt {data['prompt_id']}")
                if data["node"] is None and data["prompt_id"] == prompt_id:
                    break  # Execution is done
        else:
            continue  # previews are binary data

    history = get_history(prompt_id)[prompt_id]
    for o in history["outputs"]:
        for node_id in history["outputs"]:
            node_output = history["outputs"][node_id]
            if "images" in node_output:
                images_output = []
                for image in node_output["images"]:
                    image_data = get_image(
                        image["filename"], image["subfolder"], image["type"]
                    )
                    images_output.append(image_data)
            output_images[node_id] = images_output

    return output_images


# prompt_text = """
# {"3": {"inputs": {"seed": 8566257, "steps": 20, "cfg": 8.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}, "class_type": "KSampler"}, "4": {"inputs": {"ckpt_name": "realisticVisionV40_v40VAE.safetensors"}, "class_type": "CheckpointLoaderSimple"}, "5": {"inputs": {"width": 512, "height": 512, "batch_size": 1}, "class_type": "EmptyLatentImage"}, "6": {"inputs": {"text": "beautiful scenery nature glass bottle landscape, , purple galaxy bottle,", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"}, "7": {"inputs": {"text": "text, watermark", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"}, "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"}, "9": {"inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]}, "class_type": "SaveImage"}}
# """

with open("./api-demo-v001.json", "r") as file:
    data = json.load(file)

# prompt = json.loads(prompt_text)
prompt = data
# set the text prompt for our positive CLIPTextEncode
# prompt["6"]["inputs"]["text"] = "masterpiece best quality man"

# set the seed for our KSampler node
prompt["3"]["inputs"]["seed"] = 1213


ws = websocket.WebSocket()
ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
images = get_images(ws, prompt)

# Commented out code to display the output images:

# for node_id in images:
#     for image_data in images[node_id]:
#         from PIL import Image
#         import io
#         image = Image.open(io.BytesIO(image_data))
#         image.show()

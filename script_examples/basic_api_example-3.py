import json
from urllib import request, parse
import random

# this is the ComfyUI api prompt format. If you want it for a specific workflow you can copy it from the prompt section
# of the image metadata of images generated with ComfyUI
# keep in mind ComfyUI is pre alpha software so this format will change a bit.

# this is the one for the default workflow
prompt_text = """
{"3": {"inputs": {"seed": 8566257, "steps": 20, "cfg": 8.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}, "class_type": "KSampler"}, "4": {"inputs": {"ckpt_name": "realisticVisionV40_v40VAE.safetensors"}, "class_type": "CheckpointLoaderSimple"}, "5": {"inputs": {"width": 512, "height": 512, "batch_size": 1}, "class_type": "EmptyLatentImage"}, "6": {"inputs": {"text": "beautiful scenery nature glass bottle landscape, , purple galaxy bottle,", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"}, "7": {"inputs": {"text": "text, watermark", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"}, "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"}, "9": {"inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]}, "class_type": "SaveImage"}}
"""


def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode("utf-8")
    req = request.Request("http://127.0.0.1:8188/prompt", data=data)
    request.urlopen(req)


prompt = json.loads(prompt_text)
# # set the text prompt for our positive CLIPTextEncode
# prompt["6"]["inputs"]["text"] = "masterpiece best quality man"

# # set the seed for our KSampler node
# prompt["3"]["inputs"]["seed"] = 5


queue_prompt(prompt)

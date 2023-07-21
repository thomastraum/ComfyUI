import json
from urllib import request, parse
import random

# this is the ComfyUI api prompt format. If you want it for a specific workflow you can copy it from the prompt section
# of the image metadata of images generated with ComfyUI
# keep in mind ComfyUI is pre alpha software so this format will change a bit.

# this is the one for the default workflow
with open("./upscale-workflow.json", "r") as file:
    data = json.load(file)

# get the "Prompt" property from the first dictionary in the list
# prompt_text = data[0]["Prompt"]
# prompt_text = dataq
prompt = data  # json.loads(data)
# print(prompt)
# set the text prompt for our positive CLIPTextEncode
# prompt["6"]["inputs"]["text"] = "masterpiece best quality man"

# print(prompt["6"]["inputs"]["text"])

# set the seed for our KSampler node
# prompt["3"]["inputs"]["seed"] = 5


def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode("utf-8")
    req = request.Request("http://127.0.0.1:8188/prompt", data=data)
    request.urlopen(req)


queue_prompt(prompt)

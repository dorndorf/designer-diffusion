import json
import gradio as gr
import torch
from diffusers import DiffusionPipeline

model_name = "stabilityai/stable-diffusion-xl-base-1.0"

pipe = DiffusionPipeline.from_pretrained(model_name, torch_dtype=torch.float16)
pipe = pipe.to("cuda")

with open('./lists/designers.json', 'r') as file:
    designers_dict = json.load(file)
with open('./lists/objects.json', 'r') as file:
    object_list = json.load(file)
with open("./lists/epochs.json", "r") as file:
    epochs = json.load(file)
  
def year_to_epoch(year, epochs):
    for epoch in epochs:
        if epoch["start"] <= year <= (epoch["end"] if epoch["end"] is not None else year + 1):
            return epoch["name"]
    return "now"

def generate(designer, object, year):
  epoch = year_to_epoch(year, epochs)
  prompt = f"a product photo of a {object} in the {epoch},  designed by {designer}, higly detailed, photorealistic"
  genimage = pipe(prompt=prompt, num_inference_steps=50).images[0]
  return genimage

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=1, min_width=600):
            designer = gr.Dropdown(designers_dict.keys(), label="designer")
            design_object = gr.Dropdown(object_list, label="object")
            year = gr.Number(label="year", value=2024)
        with gr.Column(scale=2, min_width=600):
            outputs = gr.Image(type='pil')
    
    generate_btn = gr.Button("generate")
    generate_btn.click(fn=generate, inputs=[designer, design_object, year], outputs=outputs, api_name="generate")

demo.launch(share=True)
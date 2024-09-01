import discord
from discord import app_commands
from diffusers import StableDiffusionPipeline
import torch

# Load the Stable Diffusion model
def load_model():
    # Load the Stable Diffusion model from Hugging Face
    pipe = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4", torch_dtype=torch.float16)
    pipe = pipe.to("cuda")  # Use GPU for faster generation
    return pipe

# Initialize the model globally when the cog is loaded
pipe = load_model()

@discord.app_commands.command(name='imagine', description='Generate an AI image based on your prompt')
async def imagine(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()  # Defer to give time for generation

    try:
        # Generate image based on the prompt
        image = pipe(prompt).images[0]  # Generate and get the first image
        image_path = "generated_image.png"
        image.save(image_path)  # Save the image locally

        # Send the generated image to the user
        file = discord.File(image_path, filename="generated_image.png")
        await interaction.followup.send(content="Here is your AI-generated image:", file=file)

    except Exception as e:
        await interaction.followup.send(content=f"An error occurred while generating the image: {e}")

def setup(client, tree):
    # Add the imagine command to the command tree
    tree.add_command(imagine)

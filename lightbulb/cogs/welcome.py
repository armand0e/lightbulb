import discord
from easy_pil import Font, Editor, load_image_async


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


# Event listener for new members joining
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel is not None:
        general_channel = discord.utils.get(member.guild.text_channels, name="general")
        general_channel_mention = (
            f"<#{general_channel.id}>" if general_channel else "#general"
        )
        await channel.send(
            f"Hey {member.mention} Welcome to {member.guild.name}! Make sure to check out: {general_channel_mention} We hope you enjoy your stay here. :purple_heart:"
        )

        image = await load_image_async(member.display_avatar.url)
        profile = Editor(image).resize((150, 150)).circle_image()
        background = Editor("bin/banner.png")

        poppins = Font.poppins(size=50, variant="bold")
        poppins_small = Font.poppins(size=25, variant="regular")
        poppins_light = Font.poppins(size=20, variant="light")

        background.paste(profile, (325, 90))
        background.ellipse((325, 90), 150, 150, outline="white", stroke_width=4)
        background.text(
            (400, 260),
            "WELCOME",
            color="white",
            font=poppins,
            align="center",
            stroke_width=2,
        )
        background.text(
            (400, 325),
            f"{member.name}",
            color="white",
            font=poppins_small,
            align="center",
        )
        background.text(
            (400, 360),
            f"You are the {ordinal(member.guild.member_count)} Member",
            color="#0BE7F5",
            font=poppins_small,
            align="center",
        )

        file = discord.File(fp=background.image_bytes, filename=f"{member.name}.png")
        await channel.send(file=file)


def setup(client, tree):
    # Use the client associated with the tree to add the listener directly
    client.event(on_member_join)  # Register the listener directly with the client

# Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Setup and Installation](#setup-and-installation)
4. [Command Reference](#command-reference)
5. [Event Handlers](#event-handlers)
6. [Utility Modules](#utility-modules)
7. [Code Conventions and Style](#code-conventions-and-style)
8. [Contributing](#contributing)
9. [License](#license)
10. [Acknowledgments](#acknowledgments)

## Project Overview

### Introduction
This project is a Discord bot built with discord.js that allows users to play, pause, resume, skip, and manage songs from YouTube in a voice channel. It also includes commands to view and manage the song queue and respond to basic commands.

### Features
- Play, pause, resume, and skip songs
- Manage the song queue
- Respond to basic commands like "ding" to check latency

## Project Structure

### Project Tree
```
discordjs-bot/
│
├── src/
│   ├── commands/
│   │   ├── play.js
│   │   ├── skip.js
│   │   ├── stop.js
│   │   ├── queue.js
│   │   ├── remove.js
│   │   ├── pause.js
│   │   ├── resume.js
│   │   └── ding.js
│   ├── events/
│   │   ├── ready.js
│   │   └── memberJoin.js
│   ├── utils/
│   │   ├── ytdlSource.js
│   │   └── playNextSong.js
│   ├── config.json
│   └── index.js
├── .env
├── package.json
└── README.md
```

## Setup and Installation

### Environment Setup
1. Clone the repository.
2. Install dependencies using `npm install`.
3. Create a `.env` file in the root directory and add your Discord bot token:
   ```
   DISCORD_TOKEN=your-bot-token-here
   ```

### Dependencies
- `discord.js` for interacting with the Discord API
- `@discordjs/voice` for voice functionalities
- `yt-dlp-exec` for downloading and processing YouTube videos

### Running the Bot
Run the bot using:
```
node src/index.js
```

## Command Reference

### `play.js`
- **Description**: Play a song from YouTube.
- **Usage**: `/play <search>`

```javascript
const { SlashCommandBuilder } = require('@discordjs/builders');
const { joinVoiceChannel } = require('@discordjs/voice');
const YTDLSource = require('../utils/ytdlSource');
const playNextSong = require('../utils/playNextSong');

let songQueue = [];
let nowPlaying = null;

module.exports = {
    data: new SlashCommandBuilder()
        .setName('play')
        .setDescription('Play a song from YouTube')
        .addStringOption(option =>
            option.setName('search').setDescription('The search term for the song').setRequired(true)
        ),
    async execute(interaction) {
        console.log('play command received');

        const search = interaction.options.getString('search');

        if (!interaction.member.voice.channel) {
            await interaction.reply('You need to be in a voice channel to use this command!');
            return;
        }

        // Join the voice channel
        const connection = joinVoiceChannel({
            channelId: interaction.member.voice.channel.id,
            guildId: interaction.guild.id,
            adapterCreator: interaction.guild.voiceAdapterCreator,
        });

        const player = await YTDLSource.fromUrl(search);
        songQueue.push(player);

        await interaction.reply(`**Added to queue:** ${player.title}`);

        if (!nowPlaying) {
            playNextSong(interaction, connection, player, songQueue);
        }
    },
};
```

### `skip.js`
- **Description**: Skip the currently playing song.
- **Usage**: `/skip`

```javascript
const { SlashCommandBuilder } = require('@discordjs/builders');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('skip')
        .setDescription('Skip the currently playing song'),
    async execute(interaction) {
        const connection = interaction.guild.voiceStates.cache.get(interaction.client.user.id)?.connection;
        if (connection?.dispatcher && connection.dispatcher.playing) {
            connection.dispatcher.end();
            await interaction.reply('Skipped the current song.');
        } else {
            await interaction.reply('No song is currently playing.');
        }
    },
};
```

### `stop.js`
- **Description**: Stop playing music and leave the voice channel.
- **Usage**: `/stop`

```javascript
const { SlashCommandBuilder } = require('@discordjs/builders');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('stop')
        .setDescription('Stop playing music and leave the voice channel'),
    async execute(interaction) {
        const connection = interaction.guild.voiceStates.cache.get(interaction.client.user.id)?.connection;
        if (connection) {
            connection.dispatcher.end();
            connection.disconnect();
            await interaction.reply('Disconnected from the voice channel.');
        } else {
            await interaction.reply("I'm not connected to a voice channel.");
        }
    },
};
```

### `queue.js`
- **Description**: View the song queue.
- **Usage**: `/queue`

```javascript
const { SlashCommandBuilder } = require('@discordjs/builders');

let songQueue = [];

module.exports = {
    data: new SlashCommandBuilder()
        .setName('queue')
        .setDescription('View the song queue'),
    async execute(interaction) {
        let queueMessage = "**Now playing:** No song is currently playing.\n**Queue:** No songs in queue";

        if (songQueue.length > 0) {
            const nowPlaying = songQueue[0];
            queueMessage = `**Now playing:** ${nowPlaying.title}\n**Queue:**\n`;

            for (let i = 1; i < songQueue.length; i++) {
                queueMessage += `*${i}.* ${songQueue[i].title}\n`;
            }
        }

        await interaction.reply(queueMessage);
    },
};
```

### `remove.js`
- **Description**: Remove a song from the queue.
- **Usage**: `/remove <index>`

```javascript
const { SlashCommandBuilder } = require('@discordjs/builders');

let songQueue = [];

module.exports = {
    data: new SlashCommandBuilder()
        .setName('remove')
        .setDescription('Remove a song from the queue')
        .addIntegerOption(option =>
            option.setName('index')
                .setDescription('The index of the song to remove')
                .setRequired(true)
        ),
    async execute(interaction) {
        const index = interaction.options.getInteger('index');

        if (index > 0 && index <= songQueue.length) {
            const removedSong = songQueue.splice(index - 1, 1)[0];
            await interaction.reply(`Removed **${removedSong.title}** from the queue.`);
        } else {
            await interaction.reply('Invalid index. Please provide a valid number.');
        }
    },
};
```

### `pause.js`
- **Description**: Pause the currently playing song.
- **Usage**: `/pause`

```javascript
const { SlashCommandBuilder } = require('@discordjs/builders');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('pause')
        .setDescription('Pause the currently playing song'),
    async execute(interaction) {
        const connection = interaction.guild.voiceStates.cache.get(interaction.client.user.id)?.connection;
        if (connection?.dispatcher && connection.dispatcher.playing) {
            connection.dispatcher.pause();
            await interaction.reply('Paused the current song.');
        } else {
            await interaction.reply('No song is currently playing.');
        }
    },
};
```

### `resume.js`
- **Description**: Resume the currently paused song.
- **Usage**: `/resume`

```javascript
const { SlashCommandBuilder } = require('@discordjs/builders');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('resume')
        .setDescription('Resume the currently paused song'),
    async execute(interaction) {
        const connection = interaction.guild.voiceStates.cache.get(interaction.client.user.id)?.connection;
        if (connection?.dispatcher && connection.dispatcher.paused) {
            connection.dispatcher.resume();
            await interaction.reply('Resumed the current song.');
        } else {
            await interaction.reply('No song is currently paused.');
        }
    },
};
```

### `ding.js`
- **Description**: Just a ding command to check latency.
- **Usage**: `/ding`

```javascript
const { SlashCommandBuilder } = require('@discordjs/builders');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('ding')
        .setDescription('Just a ding command'),
    async execute(interaction) {
        const latency = Math.round(interaction.client.ws.ping);
        await interaction.reply(`Dong! Latency is ${latency}ms`);
    },
};
```

## Event Handlers

### `memberJoin.js`
- **Description**: Sends a welcome message when a new member joins the server.

```javascript
module.exports = {
    name: 'guildMemberAdd',
    async execute(member) {
        const welcomeChannel = member.guild.channels.cache.find(channel => channel.name === 'welcome');
        if (welcomeChannel) {
            welcomeChannel.send(`Welcome to the server, ${member}!`);
        }
    },
};
```

### `ready.js`
- **Description**: Handles the `ready` event when the bot is logged in and ready.

```javascript
module.exports = {
    name: 'ready',
    once: true,
    execute(client) {
        console.log(`Logged in as ${client.user.tag}`);
    },
};
```

## Utility Modules

### `ytdlSource.js`
- **Description**: Provides functionality to download and process YouTube audio.

```javascript
const ytdl = require('yt-dlp-exec');
const { createAudioResource } = require('@discordjs/voice');

module.exports = {
    fromUrl: async (url) => {
        const info = await ytdl(url, { format: 'bestaudio' });
        return createAudioResource(info.url);
    },
};
```

### `playNextSong.js`
- **Description**: Manages playing the next song in the queue.

```javascript
const { AudioPlayerStatus } = require('@discordjs/voice');

module.exports = async (interaction, connection, player, songQueue) => {
    const audioPlayer = connection.player;

    if (!audioPlayer) {
        interaction.reply('Audio player not found.');
        return;
    }

    audioPlayer.play(player);

    audioPlayer.on(AudioPlayerStatus.Idle, () => {
        songQueue.shift();
        if (songQueue.length > 0) {
            const nextSong = songQueue[0];
            audioPlayer.play(nextSong);
        }
    });

    audioPlayer.on('error', error => {
        console.error(error);
        songQueue.shift();
        if (songQueue.length > 0) {
            const nextSong = songQueue[0];
            audioPlayer.play(nextSong);
        }
    });
};
```

## Code Conventions and Style
- Use consistent indentation (2 spaces).
- Follow JavaScript naming conventions for variables and functions.
- Include comments and documentation where necessary.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes. Ensure your code adheres to the project's coding style.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments
- Thanks to the developers of `discord.js` and `yt-dlp-exec` for their libraries.
- Special thanks to the community for their support and contributions.

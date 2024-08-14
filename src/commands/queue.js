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

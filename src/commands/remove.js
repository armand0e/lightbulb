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

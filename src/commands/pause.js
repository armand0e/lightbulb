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

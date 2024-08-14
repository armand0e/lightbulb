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

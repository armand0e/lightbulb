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

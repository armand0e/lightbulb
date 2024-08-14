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

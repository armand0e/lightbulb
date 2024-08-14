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

const { SlashCommandBuilder } = require('@discordjs/builders');
const { joinVoiceChannel, createAudioPlayer, createAudioResource, AudioPlayerStatus } = require('@discordjs/voice');
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

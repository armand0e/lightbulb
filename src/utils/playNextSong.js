const { createAudioPlayer, createAudioResource, AudioPlayerStatus } = require('@discordjs/voice');

const playNextSong = async (interaction, connection, player, songQueue) => {
    if (!connection) {
        await interaction.followUp('Bot is not connected to a voice channel.');
        return;
    }

    const audioPlayer = createAudioPlayer();
    const resource = createAudioResource(player.filename);

    audioPlayer.play(resource);
    connection.subscribe(audioPlayer);

    nowPlaying = player;

    audioPlayer.on(AudioPlayerStatus.Idle, () => {
        player.cleanup();
        if (songQueue.length > 0) {
            playNextSong(interaction, connection, songQueue.shift(), songQueue);
        } else {
            connection.disconnect();
            nowPlaying = null;
        }
    });

    await interaction.followUp(`**Now playing:** ${player.title}`);
};

module.exports = playNextSong;

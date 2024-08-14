module.exports = {
    name: 'guildMemberAdd',
    async execute(member) {
        const channel = member.guild.systemChannel;

        if (channel) {
            const generalChannel = member.guild.channels.cache.find(c => c.name === 'general');
            const generalChannelMention = generalChannel ? `<#${generalChannel.id}>` : '#general';

            await channel.send(
                `Hey ${member}, welcome to ${member.guild.name}! Make sure to check out: ${generalChannelMention}\nWe hope you enjoy your stay here. :purple_heart:`
            );
        }
    },
};

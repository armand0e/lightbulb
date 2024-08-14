const { exec } = require('yt-dlp-exec');
const { createAudioResource } = require('@discordjs/voice');
const fs = require('fs');
const path = require('path');

class YTDLSource {
    constructor(resource, info, filename) {
        this.resource = resource;
        this.title = info.title;
        this.url = info.webpage_url;
        this.filename = filename;
    }

    static async fromUrl(url) {
        const info = await exec(url, {
            dumpSingleJson: true,
            format: 'bestaudio',
            output: '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            restrictFilenames: true,
        });

        const filename = path.resolve(info._filename);
        const resource = createAudioResource(filename);
        return new YTDLSource(resource, info, filename);
    }

    cleanup() {
        if (this.filename && fs.existsSync(this.filename)) {
            fs.unlinkSync(this.filename);
            console.log(`Deleted file: ${this.filename}`);
        }
    }
}

module.exports = YTDLSource;

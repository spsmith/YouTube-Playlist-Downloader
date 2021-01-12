# YouTube-Playlist-Downloader
Simple Python program for downloading a source video playlist from YouTube. Sources that aren't a compatible file type are converted into mp4 via ffmpeg. Sources are automatically organized into subfolders based on channel.

Requires a config.yaml file with the following fields:
| Key | Value | Example |
| --- | --- | --- |
| source-folder | Location for downloaded files. | `D:\Sources` |
| output-template | youtube-dl output template (for naming files). Must contain **title**, **id**, and **uploader**, in that order.  | `%(title)s____%(id)s____%(uploader)s`
| separator | Separator character(s) used in youtube-dl's output template. | `____` |
| playlist-id | Playlist to download. | `PLMs_JcuNozJavHPJul81lF127gQ7_sZJG` |
| api-key | YouTube Data API key used for getting playlist info. | `get your own :)` |
| rate-limit | Rate limit for youtube-dl. | `1M` |
| channel-limit | An int. If more than this many videos are downloaded from a single channel, they will be moved to a subfolder with that channel's name. | `5` |
| extensions | Video file extensions used when organizing the main folder. Used to help the organizer ignore non-video files. | `- .mp4`, `- .mkv`, etc |
| dont-sleep | Location of the Don't Sleep exe. | `D:\DontSleep_x64_p.exe` |

Requirements:
[pip](https://pypi.org/project/pip/)
[Google API Client](https://github.com/googleapis/google-api-python-client)
[youtube-dl](https://github.com/ytdl-org/youtube-dl)
[FFmpeg](https://ffmpeg.org/)
[Don't Sleep](http://www.softwareok.com/?seite=Microsoft/DontSleep)

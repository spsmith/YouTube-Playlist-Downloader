import os
import shutil
import datetime
import subprocess
import ffmpeg
import yaml
import googleapiclient.discovery
from SourceVideo import SourceVideo

def DownloadSources(yaml_file, download=True, reencode=True, organize=True):
    #make sure youtube-dl is up to date
    subprocess.call(['pip', 'install', 'youtube-dl', '--upgrade'])

    #read yaml config
    if yaml_file is None:
        print("DownloadSources error! Need a .yaml file (none given).")
        return

    with open(yaml_file, 'r') as yf:
        config = yaml.safe_load(yf)

        #run don't sleep
        #https://www.softwareok.com/?seite=Microsoft/DontSleep
        dont_sleep = subprocess.Popen([config["dont-sleep"], '-bg', 'block_standby=1', 'block_shutdown=1', 'block_logoff=1', 'block_screensaver=0'], stdin=None, stdout=None, stderr=None, close_fds=True)

        if download:
            #scan all videos in sources folder already (and subfolders)
            print("Loading sources")
            sources = LoadSources(config["source-folder"], config["separator"], config["extensions"])
            source_ids = [s.ID for s in sources if s.ID is not None]

            #load ids of previously failed downloads
            failed_ids = []
            with open("failed.txt", 'r') as failed_f:
                for line in failed_f:
                    f_id = line.strip()
                    if len(f_id) > 0:
                        failed_ids.append(f_id)
            original_failed_ids = set(failed_ids)

            #get all videos from playlist
            #https://stackoverflow.com/questions/62345198/extract-individual-links-from-a-single-youtube-playlist-link-using-python
            print("Loading source playlist")
            youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=config["api-key"])
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId=config["playlist-id"]
            )
            response = request.execute()
            playlist_items = []
            while request is not None:
                response = request.execute()
                playlist_items += response["items"]
                request = youtube.playlistItems().list_next(request, response)

            #store video ids
            video_ids = [v["snippet"]["resourceId"]["videoId"] for v in playlist_items]

            #download videos
            print("Downloading sources")
            video_ids_to_download = [v_id for v_id in video_ids if v_id not in source_ids]
            for v_id in video_ids_to_download:
                subprocess.call(['youtube-dl', '-o', '{}\{}'.format(config["source-folder"], config["output-template"]), 'https://www.youtube.com/watch?v={}'.format(v_id), '-r', config["rate-limit"]])

                #after download is done, check if file exists
                #scan the source folder again to see if video was downloaded
                #(this seemed easier than trying to catch youtube-dl output and parse for errors...)
                current_sources = LoadSources(config["source-folder"], config["separator"], config["extensions"], False)
                downloaded_video = [d_v for d_v in current_sources if d_v.ID == v_id]

                #if the video is not here, that means it was unavailable for download or the download failed partway through
                if len(downloaded_video) < 1:
                    print("{}: download error!".format(v_id))
                    failed_ids.append(v_id)

            #write failed downloads to an output file
            with open("failed.txt", 'w') as failed_f:
                for line in failed_ids:
                    failed_f.write(line + '\n')

        if reencode:
            #load sources again
            sources = LoadSources(config["source-folder"], config["separator"], config["extensions"])

            #if any videos are an unsupported format, encode them
            print("Reencoding sources")
            for source in sources:
                if (source.Extension != '.mp4' and source.Extension != '.avi') or source.GetCodec() in config["bad-codecs"]:
                    print("Converting {} to valid mp4...".format(source.Name))
                    #Convert(source)
                    Reencode(source)
                    #original file will be deleted after reencode

        if organize:
            #load sources again(!) in case any files were reencoded
            sources = LoadSources(config["source-folder"], config["separator"], config["extensions"])

            #count videos from each channel (only move videos in main source folder)
            channels = [s.Channel for s in sources if s.Channel is not None]
            unique_channels = set(channels)
            channel_count = {}
            for channel in unique_channels:
                channel_count[channel] = channels.count(channel)

            #for any channels with enough videos, move them to a subfolder
            if config["channel-limit"] > 0:
                print("Organizing sources")
                channel_folders = {}
                for channel, count in channel_count.items():
                    if count >= int(config["channel-limit"]):
                        channel_folder = os.path.join(config["source-folder"], channel)
                        if not os.path.isdir(channel_folder):
                            os.mkdir(channel_folder)
                        channel_folders[channel] = channel_folder
                for source in sources:
                    if source.Folder is not config["source-folder"]:
                        #skip videos that are already in a folder
                        continue
                    if source.Channel in channel_folders.keys():
                        #otherwise, move them to the channel folder
                        source.MoveToFolder(channel_folders[source.Channel])

        if download:
            #last step: notify any new failed downloads
            new_failed = [f_id for f_id in failed_ids if f_id not in original_failed_ids]
            if len(new_failed) > 0:
                print("NEW FAILED IDS:")
                for n_f_id in new_failed:
                    print("\n\t{}".format(n_f_id))

        #close don't sleep when done
        subprocess.call([config["dont-sleep"], 'exit'])

        print("Done downloading sources")

def LoadSources(folder, separator, extensions, recursive=True):
    sources = []

    if os.path.isdir(folder):   
        for f in os.listdir(folder):
            filepath = os.path.join(folder, f)
            if os.path.isdir(filepath):
                if recursive:
                    #get all sources in the subfolder
                    sources = sources + LoadSources(os.path.join(folder, f), separator, extensions)
            elif os.path.isfile(filepath):
                #skip files without the correct extension
                if os.path.splitext(filepath)[1] in extensions:
                    #get source
                    source_video = SourceVideo(f, folder, separator)
                    sources.append(source_video)

    return sources

def Convert(source):
    #convert to mp4
    original_filepath = os.path.join(source.Folder, source.Filename)
    new_filepath = '.'.join([os.path.splitext(original_filepath)[0], 'mp4'])
    subprocess.call(['ffmpeg', '-i', original_filepath, '-codec', 'copy', new_filepath, '-y'])

    #delete original when done
    os.remove(original_filepath)

def Reencode(source):
    #move original file to a subfolder
    original_filepath = os.path.join(source.Folder, source.Filename)
    orig_dir = os.path.join(source.Folder, SourceVideo.ORIGINAL_DIR)
    if not os.path.exists(orig_dir):
        os.mkdir(orig_dir)
    current_filepath = os.path.join(orig_dir, source.Filename)
    shutil.move(original_filepath, current_filepath)

    #reencode to a valid codec
    new_filepath = '.'.join([os.path.splitext(original_filepath)[0], 'mp4'])
    subprocess.call(['ffmpeg', '-i', current_filepath, '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-c:a', 'copy', new_filepath, '-y'])

    #delete original when done
    os.remove(current_filepath)
    if len(os.listdir(orig_dir)) == 0:
        os.rmdir(orig_dir)


if __name__ == "__main__":
    DownloadSources("config/config.yaml")
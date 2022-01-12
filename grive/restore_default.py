import os

config_json = (
    '{"Sync_Dir": "Documents/sync_grive", "Sync_Cycle": 1, "Auto_Start": false}'
)
formats_json = '{\n  "application/vnd.google-apps.spreadsheet": ".xlsx",\n  "application/vnd.google-apps.form": ".xlsx",\n  "application/vnd.google-apps.document": ".docx",\n  "application/vnd.google-apps.presentation": ".pptx"\n}'

mime_dict_json = "{\n  \"application/vnd.google-apps.spreadsheet\": \"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\",\n  \"application/vnd.google-apps.form\": \"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\",\n  \"application/vnd.google-apps.document\": \"application/vnd.openxmlformats-officedocument.wordprocessingml.document\",\n  \"application/vnd.google-apps.presentation\": \"application/vnd.openxmlformats-officedocument.presentationml.presentation\",\n  \"folder\": \"application/vnd.google-apps.folder\",\n  \"audio_file_mimelist\" : \"['audio/mpeg', 'audio/x-mpeg-3', 'audio/mpeg3', 'audio/aiff', 'audio/x-aiff', 'audio/m4a', 'audio/mp4', 'audio/flac', 'audio/mp3']\",\n  \"movie_file_mimelist\" : \"['video/mp4', 'video/x-msvideo', 'video/mpeg', 'video/flv', 'video/quicktime', 'video/mkv']\",\n  \"image_file_mimelist\" : \"['image/png', 'image/jpeg', 'image/jpg', 'image/tiff']\",\n  \"document_file_mimelist\" : \"['application/powerpoint', 'applciation/mspowerpoint','application/x-mspowerpoint', 'application/pdf','application/x-dvi','application/vnd.ms-htmlhelp','application/x-mobipocket-ebook','application/vnd.ms-publisher']\",\n  \"google_docs_re\" : \"application/vnd.google-apps\"\n}"

readme = "\n                                        Grive by Tokyo Team\n\n    Grive aims at making life simpler when switching from Windows to Linux\n\n    This was developed with the aim to create a free and open source Google Drive client to make things simpler and\n    users won't need to switch to other cloud file storing platforms or have to pay for commercial clients doing the same\n\n        The parameters that can be used are:\n\n            * -re\n                Reset account associated with Google Drive.\n                Automatically executed at the first run of Grive\n\n            * -st\n                Start the automatic Grive syncing of the folders set as upload directories\n\n            * -x\n                Stop the automatic Grive syncing of the folders set as upload directories\n\n            * -y\n                Shows whether Grive is uploading automatically or not.\n\n            * -v\n                Shows the current version of the Grive.\n\n            * -config : Gives option to edit the configuration file on which automatic upload and download works\n                Sync Directory: The directory where the files are downloaded and uploaded, relative to home directory\n                    (e.g. for \"~/Documents/sync_grive\", can input \"Documents/sync_grive\" or absolute path)\n                    (Default is \"sync_grive\" directory in you Documents folder)\n                Synchronous Cycle: Integer in range 1 ~ 60\n                        (Default is '1')\n                Run at startup: [Y/N]\n                    'Y' Start up with the system and vise versa\n                    (Default is 'Y')\n                Configuration is stored in config.json as a dictionary which can be manually edited as well\n\n            * -ls [local/remote]\n                Lists all files and folders in your Google Drive (default or when \"remote\" used)\n                Lists all files and folders in your downloads directory (when \"local\" used)\n\n            * -ls_trash : Lists all files and folders in your Google Drive trash\n\n            * -ls_folder [folder_id] : Lists files and folders in the given folder id in your drive\n\n            * -ls_files [folder_id/\"root\"] : Lists all files recursively present in the folder id given\n\n            * -d [file_id1] [file_id2] ([folder]) : Downloads the given file from your Google Drive\n                Multiple files can be downloaded by putting file_ids one after the other\n                -do     : Download with overwrite mode\n                -df     : Specify the location to save the file at the end of the command\n                -dof    : Specify the location to save the file at the end of the command with overwrite mode\n                In case\n                    Don't specify [folder]  : Save at the corresponding location on remote\n                    Specify [folder]        : Save at the specified folder\n\n            * -u [file_name/folder_name] : Upload file/folder corresponding to the root given to Google Drive.\n                -uf: Upload file/folder to selected location on Google Drive.\n                -uo: Upload file/folder corresponding to the address given to Google Drive and overwrite mode.\n\n            * -sync : Sync specified folder to Google drive\n\n            * -s [file_id] ([mail]) : Outputs the shareable link of the file\n                -sr, -rs : Share with 'reader' permission\n                -sw, -ws : Share with 'writer' permission\n                -su, -us : Unshare file\n                In case\n                    Don't specify [mail]    : Share/Unshare with type every one\n                    [mail] = 'all'          : Unshare file completely\n\n            * -restore [file_id] : Restore files from trash.\n\n            * -d [file_id/folder_id]\n                Delete the mentioned file from Google Drive sync directory and Google Drive remote.\n                You can add multiple file_ids/folder_ids one after the other, e.g. -d [file_id1] [file_id2]\n                -dl [file_name/folder_name] : Delete the mentioned file from Google Drive sync directory\n                -dr [file_id/folder_id] : Delete the mentioned file from Google Drive remote\n\n            * -open, -o  :  Opens the Sync Directory in file explorer\n\n            * -help, -h  :  Show user manual\n"

version_info = "\n                          Grive 1.0.0\n                    --Made by Tokyo Team--\n                https://github.com/Tokyo-VN-2018\nA simple program to sync your folders with your Google Drive Account.\n\n"


def restore_default():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if os.path.exists(os.path.join(dir_path, "config_dicts")) is False:
        os.mkdir(os.path.join(dir_path, "config_dicts"))
    if os.path.exists(os.path.join(dir_path, "docs")) is False:
        os.mkdir(os.path.join(dir_path, "docs"))
    f = open("config_dicts/config.json", "w")
    f.write(config_json)
    f.close()
    f = open("config_dicts/formats.json", "w")
    f.write(formats_json)
    f.close()
    f = open("config_dicts/mime_dict.json", "w")
    f.write(mime_dict_json)
    f.close()
    f = open("docs/readme.txt", "w")
    f.write(readme)
    f.close()
    f = open("docs/version_info.txt", "w")
    f.write(version_info)
    f.close()

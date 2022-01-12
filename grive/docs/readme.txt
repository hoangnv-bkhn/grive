
                                        Grive by Tokyo Team

    Grive aims at making life simpler when switching from Windows to Linux

    This was developed with the aim to create a free and open source Google Drive client to make things simpler and
    users won't need to switch to other cloud file storing platforms or have to pay for commercial clients doing the same

        The parameters that can be used are:

            * -re
                Reset account associated with Google Drive.
                Automatically executed at the first run of Grive

            * -st
                Start the automatic Grive syncing of the folders set as upload directories

            * -x
                Stop the automatic Grive syncing of the folders set as upload directories

            * -y
                Shows whether Grive is uploading automatically or not.

            * -v
                Shows the current version of the Grive.

            * -xs
                Restore Grive to the default.

            * -config : Gives option to edit the configuration file on which automatic upload and download works
                Sync Directory: The directory where the files are downloaded and uploaded, relative to home directory
                    (e.g. for "~/Documents/sync_grive", can input "Documents/sync_grive" or absolute path)
                    (Default is "sync_grive" directory in you Documents folder)
                Synchronous Cycle: Integer in range 1 ~ 60
                        (Default is '1')
                Run at startup: [Y/N]
                    'Y' Start up with the system and vise versa
                    (Default is 'Y')
                Configuration is stored in config.json as a dictionary which can be manually edited as well

            * -ls [local/remote]
                Lists all files and folders in your Google Drive (default or when "remote" used)
                Lists all files and folders in your downloads directory (when "local" used)

            * -ls_trash : Lists all files and folders in your Google Drive trash

            * -ls_folder [folder_id] : Lists files and folders in the given folder id in your drive

            * -ls_files [folder_id/"root"] : Lists all files recursively present in the folder id given

            * -d [file_id1] [file_id2] ([folder]) : Downloads the given file from your Google Drive
                Multiple files can be downloaded by putting file_ids one after the other
                -do     : Download with overwrite mode
                -df     : Specify the location to save the file at the end of the command
                -dof    : Specify the location to save the file at the end of the command with overwrite mode
                In case
                    Don't specify [folder]  : Save at the corresponding location on remote
                    Specify [folder]        : Save at the specified folder

            * -u [file_name/folder_name] : Upload file/folder corresponding to the root given to Google Drive.
                -uf: Upload file/folder to selected location on Google Drive.
                -uo: Upload file/folder corresponding to the address given to Google Drive and overwrite mode.

            * -q [file_name/folder_name]: Exclude file/folder when upload, sync.
                -qc [file_name/folder_name]: Remove from exclusion list.

            * -z [file_name/folder_name]: Sync specified folder to Google drive

            * -s [file_id] ([mail]) : Outputs the shareable link of the file
                -sr     : Share with 'reader' permission
                -sw     : Share with 'writer' permission
                -us     : Unshare file
                In case
                    Don't specify [mail]    : Share/Unshare with type every one
                    [mail] = 'all'          : Unshare file completely

            * -restore [file_id] : Restore files from trash.

            * -da [file_id/folder_id]
                Delete the mentioned file from Google Drive sync directory and Google Drive remote.
                You can add multiple file_ids/folder_ids one after the other, e.g. -d [file_id1] [file_id2]
                -dl [file_name/folder_name] : Delete the mentioned file from Google Drive sync directory
                -dr [file_id/folder_id] : Delete the mentioned file from Google Drive remote

            * -open, -o  :  Opens the Sync Directory in file explorer

            * -help, -h  :  Show user manual

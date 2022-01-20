
                                        Grive by Tokyo Team

        Grive is a command-line client for Google Drive which lets you easily sync file between your local drive
        and Google Drive cloud storage.
        It lets you upload, download & share documents, photos, and other important files with anyone from anywhere.

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

            * -c : Gives option to edit the configuration file
                Sync Folder: The directory where the files are synchronized
                    (e.g. for "~/Documents/sync_grive", can input "Documents/sync_grive" or absolute path)
                    (Default is "sync_grive" directory in your Documents folder)
                Synchronous Cycle (Minute): Integer in range 1 ~ 60
                        (Default is '1' minute)
                Network Speed Limitation: Integer in range 1 ~ 5120 KB/s
                    (e.g. for limit download rate to 100 KB/s, can input "3 download 100",
                          for disable download limitation, input 3 download n)
                    (Default upload (download) is False)
                Run at startup: [Y/N]
                    'Y' Start up with the system and vise versa
                    (Default is 'Y')
                Configuration is stored in config.json as a dictionary which can be manually edited as well

            * -l [foder_id] 
                Lists all files and folders in your Google Drive and sync directory by id
                -lr : Lists all files and folders recursively present in the folder id given

            * -lp [path]
                Lists all files and folders in your Google Drive and sync directory by path
                -lpr : Lists all files and folders recursively present in the folder path given

            * -lt : Lists all files and folders in your Google Drive trash

            * -q : Caculate the volume of data used in your Google Drive

            * -d [file_id1] [file_id2]: Downloads the given file from your Google Drive
                User '-do' option with overwrite mode
                Save at the corresponding location on remote
                Multiple files can be downloaded by putting file_ids one after the other

              -df [file_id1] [file_id2] [folder]
                User '-dfo' option with overwrite mode
                Specify the location to save the file at the end of the command

            * -u [file_name/folder_name] : Upload file/folder corresponding to the root given to Google Drive.
                -uf: Upload file/folder to selected location on Google Drive.
                -uo: Upload file/folder corresponding to the address given to Google Drive and overwrite mode.

            * -e [file_name/folder_name]: Exclude file/folder when upload, sync.
                -ec [file_name/folder_name]: Remove from exclusion list.

            * -sy [folder_name]: Sync specified folder to Google drive

            * -s [file_id] ([mail]) : Outputs the shareable link of the file
                    Multiple mails can be specified by putting mail one after another
                    Don't specify [mail] to share/unshare with share mode "every one"
                -sr     : Share with 'reader' permission
                -sw     : Share with 'writer' permission
                -us     : Unshare file ( Specified [mail] = 'all' to unshare file completely)


            * -rt [file_id] : Restore files from trash.

            * -da [file_id/folder_id]
                Delete the mentioned file from Google Drive sync directory and Google Drive remote.
                You can add multiple file_ids/folder_ids one after the other, e.g. -d [file_id1] [file_id2]
                -dl [file_name/folder_name] : Delete the mentioned file from Google Drive sync directory
                -dr [file_id/folder_id] : Delete the mentioned file from Google Drive remote

            * -o  :  Opens the Sync Directory in file explorer

            * -h  :  Show user manual

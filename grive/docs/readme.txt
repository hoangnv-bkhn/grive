
                            Grive by Tokyo Team
----------------------------------------------------------------------------

Grive aims at making life simpler when switching from Windows to Linux

This was developed with the aim to create a free and open source Google Drive client to make things simpler and users won't
need to switch to other cloud file storing platforms or have to pay for commercial clients doing the same.

The parameters that can be used are:

* -reset

Reset account associated with Google Drive and give it the read and write permissions to your Google Drive. Automatically executed at the
first run of Grive.

* -start

Start the automatic Grive syncing of the folders set as upload directories.

* -stop

Stop the automatic Grive syncing of the folders set as upload directories.

* -status

Shows whether Grive is uploading automatically or not.

* -version

Shows the current version of the Grive.

* -config

Gives option to edit the configuration file on which automatic upload and download works.
- Sync Directory: The directory where the files are downloaded and uploaded, relative to home directory.
    (e.g. for "~/Documents/sync_grive", input "Documents/sync_grive")
    (Default is "sync_grive" directory in you Documents folder)
- Remove_Post_Upload: [Y/N] 'Y' removes the local file post upload. 'N' moves the file to GDrive sync folder
post upload.
    (Default is 'N')
- Share_Link: [Y/N] 'Y' puts the shareable link of the file uploaded in share.txt in Up_Directory.
    (Default is 'Y')

Configuration is stored in config.json as a dictionary which can be manually edited as well.

* -ls [local/remote]

Lists all files and folders in your Google Drive (default or when "remote" used).
Lists all files and folders in your downloads directory (when "local" used).

* -ls_trash

Lists all files and folders in your Google Drive trash.

* -ls_folder [folder_id]

Lists files and folders in the given folder id in your drive.

* -ls_files [folder_id/"root"]

Lists all files recursively present in the folder id given.

* -download [file_id1] [file_id2]

Downloads the given file from your Google Drive. Multiple files can be downloaded by putting file_ids one after the other.
Use "-d all" argument to download entire your entire Google Drive folder.

* -upload [file_add]

Upload file/folder corresponding to the address given to Google Drive, for one time.

* -sync

Sync specified folder to Google drive

* -share [file_id]

Outputs the shareable link of the file.

* -restore [file_id]

Restore files from trash.

* -remove [local/remote] [file_name/folder_name/file_id/folder_id]

Delete the mentioned file from Google Drive sync directory or Google Drive remote. Please input file_id/folder_id if it's a
remote file. You can add multiple file_ids/folder_ids one after the other, e.g. -remove remote [file_id1] [file_id2]

* -open [upload/download]

Opens the upload or download directory in file explorer.
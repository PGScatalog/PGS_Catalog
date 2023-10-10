#!/bin/bash

if [ $# -ne 2 ]; then
  echo "This script requires 2 parameters: <local_data_dir> and <ftp_dir>"
else
  local_data_dir=$1
  ftp_dir=$2

  if [ -d ${ftp_dir} ]; then

    if [ -d ${local_data_dir} ]; then

      # Copy data files to FTP
      echo "# Copy data files to FTP"
      echo "  > copy to FTP - started"
      cp -R  ${local_data_dir}/* ${ftp_dir}
      echo "  > copy to FTP - done"

      # Update write access on FTP
      echo "# Update write access on FTP"
      cd ${ftp_dir}
      find pgs_scores_list.txt -type f -exec chmod -f 664 {} +
      echo "  > pgs_scores_list.txt file - done"
      find scores/ -type d -exec chmod -f 775 {} +
      echo "  > scores directories - done"
      find scores/ -type f -exec chmod -f 664 {} +
      echo "  > scores files - done"
      find metadata/ -type d -exec chmod -f 775 {} +
      echo "  > metadata directories - done"
      find metadata/ -type f -exec chmod -f 664 {} +
      echo "  > metadata files - done"
    else
      echo "Directory '${local_data_dir}' can't be found"
    fi
  else
    echo "Directory '${ftp_dir}' can't be found"
  fi
fi

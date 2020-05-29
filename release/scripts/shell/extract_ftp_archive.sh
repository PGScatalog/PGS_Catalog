#!/bin/bash

new_ftp_content='new_ftp_content'

if [ "$#" -eq 2 ]; then
  uploaded_file=$1
  temp_dir=$2
  if [ ! -d $temp_dir ]; then
    echo "Directory '${temp_dir}' can't be found"
  elif [ ! -f $uploaded_file ]; then
    echo "File '${uploaded_file}' can't be found"
  elif [ ! "${uploaded_file#*.}" == "tar.gz" ]; then
    echo "File '${uploaded_file}' can't be processed: expected a tar.gz file"
  else
    filename=${uploaded_file##*/}
    cd $temp_dir
    if [ -d $new_ftp_content ]; then
      rm -rf $new_ftp_content
    fi
    cp $uploaded_file ./$filename
    tar xf $filename
    find . -name '.DS_Store' -type f -delete
    find . -name '._.DS_Store' -type f -delete
    echo "Copy and extraction - done"
  fi
else
  echo "Missing parameters of the script (path to updloaded file and path to temp dir)"
fi

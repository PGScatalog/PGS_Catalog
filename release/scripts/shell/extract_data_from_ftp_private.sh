new_ftp_content='new_ftp_content'

if [ "$#" -eq 4 ]; then
  uploaded_file=$1
  temp_dir=$2
  uploaded_scoring_dir=$3
  prod_scoring_dir=$4
  # Uploaded metadata
  echo "# Step 1 - Extract Metadata"
  if [ ! -d $temp_dir ]; then
    echo "Directory '${temp_dir}' can't be found"
    exit 1
  elif [ ! -f $uploaded_file ]; then
    echo "File '${uploaded_file}' can't be found"
    exit 1
  elif [ ! "${uploaded_file#*.}" == "tar.gz" ]; then
    echo "File '${uploaded_file}' can't be processed: expected a tar.gz file"
    exit 1
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

  # Uploaded scores
  echo "# Step 2 - Copy new scoring files to production directory"
  if [ ! -d $uploaded_scoring_dir ]; then
    echo "FTP Scoring directory '${uploaded_scoring_dir}' can't be found"
    exit 1
  if [ ! -d $prod_scoring_dir ]; then
    echo "Production Scoring directory '${prod_scoring_dir}' can't be found"
    exit 1

    count_new_pgs=0
    for pgs_file_path in ${uploaded_scoring_dir}/*.txt.gz
    do
      file_name=`basename "${pgs_file_path}"`
      if [ ! -f "${prod_scoring_dir}/${file_name}" ]; then
        cp $pgs_file_path $prod_scoring_dir/
        if [ -f "${prod_scoring_dir}/${file_name}" ]; then
          echo "- New file '${file_name}' has been copied to '${prod_scoring_dir}'"
          ((count_new_pgs++))
        else
          echo ">>>>> ERROR! File '${file_name}' couldn't be copied to '${prod_scoring_dir}'!"
        fi
      fi
    done
    echo "Number of PGS files successfully copied: ${count_new_pgs}"
    chmod g+w ${prod_scoring_dir}/*

else
  echo "Missing parameters of the script:"
  echo "- path to uploaded file (on FTP private)"
  echo "- path to temp dir"
  echo "- path to uploaded Scoring files (on FTP private)"
  echo "- path to production scoring directory"
fi

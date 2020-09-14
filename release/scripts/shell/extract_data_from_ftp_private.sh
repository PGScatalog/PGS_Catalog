new_ftp_content='new_ftp_content'
scores_list_file='pgs_scores_list.txt'

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
  fi
  if [ ! -d $prod_scoring_dir ]; then
    echo "Production Scoring directory '${prod_scoring_dir}' can't be found"
    exit 1
  fi
  # Extract the list of released PGS IDs
  if [ ! -f "${new_ftp_content}/${scores_list_file}" ]; then
    echo "File '${scores_list_file}' can't be found in ${new_ftp_content}!"
    exit 1
  else
    score_list_string=$(cat "${new_ftp_content}/${scores_list_file}" | tr "\n" " ")
    score_list_array=(${score_list_string})
  fi

  # Copy Scoring files
  count_new_pgs=0
  count_updated_pgs=0
  count_skipped_pgs=0

  for pgs_file_path in ${uploaded_scoring_dir}/*.txt.gz
  do
    file_name=`basename "${pgs_file_path}"`
    score_id=`echo $file_name | cut -f 1 -d '.'`
    if [[ ! " ${score_list_array[@]} " =~ " ${score_id} " ]]; then
      echo "> File '${file_name}' has been skipped: not present in the list of released scores!"
      ((count_skipped_pgs++))
      continue
    fi
    prod_file="${prod_scoring_dir}/${file_name}"
    if [ ! -f "${prod_file}" ]; then
      cp $pgs_file_path $prod_scoring_dir/
      if [ -f "${prod_file}" ]; then
        echo "- New file '${file_name}' has been copied to '${prod_scoring_dir}'"
        ((count_new_pgs++))
      else
        echo ">>>>> ERROR! File '${file_name}' couldn't be copied to '${prod_scoring_dir}'!"
      fi
    else
      md5_upload=`md5sum ${pgs_file_path} | awk '{ print $1 }'`
      md5_prod=`md5sum ${prod_file} | awk '{ print $1 }'`
      if [[ "$md5_upload" != "$md5_prod" ]]; then
        cp $pgs_file_path $prod_scoring_dir/
        if [ -f "${prod_file}" ]; then
          echo " > Updated file '${file_name}' has been copied to '${prod_scoring_dir}'"
          ((count_updated_pgs++))
        else
          echo ">>>>> ERROR! Updated file '${file_name}' couldn't be copied to '${prod_scoring_dir}'!"
        fi
      fi
    fi
  done
  total_count=$((${count_new_pgs}+${count_updated_pgs}))
  echo "Number of PGS files successfully copied: ${total_count} (New: ${count_new_pgs} | Updated: ${count_updated_pgs} | Skipped: ${count_skipped_pgs})"
  chmod g+w ${prod_scoring_dir}/*

else
  echo "Missing parameters of the script:"
  echo "- path to uploaded file (on FTP private)"
  echo "- path to temp dir"
  echo "- path to uploaded Scoring files (on FTP private)"
  echo "- path to production scoring directory"
fi

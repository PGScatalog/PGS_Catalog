#!/bin/bash

if [ $# -eq  "0" ]; then
  echo "Missing parameter of the script (the root directory)"
else
  if [ -d $1 ]; then
    cd $1
    find scores/ -type d -exec chmod 775 {} +
    echo "> scores directories - done"
    find scores/ -type f -exec chmod 664 {} +
    echo "> scores files - done"
    find metadata/ -type d -exec chmod 775 {} +
    echo "> metadata directories - done"
    find metadata/ -type f -exec chmod 664 {} +
    echo "> metadata files - done"
  else
    echo "Directory '$1' can't be found"
  fi
fi

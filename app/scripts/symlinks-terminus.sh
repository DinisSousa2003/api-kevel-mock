#!/bin/bash

# Step 1: Ensure the container is running
docker ps | grep terminusdb > /dev/null
if [ $? -ne 0 ]; then
  echo "Error: Container 'terminusdb' is not running."
  exit 1
fi

# Step 2: Open bash for the container and execute commands
docker exec terminusdb bash -c "
  cd /app/terminusdb/storage && \
  echo 'Current directory: $(pwd)' && \
  for dir in db/*; do 
    name=\$(basename \"\$dir\")
    linkname=\"db\$name\"
    if [ ! -e \"\$linkname\" ]; then
      echo \"Creating symlink: ln -s db/\$name \$linkname\"
      ln -s \"db/\$name\" \"\$linkname\"
    else
      echo \"Skipping existing: \$linkname\"
    fi
  done
"

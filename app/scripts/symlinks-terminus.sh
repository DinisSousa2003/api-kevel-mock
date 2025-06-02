#!/bin/bash

cd /app/terminusdb/storage || {
  echo "Error: Cannot change to /app/terminusdb/storage"
  exit 1
}

echo "Current directory: $(pwd)"

for dir in db/*; do 
  name=$(basename "$dir")
  linkname="db$name"
  if [ ! -e "$linkname" ]; then
    echo "Creating symlink: ln -s db/$name $linkname"
    ln -s "db/$name" "$linkname"
  else
    echo "Skipping existing: $linkname"
  fi
done

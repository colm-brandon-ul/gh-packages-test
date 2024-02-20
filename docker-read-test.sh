#!/bin/bash


for dockerfile in $(find . -name Dockerfile); do
          dir_of_image=$(dirname "$dockerfile")
          echo "Building image in $dir_of_image"
          # Get the tail of the directory
          image_name=$(basename "$dir_of_image")
          image_name=${image_name//\//-}
          echo "Image Name; $image_name"
          docker_image_name="cinco-de-bio-${image_name//[^a-zA-Z0-9]/-}"

          # Check if the path is newly added - currently solution does not work

          if git log --quiet --diff-filter=A HEAD~1..HEAD -- "$dir_of_image"; then
            echo "$image_name is a newly added path"

          else
            echo "$image_name is not a newly added path"
            if git diff --quiet HEAD HEAD~1 -- "$image_name"; then
              echo "No changes in $image_name, skipping build"
            else
              echo "Changes in $image_name, building image"
            fi
          fi

          
        done
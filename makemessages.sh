#!/bin/bash

# If executed from lava, go back to project folder
run_from_lava=false
if [[ "$PWD" == *"/lava" ]]; then
    cd ..
    run_from_lava=true
fi

. ./setenv.sh

# Get name of Django app from command-line argument
app=$1

# Remove the first item from the command-line arguments (app name in this case)
shift

cd $app

mkdir -p "locale"

# Get list of locales from remaining command-line arguments
locales=("$@")

# Loop through each locale and run makemessages
for locale in "${locales[@]}"
do
    echo "Generating messages for $locale in app $app..."
    python ../manage.py makemessages -l $locale \
                                  -d django \
                                  -e py,html \
                                  -i "venv/*" \
                                  -i ".git/*" \
                                  -i "static/*" \
                                  -i "media/*" \
                                  -i ".idea/*" \
                                  -i "*/migrations/*" \
                                  -i '*.log' \
                                  -i '*.pot' \
                                  -i '*.md' \
                                  -i '*.txt' \
                                  -i '*.pyc' \
                                  -i '*.pyo' \
                                  -i '*.zip' \
                                  -i '*.tar.gz' \
                                  -i '*.tar.bz2' \
                                  -i '*.gz' \
                                  -i '*.bz2' \
                                  -i '*.DS_Store' \
                                  -i '*.swo' \
                                  -i '*.swp' \
                                  -i '*.mo' \
                                  -i '*.po' \
                                  -i '*.json' \
                                  -i '*.ini' \
                                  -i '*.conf' \
                                  -i '*.log.*' \
                                  -i '*.pid' \
                                  -i '*.coverage' \
                                  -i '*.css' \
                                  -i '*.js' \
                                  -i '*.scss' \
                                  -i '*.png' \
                                  -i '*.jpg' \
                                  -i '*.jpeg' \
                                  -i '*.gif' \
                                  -i '*.svg' \
                                  -i '*.ico' \
                                  -i '*.ttf' \
                                  -i '*.woff' \
                                  -i '*.woff2' \
                                  -i '*.otf' \
                                  -i '*.eot' \
                                  -i '*.mp3' \
                                  -i '*.mp4' \
                                  -i '*.pdf' \
                                  -i '*.doc' \
                                  -i '*.docx' \
                                  -i '*.xls' \
                                  -i '*.xlsx' \
                                  -i '*.ppt' \
                                  -i '*.pptx' \
                                  -i '*.zip' \
                                  -i '*.rar' \
                                  -i '*.tar' \
                                  -i '*.7z' \
                                  -i '*.bz2' \
                                  -i '*.gz' \
                                  -i '*.json' \
                                  -i '*.xml' \
                                  -i '*.yaml' \
                                  -i '*.yml'
done

cd ..

# Go back to lava folder
if [ "$run_from_lava" = true ]; then
    cd lava
fi

#!/bin/bash
echo "1: $1";
echo "2: $2";
echo "3: $3";
echo "4: $4";
echo "5: $5";
echo "$(npm bin)"
$4 --server "$1" "$2"  -c "browserName='chrome' goog:chromeOptions.args=[disable-infobars, headless]" --output-directory="$3";



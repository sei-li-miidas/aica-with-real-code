#!/bin/bash

REPO_URL="git@github.com:modelcontextprotocol/inspector.git"
FOLDER="inspector"
DEV_URL="http://localhost:6274"

# Check if the "inspector" folder exists
if [ -d "$FOLDER" ]; then
  echo "Folder '$FOLDER' exists. Pulling latest changes..."
  cd "$FOLDER" || { echo "Failed to cd into $FOLDER"; exit 1; }
  git pull || { echo "Failed to pull latest changes"; exit 1; }
else
  echo "Folder '$FOLDER' does not exist. Cloning repository..."
  git clone "$REPO_URL" || { echo "Failed to clone repository"; exit 1; }
  cd "$FOLDER" || { echo "Failed to cd into $FOLDER"; exit 1; }
fi

# Install dependencies and run the development server
echo "Installing dependencies..."
npm i || { echo "npm install failed"; exit 1; }

echo "Starting development server..."
# Run "npm run dev" in the background so that the script can continue
npm run build
npm run start &

# Optionally, wait a few seconds for the server to start
sleep 5

# Open the URL in the default browser
echo "Opening ${DEV_URL} in the default browser..."

wait

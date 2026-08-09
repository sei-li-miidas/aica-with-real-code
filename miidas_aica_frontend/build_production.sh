#!/bin/bash

# rename .env.local to .env.local.bak
mv .env.local .env.local.example

# rename .env.production.bak to .env.production
mv .env.production.example .env.production

# build
npm run build

# rename .env files
mv .env.production .env.production.example
mv .env.local.example .env.local

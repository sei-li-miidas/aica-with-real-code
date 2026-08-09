#!/bin/bash

# 事前にSESSION_IDをexportしてください
# export SESSION_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# これらは成功するケースですので、「保存しました」と出力されたらOKです。

curl -X POST \
  "http://localhost:8000/agent/profile/education" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "school_type": 2,
    "graduation_year": 2013,
    "english_level": 3
}
EOF

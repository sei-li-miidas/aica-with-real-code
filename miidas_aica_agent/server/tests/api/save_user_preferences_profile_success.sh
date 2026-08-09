#!/bin/bash

# 事前にSESSION_IDをexportしてください
# export SESSION_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

echo ""
echo "居住地希望＋職種キーワード希望"
curl -X POST \
  "http://localhost:8000/agent/profile/preferences" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "income": 350,
    "work_location_from_residence": true,
    "job_type_from_keywords": true,
    "job_type_keywords": ["オフィスワーク", "総務", "事務"],
    "job_change_timeline": 4,
    "job_matching_service": true
}
EOF

echo ""
echo "---------------------------------------------"
echo "居住地以外希望＋職種キーワード以外希望"
curl -X POST \
  "http://localhost:8000/agent/profile/preferences" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "income": 350,
    "work_location_from_residence": false,
    "work_location_ids": [111007, 139999, 141003],
    "job_type_from_keywords": false,
    "job_type_ids": [101310, 101311],
    "job_change_timeline": 4,
    "job_matching_service": true
}
EOF
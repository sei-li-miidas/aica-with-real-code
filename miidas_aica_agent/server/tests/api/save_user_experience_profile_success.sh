#!/bin/bash

# 事前にSESSION_IDをexportしてください
# export SESSION_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

echo ""
echo "成功するユーザー経歴保存"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 3,
    "management_experience_people": null,
    "worked_company_name": "有限会社山田商会",
    "worked_company_industry_id": 101010,
    "worked_company_size": 4,
    "worked_company_main_job_type_id": 202020,
    "worked_company_income": 350,
    "worked_company_joined_at": "2020-04-01",
    "worked_company_left_at": "2025-03-31"
}
EOF

echo ""
echo "退職年月なし（在籍中）"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 3,
    "management_experience_people": null,
    "worked_company_name": "有限会社山田商会",
    "worked_company_industry_id": 101010,
    "worked_company_size": 4,
    "worked_company_main_job_type_id": 202020,
    "worked_company_income": 350,
    "worked_company_joined_at": "2020-04-01",
    "worked_company_left_at": ""
}
EOF

echo ""
echo "---------------------------------------------"
echo "ゼロ社経験は企業情報未入力でもOK"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  --data-binary '{"number_of_companies_worked":1}'

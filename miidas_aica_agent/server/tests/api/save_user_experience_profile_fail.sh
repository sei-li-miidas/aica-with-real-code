#!/bin/bash

# 事前にSESSION_IDをexportしてください
# export SESSION_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 経験社数 1：0社, 2：1社, 3：2社, 4：3社, 5：4社, 6：5社, 7：6社, 8：7社, 9：8社, 10：9社, 11：10社以上
# number_of_companies_workedがゼロ社の場合、マスタでは「1」

echo ""
echo "---------------------------------------------"
echo "空のオブジェクト"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  --data-binary '{}'

echo ""
echo "---------------------------------------------"
echo "マネジメント経験人数がマスタ範囲外（ゼロ）"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 1,
    "management_experience_people": 0
}
EOF

echo ""
echo "---------------------------------------------"
echo "マネジメント経験人数がマスタ範囲外（6）"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 1,
    "management_experience_people": 6
}
EOF

echo ""
echo "---------------------------------------------"
echo "1社経験しているのに企業名が未入力"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 2,
    "management_experience_people": null,
    "worked_company_name": "",
    "worked_company_industry_id": 101010,
    "worked_company_size": 4,
    "worked_company_main_job_type_id": 202020,
    "worked_company_income": 350,
    "worked_company_joined_at": "2020-04-01",
    "worked_company_left_at": "2025-03-31"
}
EOF

echo ""
echo "---------------------------------------------"
echo "1社経験しているのに企業名が255文字以上"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 2,
    "management_experience_people": null,
    "worked_company_name": "abcdefghijklmnopqrstuvwxyabcdefghijklmnopqrstuvwxyabcdefghijklmnopqrstuvwxyabcdefghijklmnopqrstuvwxyabcdefghijklmnopqrstuvwxyabcdefghijklmnopqrstuvwxyabcdefghijklmnopqrstuvwxyabcdefghijklmnopqrstuvwxyabcdefghijklmnopqrstuvwxyabcdefghijklmnopqrstuvwxyabcdef",
    "worked_company_industry_id": 101010,
    "worked_company_size": 4,
    "worked_company_main_job_type_id": 202020,
    "worked_company_income": 350,
    "worked_company_joined_at": "2020-04-01",
    "worked_company_left_at": "2025-03-31"
}
EOF

echo ""
echo "---------------------------------------------"
echo "1社経験しているのに業種IDが未入力"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 2,
    "management_experience_people": null,
    "worked_company_name": "有限会社山田商会",
    "worked_company_industry_id": null,
    "worked_company_size": 4,
    "worked_company_main_job_type_id": 202020,
    "worked_company_income": 350,
    "worked_company_joined_at": "2020-04-01",
    "worked_company_left_at": "2025-03-31"
}
EOF

echo ""
echo "---------------------------------------------"
echo "1社経験しているのに企業規模が未入力"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 2,
    "management_experience_people": null,
    "worked_company_name": "有限会社山田商会",
    "worked_company_industry_id": 101010,
    "worked_company_size": null,
    "worked_company_main_job_type_id": 202020,
    "worked_company_income": 350,
    "worked_company_joined_at": "2020-04-01",
    "worked_company_left_at": "2025-03-31"
}
EOF

echo ""
echo "---------------------------------------------"
echo "企業規模がマスタ範囲外（ゼロ）"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 2,
    "management_experience_people": null,
    "worked_company_name": "有限会社山田商会",
    "worked_company_industry_id": 101010,
    "worked_company_size": 0,
    "worked_company_main_job_type_id": 202020,
    "worked_company_income": 350,
    "worked_company_joined_at": "2020-04-01",
    "worked_company_left_at": "2025-03-31"
}
EOF

echo ""
echo "---------------------------------------------"
echo "企業規模がマスタ範囲外（8）"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 2,
    "management_experience_people": null,
    "worked_company_name": "有限会社山田商会",
    "worked_company_industry_id": 101010,
    "worked_company_size": 8,
    "worked_company_main_job_type_id": 202020,
    "worked_company_income": 350,
    "worked_company_joined_at": "2020-04-01",
    "worked_company_left_at": "2025-03-31"
}
EOF

echo ""
echo "---------------------------------------------"
echo "職種が未入力"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 2,
    "management_experience_people": null,
    "worked_company_name": "有限会社山田商会",
    "worked_company_industry_id": 101010,
    "worked_company_size": 7,
    "worked_company_main_job_type_id": null,
    "worked_company_income": 350,
    "worked_company_joined_at": "2020-04-01",
    "worked_company_left_at": "2025-03-31"
}
EOF

echo ""
echo "---------------------------------------------"
echo "年収がゼロ"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 2,
    "management_experience_people": null,
    "worked_company_name": "有限会社山田商会",
    "worked_company_industry_id": 101010,
    "worked_company_size": 7,
    "worked_company_main_job_type_id": 202020,
    "worked_company_income": 0,
    "worked_company_joined_at": "2020-04-01",
    "worked_company_left_at": "2025-03-31"
}
EOF

echo ""
echo "---------------------------------------------"
echo "年収が10,001万円以上"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 2,
    "management_experience_people": null,
    "worked_company_name": "有限会社山田商会",
    "worked_company_industry_id": 101010,
    "worked_company_size": 7,
    "worked_company_main_job_type_id": 202020,
    "worked_company_income": 10001,
    "worked_company_joined_at": "2020-04-01",
    "worked_company_left_at": "2025-03-31"
}
EOF

echo ""
echo "---------------------------------------------"
echo "入社年月が1940年より前"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 2,
    "management_experience_people": null,
    "worked_company_name": "有限会社山田商会",
    "worked_company_industry_id": 101010,
    "worked_company_size": 7,
    "worked_company_main_job_type_id": 202020,
    "worked_company_income": 350,
    "worked_company_joined_at": "1939-04-01",
    "worked_company_left_at": "2025-03-31"
}
EOF

echo ""
echo "---------------------------------------------"
echo "入社年月が未来"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 2,
    "management_experience_people": null,
    "worked_company_name": "有限会社山田商会",
    "worked_company_industry_id": 101010,
    "worked_company_size": 7,
    "worked_company_main_job_type_id": 202020,
    "worked_company_income": 350,
    "worked_company_joined_at": "2050-04-01",
    "worked_company_left_at": "2025-03-31"
}
EOF

echo ""
echo "---------------------------------------------"
echo "退社年月が入社年月より前"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 2,
    "management_experience_people": null,
    "worked_company_name": "有限会社山田商会",
    "worked_company_industry_id": 101010,
    "worked_company_size": 7,
    "worked_company_main_job_type_id": 202020,
    "worked_company_income": 350,
    "worked_company_joined_at": "2020-04-01",
    "worked_company_left_at": "2020-03-31"
}
EOF

echo ""
echo "---------------------------------------------"
echo "退社年月が未来"
curl -X POST \
  "http://localhost:8000/agent/profile/experience" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "number_of_companies_worked": 2,
    "management_experience_people": null,
    "worked_company_name": "有限会社山田商会",
    "worked_company_industry_id": 101010,
    "worked_company_size": 7,
    "worked_company_main_job_type_id": 202020,
    "worked_company_income": 350,
    "worked_company_joined_at": "2020-04-01",
    "worked_company_left_at": "2050-03-31"
}
EOF




#!/bin/bash

# 事前にSESSION_IDをexportしてください
# export SESSION_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# これらは失敗するケースですので、「保存しました」と出力されなければOKです。

echo ""
echo "---------------------------------------------"
echo "空のオブジェクト"
curl -X POST \
  "http://localhost:8000/agent/profile/education" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  --data-binary "{}"

echo ""
echo "---------------------------------------------"
echo "学校種別なし"
curl -X POST \
  "http://localhost:8000/agent/profile/education" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "school_type": null,
    "graduation_year": 2013,
    "english_level": 3
}
EOF

echo ""
echo "---------------------------------------------"
echo "学校種別マスタ範囲外（ゼロ）"
curl -X POST \
  "http://localhost:8000/agent/profile/education" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "school_type": 0,
    "graduation_year": 2013,
    "english_level": 3
}
EOF

echo ""
echo "---------------------------------------------"
echo "学校種別マスタ範囲外（8）"
curl -X POST \
  "http://localhost:8000/agent/profile/education" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "school_type": 8,
    "graduation_year": 2013,
    "english_level": 3
}
EOF

echo ""
echo "---------------------------------------------"
echo "卒業年なし"
curl -X POST \
  "http://localhost:8000/agent/profile/education" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "school_type": 2,
    "graduation_year": null,
    "english_level": 3
}
EOF

echo ""
echo "---------------------------------------------"
echo "卒業年が未来"
curl -X POST \
  "http://localhost:8000/agent/profile/education" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "school_type": 2,
    "graduation_year": 2050,
    "english_level": 3
}
EOF

echo ""
echo "---------------------------------------------"
echo "英語力なし"
curl -X POST \
  "http://localhost:8000/agent/profile/education" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "school_type": 2,
    "graduation_year": 2013,
    "english_level": null
}
EOF

echo ""
echo "---------------------------------------------"
echo "英語力マスタ範囲外（ゼロ）"
curl -X POST \
  "http://localhost:8000/agent/profile/education" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "school_type": 2,
    "graduation_year": 2013,
    "english_level": 0
}
EOF

echo ""
echo "---------------------------------------------"
echo "英語力マスタ範囲外（5）"
curl -X POST \
  "http://localhost:8000/agent/profile/education" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "school_type": 2,
    "graduation_year": 2013,
    "english_level": 5
}
EOF

#!/bin/bash

# 事前にSESSION_IDをexportしてください
# export SESSION_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# これらは失敗するケースですので、「保存しました」と出力されなければOKです。

echo ""
echo "空のユーザープロフィール"
curl -X POST \
  "http://localhost:8000/agent/profile/basic" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  --data-binary "{}"

echo ""
echo "---------------------------------------------"
echo "電話番号 14桁"
curl -X POST \
  "http://localhost:8000/agent/profile/basic" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "gender": 1,
    "last_name": "山田",
    "first_name": "太郎",
    "last_name_kana": "ヤマダ",
    "first_name_kana": "タロウ",
    "birthday": "1991-02-03",
    "email": "yamada.taro@example.com",
    "password": "password1234",
    "phone_no": "01234567890123",
    "residence_prefecture_name": "埼玉県",
    "residence_city_name": "さいたま市"
}
EOF

echo ""
echo "---------------------------------------------"
echo "電話番号 9桁"
curl -X POST \
  "http://localhost:8000/agent/profile/basic" \
  -H "Content-Type: application/json" \
  -H "X-SESSION-ID: $SESSION_ID" \
  -d @- <<-EOF
{
    "gender": 1,
    "last_name": "山田",
    "first_name": "太郎",
    "last_name_kana": "ヤマダ",
    "first_name_kana": "タロウ",
    "birthday": "1991-02-03",
    "email": "yamada.taro@example.com",
    "password": "password1234",
    "phone_no": "012345678",
    "residence_prefecture_name": "埼玉県",
    "residence_city_name": "さいたま市"
}
EOF
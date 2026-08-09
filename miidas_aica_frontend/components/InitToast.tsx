import "./InitToast.scss";
import { useState } from "react";
import Card from "@mui/material/Card";
import CardHeader from "@mui/material/CardHeader";
import CardContent from "@mui/material/CardContent";
import CardActions from "@mui/material/CardActions";
import Button from "@mui/material/Button";
import InfoIcon from "@mui/icons-material/Info";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

type CloseHandler = () => void;

interface VersionToastProps {
  onClose: CloseHandler;
}

export default function VersionToast({ onClose }: VersionToastProps) {
  const [open, setOpen] = useState(true);

  if (!open) {
    return null;
  }

  const handleClick = () => {
    setOpen(false);
    onClose();
  };

  return (
    <Box className="version-toast-container">
      <Card className="card">
        <CardHeader
          avatar={<InfoIcon color="primary" />}
          title={
            <Typography variant="h6">ご利用にあたっての注意事項</Typography>
          }
        />
        <CardContent className="card-content">
          <Box className="text-container">
            <p>以下の事項をご理解の上、ご利用ください。</p>
            <h4>1. 正確性の保証、責任範囲について</h4>
            <ul>
              <li>
                本機能の回答は、その正確性、完全性、有用性を保証するものではありません。
              </li>
              <li>
                回答はAIが自動生成しているため、不正確または不適切な情報が含まれる可能性があります。
              </li>
              <li>
                本機能の情報に基づく一切の行動、およびこれにより生じた損害について、当社は一切責任を負いません。
              </li>
              <li>
                キャリアに関する最終的な意思決定は、必ずご自身の責任と判断で行ってください。
              </li>
            </ul>
            <h4>
              2. 個人情報入力の禁止について下記情報の入力は固く禁止いたします。
            </h4>
            <ul>
              <li>
                氏名、住所、電話番号、メールアドレスなど、特定の個人を識別できる情報（個人情報）
              </li>
              <li>機密情報、営業秘密、その他公開を意図しない情報</li>
            </ul>
            <p>
              万が一、個人情報や機密情報をご入力された場合でも、当社ではこれらの情報を取得、保存、管理する責任を負いません。
            </p>
            <p>
              また、これにより生じた損害や不利益について、当社は一切の責任を負いません。
              ご協力をお願いいたします。
            </p>
          </Box>
        </CardContent>
      </Card>
      <CardActions className="footer">
        <Button variant="contained" onClick={handleClick}>
          了解しました
        </Button>
      </CardActions>
      <Typography className="citation">
        出典：令和２年国勢調査（総務省）を加工・利用
      </Typography>
    </Box>
  );
}

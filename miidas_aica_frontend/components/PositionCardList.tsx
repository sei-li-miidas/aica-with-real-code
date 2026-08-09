import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import CardMedia from "@mui/material/CardMedia";
import Typography from "@mui/material/Typography";
import { IPositionSummary } from "@/lib/common";
import { Box } from "@mui/material";
import { useRouter } from "next/navigation";
import { LOCALSTORAGE_SOURCE_COMPONENT_KEY } from "@/constants/localStorage";

import "./PositionCardList.scss";
import { useAppDispatch } from "@/lib/store/hooks";
import { registerPositionItemKey } from "@/lib/store/features/global_state/globalStateSlice";
import { PagePath, SourceComponentNames } from "@/constants/enum";
import { useDummyImageLoader } from "@/utils/dummyImage";

interface IPositionCardListProps {
  searchKey: string;
  positions: IPositionSummary[];
}

export default function PositionCard({
  searchKey,
  positions,
}: IPositionCardListProps) {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const dummyImageData = useDummyImageLoader();

  const generatePositionItemKey = (positionId: string) => {
    return searchKey + "-" + positionId;
  };

  const handleClick = (id: string) => {
    // 分析用の項目を一時的にローカルストレージに保存
    localStorage.setItem(
      LOCALSTORAGE_SOURCE_COMPONENT_KEY,
      SourceComponentNames.Position,
    );
    // 詳細を閲覧するポジションのid
    dispatch(registerPositionItemKey(generatePositionItemKey(id)));
    router.push(`${PagePath.PositionDetail}/?positionId=${id}`);
  };

  return (
    <Box className="position-cards-list">
      {positions.map((position) => (
        <Card
          key={generatePositionItemKey(position.ID)}
          id={generatePositionItemKey(position.ID)}
          className="position-card"
        >
          <CardActionArea onClick={() => handleClick(position.ID)}>
            {(position.Image || dummyImageData) &&
            <CardMedia
              component="img"
              alt={position.Title}
              className="position-card-media"
              image={
                position.Image
                  ? position.Image
                  : dummyImageData
              }
              onError={(e) => {
                if (!dummyImageData) return;
                (e.currentTarget as HTMLImageElement).src =
                  dummyImageData;
              }}
            />
            }
            <CardContent>
              <Typography
                gutterBottom
                variant="h5"
                component="div"
                className="position-title"
              >
                {position.Title}
              </Typography>
              <Typography component="p" className="position-description">
                {position.MainJobText}
              </Typography>
            </CardContent>
          </CardActionArea>
        </Card>
      ))}
    </Box>
  );
}

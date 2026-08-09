import {
  createPositionSearchResultItem,
  IPositionSearchLinkItem,
  IPositionSearchLink,
} from "@/lib/common";
import { useCallback, useState, type ReactNode } from "react";
import AutorenewRoundedIcon from "@mui/icons-material/AutorenewRounded";
import LocationOnOutlinedIcon from "@mui/icons-material/LocationOnOutlined";
import AttachMoneyOutlinedIcon from "@mui/icons-material/AttachMoneyOutlined";
import WorkOutlineOutlinedIcon from "@mui/icons-material/WorkOutlineOutlined";
import HomeWorkOutlinedIcon from "@mui/icons-material/HomeWorkOutlined";
import CircularProgress from "@mui/material/CircularProgress";
import { clsx } from "@/utils/className";
import "./PositionSearchLinkCard.scss";
import { fetchApiData } from "@/utils/fetch";
import {
  replaceMainChatPositionSearchLink,
  updatePositions,
} from "@/lib/store/features/websocket/websocketSlice";
import { useAppDispatch } from "@/lib/store/hooks";

interface PositionSearchLinkCardProps {
  item: IPositionSearchLinkItem;
}

const formatSalary = (salary?: number): string | null => {
  if (!salary || Number.isNaN(Number(salary))) {
    return null;
  }
  return `${Number(salary).toLocaleString()}万円くらい`;
};

const getJobLabel = (link: IPositionSearchLink): string | null => {
  if (link.JobtypeNames?.length) {
    return link.JobtypeNames.join("、");
  }

  if (link.PositionKeyword) {
    return link.PositionKeyword;
  }

  return null;
};

const getPrimaryLocation = (link: IPositionSearchLink): string | null => {
  if (link.WorkLocations?.length) {
    return link.WorkLocations[0];
  }

  if (link.Residence) {
    return link.Residence;
  }

  return null;
};

const PositionSearchLinkCard = ({ item }: PositionSearchLinkCardProps) => {
  const dispatch = useAppDispatch();
  const link = item.positionSearchLink;
  const primaryLocation = getPrimaryLocation(link);
  const salaryLabel = formatSalary(link.Salary);
  const jobLabel = getJobLabel(link);

  const remoteLabel = link.IsFullyRemoteWork ? "フルリモート可能" : null;
  const [isLoading, setIsLoading] = useState(false);

  const { itemId } = item;
  const toolCallId = item.positionSearchLink.ToolCallId;

  const conditionRows: Array<{
    key: string;
    icon: ReactNode;
    label: string;
  }> = [];

  const handleClick = useCallback(async () => {
    if (isLoading) {
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetchApiData(
        `positions/re-search/${toolCallId}`,
        "求人検索が失敗しました",
      );

      if (!response?.data) {
        return;
      }

      const resultItem = createPositionSearchResultItem(
        itemId,
        JSON.stringify(response.data),
      );

      dispatch(updatePositions(response.data.Positions));
      dispatch(replaceMainChatPositionSearchLink(resultItem));
    } catch (error) {
      console.error(
        `Failed to handle position search link click for tool call ${toolCallId}:`,
        error,
      );
    } finally {
      setIsLoading(false);
    }
  }, [dispatch, isLoading, itemId, toolCallId]);

  if (primaryLocation) {
    conditionRows.push({
      key: "location",
      icon: <LocationOnOutlinedIcon fontSize="small" />,
      label: primaryLocation,
    });
  }

  if (salaryLabel) {
    conditionRows.push({
      key: "salary",
      icon: <AttachMoneyOutlinedIcon fontSize="small" />,
      label: salaryLabel,
    });
  }

  if (jobLabel) {
    conditionRows.push({
      key: "job",
      icon: <WorkOutlineOutlinedIcon fontSize="small" />,
      label: jobLabel,
    });
  }

  if (remoteLabel) {
    conditionRows.push({
      key: "remote",
      icon: <HomeWorkOutlinedIcon fontSize="small" />,
      label: remoteLabel,
    });
  }

  return (
    <div className="position-search-link-card">
      <p className="position-search-link-card__heading">
        以下の条件で求人を検索します。
      </p>
      <ul className="position-search-link-card__conditions">
        {conditionRows.map((condition) => (
          <li
            className="position-search-link-card__condition"
            key={condition.key}
          >
            <span className="position-search-link-card__condition-icon">
              {condition.icon}
            </span>
            <span className="position-search-link-card__condition-label">
              {condition.label}
            </span>
          </li>
        ))}
      </ul>
      <button
        type="button"
        className={clsx(
          "position-search-link-card__button",
          isLoading && "is-loading",
        )}
        onClick={handleClick}
        disabled={isLoading}
        aria-busy={isLoading}
      >
        {isLoading ? (
          <CircularProgress
            size={20}
            className="position-search-link-card__spinner"
          />
        ) : (
          <AutorenewRoundedIcon className="position-search-link-card__icon" />
        )}
        <span className="position-search-link-card__button-label">
          最新のポジションを検索する
        </span>
      </button>
    </div>
  );
};

export default PositionSearchLinkCard;

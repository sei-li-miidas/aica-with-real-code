"use client";

import "./SurveyLink.scss";
import Box from "@mui/material/Box";
import Link from "@mui/material/Link";
import AssignmentOutlinedIcon from "@mui/icons-material/AssignmentOutlined";

const SURVEY_LINK_PREFIX =
  "https://docs.google.com/forms/d/e/1FAIpQLSe-3JHjM6pKpFCa4KbabXT4kROYNFHTIuARdgLhcEEEqJuonA/viewform?usp=pp_url&entry.1504136593=";

export interface ISurveyLinkProps {
  sessionId: string;
}

export default function SurveyLink({ sessionId }: ISurveyLinkProps) {
  const url = SURVEY_LINK_PREFIX + sessionId;
  return (
    <Box className="survey-link-container">
      <AssignmentOutlinedIcon />
      会話後は
      <Link target="_blank" rel="noreferrer" href={url}>
        アンケート
      </Link>
      にご協力ください
    </Box>
  );
}

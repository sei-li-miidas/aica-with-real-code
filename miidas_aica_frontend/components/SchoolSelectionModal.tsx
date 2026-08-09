"use client";

import "./SelectionModal.scss";
import { useState, useEffect, useRef, useMemo } from "react";
import {
  Dialog,
  DialogContent,
  TextField,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Typography,
  Box,
  IconButton,
  InputAdornment,
  Divider,
  Button,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import SearchIcon from "@mui/icons-material/Search";
import CloseIcon from "@mui/icons-material/Close";
import { useAppDispatch, useAppSelector } from "@/lib/store/hooks";
import { School } from "@/types/utility-types";
import { MASTER_KEYS } from "@/constants/master";
import { getMasterData } from "@/utils/fetch";
import { setMasterData } from "@/lib/store/features/masterdata/masterdataSlice";

interface SchoolSelectionModalProps {
  open: boolean;
  onClose: () => void;
  onSelect: (schoolName: string) => void;
  selectedSchoolName?: string;
  schoolType: number;
}

export default function SchoolSelectionModal({
  open,
  onClose,
  onSelect,
  selectedSchoolName,
  schoolType,
}: SchoolSelectionModalProps) {
  const dispatch = useAppDispatch();

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<School[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const allSchools = useAppSelector((state) => state.masterdata.School);
  const allSchoolsLength = allSchools.length;
  const schools = useMemo(
    () =>
      allSchools.filter(
        (school: School) => school.SchoolTypeID === schoolType,
      ),
    [allSchools, schoolType],
  );

  useEffect(() => {
    if (!open || allSchoolsLength > 0) {
      return;
    }

    const abortController = new AbortController();

    getMasterData([MASTER_KEYS.SCHOOL], {
      signal: abortController.signal,
    }).then((data) => {
      if (data) {
        data.forEach((item: any) => {
          if (item.Name === MASTER_KEYS.SCHOOL) {
            dispatch(
              setMasterData({
                key: MASTER_KEYS.SCHOOL,
                data: item.Values,
              }),
            );
            return;
          }
        });
      }
    });

    return () => {
      // ページクローズ時にリクエストを廃止します。
      abortController.abort();
    };
  }, [open, allSchoolsLength, dispatch]);

  useEffect(() => {
    if (open && selectedSchoolName) {
      setSearchQuery(selectedSchoolName);
    }
  }, [open, selectedSchoolName]);

  useEffect(() => {
    const searchSchools = () => {
      if (!searchQuery.trim()) {
        setSearchResults(schools);
        return;
      }

      const filteredSchools = schools.filter((school: School) => {
        const keyword = searchQuery.trim().toLowerCase();
        const nameMatch = school.Name.toLowerCase().includes(keyword);
        const kanaMatch = school.Kana.toLowerCase().includes(keyword);

        return nameMatch || kanaMatch;
      });

      setSearchResults(filteredSchools);
    };

    // Debounce処理
    const timeoutId = setTimeout(() => {
      searchSchools();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, schools, schoolType]);

  const handleSchoolSelect = (schoolName: string) => {
    onSelect(schoolName);
    handleClose();
  };

  const handleClose = () => {
    setSearchQuery("");
    setSearchResults([]);
    onClose();
  };

  const handleDialogEntered = () => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      fullScreen
      onTransitionEnter={handleDialogEntered}
      slotProps={{ paper: { className: "selection-modal__paper" } }}
    >
      <DialogContent className="selection-modal__content">
        <Box className="selection-modal__search">
          <Box className="selection-modal__search-row">
            <IconButton
              onClick={handleClose}
              aria-label="戻る"
              className="selection-modal__back"
            >
              <ArrowBackIcon />
            </IconButton>
            <TextField
              inputRef={inputRef}
              fullWidth
              placeholder="学校名を検索"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              variant="outlined"
              size="small"
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                  endAdornment: searchQuery ? (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setSearchQuery("")}
                        edge="end"
                        size="small"
                        aria-label="クリア"
                      >
                        <CloseIcon fontSize="small" />
                      </IconButton>
                    </InputAdornment>
                  ) : null,
                },
              }}
            />
          </Box>
        </Box>

        {/* 検索結果 */}
        <List className="selection-modal__list">
          {searchResults.length > 0 ? (
            searchResults.map((school, index) => (
              <Box key={school.ID}>
                <ListItem disablePadding>
                  <ListItemButton
                    onClick={() => handleSchoolSelect(school.Name)}
                    className="selection-modal__action"
                  >
                    <ListItemText
                      primary={school.Name}
                      primaryTypographyProps={{
                        className: "selection-modal__primary-text",
                      }}
                    />
                  </ListItemButton>
                </ListItem>
                {index < searchResults.length - 1 && (
                  <Divider className="selection-modal__divider" />
                )}
              </Box>
            ))
          ) : (
            <Box className="selection-modal__state selection-modal__state--center">
              {searchQuery.trim() ? (
                <Button
                  variant="outlined"
                  onClick={() => {
                    handleSchoolSelect(searchQuery);
                  }}
                  className="selection-modal__state-message"
                >
                  そのまま登録する
                </Button>
              ) : (
                <Typography
                  color="text.secondary"
                  className="selection-modal__state-message--left"
                >
                  ※最終学歴の学校名を入力して下さい
                </Typography>
              )}
            </Box>
          )}
        </List>
      </DialogContent>
    </Dialog>
  );
}

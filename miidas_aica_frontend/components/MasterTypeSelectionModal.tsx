"use client";

import "./SelectionModal.scss";
import { useState, useEffect, useRef } from "react";
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
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import SearchIcon from "@mui/icons-material/Search";
import CloseIcon from "@mui/icons-material/Close";
import { useAppDispatch, useAppSelector } from "@/lib/store/hooks";
import { SortedMasterType } from "@/types/utility-types";
import { MASTER_KEYS } from "@/constants/master";
import { getMasterData } from "@/utils/fetch";
import { setMasterData } from "@/lib/store/features/masterdata/masterdataSlice";

interface MasterTypeSelectionModalProps {
  open: boolean;
  onClose: () => void;
  onSelect: (masterType: SortedMasterType) => void;
  selectedMasterKey: string;
  selectedResultName?: string;
}

export default function MasterTypeSelectionModal({
  open,
  onClose,
  onSelect,
  selectedMasterKey,
  selectedResultName,
}: MasterTypeSelectionModalProps) {
  const dispatch = useAppDispatch();

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SortedMasterType[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const masterTypes = useAppSelector((state) => {
    switch (selectedMasterKey) {
      case MASTER_KEYS.DEPARTMENT_TYPE:
        return state.masterdata.DepartmentType;
      case MASTER_KEYS.PROFESSIONAL_TRAINING_COLLEGE_CATEGORY:
        return state.masterdata.ProfessionalTrainingCollegeCategory;
      default:
        return [];
    }
  });

  useEffect(() => {
    if (!open || masterTypes.length > 0) {
      return;
    }

    const abortController = new AbortController();

    getMasterData([selectedMasterKey], {
      signal: abortController.signal,
    }).then((data) => {
      if (data) {
        data.forEach((item: any) => {
          dispatch(
            setMasterData({
              key: item.Name,
              data: item.Values,
            }),
          );
        });
      }
    });

    return () => {
      // ページクローズ時にリクエストを廃止します。
      abortController.abort();
    };
  }, [open, selectedMasterKey, masterTypes, dispatch]);

  useEffect(() => {
    if (open && selectedResultName) {
      setSearchQuery(selectedResultName);
    }
  }, [open, selectedResultName]);

  useEffect(() => {
    const searchMasterTypes = () => {
      if (!searchQuery.trim()) {
        setSearchResults(masterTypes);
        return;
      }

      const filteredMasterTypes = masterTypes.filter(
        (masterType: SortedMasterType) => {
          const keyword = searchQuery.trim().toLowerCase();
          const nameMatch = masterType.Name.toLowerCase().includes(keyword);

          return nameMatch;
        },
      );

      setSearchResults(filteredMasterTypes);
    };

    // Debounce処理
    const timeoutId = setTimeout(() => {
      searchMasterTypes();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, masterTypes]);

  const handleMasterTypeSelect = (masterType: SortedMasterType) => {
    onSelect(masterType);
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
              placeholder="学部・学科系統を検索"
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
            searchResults.map((masterType, index) => (
              <Box key={masterType.ID}>
                <ListItem disablePadding>
                  <ListItemButton
                    onClick={() => handleMasterTypeSelect(masterType)}
                    className="selection-modal__action"
                  >
                    <ListItemText
                      primary={masterType.Name}
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
            <Box className="selection-modal__state">
              {searchQuery.trim() ? (
                <Typography color="text.secondary">
                  該当する学部・学科系統が見つかりません
                </Typography>
              ) : (
                <Typography color="text.secondary">
                  ※学部・学科系統を教えて下さい
                </Typography>
              )}
            </Box>
          )}
        </List>
      </DialogContent>
    </Dialog>
  );
}

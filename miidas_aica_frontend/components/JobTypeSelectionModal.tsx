"use client";

import "./SelectionModal.scss";
import { useState, useEffect, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogActions,
  TextField,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Typography,
  Box,
  IconButton,
  InputAdornment,
  CircularProgress,
  Button,
  Divider,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import SearchIcon from "@mui/icons-material/Search";
import CloseIcon from "@mui/icons-material/Close";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import { searchJobtypeByKeyword } from "@/utils/fetch";
import { JobType } from "@/types/utility-types";

interface JobTypeSelectionModalProps {
  open: boolean;
  onClose: () => void;
  onSelect: (jobTypeId: number, jobTypeName: string) => void;
  selectedJobTypeName?: string;
}

export default function JobTypeSelectionModal({
  open,
  onClose,
  onSelect,
  selectedJobTypeName,
}: JobTypeSelectionModalProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<JobType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDescriptionDialog, setShowDescriptionDialog] = useState(false);
  const [selectedDescription, setSelectedDescription] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open && selectedJobTypeName) {
      setSearchQuery(selectedJobTypeName);
    }
  }, [open, selectedJobTypeName]);

  useEffect(() => {
    const searchJobTypes = async (keyword: string) => {
      if (!keyword.trim()) {
        setSearchResults([]);
        return;
      }

      setIsLoading(true);
      setSearchResults(await searchJobtypeByKeyword(keyword));
      setIsLoading(false);
    };

    // Debounce処理
    const timeoutId = setTimeout(() => {
      searchJobTypes(searchQuery);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  const handleJobTypeSelect = (jobType: JobType) => {
    onSelect(jobType.ID, jobType.Name);
    handleClose();
  };

  const handleClose = () => {
    setSearchQuery("");
    setSearchResults([]);
    setShowDescriptionDialog(false);
    setSelectedDescription("");
    onClose();
  };

  const handleDialogEntered = () => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const handleHelpClick = (
    event: React.MouseEvent<HTMLElement>,
    description: string,
  ) => {
    event.stopPropagation();
    setSelectedDescription(description);
    setShowDescriptionDialog(true);
  };

  const handleDescriptionDialogClose = () => {
    setShowDescriptionDialog(false);
    setSelectedDescription("");
  };

  return (
    <>
      <Dialog
        open={open}
        onClose={handleClose}
        fullScreen
        onTransitionEnter={handleDialogEntered}
        slotProps={{ paper: { className: "selection-modal__paper" } }}
      >
        <DialogContent className="selection-modal__content">
          {/* Search field at the top */}
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
                placeholder="職種を検索（例：エンジニア、営業、マーケティング）"
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
            {isLoading ? (
              <Box className="selection-modal__state selection-modal__state--center">
                <CircularProgress size={24} />
                <Typography
                  className="selection-modal__state-message"
                  color="text.secondary"
                >
                  職種を検索中...
                </Typography>
              </Box>
            ) : searchResults.length > 0 ? (
              searchResults.map((jobType, index) => (
                <Box key={jobType.ID}>
                  <ListItem disablePadding>
                    <ListItemButton
                      onClick={() => handleJobTypeSelect(jobType)}
                      className="selection-modal__action"
                    >
                      <ListItemText
                        primary={jobType.Name}
                        primaryTypographyProps={{
                          className: "selection-modal__primary-text",
                        }}
                      />
                      <IconButton
                        onClick={(event) =>
                          handleHelpClick(event, jobType.Description)
                        }
                        size="small"
                        className="selection-modal__help"
                        aria-label="詳細を表示"
                      >
                        <HelpOutlineIcon fontSize="small" />
                      </IconButton>
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
                    該当する職種が見つかりません
                  </Typography>
                ) : (
                  <Typography
                    color="text.secondary"
                    className="selection-modal__note"
                  >
                    ※職種が分からない場合、具体的な仕事内容を入力してください。
                  </Typography>
                )}
              </Box>
            )}
          </List>
        </DialogContent>
      </Dialog>

      {/* 詳細説明ダイアログ */}
      <Dialog
        open={showDescriptionDialog}
        onClose={handleDescriptionDialogClose}
        maxWidth="sm"
        fullWidth
        slotProps={{
          paper: { className: "selection-modal__description-paper" },
        }}
      >
        <DialogContent className="selection-modal__description-content">
          <Typography
            variant="body1"
            className="selection-modal__description-body"
          >
            {selectedDescription}
          </Typography>
        </DialogContent>
        <DialogActions className="selection-modal__description-actions">
          <Button
            onClick={handleDescriptionDialogClose}
            variant="outlined"
            className="selection-modal__description-close"
          >
            閉じる
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

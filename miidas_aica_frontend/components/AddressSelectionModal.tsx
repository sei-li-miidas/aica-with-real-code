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
  CircularProgress,
  Divider,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import SearchIcon from "@mui/icons-material/Search";
import CloseIcon from "@mui/icons-material/Close";
import { searchAddressByKeyword } from "@/utils/fetch";
import { Address } from "@/types/utility-types";

interface AddressSelectionModalProps {
  hint: string;
  open: boolean;
  onClose: () => void;
  onSelect: (address: Address) => void;
  selectedPrefectureName?: string;
  selectedCityName?: string;
}

export default function AddressSelectionModal({
  hint,
  open,
  onClose,
  onSelect,
  selectedPrefectureName,
  selectedCityName,
}: AddressSelectionModalProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Address[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open && selectedPrefectureName && selectedCityName) {
      const initialQuery = `${selectedPrefectureName}${selectedCityName}`;
      setSearchQuery(initialQuery);
    }
  }, [open, selectedPrefectureName, selectedCityName]);

  useEffect(() => {
    const searchAddresses = async (keyword: string) => {
      if (!keyword.trim()) {
        setSearchResults([]);
        return;
      }

      setIsLoading(true);
      const result = await searchAddressByKeyword(keyword);
      setSearchResults(result);
      setIsLoading(false);
    };

    // Debounce処理
    const timeoutId = setTimeout(() => {
      searchAddresses(searchQuery);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  const handleAddressSelect = (address: Address) => {
    setSearchQuery("");
    setSearchResults([]);
    onSelect(address);
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
              placeholder="都道府県・市区町村を検索（例：東京都新宿区、大阪市、札幌）"
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
                住所を検索中...
              </Typography>
            </Box>
          ) : searchResults.length > 0 ? (
            searchResults.map((address, index) => (
              <Box key={`${address.prefecture.ID}-${address.city.ID}`}>
                <ListItem disablePadding>
                  <ListItemButton
                    onClick={() => handleAddressSelect(address)}
                    className="selection-modal__option-button"
                  >
                    <ListItemText
                      primary={`${address.prefecture.Name}${address.city.Name}`}
                      primaryTypographyProps={{
                        className:
                          "selection-modal__primary-text selection-modal__primary-text--large",
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
                  該当する住所が見つかりません
                </Typography>
              ) : (
                <>
                  <Typography color="text.secondary">
                    {hint}
                    <br />※
                    東京23区にお住まいの方は、候補から「東京23区」を選択してください
                  </Typography>
                </>
              )}
            </Box>
          )}
        </List>
      </DialogContent>
    </Dialog>
  );
}

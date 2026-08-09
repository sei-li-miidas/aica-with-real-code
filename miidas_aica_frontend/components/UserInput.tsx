import "./UserInput.scss";
import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import Box from "@mui/material/Box";
import TextareaAutosize from "@mui/material/TextareaAutosize";
import Snackbar from "@mui/material/Snackbar";
import IconButton from "@mui/material/IconButton";
import SendIcon from "@mui/icons-material/Send";
import MicrophoneIcon from "@mui/icons-material/Mic";
import MicOnIcon from "@/components/icons/MicOnIcon";
import SpeechRecognition, {
  useSpeechRecognition,
} from "react-speech-recognition";
import { removeSpaces } from "@/lib/strings";
import TimeoutBar from "./TimeoutBar";
import { VOICE_INPUT_SILENCE_THRESHOLD } from "@/constants/app";

const SNACKBAR_DISPLAY_TIME: number = 4000;

type SendHandler = (userInput: string, isVoice: boolean) => void;

export interface IUserInputProps {
  sendCallback: SendHandler;
}

enum InputMode {
  Keyboard,
  Voice,
}

enum ButtonIconMode {
  None,
  MicrophoneOff,
  MicrophoneOn,
  Send,
}

export default function UserInput({ sendCallback }: IUserInputProps) {
  const textareaRef = useRef(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const { transcript, resetTranscript, browserSupportsSpeechRecognition } =
    useSpeechRecognition();
  const [inputMode, setInputMode] = useState(InputMode.Keyboard);
  const [showTimeoutBar, setShowTimeoutBar] = useState(false);
  const [isSnackbarOpen, setIsSnackbarOpen] = useState(false);
  const [speechActivityKey, setSpeechActivityKey] = useState(0); // 文字起こし回数（タイムアウトバーの更新するため）
  const [localValue, setLocalValue] = useState("");

  const handleSnackbarClose = () => {
    setIsSnackbarOpen(false);
  };

  const toggleListening = (turnOn: boolean) => {
    if (turnOn) {
      SpeechRecognition.startListening({ continuous: true, language: "ja-JP" });
    } else {
      SpeechRecognition.stopListening();
    }
  };

  useEffect(() => {
    // windowにフォーカスが当たった場合、
    // 入力モードが音声であれば、マイクを再開する
    const handleFocus = (event: FocusEvent) => {
      console.debug("Window gained focus!", event);
      if (inputMode !== InputMode.Voice) {
        return;
      }
      toggleListening(true);
    };

    const handleBlur = (event: FocusEvent) => {
      console.debug("Window lost focus!", event);
      toggleListening(false);
    };

    // Add both event listeners
    window.addEventListener("focus", handleFocus);
    window.addEventListener("blur", handleBlur);

    // Cleanup event listeners on component unmount
    return () => {
      window.removeEventListener("focus", handleFocus);
      window.removeEventListener("blur", handleBlur);
      if (timerRef.current) {
        console.debug("going to clearTimeout on unmount");
        clearTimeout(timerRef.current);
      }
    };
  }, [inputMode]);

  // 入力されたまたは文字起こしされたテキストを送信する
  const sendUserInput = useCallback(
    (userInput: string, isVoice: boolean) => {
      sendCallback(userInput, isVoice);
      setLocalValue("");
      resetTranscript();
      console.debug("userInput sent, localValue cleared");
    },
    [sendCallback, resetTranscript],
  );

  // const handleRecognitionEnd = useCallback(
  //   (transcription: string) => {
  //     console.debug(
  //       "handleRecognitionEnd called with transcription\n",
  //       transcription,
  //     );
  //     if (transcription.length === 0) {
  //       return;
  //     }

  //     // 最後の文字起こしであれば送信する
  //     sendUserInput(transcript);
  //   },
  //   [sendUserInput],
  // );

  // 音声からの文字起こしを処理する
  useEffect(() => {
    console.debug("useEffect transcript =", transcript);
    const newValue = removeSpaces(transcript);
    if (newValue.length === 0) {
      console.debug("useEffect newValue.length = 0");
      return;
    }
    setShowTimeoutBar(true);
    setSpeechActivityKey((prev) => prev + 1); // Increment key to force TimeoutBar remount

    if (timerRef.current) {
      console.debug("useEffect clearTimeout");
      clearTimeout(timerRef.current);
    }

    timerRef.current = setTimeout(() => {
      console.log("Voice input stopped, sending...");
      // タイムアウトすれば文字起こしであれば送信する
      sendUserInput(newValue, true);
      setShowTimeoutBar(false);
    }, VOICE_INPUT_SILENCE_THRESHOLD);
    console.debug("useEffect new setTimeout", timerRef.current);

    // TextAreaに追加する
    setLocalValue(newValue);
  }, [transcript, sendUserInput]);

  const handleClick = useCallback(() => {
    console.debug("handleClick called");

    if (inputMode === InputMode.Voice) {
      // 現在の入力モードが音声入力の場合
      console.debug("going to switch to keyboard mode");
      toggleListening(false);

      // キーボード入力モードに切り替える
      setInputMode(InputMode.Keyboard);
    } else if (removeSpaces(localValue).length > 0) {
      // 入力テキストの長さが1文字以上であれば送信する
      console.debug("going to send userInput");
      sendUserInput(localValue, false);
    } else if (browserSupportsSpeechRecognition) {
      console.debug("going to switch to voice mode");
      toggleListening(true);
      // 音声入力モードに切り替える
      setInputMode(InputMode.Voice);
    } else {
      setIsSnackbarOpen(true);
    }
  }, [inputMode, sendUserInput, browserSupportsSpeechRecognition, localValue]);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const newValue = e.target.value;
      setLocalValue(newValue);
    },
    [],
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (inputMode === InputMode.Keyboard && e.ctrlKey && e.key === "Enter") {
      sendUserInput(localValue, false);
    }
  };

  const buttonIconMode = useMemo(() => {
    if (!browserSupportsSpeechRecognition) {
      if (localValue.length > 0) {
        return ButtonIconMode.Send;
      }
      return ButtonIconMode.None;
    }

    if (inputMode === InputMode.Voice) {
      return ButtonIconMode.MicrophoneOn;
    }

    if (localValue.length === 0) {
      return ButtonIconMode.MicrophoneOff;
    }

    return ButtonIconMode.Send;
  }, [browserSupportsSpeechRecognition, inputMode, localValue]);

  return (
    <>
      <Box className="timeoutbar-container">
        {showTimeoutBar && <TimeoutBar key={speechActivityKey} />}
      </Box>
      <Box className="user-input-footer">
        <Box className="textarea-container">
          <TextareaAutosize
            ref={textareaRef}
            className={`${localValue.length > 0 ? "active" : "inactive"}`}
            placeholder="入力またはマイクを押してください"
            value={localValue}
            minRows={1}
            maxRows={5}
            readOnly={inputMode === InputMode.Voice}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
          />
        </Box>
        {buttonIconMode !== ButtonIconMode.None && (
          <IconButton onClick={handleClick}>
            {buttonIconMode === ButtonIconMode.MicrophoneOff && (
              <MicrophoneIcon color="primary" />
            )}
            {buttonIconMode === ButtonIconMode.MicrophoneOn && (
              <MicOnIcon
                className="user-input-mic-on-icon"
                fallback={<MicrophoneIcon color="secondary" />}
              />
            )}
            {buttonIconMode === ButtonIconMode.Send && (
              <SendIcon color="primary" />
            )}
          </IconButton>
        )}
        <Snackbar
          open={isSnackbarOpen}
          autoHideDuration={SNACKBAR_DISPLAY_TIME}
          onClose={handleSnackbarClose}
          message="メッセージを入力してください"
        />
      </Box>
    </>
  );
}

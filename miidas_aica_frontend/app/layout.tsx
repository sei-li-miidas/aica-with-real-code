"use client";
import "./globals.css";
import localFont from "next/font/local";
import Script from "next/script";
import ThemeOptions from "../lib/themeOptions";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import {
  Dialog,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Box,
} from "@mui/material";
import ConstructionIcon from "@mui/icons-material/Construction";
import SafeArea from "@/components/SafeArea";
import StoreProvider from "./StoreProvider";
import WebSocketProvider from "@/app/WebSocketProvider";
import { useAppSelector } from "@/lib/store/hooks";
import { nl2br } from "@/utils/jsx";

const theme = createTheme(ThemeOptions);

const notoSansJP = localFont({
  src: "./assets/fonts/NotoSansJP-VariableFont_wght.ttf",
});

const GTM_ID_PATTERN = /^GTM-[A-Z0-9]+$/;

// Client component for providers
function Providers({ children }: { children: React.ReactNode }) {
  return (
    <StoreProvider>
      <WebSocketProvider>
        <ThemeProvider theme={theme}>
          <MaintenanceWrapper>{children}</MaintenanceWrapper>
        </ThemeProvider>
      </WebSocketProvider>
    </StoreProvider>
  );
}

function MaintenanceWrapper({ children }: { children: React.ReactNode }) {
  const maintenanceMessage = useAppSelector(
    (state) => state.websocket.maintenanceMessage,
  );

  return (
    <>
      <Dialog open={!!maintenanceMessage} disableEscapeKeyDown>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <ConstructionIcon />
            お知らせ
          </Box>
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {nl2br(maintenanceMessage || "")}
          </DialogContentText>
        </DialogContent>
      </Dialog>
      {!maintenanceMessage && <SafeArea>{children}</SafeArea>}
    </>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const rawGtmId = process.env.NEXT_PUBLIC_GTM_TRACKING_CODE?.trim() ?? "";
  const gtmId = GTM_ID_PATTERN.test(rawGtmId) ? rawGtmId : "";

  // interactive-widget=resizes-contentはChromium向けの機能で、
  // iOS Safariで使えないので、警告が出てますが、レイアウトに影響しない。
  return (
    <html lang="en">
      <head>
        {gtmId && (
          <Script
            id="gtm-loader"
            strategy="beforeInteractive"
          >{`(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','${gtmId}');`}</Script>
        )}
        <meta charSet="utf-8" />
        <meta name="theme-color" content="#ffffff" />
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1, minimum-scale=1, maximum-scale=1, interactive-widget=resizes-content"
        />
        <title>ミイダス AI転職アドバイザー</title>
      </head>
      <body className={notoSansJP.className}>
        {gtmId && (
          <noscript>
            <iframe
              src={`https://www.googletagmanager.com/ns.html?id=${gtmId}`}
              height="0"
              width="0"
              style={{ display: "none", visibility: "hidden" }}
            />
          </noscript>
        )}
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

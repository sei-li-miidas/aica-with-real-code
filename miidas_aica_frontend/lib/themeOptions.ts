const themeOptions: object = {
  cssVariables: true,
  palette: {
    mode: "light",
    primary: {
      main: "#5e59ec",
      light: "#e9e8fd",
      dark: "#2300a9",
    },
    secondary: {
      main: "#FF9D0A",
      light: "#fff8e1",
      dark: "#fe6c0b",
      contrastText: "#fffefa",
    },
    text: {
      primary: "#2E3679",
      secondary: "#273340",
      disabled: "rgba(46,54,121,0.5)",
      hint: "rgba(34,25,77,0.7)",
    },
    background: {
      default: "#dcedff",
    },
    error: {
      main: "#ff637d",
    },
  },
  // typography: {
  //   fontFamily: "Noto Sans JP",
  // },
  props: {
    MuiAppBar: {
      color: "transparent",
    },
  },
};

export default themeOptions;

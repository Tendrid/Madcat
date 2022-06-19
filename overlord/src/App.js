import React from 'react';

import { LegionProvider } from './js/components/context/LegionProvider.jsx'
import Legion from "./js/components/container/Legion.jsx";
import { createMuiTheme, makeStyles, ThemeProvider } from '@material-ui/core/styles';
import CssBaseline from "@material-ui/core/CssBaseline";
import { blue, orange, red } from '@material-ui/core/colors';


const theme = createMuiTheme({
  palette: {
    type: 'dark',
    primary: {
      main: blue[500],
    },
    secondary: {
      main: red[900],
    },
  },
});

const App = () => (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <LegionProvider />
    </ThemeProvider>
);

export default App;

import React from 'react';
import { withStyles } from '@material-ui/core/styles';
import PropTypes from "prop-types";
import Grid from '@material-ui/core/Grid';
import Squadron from './Squadron.jsx'
import Typography from '@material-ui/core/Typography';


function Battalion(props) {
  return (
    <div>
      <Typography variant="h4">Battalion {props.bid}</Typography>
      {Object.keys(props.squardons).map((sid) => {
        return <Squadron key={sid} sid={sid} {...{units:props.squardons[sid]}} />
      })}
    </div>
  );
}


export default Battalion;
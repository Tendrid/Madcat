import React, { useState } from 'react';
import Grid from '@material-ui/core/Grid';
import Firework from './Firework.jsx';

import Divider from '@material-ui/core/Divider';
import List from '@material-ui/core/List';
import Typography from '@material-ui/core/Typography';


/*
    <Grid container spacing={3} justify="space-evenly" direction="row" width="200px">
      {props.units.map((uid) => {
        return <Firework key={uid} uid={uid} />
      })}
    </Grid>
*/

function Squadron(props) {
  return (
    <div>
      <Divider />
      <List>
        <Typography>Squadron {props.sid}</Typography>
        {props.units.map((uid) => (
          <Firework key={uid} uid={uid} />
        ))}
      </List>
    </div>
  );
}

export default Squadron;
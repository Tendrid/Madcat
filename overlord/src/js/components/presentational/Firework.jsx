import React, { useState, useEffect, useContext } from 'react';
import { makeStyles } from '@material-ui/core/styles';
import PropTypes from "prop-types";
import Grid from '@material-ui/core/Grid';
import Button from '@material-ui/core/Button';
import Fab from '@material-ui/core/Fab';
import Avatar from '@material-ui/core/Avatar';
import Badge from '@material-ui/core/Badge';
import CircularProgress from '@material-ui/core/CircularProgress';
import Zoom from '@material-ui/core/Zoom';

import ListItem from '@material-ui/core/ListItem';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import ListItemText from '@material-ui/core/ListItemText';
import ListSubheader from '@material-ui/core/ListSubheader';


import { orange, red } from '@material-ui/core/colors';

import {LegionContext} from '../context/LegionProvider.jsx'

const useStyles = makeStyles((theme) => ({
  test: theme,
  root: {
    display: 'flex',
    alignItems: 'center',
  },
  wrapper: {
    margin: theme.spacing(1),
    position: 'relative',
  },
  preFire: {
    color: orange[300],
    position: 'absolute',
    top: -6,
    left: -6,
  },
  fired: {
    color: theme.palette.secondary.main,
    position: 'absolute',
    top: -6,
    left: -6,
  },
  itemText: {
    marginLeft: '20px'
  }
}));

const fireDelay = 3000;

function Firework(props) {
  const context = useContext(LegionContext)
  const unit = context.units[props.uid]
  console.log(unit)

  const [progress, setProgress] = useState(0);
  const [countdown, setCountdown] = useState(unit.fired ? 0 : unit.duration);
  const [preFire, setPreFire] = useState(false)
  const [error, setError] = useState(unit.error)

  const classes = useStyles();

  useEffect(() => {
    console.log("in effect", progress);
    setError('')
    if (progress === -1 && unit.fired > 0 && unit.armed === true) {
      let p = 0
      const timer = setInterval(() => {
          p = p + (100/ unit.duration)
          setCountdown(Math.ceil(unit.duration - ((p/100) * unit.duration)))
          if (p >= 100){
              p = 0;
              clearInterval(timer)
              unit.armed = true;
          }
          setProgress(p)
      }, 1000);
    }
  }, [unit.fired]);

  useEffect(() => {
    if (unit.error) {
      setError(unit.error)
      setPreFire(false)
      setProgress(0)
    }
  }, [unit.error]);

  const handleFireEvent = (uid) => {
    setPreFire(true)
    setProgress(-1)
    context.fireUnit(uid)
    setTimeout(() => {
      setPreFire(false)
    }, fireDelay)
  }

  //                src={unit.phantom_def ? `http://fireworks.com/${unit.phantom_def.img}` : null}

  return (
    <ListItem>
      <div className={classes.root}>
        <div className={classes.wrapper}>
          <Badge
            color="secondary"
            anchorOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            badgeContent={unit.fired}
          >
            <Fab
              aria-label="fire"
              color={unit.fired && unit.armed ? 'secondary': 'primary'}
              onClick={() => handleFireEvent(props.uid)}
              disabled={!unit.armed}
            >
              <Avatar alt={unit.phantom_def ? unit.phantom_def.name : unit.name}>
                {progress ? countdown : unit.tid}
              </Avatar>
            </Fab>
            {progress != 0 && 
              <CircularProgress
                size={68}
                variant="static"
                value={progress}
                className={preFire ? classes.preFire : classes.fired}
              />
            }
          </Badge>
        </div>
      </div>
      <ListItemText className={classes.itemText} primary={unit.name} secondary={error || `${unit.phid} - ${unit.duration}s`} />
    </ListItem>
  );

}


export default Firework;
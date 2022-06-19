import React from 'react';
import Container from '@material-ui/core/Container';
import Paper from '@material-ui/core/Paper';
import Battalion from '../presentational/Battalion.jsx'
import Cue from '../presentational/Cue.jsx'


function Legion(props) {
  //       {Object.keys(props.cues || []).map((cue) => { return <Cue key={cue} name={cue} duration={props.cues[cue].duration} cue={props.cues[cue].cue} /> })}

  return (
    <Container>
      {Object.keys(props.battalions || {}).map((bid) => { return <Battalion key={bid} bid={bid} squardons={props.battalions[bid]} /> })}
    </Container>
  );
}

export default Legion;
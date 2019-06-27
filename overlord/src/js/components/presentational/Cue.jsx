import React from 'react';
import { withStyles } from '@material-ui/core/styles';
import PropTypes from "prop-types";
import Button from '@material-ui/core/Button';

const styles = {
  root: {
    background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)',
    border: 0,
    borderRadius: 3,
    boxShadow: '0 3px 5px 2px rgba(255, 105, 135, .3)',
    color: 'white',
    height: 48,
    padding: '0 30px',
  },
};


class Cue extends React.Component {
  constructor(props) {
    super(props);
    this.state = {fired: props.fired};

    this.handleClick = this.handleClick.bind(this);
  }

  handleClick() {
    const state = this.state;
    fetch('/cue', {
      method: "POST",
      body: JSON.stringify({"cue":this.props.name}),
    })
    .then(response => response.json())
    .then(message => {
      console.log(message)
    })
    .catch(error => console.error(error));
  }

  render() {
    return (
      <Button variant="contained" onClick={this.handleClick}>
         {this.props.name} ({this.props.duration}s)
      </Button>
    );
  }
}

Cue.propTypes = {
  name: PropTypes.string.isRequired,
  duration: PropTypes.number.isRequired,
  cue: PropTypes.array.isRequired
};

export default withStyles(styles)(Cue);
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


class Firework extends React.Component {
  constructor(props) {
    super(props);
    this.state = {fired: props.fired};

    this.handleClick = this.handleClick.bind(this);
  }

  handleClick() {
    const state = this.state;
    fetch('/fire', {
      method: "POST",
      body: JSON.stringify({"tube":this.props.tid}),
    })
    .then(response => response.json())
    .then(message => {
      this.setState({fired:true})
      console.log(message)
    })
    .catch(error => console.error(error));
  }

  render() {
    return (
      <Button variant="contained" fired={this.state.fired} color="primary" height={this.props.height} onClick={this.handleClick}>
         {this.props.name}
      </Button>
    );
  }
}

Firework.propTypes = {
  tid: PropTypes.string.isRequired,
  phid: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  length: PropTypes.number.isRequired,
  width: PropTypes.number.isRequired,
  duration: PropTypes.number.isRequired,
  fired: PropTypes.bool.isRequired
};

export default withStyles(styles)(Firework);
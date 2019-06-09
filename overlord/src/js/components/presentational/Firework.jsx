import React from 'react';
import { withStyles } from '@material-ui/core/styles';
import PropTypes from "prop-types";

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
  render() {
    return (
      <button className="firework">
         {this.props.name}
      </button>
    );
  }
}

Firework.propTypes = {
  tid: PropTypes.string.isRequired,
  bid: PropTypes.string.isRequired,
  phid: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  length: PropTypes.number.isRequired,
  width: PropTypes.number.isRequired,
  duration: PropTypes.number.isRequired
};

export default withStyles(styles)(Firework);
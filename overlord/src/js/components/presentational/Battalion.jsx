import React from 'react';
import { withStyles } from '@material-ui/core/styles';
import PropTypes from "prop-types";
import Firework from './Firework.jsx'

const styles = {
  root: {
    border: 0,
    borderRadius: 3,
    boxShadow: '0 3px 5px 2px rgba(255, 105, 135, .3)',
    color: 'white',
  },
};

class Battalion extends React.Component {
  constructor(props) {
      super(props);
      this.state = {
          tubes: props.tubes
      };
  }

  renderFirework() {
      const tubes = this.state.tubes || []
      let field = tubes.map((props) => {
          if (props.name) {
              return <Firework key={props.tid} {...props} />
          }
      })
      return field
  }

  render() {
    return (
      <div>
         <h4>{this.props.bid}</h4>
         {this.renderFirework()}
      </div>
    );
  }
}

Battalion.propTypes = {
  bid: PropTypes.string.isRequired,
  tubes: PropTypes.array.isRequired,
};

export default withStyles(styles)(Battalion);
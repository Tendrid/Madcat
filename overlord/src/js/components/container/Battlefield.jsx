import React from 'react';
import ReactDOM from 'react-dom'
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import Grid from '@material-ui/core/Grid';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import RadioGroup from '@material-ui/core/RadioGroup';
import Radio from '@material-ui/core/Radio';
import Paper from '@material-ui/core/Paper';

//import Firework from '../presentational/Firework.jsx'
import Battalion from '../presentational/Battalion.jsx'

class Battlefield extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            battalions: Array()
        };
    }

    loadBattlefield(){
        fetch("/battlefield")
            .then( (response) => {
                return response.json()
            })
            .then( (json) => {
                console.log(json)
                this.setState(json)
            });
    }

    componentDidMount() {
        this.loadBattlefield();
    }

    renderBattalion() {
        console.log(this.state)
        let field = this.state.battalions.map((props) => {
            return <Battalion key={props.bid} {...props} />
        })
        return field
    }

    render() {
        return (
            <Paper>
                <p>Battalions:</p>
                {this.renderBattalion()}
            </Paper>
        );
    }
}


export default Battlefield;
import React from 'react';
import ReactDOM from 'react-dom'
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import Grid from '@material-ui/core/Grid';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import RadioGroup from '@material-ui/core/RadioGroup';
import Radio from '@material-ui/core/Radio';
import Paper from '@material-ui/core/Paper';

import Firework from '../presentational/Firework.jsx'

class Battlefield extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            tubes: Array()
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


    createFirework = () => {
        return React.createElement(
            stock[def.component], 
            def.props,
            ((def.props || {}).children || [])
                .map(c => this.createElement(c))
        );
    };

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
            <Paper>
                <p>Fireworks:</p>
                {this.renderFirework()}
            </Paper>
        );
    }
}


export default Battlefield;
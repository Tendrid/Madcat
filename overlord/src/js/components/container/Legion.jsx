import React from 'react';
import ReactDOM from 'react-dom'
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import Grid from '@material-ui/core/Grid';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import RadioGroup from '@material-ui/core/RadioGroup';
import Radio from '@material-ui/core/Radio';
import Paper from '@material-ui/core/Paper';

import Battalion from '../presentational/Battalion.jsx'
import Cue from '../presentational/Cue.jsx'

class Legion extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            battalions: Array(),
            cues: Array(),
            squadrons: Object(),
        };
    }

    loadLegion(){
        fetch("/legion")
            .then( (response) => {
                return response.json()
            })
            .then( (json) => {
                //console.log(json)
                this.setState(json)
            });
    }

    componentDidMount() {
        this.loadLegion();
    }

    renderBattalion() {
        console.log(this.state.squadrons)
        let field = this.state.battalions.map((props) => {
            return <Battalion key={props.bid} {...props} />
        })
        return field
    }

    renderCues() {
        //let field = Object.entries(this.state.cues).map((cue) => {
        let field = Object.entries(this.state.cues).map((cue) => {
            let [name, config] = cue
            return <Cue key={name} name={name} duration={config.duration} cue={config.cue} />
        })
        return field
    }

    render() {
        return (
            <Paper>
                <p>Battalions:</p>
                {this.renderBattalion()}
                <p>Cues:</p>
                {this.renderCues()}
            </Paper>
        );
    }
}


export default Legion;
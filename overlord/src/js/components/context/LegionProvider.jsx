import React, { createContext, createReducer } from 'react';
import Legion from "../container/Legion.jsx";

export const LegionContext = createContext();

export class LegionProvider extends React.Component {
  constructor(props) {
    super(props);

    this.battalions = Object()
    this.squardons = Object()
    this.cues = Array()

    this.fireUnit = (uid) => {
      var units = {...this.state.units}
      units[uid].error = '';
      this.setState({units});

      fetch('/fire', {
        method: "POST",
        body: JSON.stringify({"unit":uid}),
      })
      .then(response => {
        if (!units[uid].fired) {
          units[uid].fired = 0
        }
        if (response.ok) {
          const message = response.json()
          units[uid].fired += 1;
          this.setState({units});
        } else {
          units[uid].error = 'Failed to fire';
          this.setState({units});
        }
      })
      .catch(error => {
        console.error('There has been a problem with your fetch operation:', error);
      });
    }

    this.state = {
        units: Object(),
        fireUnit: this.fireUnit
    };

    fetch("/legion")
      .then( (response) => {
        console.log("api hit");
        return response.json()
      }).then( (json) => {
        this.battalions = json.battalions;
        this.squardons = json.squardons;
        this.cues = json.cues;
        this.setState({units:json.units, fireUnit: this.fireUnit})
      });
  }

  render() {
    console.log(this.battalions);
    return (
      <LegionContext.Provider value={this.state}>
        <Legion battalions={this.battalions} squardons={this.squardons} cues={this.cues}/>
      </LegionContext.Provider>
    );
  }
}

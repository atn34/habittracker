import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';
import Goals from './Goals.js';
import AppState from './AppState.js'
import axios from 'axios';

class App extends Component {

    constructor(props) {
        super(props);
        AppState.setOnChange(this.onChangeState.bind(this));
    }

    onChangeState() {
        this.setState(() => AppState.getState());
    }

    componentDidMount() {
        axios.get('/api/user/1/goals')
            .then((res) => {
                AppState.setState(res.data);
            });
    }

    render() {
        return (
            <div className="App">
                <div className="App-header">
                    <img src={logo} className="App-logo" alt="logo" />
                    <h2>Welcome to React</h2>
                </div>
                <Goals goals={AppState.getState().goals.toArray()} />
            </div>
        );
    }
}

export default App;

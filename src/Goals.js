import React, { Component } from 'react';
import AppState from './AppState'
import './Goals.css'
import axios from 'axios';

const DoneToday = (goal, now) => {
    const lastDone = new Date(goal.lastDone);
    return now.getDate() === lastDone.getDate()
        && now.getMonth() === lastDone.getMonth() && now.getFullYear() === lastDone.getFullYear();
};

const Goal = ({ goal, doneToday, handleGoalClick }) => {
    return (
        <tr>
            {!doneToday &&
                <td><button type="button" className="Goal-Button" onClick={() => {
                    axios.post(`/api/goal/${goal.goalid}/markdone`)
                        .then((res) => {
                            AppState.markGoalDone(res.data);
                        })
                }}>Mark Done</button></td>
            }
            <td><b>{goal.name}</b></td>
        </tr>
    );
};

class AddGoal extends Component {
    constructor(props) {
        super(props);
        this.state = { value: '', error: null };

        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
    }

    handleChange(event) {
        this.setState({ value: event.target.value });
    }

    handleSubmit() {
        if (this.state.value === "") {
            this.setState({ value: this.state.value, error: "Must not be empty" });
        } else {
            axios.post("/api/user/1/goal", { name: this.state.value })
                .then((res) => {
                    AppState.addGoal(res.data);
                });
        }
    }

    render() {
        const error = this.state.error;
        return (
            <tr>
                <td><button type="button" className="Goal-Button" onClick={this.handleSubmit}>Add New Goal</button></td>
                <td><input type="text" value={this.state.value} onChange={this.handleChange} /></td>
                {error && <td><div className="Error">{error}</div></td>}
            </tr >
      );
    }
}

const Goals = ({ goals }) => {
    const now = new Date();
    const goalsToDo = goals.filter(goal => !DoneToday(goal, now));
    return (
        <div className="Goals">
            <h2>TODO</h2>
            <table className="Goals">
                <tbody>
                    { goalsToDo.length > 0 &&
                        goalsToDo.map(goal => <Goal goal={goal} key={goal.goalid} doneToday={false} />)
                    }
                    { goalsToDo.length === 0 &&
                        <tr><td>No more goals to do!</td></tr>
                    }
                    <AddGoal />
                </tbody>
            </table>
            <h2>Done</h2>
            <table className="Goals">
                <tbody>
                    {goals
                        .filter(goal => DoneToday(goal, now))
                        .map(goal => <Goal goal={goal} key={goal.goalid} doneToday={true} />)
                    }
                </tbody>
            </table>
        </div>
    );
}

export default Goals;

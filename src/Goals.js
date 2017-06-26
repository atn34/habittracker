import React from 'react';
import './Goals.css'

const DoneToday = (goal, now) => {
    const lastDone = new Date(goal.get("lastDone"));
    return now.getDate() === lastDone.getDate()
        && now.getMonth() === lastDone.getMonth() && now.getFullYear() === lastDone.getFullYear();
};

const Goal = ({ goal, doneToday, handleGoalClick }) => {
    return (
        <tr>
            { !doneToday &&
                <td><button type="button" className="Goal-Button" onClick={() => (handleGoalClick(goal))}>Mark Done</button></td>
            }
            <td><b>{goal.get("name")}</b></td>
            <td>{`state: ${goal.get("state")}`}</td>
            <td>{`lastDone: ${goal.get("lastDone")}`}</td>
        </tr>
    );
};

const Goals = ({ goals, handleGoalClick }) => {
    const now = new Date();
    return (
        <div className="Goals">
            <h2>TODO</h2>
            <table className="Goals">
                <tbody>
                    {goals
                        .filter(goal => !DoneToday(goal, now))
                        .map(goal => <Goal goal={goal} key={goal.get("goalid")} doneToday={false} handleGoalClick={handleGoalClick} />)
                    }
                </tbody>
            </table>
            <h2>Done</h2>
            <table className="Goals">
                <tbody>
                    {goals
                        .filter(goal => DoneToday(goal, now))
                        .map(goal => <Goal goal={goal} key={goal.get("goalid")} doneToday={true} handleGoalClick={handleGoalClick} />)
                    }
                </tbody>
            </table>
        </div>
    );
}

export default Goals;

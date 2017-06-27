import { Map, Record } from 'immutable'

const Goal = Record({
    name: "",
    goalid: null,
    lastDone: Date(null),
    userid: null,
}, 'Goal');

const State = Record({
    goals: Map(),
}, 'State');

class AppState {
    constructor() {
        this.onChange = () => { };
        this.state = State({});
    }

    setOnChange(onChange) { this.onChange = onChange; }

    getState() { return this.state; }
    
    setState({ goals }) {
        this.state = State({
            goals: Map(goals.map(goal => [goal.goalid, Goal(goal)]))
        });
        this.onChange();
    }

    addGoal(goal) {
        this.state = this.state.set("goals", this.state.goals.set(goal.goalid, Goal(goal)));
        this.onChange();
    }

    markGoalDone({ goalid, lastDone }) {
        this.state = this.state.set("goals", this.state.goals.update(
            goalid, (goal) => goal.set('lastDone', Date(lastDone))));
        this.onChange();
    }
}

export default (new AppState());
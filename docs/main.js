import { DebaterSelector } from './components/DebaterSelector.js';
console.log('Speaker Stats app initialized!');
const state = {
    allDebaters: [],
    currentDebater: null
};
let debaterSelector = null;
async function loadData() {
    try {
        const response = await fetch('./example_stats.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        state.allDebaters = data;
        state.currentDebater = data[0] || null;
        console.log('Data loaded successfully');
        console.log(`Loaded ${state.allDebaters.length} debaters`);
        console.log('Current debater:', state.currentDebater?.name);
        initializeComponents();
    }
    catch (error) {
        console.error('Failed to load data:', error);
    }
}
function initializeComponents() {
    if (!state.currentDebater) {
        console.error('No debater selected');
        return;
    }
    debaterSelector = new DebaterSelector('debater-selector', state.allDebaters, state.currentDebater, onDebaterSelected);
}
function onDebaterSelected(debater) {
    console.log('Debater selected:', debater.name);
    state.currentDebater = debater;
    // TODO: Update other components here
    // updateWinRateChart(debater);
    // updateSpeakerPointsChart(debater);
    // updateMotionStats(debater);
    // updatePositionStats(debater);
    // updateDebatesTable(debater);
}
loadData();

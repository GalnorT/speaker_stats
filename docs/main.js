import { DebaterSelector } from './components/DebaterSelector.js';
import { WinRateChart } from './components/WinRateChart.js';
console.log('Speaker Stats app initialized!');
const state = {
    allDebaters: [],
    currentDebater: null
};
let debaterSelector = null;
let winRateChart = null;
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
    winRateChart = new WinRateChart('win-rate-chart', state.currentDebater);
}
function onDebaterSelected(debater) {
    console.log('Debater selected:', debater.name);
    state.currentDebater = debater;
    if (winRateChart) {
        winRateChart.update(debater);
    }
    // TODO: Update other components here
    // updateSpeakerPointsChart(debater);
    // updateMotionStats(debater);
    // updatePositionStats(debater);
    // updateDebatesTable(debater);
}
loadData();

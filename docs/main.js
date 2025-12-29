console.log('Speaker Stats app initialized!');
const state = {
    allDebaters: [],
    currentDebater: null
};
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
    }
    catch (error) {
        console.error('Failed to load data:', error);
    }
}
// Initialize app
loadData();
export {};

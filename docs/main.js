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
        console.log('Data loaded successfully:', state);
        console.log(`Loaded ${state.allDebaters.length} debaters`);
        displayLoadStatus(true);
    }
    catch (error) {
        console.error('Failed to load data:', error);
        displayLoadStatus(false, error);
    }
}
function displayLoadStatus(success, error) {
    const app = document.getElementById('app');
    if (!app)
        return;
    app.innerHTML = ''; // Clear any existing content
    const heading = document.createElement('h1');
    heading.textContent = 'Speaker Stats';
    heading.style.cssText = 'color: #3b82f6; font-family: system-ui, sans-serif; text-align: center; margin-top: 2rem;';
    app.appendChild(heading);
    const status = document.createElement('p');
    status.style.cssText = 'text-align: center; font-family: system-ui, sans-serif;';
    if (success) {
        status.textContent = `Data loaded: ${state.allDebaters.length} debaters found`;
        status.style.color = '#22c55e';
        // Display debater names
        const list = document.createElement('ul');
        list.style.cssText = 'text-align: center; list-style: none; padding: 0;';
        state.allDebaters.forEach(debater => {
            const item = document.createElement('li');
            item.textContent = `${debater.name} (${debater.debates.length} debates)`;
            item.style.cssText = 'margin: 0.5rem 0; color: #6b7280;';
            list.appendChild(item);
        });
        app.appendChild(list);
    }
    else {
        status.textContent = `Failed to load data: ${error}`;
        status.style.color = '#ef4444';
    }
    app.appendChild(status);
}
// Initialize app
loadData();
export {};

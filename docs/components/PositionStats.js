export class PositionStats {
    constructor(containerId, debater) {
        const container = document.getElementById(containerId);
        if (!container) {
            throw new Error(`Container with id "${containerId}" not found`);
        }
        this.container = container;
        this.currentDebater = debater;
        this.render();
    }
    render() {
        // Clear existing content except h2
        const h2 = this.container.querySelector('h2');
        this.container.innerHTML = '';
        if (h2) {
            this.container.appendChild(h2);
        }
        const list = document.createElement('ul');
        list.className = 'stats-list';
        const positions = ['1', '2', '3'];
        positions.forEach(position => {
            const points = this.currentDebater.positions_speaker_points[position];
            const item = document.createElement('li');
            item.className = 'stats-item';
            const positionLabel = document.createElement('span');
            positionLabel.className = 'stats-category';
            positionLabel.textContent = `Position ${position}`;
            const value = document.createElement('span');
            value.className = 'stats-value';
            value.textContent = points.toFixed(1);
            item.appendChild(positionLabel);
            item.appendChild(value);
            list.appendChild(item);
        });
        this.container.appendChild(list);
    }
    update(debater) {
        this.currentDebater = debater;
        this.render();
    }
}

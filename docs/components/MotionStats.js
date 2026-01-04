export class MotionStats {
    constructor(containerId, debater) {
        const container = document.getElementById(containerId);
        if (!container) {
            throw new Error(`Container with id "${containerId}" not found`);
        }
        this.container = container;
        this.currentDebater = debater;
        this.render();
    }
    createSection(titleText, stats, itemClass) {
        const section = document.createElement('div');
        section.className = 'stats-section';
        const title = document.createElement('h3');
        title.textContent = titleText;
        section.appendChild(title);
        const list = document.createElement('ul');
        list.className = 'stats-list';
        const item = document.createElement('li');
        item.className = `stats-item ${itemClass}`;
        stats.forEach(stat => {
            const category = document.createElement('span');
            category.className = 'stats-category';
            category.textContent = stat.category;
            const value = document.createElement('span');
            value.className = 'stats-value';
            value.textContent = `${(stat.win_rate * 100).toFixed(1)}%`;
            item.appendChild(category);
            item.appendChild(value);
            list.appendChild(item);
        });
        section.appendChild(list);
        return section;
    }
    render() {
        // Clear existing content except h2
        const h2 = this.container.querySelector('h2');
        this.container.innerHTML = '';
        if (h2) {
            this.container.appendChild(h2);
        }
        const top3Section = this.createSection('Best Categories', this.currentDebater.motion_category_stats.top_3, 'success');
        this.container.appendChild(top3Section);
        const bottom3Section = this.createSection('Worst Categories', this.currentDebater.motion_category_stats.bottom_3, 'danger');
        this.container.appendChild(bottom3Section);
    }
    update(debater) {
        this.currentDebater = debater;
        this.render();
    }
}

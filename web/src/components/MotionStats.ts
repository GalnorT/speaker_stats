import { DebaterStats, type CategoryStat } from '../types.js';

export class MotionStats {
  private container: HTMLElement;
  private currentDebater: DebaterStats;

  constructor(containerId: string, debater: DebaterStats) {
    const container = document.getElementById(containerId);
    if (!container) {
      throw new Error(`Container with id "${containerId}" not found`);
    }
    
    this.container = container;
    this.currentDebater = debater;
    
    this.render();
  }

   private createSection(titleText: string, stats: CategoryStat[], itemClass: string): HTMLElement{
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

  public render(): void {
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

  public update(debater: DebaterStats): void {
    this.currentDebater = debater;
    this.render();
  }
}
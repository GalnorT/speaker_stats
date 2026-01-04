import { DebaterStats } from '../types.js';

export class DebatesTable {
  private container: HTMLElement;
  private currentDebater: DebaterStats;
  private tableElement: HTMLTableElement | null = null;
  private sortColumn: string = 'date';
  private sortAscending: boolean = false;

  constructor(containerId: string, debater: DebaterStats) {
    const container = document.getElementById(containerId);
    if (!container) {
      throw new Error(`Container with id "${containerId}" not found`);
    }
    
    this.container = container;
    this.currentDebater = debater;
    
    this.render();
  }

  public render(): void {
    // Clear existing content except h2
    const h2 = this.container.querySelector('h2');
    this.container.innerHTML = '';
    if (h2) {
      this.container.appendChild(h2);
    }

    this.tableElement = document.createElement('table');
    this.tableElement.className = 'debates-table';

    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    const headers = [
      { key: 'ballots_gained', label: 'Ballots' },
      { key: 'opponent', label: 'Opponent' },
      { key: 'side', label: 'Side' },
      { key: 'speaker_points', label: 'Points' },
      { key: 'date', label: 'Date' },
      { key: 'link', label: 'Info', sortable: false }
    ];

    headers.forEach(header => {
      const th = document.createElement('th');
      th.textContent = header.label;
      
      if (header.sortable !== false) {
        th.style.cursor = 'pointer';
        th.addEventListener('click', () => this.sortBy(header.key));
        
        // Add sort indicator
        if (this.sortColumn === header.key) {
          th.textContent += this.sortAscending ? ' ↑' : ' ↓';
        }
      } else {
        th.className = 'no-sort';
      }
      
      headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    this.tableElement.appendChild(thead);

    const tbody = document.createElement('tbody');
    this.renderRows(tbody);
    this.tableElement.appendChild(tbody);

    this.container.appendChild(this.tableElement);
  }

  private renderRows(tbody: HTMLTableSectionElement): void {
    const sortedDebates = [...this.currentDebater.debates].sort((a, b) => {
      let aVal: any;
      let bVal: any;

      switch (this.sortColumn) {
        case 'ballots_gained':
          aVal = a.ballots_gained;
          bVal = b.ballots_gained;
          break;
        case 'opponent':
          aVal = a.opponent.toLowerCase();
          bVal = b.opponent.toLowerCase();
          break;
        case 'side':
          aVal = a.was_aff ? 'A' : 'N';
          bVal = b.was_aff ? 'A' : 'N';
          break;
        case 'speaker_points':
          aVal = a.speaker_points;
          bVal = b.speaker_points;
          break;
        case 'date':
          aVal = new Date(a.date).getTime();
          bVal = new Date(b.date).getTime();
          break;
        default:
          return 0;
      }

      if (aVal < bVal) return this.sortAscending ? -1 : 1;
      if (aVal > bVal) return this.sortAscending ? 1 : -1;
      return 0;
    });

    sortedDebates.forEach(debate => {
      const row = document.createElement('tr');
      
      if (debate.ballots_gained >= 2) {
        row.className = 'row-success';
      } else {
        row.className = 'row-danger';
      }

      this.addCellToRow(row, debate.ballots_gained.toString());
      this.addCellToRow(row, debate.opponent);
      this.addCellToRow(row, debate.was_aff ? 'A' : 'N');
      this.addCellToRow(row, debate.speaker_points.toFixed(1));
      this.addCellToRow(row, debate.date);

      const linkCell = document.createElement('td');
      const linkIcon = document.createElement('a');
      linkIcon.href = debate.link;
      linkIcon.target = '_blank';
      linkIcon.className = 'link-icon';
      linkIcon.textContent = 'ℹ️';
      linkIcon.title = 'View debate details';
      linkCell.appendChild(linkIcon);
      row.appendChild(linkCell);

      tbody.appendChild(row);
    });
  }

  private sortBy(column: string): void {
    if (this.sortColumn === column) {
      this.sortAscending = !this.sortAscending;
    } else {
      // New column, default to descending
      this.sortColumn = column;
      this.sortAscending = false;
    }

    this.render();
  }

  private addCellToRow(rowElement: HTMLTableRowElement, cellText: string): void {
    const td = document.createElement('td');
    td.textContent = cellText;
    rowElement.appendChild(td);
  }

  public update(debater: DebaterStats): void {
    this.currentDebater = debater;
    this.sortColumn = 'date';
    this.sortAscending = false;
    this.render();
  }
}
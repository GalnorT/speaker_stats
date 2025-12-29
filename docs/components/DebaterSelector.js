export class DebaterSelector {
    constructor(containerId, allDebaters, currentDebater, onSelect) {
        this.inputElement = null;
        this.dropdownElement = null;
        const container = document.getElementById(containerId);
        if (!container) {
            throw new Error(`Container with id "${containerId}" not found`);
        }
        this.container = container;
        this.allDebaters = allDebaters;
        this.currentDebater = currentDebater;
        this.onSelectCallback = onSelect;
        this.initializeFuse();
        this.render();
    }
    async initializeFuse() {
        // Load Fuse.js from CDN
        // @ts-ignore
        const Fuse = (await import('https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.mjs')).default;
        this.fuse = new Fuse(this.allDebaters, {
            keys: ['name'],
            threshold: 0.75, // Lower = stricter matching
            distance: 100,
            includeScore: true
        });
    }
    render() {
        const h2 = this.container.querySelector('h2');
        this.container.innerHTML = '';
        if (h2) {
            this.container.appendChild(h2);
        }
        this.inputElement = document.createElement('input');
        this.inputElement.type = 'text';
        this.inputElement.className = 'selector-input';
        this.inputElement.placeholder = 'Search for a debater...';
        this.inputElement.value = this.currentDebater?.name || '';
        this.dropdownElement = document.createElement('div');
        this.dropdownElement.className = 'selector-dropdown';
        const hint = document.createElement('p');
        hint.className = 'selector-hint';
        hint.textContent = 'Tip: Search or scroll to find other debaters';
        this.container.appendChild(this.inputElement);
        this.container.appendChild(this.dropdownElement);
        this.container.appendChild(hint);
        this.attachEventListeners();
        this.container.classList.add('highlight');
        setTimeout(() => {
            this.container.classList.remove('highlight');
        }, 6000);
    }
    attachEventListeners() {
        if (!this.inputElement || !this.dropdownElement)
            return;
        this.inputElement.addEventListener('focus', () => {
            this.showAllDebaters();
        });
        this.inputElement.addEventListener('input', (e) => {
            const query = e.target.value;
            if (query.trim() === '') {
                this.showAllDebaters();
            }
            else {
                this.showFilteredDebaters(query);
            }
        });
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.hideDropdown();
            }
        });
    }
    showAllDebaters() {
        if (!this.dropdownElement)
            return;
        this.dropdownElement.innerHTML = '';
        const debatersToShow = this.allDebaters.slice(0, 5);
        debatersToShow.forEach(debater => {
            this.addOptionToDropdown(debater);
        });
        this.dropdownElement.classList.add('active');
    }
    showFilteredDebaters(query) {
        if (!this.dropdownElement || !this.fuse)
            return;
        const results = this.fuse.search(query);
        this.dropdownElement.innerHTML = '';
        const topResults = results.slice(0, 5);
        if (topResults.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'selector-option';
            noResults.textContent = 'No debaters found';
            noResults.style.cursor = 'default';
            noResults.style.color = 'var(--color-text-muted)';
            this.dropdownElement.appendChild(noResults);
        }
        else {
            topResults.forEach(result => {
                this.addOptionToDropdown(result.item);
            });
        }
        this.dropdownElement.classList.add('active');
    }
    addOptionToDropdown(debater) {
        if (!this.dropdownElement)
            return;
        const option = document.createElement('div');
        option.className = 'selector-option';
        option.textContent = debater.name;
        if (this.currentDebater?.name === debater.name) {
            option.classList.add('selected');
        }
        option.addEventListener('click', () => {
            this.selectDebater(debater);
        });
        this.dropdownElement.appendChild(option);
    }
    selectDebater(debater) {
        this.currentDebater = debater;
        if (this.inputElement) {
            this.inputElement.value = debater.name;
        }
        this.hideDropdown();
        this.onSelectCallback(debater);
    }
    hideDropdown() {
        if (this.dropdownElement) {
            this.dropdownElement.classList.remove('active');
        }
    }
    update(debater) {
        this.currentDebater = debater;
        if (this.inputElement) {
            this.inputElement.value = debater.name;
        }
    }
}

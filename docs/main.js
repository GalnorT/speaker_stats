"use strict";
console.log('Speaker Stats app initialized!');
// Test: Create a simple heading
const app = document.getElementById('app');
if (app) {
    const heading = document.createElement('h1');
    heading.textContent = 'Speaker Stats - Test Build';
    heading.style.color = '#3b82f6';
    heading.style.fontFamily = 'system-ui, sans-serif';
    heading.style.textAlign = 'center';
    heading.style.marginTop = '2rem';
    app.appendChild(heading);
    const status = document.createElement('p');
    status.textContent = '✅ TypeScript compilation successful!';
    status.style.textAlign = 'center';
    status.style.color = '#22c55e';
    app.appendChild(status);
}

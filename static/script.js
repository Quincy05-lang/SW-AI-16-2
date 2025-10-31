document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;
            
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(tc => tc.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');
            
            if (targetTab === 'dashboard') {
                loadDashboard();
            }
        });
    });
    
    const predictForm = document.getElementById('predictForm');
    if (predictForm) {
        predictForm.addEventListener('submit', handlePredict);
    }
    
    const optimizeForm = document.getElementById('optimizeForm');
    if (optimizeForm) {
        optimizeForm.addEventListener('submit', handleOptimize);
    }
});

async function handlePredict(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        maize_bran: parseFloat(formData.get('maize_bran')),
        cottonseed: parseFloat(formData.get('cottonseed')),
        brewers_grain: parseFloat(formData.get('brewers_grain')),
        grass_silage: parseFloat(formData.get('grass_silage')),
        nel: parseFloat(formData.get('nel')),
        cp: parseFloat(formData.get('cp')),
        lysine: parseFloat(formData.get('lysine')),
        days_in_milk: parseFloat(formData.get('days_in_milk'))
    };
    
    const resultsDiv = document.getElementById('predictResults');
    resultsDiv.classList.remove('hidden');
    resultsDiv.innerHTML = '<div class="loading">Calculating predictions...</div>';
    
    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayPredictResults(result);
        } else {
            resultsDiv.innerHTML = `<div class="error">Error: ${result.error}</div>`;
        }
    } catch (error) {
        resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
}

function displayPredictResults(result) {
    const resultsDiv = document.getElementById('predictResults');
    
    resultsDiv.innerHTML = `
        <div class="result-card">
            <h3>Prediction Results</h3>
            <div class="metrics">
                <div class="metric">
                    <span class="metric-label">Predicted Milk Yield</span>
                    <span class="metric-value">${result.milk_yield.toFixed(2)}</span>
                    <span class="metric-unit">Liters</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Feed Efficiency</span>
                    <span class="metric-value">${result.feed_efficiency.toFixed(2)}</span>
                    <span class="metric-unit">L/kg DM</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Dry Matter</span>
                    <span class="metric-value">${result.total_dm.toFixed(2)}</span>
                    <span class="metric-unit">kg</span>
                </div>
            </div>
        </div>
    `;
}

async function handleOptimize(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        target_milk: parseFloat(formData.get('target_milk')),
        max_cost: parseFloat(formData.get('max_cost'))
    };
    
    const resultsDiv = document.getElementById('optimizeResults');
    resultsDiv.classList.remove('hidden');
    resultsDiv.innerHTML = '<div class="loading">Optimizing feed formulation...</div>';
    
    try {
        const response = await fetch('/api/optimize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayOptimizeResults(result);
        } else {
            resultsDiv.innerHTML = `<div class="error">Error: ${result.error}</div>`;
        }
    } catch (error) {
        resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
}

function displayOptimizeResults(result) {
    const resultsDiv = document.getElementById('optimizeResults');
    
    let nutrientsRows = '';
    for (const [nutrient, data] of Object.entries(result.nutrients)) {
        const status = data.balance >= -0.1 ? 'MET' : 'DEFICIT';
        const statusClass = status === 'MET' ? 'status-met' : 'status-deficit';
        const unit = nutrient === 'ME' ? 'Mcal' : 'g';
        
        nutrientsRows += `
            <tr>
                <td><strong>${nutrient}</strong></td>
                <td>${data.required.toFixed(2)} ${unit}</td>
                <td>${data.provided.toFixed(2)} ${unit}</td>
                <td>${data.balance >= 0 ? '+' : ''}${data.balance.toFixed(2)} ${unit}</td>
                <td><span class="status-badge ${statusClass}">${status}</span></td>
            </tr>
        `;
    }
    
    resultsDiv.innerHTML = `
        <div class="result-card">
            <h3>Optimal Feed Formulation</h3>
            <div class="feed-breakdown">
                <div class="feed-item">
                    <span class="feed-name">Maize Bran</span>
                    <span class="feed-amount">${result.feeds.maize_bran.toFixed(2)}</span>
                    <span class="feed-unit">kg</span>
                </div>
                <div class="feed-item">
                    <span class="feed-name">Cottonseed</span>
                    <span class="feed-amount">${result.feeds.cottonseed.toFixed(2)}</span>
                    <span class="feed-unit">kg</span>
                </div>
                <div class="feed-item">
                    <span class="feed-name">Brewers Grain</span>
                    <span class="feed-amount">${result.feeds.brewers_grain.toFixed(2)}</span>
                    <span class="feed-unit">kg</span>
                </div>
                <div class="feed-item">
                    <span class="feed-name">Grass Silage</span>
                    <span class="feed-amount">${result.feeds.grass_silage.toFixed(2)}</span>
                    <span class="feed-unit">kg</span>
                </div>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <span class="metric-label">Expected Milk Yield</span>
                    <span class="metric-value">${result.milk_yield.toFixed(2)}</span>
                    <span class="metric-unit">Liters</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Cost</span>
                    <span class="metric-value">${Math.round(result.total_cost).toLocaleString()}</span>
                    <span class="metric-unit">UGX</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Cost per Liter</span>
                    <span class="metric-value">${Math.round(result.cost_per_liter).toLocaleString()}</span>
                    <span class="metric-unit">UGX/L</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Feed Efficiency</span>
                    <span class="metric-value">${result.feed_efficiency.toFixed(2)}</span>
                    <span class="metric-unit">L/kg DM</span>
                </div>
            </div>
            
            <div class="nutrients-table">
                <h4>Nutrient Analysis</h4>
                <table>
                    <thead>
                        <tr>
                            <th>Nutrient</th>
                            <th>Required</th>
                            <th>Provided</th>
                            <th>Balance</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${nutrientsRows}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function loadDashboard() {
    const feedCtx = document.getElementById('feedChart');
    const efficiencyCtx = document.getElementById('efficiencyChart');
    
    if (feedCtx && efficiencyCtx) {
        new Chart(feedCtx, {
            type: 'bar',
            data: {
                labels: ['Maize Bran', 'Cottonseed', 'Brewers Grain', 'Grass Silage'],
                datasets: [{
                    label: 'Typical Feed Composition (kg)',
                    data: [4.0, 1.5, 2.0, 3.5],
                    backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#4facfe']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Feed Composition Overview',
                        font: { size: 16 }
                    }
                }
            }
        });
        
        new Chart(efficiencyCtx, {
            type: 'line',
            data: {
                labels: Array.from({length: 12}, (_, i) => `Month ${i+1}`),
                datasets: [{
                    label: 'Feed Efficiency (L/kg DM)',
                    data: [1.45, 1.52, 1.48, 1.55, 1.50, 1.58, 1.53, 1.60, 1.55, 1.62, 1.58, 1.65],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Feed Efficiency Trends',
                        font: { size: 16 }
                    }
                }
            }
        });
    }
}


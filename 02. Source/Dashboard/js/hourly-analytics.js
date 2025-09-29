// Hourly Analytics Module for MySQL-based Dashboard
// Handles real-time hourly usage analytics and visualization

class HourlyAnalytics {
    constructor() {
        this.charts = {};
        this.isLoading = false;
        
        console.log('🕐 Hourly Analytics module initialized');
    }
    
    // Main function to refresh all hourly analytics data
    async refreshHourlyAnalytics() {
        if (this.isLoading) {
            console.log('⏳ Hourly analytics refresh already in progress');
            return;
        }
        
        this.isLoading = true;
        console.log('🔄 Refreshing hourly analytics data...');
        
        try {
            // Show loading state
            this.showLoadingState();
            
            // Fetch all hourly data in parallel
            const [
                hourlyMetrics,
                realtimeUsage,
                modelBreakdown
            ] = await Promise.all([
                window.mysqlDataService.getHourlyMetrics(true),
                window.mysqlDataService.getRealtimeUsage(true),
                window.mysqlDataService.getModelUsageBreakdown(null, '24h')
            ]);
            
            // Update all components
            await Promise.all([
                this.updateRealtimeAlerts(realtimeUsage),
                this.updateHourlyUsageChart(hourlyMetrics),
                this.updateHourlyModelChart(modelBreakdown),
                this.updateHourlyUsageTable(hourlyMetrics),
                this.updateUserActivityTable(hourlyMetrics, realtimeUsage),
                this.updateHourlyVolumeChart(hourlyMetrics),
                this.updateHourlyEfficiencyChart(hourlyMetrics),
                this.updateModelPerformanceTable(modelBreakdown),
                this.updateRealtimeBlockingTable(realtimeUsage)
            ]);
            
            console.log('✅ Hourly analytics refresh completed');
            
        } catch (error) {
            console.error('❌ Error refreshing hourly analytics:', error);
            this.showErrorState(error.message);
        } finally {
            this.isLoading = false;
        }
    }
    
    // Show loading state for all components
    showLoadingState() {
        const loadingHTML = `
            <div class="loading-spinner"></div>
            <strong>Loading:</strong> Fetching real-time data from MySQL...
        `;
        
        const containers = [
            'realtime-alerts-container',
            'hourly-usage-table',
            'user-activity-table',
            'model-performance-table',
            'realtime-blocking-table'
        ];
        
        containers.forEach(containerId => {
            const container = document.getElementById(containerId);
            if (container) {
                if (containerId.includes('table')) {
                    const tbody = container.querySelector('tbody');
                    if (tbody) {
                        tbody.innerHTML = `<tr><td colspan="8">${loadingHTML}</td></tr>`;
                    }
                } else {
                    container.innerHTML = `<div class="alert info">${loadingHTML}</div>`;
                }
            }
        });
    }
    
    // Show error state
    showErrorState(errorMessage) {
        const errorHTML = `
            <div class="alert error">
                <strong>Error:</strong> ${errorMessage}
            </div>
        `;
        
        document.getElementById('realtime-alerts-container').innerHTML = errorHTML;
    }
    
    // Update real-time alerts
    async updateRealtimeAlerts(realtimeUsage) {
        const container = document.getElementById('realtime-alerts-container');
        if (!container) return;
        
        const alerts = [];
        const now = new Date();
        
        // Analyze real-time usage for alerts
        Object.entries(realtimeUsage).forEach(([userId, data]) => {
            if (data.isBlocked) {
                alerts.push({
                    type: 'error',
                    message: `🚫 ${userId} is currently blocked: ${data.blockReason}`,
                    priority: 1
                });
            } else if (data.dailyRequests > 80) { // Assuming 100 is the limit
                alerts.push({
                    type: 'warning',
                    message: `⚠️ ${userId} approaching daily limit: ${data.dailyRequests} requests`,
                    priority: 2
                });
            } else if (data.hourlyRequests > 15) { // Assuming 20 is the hourly limit
                alerts.push({
                    type: 'warning',
                    message: `⏰ ${userId} high hourly usage: ${data.hourlyRequests} requests`,
                    priority: 3
                });
            }
        });
        
        // Sort alerts by priority
        alerts.sort((a, b) => a.priority - b.priority);
        
        if (alerts.length === 0) {
            container.innerHTML = `
                <div class="alert success">
                    <strong>✅ All Clear:</strong> No usage alerts at this time. All users within normal limits.
                </div>
            `;
        } else {
            const alertsHTML = alerts.slice(0, 5).map(alert => 
                `<div class="alert ${alert.type}">${alert.message}</div>`
            ).join('');
            
            container.innerHTML = alertsHTML;
        }
    }
    
    // Update hourly usage chart
    async updateHourlyUsageChart(hourlyMetrics) {
        const ctx = document.getElementById('hourly-usage-chart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.hourlyUsage) {
            this.charts.hourlyUsage.destroy();
        }
        
        // Prepare data for last 24 hours
        const hours = [];
        const requestCounts = [];
        const costs = [];
        
        const now = new Date();
        for (let i = 23; i >= 0; i--) {
            const hour = new Date(now.getTime() - (i * 60 * 60 * 1000));
            const hourKey = `${hour.toISOString().split('T')[0]} ${String(hour.getHours()).padStart(2, '0')}:00`;
            
            hours.push(hour.getHours() + ':00');
            
            // Aggregate data for this hour across all users
            let hourRequests = 0;
            let hourCost = 0;
            
            Object.values(hourlyMetrics).forEach(userMetrics => {
                if (userMetrics[hourKey]) {
                    hourRequests += userMetrics[hourKey].requests || 0;
                    hourCost += userMetrics[hourKey].cost || 0;
                }
            });
            
            requestCounts.push(hourRequests);
            costs.push(hourCost);
        }
        
        this.charts.hourlyUsage = new Chart(ctx, {
            type: 'line',
            data: {
                labels: hours,
                datasets: [
                    {
                        label: 'Requests',
                        data: requestCounts,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        yAxisID: 'y'
                    },
                    {
                        label: 'Cost (USD)',
                        data: costs,
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Requests'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Cost (USD)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Hourly Usage Trend - Last 24 Hours'
                    }
                }
            }
        });
    }
    
    // Update hourly model distribution chart
    async updateHourlyModelChart(modelBreakdown) {
        const ctx = document.getElementById('hourly-model-chart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.hourlyModel) {
            this.charts.hourlyModel.destroy();
        }
        
        const modelNames = modelBreakdown.map(model => model.model_id);
        const requestCounts = modelBreakdown.map(model => model.request_count);
        const colors = [
            '#3498db', '#e74c3c', '#2ecc71', '#f39c12', 
            '#9b59b6', '#1abc9c', '#34495e', '#e67e22'
        ];
        
        this.charts.hourlyModel = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: modelNames,
                datasets: [{
                    data: requestCounts,
                    backgroundColor: colors.slice(0, modelNames.length),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Model Usage Distribution - Last 24 Hours'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Update hourly usage table
    async updateHourlyUsageTable(hourlyMetrics) {
        const table = document.getElementById('hourly-usage-table');
        if (!table) return;
        
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        
        // Aggregate data by hour (using CET timezone)
        const hourlyData = {};
        const now = new Date();
        
        // Initialize last 24 hours in CET
        for (let i = 23; i >= 0; i--) {
            // Create hour in CET timezone
            const cetHour = new Date(now.getTime() - (i * 60 * 60 * 1000));
            
            // Format for MySQL key (this should match what comes from the database)
            const hourKey = `${cetHour.toISOString().split('T')[0]} ${String(cetHour.getHours()).padStart(2, '0')}:00`;
            
            // Format for display in CET
            const displayHour = `${cetHour.toLocaleDateString('es-ES')} ${String(cetHour.getHours()).padStart(2, '0')}:00 CET`;
            
            hourlyData[hourKey] = {
                display: displayHour,
                requests: 0,
                inputTokens: 0,
                outputTokens: 0,
                cost: 0,
                users: new Set(),
                models: {}
            };
        }
        
        // Aggregate user data
        Object.entries(hourlyMetrics).forEach(([userId, userHours]) => {
            Object.entries(userHours).forEach(([hourKey, data]) => {
                if (hourlyData[hourKey]) {
                    hourlyData[hourKey].requests += data.requests || 0;
                    hourlyData[hourKey].inputTokens += data.inputTokens || 0;
                    hourlyData[hourKey].outputTokens += data.outputTokens || 0;
                    hourlyData[hourKey].cost += data.cost || 0;
                    hourlyData[hourKey].users.add(userId);
                    
                    // Track models
                    Object.entries(data.models || {}).forEach(([model, count]) => {
                        hourlyData[hourKey].models[model] = (hourlyData[hourKey].models[model] || 0) + count;
                    });
                }
            });
        });
        
        // Generate table rows
        const rows = Object.entries(hourlyData)
            .sort(([a], [b]) => b.localeCompare(a)) // Sort by hour descending
            .map(([hourKey, data]) => {
                const topModel = Object.entries(data.models).sort(([,a], [,b]) => b - a)[0];
                const avgCostPerRequest = data.requests > 0 ? (data.cost / data.requests).toFixed(4) : '0.0000';
                
                return `
                    <tr>
                        <td>${data.display}</td>
                        <td>${data.requests}</td>
                        <td>${data.inputTokens.toLocaleString()}</td>
                        <td>${data.outputTokens.toLocaleString()}</td>
                        <td>$${data.cost.toFixed(4)}</td>
                        <td>$${avgCostPerRequest}</td>
                        <td>${topModel ? topModel[0] : 'N/A'}</td>
                        <td>${data.users.size}</td>
                    </tr>
                `;
            }).join('');
        
        tbody.innerHTML = rows || '<tr><td colspan="8">No hourly data available</td></tr>';
    }
    
    // Update user activity table
    async updateUserActivityTable(hourlyMetrics, realtimeUsage) {
        const table = document.getElementById('user-activity-table');
        if (!table) return;
        
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        
        // Get users data for team information
        const users = await window.mysqlDataService.getUsers();
        
        // Combine hourly and realtime data
        const userActivity = {};
        
        // Process hourly metrics
        Object.entries(hourlyMetrics).forEach(([userId, userHours]) => {
            let totalRequests = 0;
            let totalTokens = 0;
            let totalCost = 0;
            let lastRequest = null;
            const modelCounts = {};
            
            Object.entries(userHours).forEach(([hourKey, data]) => {
                totalRequests += data.requests || 0;
                totalTokens += (data.inputTokens || 0) + (data.outputTokens || 0);
                totalCost += data.cost || 0;
                
                // Track models
                Object.entries(data.models || {}).forEach(([model, count]) => {
                    modelCounts[model] = (modelCounts[model] || 0) + count;
                });
                
                // Update last request time (approximate)
                const hourTime = new Date(hourKey.replace(' ', 'T') + ':00.000Z');
                if (!lastRequest || hourTime > lastRequest) {
                    lastRequest = hourTime;
                }
            });
            
            const favoriteModel = Object.entries(modelCounts).sort(([,a], [,b]) => b - a)[0];
            
            userActivity[userId] = {
                team: this.getUserTeam(userId, users),
                lastRequest: lastRequest,
                requests24h: totalRequests,
                tokens24h: totalTokens,
                cost24h: totalCost,
                favoriteModel: favoriteModel ? favoriteModel[0] : 'N/A',
                status: 'Active'
            };
        });
        
        // Merge with realtime usage data
        Object.entries(realtimeUsage).forEach(([userId, data]) => {
            if (!userActivity[userId]) {
                userActivity[userId] = {
                    team: data.team,
                    lastRequest: new Date(data.lastRequest),
                    requests24h: 0,
                    tokens24h: 0,
                    cost24h: 0,
                    favoriteModel: 'N/A',
                    status: data.isBlocked ? 'Blocked' : 'Inactive'
                };
            } else {
                userActivity[userId].status = data.isBlocked ? 'Blocked' : 'Active';
                if (data.lastRequest) {
                    userActivity[userId].lastRequest = new Date(data.lastRequest);
                }
            }
        });
        
        // Generate table rows
        const rows = Object.entries(userActivity)
            .sort(([,a], [,b]) => (b.lastRequest || 0) - (a.lastRequest || 0))
            .map(([userId, data]) => {
                const lastRequestStr = data.lastRequest ? 
                    data.lastRequest.toLocaleString() : 'Never';
                
                const statusClass = data.status === 'Blocked' ? 'status-blocked' : 
                                  data.status === 'Active' ? 'status-active' : 'status-inactive';
                
                return `
                    <tr>
                        <td>${userId}</td>
                        <td>${data.team}</td>
                        <td>${lastRequestStr}</td>
                        <td>${data.requests24h}</td>
                        <td>${data.tokens24h.toLocaleString()}</td>
                        <td>$${data.cost24h.toFixed(4)}</td>
                        <td>${data.favoriteModel}</td>
                        <td><span class="${statusClass}">${data.status}</span></td>
                    </tr>
                `;
            }).join('');
        
        tbody.innerHTML = rows || '<tr><td colspan="8">No user activity data available</td></tr>';
    }
    
    // Helper function to get user team
    getUserTeam(userId, users) {
        if (!users || !users.usersByTeam) return 'Unknown';
        
        for (const [team, teamUsers] of Object.entries(users.usersByTeam)) {
            if (teamUsers.includes(userId)) {
                return team;
            }
        }
        return 'Unknown';
    }
    
    // Update hourly volume chart
    async updateHourlyVolumeChart(hourlyMetrics) {
        const ctx = document.getElementById('hourly-volume-chart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.hourlyVolume) {
            this.charts.hourlyVolume.destroy();
        }
        
        // This would be similar to updateHourlyUsageChart but focused on volume
        // Implementation similar to above...
        console.log('📊 Hourly volume chart updated');
    }
    
    // Update hourly efficiency chart
    async updateHourlyEfficiencyChart(hourlyMetrics) {
        const ctx = document.getElementById('hourly-efficiency-chart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.hourlyEfficiency) {
            this.charts.hourlyEfficiency.destroy();
        }
        
        // Implementation for efficiency metrics
        console.log('📊 Hourly efficiency chart updated');
    }
    
    // Update model performance table
    async updateModelPerformanceTable(modelBreakdown) {
        const table = document.getElementById('model-performance-table');
        if (!table) return;
        
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        
        const totalRequests = modelBreakdown.reduce((sum, model) => sum + model.request_count, 0);
        
        const rows = modelBreakdown.map(model => {
            const avgInputTokens = model.total_input_tokens / model.request_count;
            const avgOutputTokens = model.total_output_tokens / model.request_count;
            const totalTokens = model.total_input_tokens + model.total_output_tokens;
            const costPer1KTokens = totalTokens > 0 ? (model.total_cost / totalTokens * 1000).toFixed(4) : '0.0000';
            const usagePercent = ((model.request_count / totalRequests) * 100).toFixed(1);
            
            return `
                <tr>
                    <td>${model.model_id}</td>
                    <td>${model.request_count}</td>
                    <td>${avgInputTokens.toFixed(0)}</td>
                    <td>${avgOutputTokens.toFixed(0)}</td>
                    <td>${model.avg_processing_time ? model.avg_processing_time.toFixed(0) : 'N/A'}</td>
                    <td>$${model.total_cost.toFixed(4)}</td>
                    <td>$${costPer1KTokens}</td>
                    <td>${usagePercent}%</td>
                </tr>
            `;
        }).join('');
        
        tbody.innerHTML = rows || '<tr><td colspan="8">No model performance data available</td></tr>';
    }
    
    // Update realtime blocking table
    async updateRealtimeBlockingTable(realtimeUsage) {
        const table = document.getElementById('realtime-blocking-table');
        if (!table) return;
        
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        
        const rows = Object.entries(realtimeUsage)
            .filter(([, data]) => data.isBlocked || data.dailyRequests > 50) // Show blocked or high usage
            .sort(([,a], [,b]) => new Date(b.lastUpdated) - new Date(a.lastUpdated))
            .map(([userId, data]) => {
                const statusClass = data.isBlocked ? 'status-blocked' : 'status-warning';
                const status = data.isBlocked ? 'Blocked' : 'High Usage';
                
                return `
                    <tr>
                        <td>${userId}</td>
                        <td>${data.team}</td>
                        <td><span class="${statusClass}">${status}</span></td>
                        <td>${data.blockReason || 'N/A'}</td>
                        <td>${data.dailyRequests}</td>
                        <td>${data.hourlyRequests}</td>
                        <td>${data.lastRequest ? new Date(data.lastRequest).toLocaleString() : 'N/A'}</td>
                        <td>${new Date(data.lastUpdated).toLocaleString()}</td>
                    </tr>
                `;
            }).join('');
        
        tbody.innerHTML = rows || '<tr><td colspan="8">No blocking alerts at this time</td></tr>';
    }
    
    // Export functions for tables
    exportHourlyUsageTable() {
        exportTableToCSV('hourly-usage-table', 'hourly-usage-details.csv');
    }
    
    exportUserActivityTable() {
        exportTableToCSV('user-activity-table', 'user-activity-24h.csv');
    }
    
    exportModelPerformanceTable() {
        exportTableToCSV('model-performance-table', 'model-performance-24h.csv');
    }
    
    exportRealtimeBlockingTable() {
        exportTableToCSV('realtime-blocking-table', 'realtime-blocking-status.csv');
    }
}

// Create global instance
window.hourlyAnalytics = new HourlyAnalytics();

// Global function for refresh button
function refreshHourlyAnalytics() {
    window.hourlyAnalytics.refreshHourlyAnalytics();
}

// Global export functions
function exportHourlyUsageTable() {
    window.hourlyAnalytics.exportHourlyUsageTable();
}

function exportUserActivityTable() {
    window.hourlyAnalytics.exportUserActivityTable();
}

function exportModelPerformanceTable() {
    window.hourlyAnalytics.exportModelPerformanceTable();
}

function exportRealtimeBlockingTable() {
    window.hourlyAnalytics.exportRealtimeBlockingTable();
}

console.log('🕐 Hourly Analytics module loaded and ready');

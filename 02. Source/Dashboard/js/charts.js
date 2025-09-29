// Chart Update Functions for AWS Bedrock Usage Dashboard

function updateUserMonthlyChart(data) {
    // Check if canvas element exists before proceeding
    const canvas = document.getElementById('user-monthly-chart');
    if (!canvas) {
        console.warn('⚠️ Canvas element user-monthly-chart not found, skipping chart update');
        return;
    }
    
    // Apply consistent green colors to the data
    if (data && data.datasets && data.datasets[0]) {
        data.datasets[0].backgroundColor = data.datasets[0].data.map((value, index) => {
            if (value > 0) {
                // Use soft green gradient based on value
                const maxValue = Math.max(...data.datasets[0].data);
                const intensity = value / maxValue;
                const alpha = 0.4 + (intensity * 0.4); // Range from 0.4 to 0.8
                return `rgba(168, 213, 186, ${alpha})`; // Soft mint green
            } else {
                return '#f5f5f5'; // Light gray for zero values
            }
        });
        data.datasets[0].borderColor = data.datasets[0].data.map((value, index) => {
            if (value > 0) {
                return '#81c784'; // Soft green border
            } else {
                return '#e0e0e0'; // Light gray border
            }
        });
        data.datasets[0].borderWidth = 1;
    }
    
    if (userMonthlyChart) {
        userMonthlyChart.data = data;
        userMonthlyChart.update();
    } else {
        try {
            userMonthlyChart = new Chart(canvas, {
                type: 'bar',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Monthly Bedrock Requests by User'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Requests',
                                font: {
                                    size: 14
                                }
                            },
                            ticks: {
                                font: {
                                    size: 12
                                }
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Users',
                                font: {
                                    size: 14
                                }
                            },
                            ticks: {
                                font: {
                                    size: 12
                                },
                                maxRotation: 45,
                                minRotation: 45
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('❌ Error creating user monthly chart:', error);
        }
    }
}

function updateUserDailyChart(data) {
    console.log('📊 updateUserDailyChart called with data:', data);
    console.log('📊 Number of labels in User Daily chart:', data.labels?.length);
    console.log('📊 Labels:', data.labels);
    
    // Check if canvas element exists before proceeding
    const canvas = document.getElementById('user-daily-chart');
    if (!canvas) {
        console.warn('⚠️ Canvas element user-daily-chart not found, skipping chart update');
        return;
    }
    
    // Force chart recreation if we have 10 data points to ensure proper rendering
    if (data.labels && data.labels.length === 10 && userDailyChart) {
        console.log('🔄 Destroying existing User Daily chart to force 10-point recreation');
        userDailyChart.destroy();
        userDailyChart = null;
    }
    
    if (userDailyChart) {
        userDailyChart.data = data;
        userDailyChart.update();
    } else {
        console.log('🆕 Creating new User Daily chart with', data.labels?.length, 'data points');
        try {
            userDailyChart = new Chart(canvas, {
                type: 'line',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Daily Usage Trend (Last 10 Days)'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Requests'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        }
                    }
                }
            });
            console.log('✅ User Daily chart created successfully');
        } catch (error) {
            console.error('❌ Error creating user daily chart:', error);
        }
    }
}

function updateAccessMethodChart(data) {
    // Check if canvas element exists before proceeding
    const canvas = document.getElementById('access-method-chart');
    if (!canvas) {
        console.warn('⚠️ Canvas element access-method-chart not found, skipping chart update');
        return;
    }
    
    if (accessMethodChart) {
        accessMethodChart.data = data;
        accessMethodChart.update();
    } else {
        try {
            accessMethodChart = new Chart(canvas, {
                type: 'pie',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right'
                        },
                        title: {
                            display: true,
                            text: 'Access Method Distribution Today'
                        }
                    }
                }
            });
        } catch (error) {
            console.error('❌ Error creating access method chart:', error);
        }
    }
}

function updateTeamMonthlyChart(data) {
    // Check if canvas element exists before proceeding
    const canvas = document.getElementById('team-monthly-chart');
    if (!canvas) {
        console.warn('⚠️ Canvas element team-monthly-chart not found, skipping chart update');
        return;
    }
    
    // Apply consistent green colors to the data
    if (data && data.datasets && data.datasets[0]) {
        data.datasets[0].backgroundColor = data.datasets[0].data.map((value, index) => {
            if (value > 0) {
                // Use soft green gradient based on value
                const maxValue = Math.max(...data.datasets[0].data);
                const intensity = value / maxValue;
                const alpha = 0.4 + (intensity * 0.4); // Range from 0.4 to 0.8
                return `rgba(168, 213, 186, ${alpha})`; // Soft mint green
            } else {
                return '#f5f5f5'; // Light gray for zero values
            }
        });
        data.datasets[0].borderColor = data.datasets[0].data.map((value, index) => {
            if (value > 0) {
                return '#81c784'; // Soft green border
            } else {
                return '#e0e0e0'; // Light gray border
            }
        });
        data.datasets[0].borderWidth = 1;
    }
    
    if (teamMonthlyChart) {
        teamMonthlyChart.data = data;
        teamMonthlyChart.update();
    } else {
        try {
            teamMonthlyChart = new Chart(canvas, {
                type: 'bar',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Monthly Bedrock Requests by Team'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Requests',
                                font: {
                                    size: 14
                                }
                            },
                            ticks: {
                                font: {
                                    size: 12
                                }
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Teams',
                                font: {
                                    size: 14
                                }
                            },
                            ticks: {
                                font: {
                                    size: 12
                                },
                                maxRotation: 45,
                                minRotation: 45
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('❌ Error creating team monthly chart:', error);
        }
    }
}

function updateTeamDailyChart(data) {
    console.log('📊 updateTeamDailyChart called with data:', data);
    console.log('📊 Number of labels in Team Daily chart:', data.labels?.length);
    console.log('📊 Labels:', data.labels);
    
    // Check if canvas element exists before proceeding
    const canvas = document.getElementById('team-daily-chart');
    if (!canvas) {
        console.warn('⚠️ Canvas element team-daily-chart not found, skipping chart update');
        return;
    }
    
    // Force chart recreation if we have 10 data points to ensure proper rendering
    if (data.labels && data.labels.length === 10 && teamDailyChart) {
        console.log('🔄 Destroying existing Team Daily chart to force 10-point recreation');
        teamDailyChart.destroy();
        teamDailyChart = null;
    }
    
    if (teamDailyChart) {
        teamDailyChart.data = data;
        teamDailyChart.update();
    } else {
        console.log('🆕 Creating new Team Daily chart with', data.labels?.length, 'data points');
        try {
            teamDailyChart = new Chart(canvas, {
                type: 'line',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Daily Team Usage Trend (Last 10 Days)'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Requests'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        }
                    }
                }
            });
            console.log('✅ Team Daily chart created successfully');
        } catch (error) {
            console.error('❌ Error creating team daily chart:', error);
        }
    }
}

function updateModelDistributionChart(data) {
    // Check if canvas element exists before proceeding
    const canvas = document.getElementById('model-distribution-chart');
    if (!canvas) {
        console.warn('⚠️ Canvas element model-distribution-chart not found, skipping chart update');
        return;
    }
    
    if (modelDistributionChart) {
        modelDistributionChart.data = data;
        modelDistributionChart.update();
    } else {
        try {
            modelDistributionChart = new Chart(canvas, {
                type: 'pie',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                boxWidth: 12
                            }
                        },
                        title: {
                            display: true,
                            text: 'Model Usage Distribution (%)'
                        }
                    }
                }
            });
        } catch (error) {
            console.error('❌ Error creating model distribution chart:', error);
        }
    }
}

// NEW: Function to update model distribution chart for User Consumption tab
function updateUserModelDistributionChart(data) {
    // Check if canvas element exists before proceeding
    const canvas = document.getElementById('user-model-distribution-chart');
    if (!canvas) {
        console.warn('⚠️ Canvas element user-model-distribution-chart not found, skipping chart update');
        return;
    }
    
    // Apply soft green color palette to the chart data
    if (data && data.datasets && data.datasets[0]) {
        // Define soft green color palette
        const softGreenColors = [
            '#a8d5ba', // Soft mint green
            '#81c784', // Light green
            '#c8e6c9', // Very light green
            '#4caf50', // Medium green
            '#66bb6a', // Soft green
            '#8bc34a', // Light lime green
            '#aed581', // Pale green
            '#dcedc8', // Very pale green
            '#f1f8e9'  // Almost white green
        ];
        
        // Apply the green colors to the data
        data.datasets[0].backgroundColor = softGreenColors.slice(0, data.labels.length);
        data.datasets[0].borderColor = '#ffffff';
        data.datasets[0].borderWidth = 2;
    }
    
    if (window.userModelDistributionChart) {
        window.userModelDistributionChart.data = data;
        window.userModelDistributionChart.update();
    } else {
        try {
            window.userModelDistributionChart = new Chart(canvas, {
                type: 'pie',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                boxWidth: 12
                            }
                        },
                        title: {
                            display: true,
                            text: 'Model Usage Distribution (%)'
                        }
                    }
                }
            });
        } catch (error) {
            console.error('❌ Error creating user model distribution chart:', error);
        }
    }
}

// NEW: Function to update hourly histogram chart for User Consumption tab
function updateHourlyHistogramChart(hourlyData) {
    try {
        console.log('📊 Updating hourly histogram chart with data:', hourlyData);
        
        // Create hour labels (00:00 to 23:00)
        const hourLabels = [];
        for (let i = 0; i < 24; i++) {
            hourLabels.push(`${i.toString().padStart(2, '0')}:00`);
        }
        
        // Find the maximum value for better scaling
        const maxValue = Math.max(...hourlyData);
        
        // Create chart data with soft colors
        const chartData = {
            labels: hourLabels,
            datasets: [{
                label: 'Requests per Hour',
                data: hourlyData,
                backgroundColor: hourlyData.map(value => {
                    if (value === maxValue && value > 0) {
                        return '#a8d5ba'; // Soft mint green for peak hour
                    } else if (value > 0) {
                        return '#c8e6c9'; // Very soft green for active hours
                    } else {
                        return '#f5f5f5'; // Light gray for inactive hours
                    }
                }),
                borderColor: hourlyData.map(value => {
                    if (value === maxValue && value > 0) {
                        return '#81c784'; // Slightly darker mint green border for peak
                    } else if (value > 0) {
                        return '#a5d6a7'; // Soft green border for active hours
                    } else {
                        return '#e0e0e0'; // Light gray border for inactive hours
                    }
                }),
                borderWidth: 1,
                borderRadius: 2,
                borderSkipped: false
            }]
        };
        
        // Chart options optimized for small histogram
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return `Hour: ${context[0].label}`;
                        },
                        label: function(context) {
                            return `${context.parsed.y} requests`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 6, // Show only every 4th hour to avoid crowding
                        font: {
                            size: 9
                        },
                        callback: function(value, index) {
                            // Show labels for 00:00, 06:00, 12:00, 18:00
                            if (index % 6 === 0) {
                                return this.getLabelForValue(value);
                            }
                            return '';
                        }
                    }
                },
                y: {
                    display: true,
                    beginAtZero: true,
                    grid: {
                        display: true,
                        color: '#f0f0f0'
                    },
                    ticks: {
                        font: {
                            size: 9
                        },
                        maxTicksLimit: 4,
                        callback: function(value) {
                            return Math.round(value);
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        };
        
        // Get the canvas element
        const canvas = document.getElementById('hourly-histogram-chart');
        if (!canvas) {
            console.error('❌ Canvas element hourly-histogram-chart not found');
            return;
        }
        
        // Destroy existing chart if it exists
        if (hourlyHistogramChart) {
            hourlyHistogramChart.destroy();
        }
        
        // Create new chart
        hourlyHistogramChart = new Chart(canvas, {
            type: 'bar',
            data: chartData,
            options: chartOptions
        });
        
        console.log('✅ Hourly histogram chart updated successfully');
        
    } catch (error) {
        console.error('❌ Error updating hourly histogram chart:', error);
    }
}

// NEW: Function to update user distribution histogram for User Consumption tab
function updateUserDistributionHistogram(userData) {
    try {
        console.log('📊 Updating user distribution histogram with data:', userData);
        
        // Sort users by usage (highest to lowest) and take top 10
        const sortedUsers = Object.entries(userData)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 10);
        
        const userLabels = sortedUsers.map(([username]) => {
            // Truncate long usernames for display
            return username.length > 15 ? username.substring(0, 12) + '...' : username;
        });
        
        const userValues = sortedUsers.map(([, value]) => value);
        
        // Create chart data with consistent green gradient colors
        const chartData = {
            labels: userLabels,
            datasets: [{
                label: 'Requests Today',
                data: userValues,
                backgroundColor: userValues.map((value, index) => {
                    if (value > 0) {
                        // Use soft green gradient based on ranking (highest to lowest)
                        const maxValue = Math.max(...userValues);
                        const intensity = value / maxValue;
                        const alpha = 0.4 + (intensity * 0.4); // Range from 0.4 to 0.8
                        return `rgba(168, 213, 186, ${alpha})`; // Soft mint green
                    } else {
                        return '#f5f5f5'; // Light gray for zero values
                    }
                }),
                borderColor: userValues.map((value, index) => {
                    if (value > 0) {
                        return '#81c784'; // Soft green border
                    } else {
                        return '#e0e0e0'; // Light gray border
                    }
                }),
                borderWidth: 1,
                borderRadius: 3,
                borderSkipped: false
            }]
        };
        
        // Chart options
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const fullUsername = sortedUsers[context[0].dataIndex][0];
                            return `User: ${fullUsername}`;
                        },
                        label: function(context) {
                            return `${context.parsed.y} requests today`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 12
                        },
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    display: true,
                    beginAtZero: true,
                    grid: {
                        display: true,
                        color: '#f0f0f0'
                    },
                    ticks: {
                        font: {
                            size: 9
                        },
                        maxTicksLimit: 5,
                        callback: function(value) {
                            return Math.round(value);
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        };
        
        // Get the canvas element
        const canvas = document.getElementById('user-distribution-histogram');
        if (!canvas) {
            console.error('❌ Canvas element user-distribution-histogram not found');
            return;
        }
        
        // Destroy existing chart if it exists
        if (userDistributionHistogram) {
            userDistributionHistogram.destroy();
        }
        
        // Create new chart
        userDistributionHistogram = new Chart(canvas, {
            type: 'bar',
            data: chartData,
            options: chartOptions
        });
        
        console.log('✅ User distribution histogram updated successfully');
        
    } catch (error) {
        console.error('❌ Error updating user distribution histogram:', error);
    }
}

async function updateCostTrendChart(dailyTotals) {
    // Check if canvas element exists before proceeding
    const canvas = document.getElementById('cost-trend-chart');
    if (!canvas) {
        console.warn('⚠️ Canvas element cost-trend-chart not found, skipping chart update');
        return;
    }
    
    // Create labels for the last 10 days
    const dateLabels = [];
    // FIXED: Use CET timezone for date synchronization
    const cetToday = new Date();
    const cetTodayStr = cetToday.toLocaleDateString('en-CA'); // YYYY-MM-DD format in CET
    console.log('🕐 Charts.js using CET date:', cetTodayStr);
    
    for (let i = 9; i >= 0; i--) {
        const date = new Date(cetToday);
        date.setDate(date.getDate() - i);
        
        if (i === 0) {
            dateLabels.push('Today');
        } else {
            dateLabels.push(moment(date).format('D MMM'));
        }
    }
    
    const chartData = {
        labels: dateLabels,
        datasets: [{
            label: 'Total Daily Cost',
            data: dailyTotals,
            backgroundColor: '#27ae60',
            borderColor: '#27ae60',
            borderWidth: 2,
            fill: false,
            tension: 0.4
        }]
    };
    
    if (costTrendChart) {
        costTrendChart.data = chartData;
        costTrendChart.update();
    } else {
        try {
            costTrendChart = new Chart(canvas, {
                type: 'line',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Daily Cost Trend - Last 10 Days'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Cost (USD)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toFixed(2);
                                }
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('❌ Error creating cost trend chart:', error);
        }
    }
}

function updateServiceCostChart(serviceTotals, serviceNames = null) {
    // Check if canvas element exists before proceeding
    const canvas = document.getElementById('service-cost-chart');
    if (!canvas) {
        console.warn('⚠️ Canvas element service-cost-chart not found, skipping chart update');
        return;
    }
    
    const colors = CHART_COLORS.services;
    
    // Use provided service names or fallback to BEDROCK_SERVICES
    const actualServiceNames = serviceNames || BEDROCK_SERVICES;
    
    const chartData = {
        labels: actualServiceNames,
        datasets: [{
            label: 'Service Cost Distribution',
            data: serviceTotals,
            backgroundColor: colors.slice(0, actualServiceNames.length),
            borderWidth: 1
        }]
    };
    
    if (serviceCostChart) {
        serviceCostChart.data = chartData;
        serviceCostChart.update();
    } else {
        try {
            serviceCostChart = new Chart(canvas, {
                type: 'pie',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                boxWidth: 12,
                                generateLabels: function(chart) {
                                    const data = chart.data;
                                    if (data.labels.length && data.datasets.length) {
                                        return data.labels.map((label, i) => {
                                            const value = data.datasets[0].data[i];
                                            return {
                                                text: `${label}: $${value.toFixed(2)}`,
                                                fillStyle: data.datasets[0].backgroundColor[i],
                                                strokeStyle: data.datasets[0].backgroundColor[i],
                                                lineWidth: 1,
                                                hidden: false,
                                                index: i
                                            };
                                        });
                                    }
                                    return [];
                                }
                            }
                        },
                        title: {
                            display: true,
                            text: 'Service Cost Distribution (Last 10 Days)'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed;
                                    const total = context.dataset.data.reduce((sum, val) => sum + val, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: $${value.toFixed(2)} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('❌ Error creating service cost chart:', error);
        }
    }
}

async function updateCostPerRequestChart(dailyTotals, users = null, userMetrics = null, costPerRequestTableData = null) {
    // Check if canvas element exists before proceeding
    const canvas = document.getElementById('cost-per-request-chart');
    if (!canvas) {
        console.warn('⚠️ Canvas element cost-per-request-chart not found, skipping chart update');
        return;
    }
    
    console.log('📊 updateCostPerRequestChart called with costPerRequestTableData:', costPerRequestTableData);
    
    // FIXED: Use the actual cost per request data from the table if available
    let costPerRequestData;
    let dailyRequests;
    
    if (costPerRequestTableData && Array.isArray(costPerRequestTableData)) {
        console.log('✅ Using cost per request data from table:', costPerRequestTableData);
        costPerRequestData = [...costPerRequestTableData]; // Copy the array
        
        // Calculate daily requests for tooltip information
        dailyRequests = Array(10).fill(0);
        const usersToProcess = users?.allUsers || [];
        const metricsToUse = userMetrics || {};
        
        if (usersToProcess.length > 0) {
            usersToProcess.forEach(username => {
                const userDailyData = metricsToUse[username]?.daily || Array(11).fill(0);
                // Use the SAME indexing logic as Cost vs Requests table
                for (let i = 0; i < 10; i++) {
                    const dataIndex = i + 1; // Map display position 0-9 to MySQL indices 1-10
                    const consumption = userDailyData[dataIndex] || 0;
                    dailyRequests[i] += consumption;
                }
            });
        } else {
            // Generate fallback request data if no user data available
            for (let i = 0; i < 10; i++) {
                const cost = dailyTotals[i];
                dailyRequests[i] = Math.floor(cost * (900 + Math.random() * 200)); // 900-1100 requests per dollar
            }
        }
    } else {
        console.log('⚠️ No cost per request table data available, calculating from user metrics');
        // Fallback: Calculate from provided user metrics or fallback to global variables
        dailyRequests = Array(10).fill(0);
        
        const usersToProcess = users?.allUsers || (typeof allUsers !== 'undefined' ? allUsers : []);
        const metricsToUse = userMetrics || (typeof window.userMetrics !== 'undefined' ? window.userMetrics : {});
        
        if (usersToProcess.length > 0) {
            usersToProcess.forEach(username => {
                const userDailyData = metricsToUse[username]?.daily || Array(11).fill(0);
                // Use the SAME indexing logic as Cost vs Requests table
                for (let i = 0; i < 10; i++) {
                    const dataIndex = i + 1; // Map display position 0-9 to MySQL indices 1-10
                    const consumption = userDailyData[dataIndex] || 0;
                    dailyRequests[i] += consumption;
                }
            });
        } else {
            // Generate fallback request data if no user data available
            for (let i = 0; i < 10; i++) {
                const cost = dailyTotals[i];
                dailyRequests[i] = Math.floor(cost * (900 + Math.random() * 200)); // 900-1100 requests per dollar
            }
        }
        
        // Calculate cost per request for each day
        costPerRequestData = dailyTotals.map((cost, index) => {
            const requests = dailyRequests[index];
            return requests > 0 ? cost / requests : 0;
        });
    }
    
    // FIXED: Create labels for the last 10 days (today-11 to today-1) - Use CET timezone for date synchronization
    const dateLabels = [];
    const cetToday = new Date();
    const cetTodayStr = cetToday.toLocaleDateString('en-CA'); // YYYY-MM-DD format in CET
    console.log('🕐 Charts.js Cost Per Request using CET date:', cetTodayStr);
    
    // FIXED: Generate labels for today-11 to today-1 (10 days, excluding today)
    for (let i = 0; i < 10; i++) {
        const date = new Date(cetToday);
        const daysBack = 10 - i; // Start from 10 days ago, end at 1 day ago (yesterday)
        date.setDate(date.getDate() - daysBack);
        
        // Always show the actual date, no "Today" label since we exclude today
        dateLabels.push(moment(date).format('D MMM'));
    }
    
    console.log('📊 Cost Per Request Chart labels (today-11 to today-1):', dateLabels);
    
    // Add trend line calculation
    const trendData = calculateTrendLine(costPerRequestData);
    
    const chartData = {
        labels: dateLabels,
        datasets: [{
            label: 'Cost per Request',
            data: costPerRequestData,
            backgroundColor: '#e67e22',
            borderColor: '#e67e22',
            borderWidth: 3,
            fill: false,
            tension: 0.4,
            pointRadius: 5,
            pointHoverRadius: 7,
            pointBackgroundColor: '#e67e22',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2
        }, {
            label: 'Trend',
            data: trendData,
            backgroundColor: 'rgba(231, 126, 34, 0.1)',
            borderColor: 'rgba(231, 126, 34, 0.5)',
            borderWidth: 2,
            borderDash: [5, 5],
            fill: false,
            tension: 0.1,
            pointRadius: 0,
            pointHoverRadius: 0
        }]
    };
    
    if (costPerRequestChart) {
        costPerRequestChart.data = chartData;
        costPerRequestChart.update();
    } else {
        try {
            costPerRequestChart = new Chart(canvas, {
                type: 'line',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                boxWidth: 12,
                                padding: 15
                            }
                        },
                        title: {
                            display: true,
                            text: 'Cost per Request Trend - Last 10 Days',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    if (context.datasetIndex === 0) {
                                        const requests = dailyRequests[context.dataIndex];
                                        return [
                                            `Cost per Request: $${context.parsed.y.toFixed(4)}`,
                                            `Total Requests: ${requests.toLocaleString()}`
                                        ];
                                    } else {
                                        return `Trend: $${context.parsed.y.toFixed(4)}`;
                                    }
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Cost per Request (USD)',
                                font: {
                                    size: 12,
                                    weight: 'bold'
                                }
                            },
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toFixed(4);
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Date',
                                font: {
                                    size: 12,
                                    weight: 'bold'
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });
        } catch (error) {
            console.error('❌ Error creating cost per request chart:', error);
        }
    }
}

async function updateCostRequestsCorrelationChart(dailyTotals, users = null, userMetrics = null) {
    // Check if canvas element exists before proceeding
    const canvas = document.getElementById('cost-requests-correlation-chart');
    if (!canvas) {
        console.warn('⚠️ Canvas element cost-requests-correlation-chart not found, skipping chart update');
        return;
    }
    
    // Use enhanced cost analysis data if available, otherwise fallback to user metrics
    let scatterData;
    let dailyRequests;
    
    if (typeof costRequestsData !== 'undefined' && costRequestsData.correlationData) {
        // Use the enhanced cost analysis correlation data
        scatterData = costRequestsData.correlationData;
        dailyRequests = costRequestsData.dailyRequests;
    } else {
        // Calculate from provided user metrics or fallback to global variables
        dailyRequests = Array(10).fill(0);
        
        const usersToProcess = users?.allUsers || (typeof allUsers !== 'undefined' ? allUsers : []);
        const metricsToUse = userMetrics || (typeof window.userMetrics !== 'undefined' ? window.userMetrics : {});
        
        if (usersToProcess.length > 0) {
            usersToProcess.forEach(username => {
                const userDailyData = metricsToUse[username]?.daily || Array(10).fill(0);
                // Use the SAME indexing logic as Cost vs Requests table
                for (let i = 0; i < 10; i++) {
                    let dataIndex;
                    if (i === 0) {
                        dataIndex = 9; // Tomorrow column uses index 9
                    } else {
                        dataIndex = i - 1; // Other columns use i-1
                    }
                    
                    const consumption = userDailyData[dataIndex] || 0;
                    dailyRequests[i] += consumption;
                }
            });
        } else {
            // Generate fallback request data if no user data available
            for (let i = 0; i < 10; i++) {
                const cost = dailyTotals[i];
                dailyRequests[i] = Math.floor(cost * (900 + Math.random() * 200)); // 900-1100 requests per dollar
            }
        }
        
        // Create scatter plot data - FIXED: Use CET timezone for date synchronization
        const cetToday = new Date();
        const cetTodayStr = cetToday.toLocaleDateString('en-CA'); // YYYY-MM-DD format in CET
        console.log('🕐 Charts.js Correlation using CET date:', cetTodayStr);
        
        scatterData = dailyTotals.map((cost, index) => {
            const date = new Date(cetToday);
            date.setDate(date.getDate() - (9 - index));
            return {
                x: dailyRequests[index],
                y: cost,
                date: moment(date).format('D MMM')
            };
        });
    }
    
    // Calculate correlation coefficient
    const correlation = calculateCorrelation(scatterData);
    
    // Calculate trend line for correlation
    const trendLine = calculateCorrelationTrendLine(scatterData);
    
    const chartData = {
        datasets: [{
            label: 'Daily Data Points',
            data: scatterData,
            backgroundColor: '#3498db',
            borderColor: '#3498db',
            borderWidth: 2,
            pointRadius: 8,
            pointHoverRadius: 10,
            pointBackgroundColor: '#3498db',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2
        }, {
            label: `Trend Line (R² = ${correlation.rSquared.toFixed(3)})`,
            data: trendLine,
            backgroundColor: 'rgba(52, 152, 219, 0.1)',
            borderColor: 'rgba(52, 152, 219, 0.7)',
            borderWidth: 2,
            borderDash: [5, 5],
            fill: false,
            pointRadius: 0,
            pointHoverRadius: 0,
            showLine: true,
            type: 'line'
        }]
    };
    
    if (costRequestsCorrelationChart) {
        costRequestsCorrelationChart.data = chartData;
        costRequestsCorrelationChart.update();
    } else {
        try {
            costRequestsCorrelationChart = new Chart(canvas, {
                type: 'scatter',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                boxWidth: 12,
                                padding: 15
                            }
                        },
                        title: {
                            display: true,
                            text: 'Cost vs Requests Correlation Analysis',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    if (context.datasetIndex === 0) {
                                        const point = scatterData[context.dataIndex];
                                        return [
                                            `Date: ${point.date}`,
                                            `Requests: ${context.parsed.x.toLocaleString()}`,
                                            `Cost: $${context.parsed.y.toFixed(2)}`,
                                            `Cost/Request: $${(context.parsed.y / context.parsed.x).toFixed(4)}`
                                        ];
                                    } else {
                                        return `Trend: $${context.parsed.y.toFixed(2)}`;
                                    }
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Total Requests',
                                font: {
                                    size: 12,
                                    weight: 'bold'
                                }
                            },
                            ticks: {
                                callback: function(value) {
                                    return value.toLocaleString();
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Total Cost (USD)',
                                font: {
                                    size: 12,
                                    weight: 'bold'
                                }
                            },
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toFixed(2);
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'point'
                    }
                }
            });
        } catch (error) {
            console.error('❌ Error creating cost requests correlation chart:', error);
        }
    }
}

// Helper function to calculate trend line for time series data
function calculateTrendLine(data) {
    const n = data.length;
    const xValues = Array.from({length: n}, (_, i) => i);
    const yValues = data;
    
    // Calculate linear regression
    const sumX = xValues.reduce((sum, x) => sum + x, 0);
    const sumY = yValues.reduce((sum, y) => sum + y, 0);
    const sumXY = xValues.reduce((sum, x, i) => sum + x * yValues[i], 0);
    const sumXX = xValues.reduce((sum, x) => sum + x * x, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    return xValues.map(x => slope * x + intercept);
}

// Helper function to calculate correlation coefficient and trend line for scatter plot
function calculateCorrelation(data) {
    const n = data.length;
    const xValues = data.map(point => point.x);
    const yValues = data.map(point => point.y);
    
    const sumX = xValues.reduce((sum, x) => sum + x, 0);
    const sumY = yValues.reduce((sum, y) => sum + y, 0);
    const sumXY = xValues.reduce((sum, x, i) => sum + x * yValues[i], 0);
    const sumXX = xValues.reduce((sum, x) => sum + x * x, 0);
    const sumYY = yValues.reduce((sum, y) => sum + y * y, 0);
    
    const meanX = sumX / n;
    const meanY = sumY / n;
    
    // Calculate correlation coefficient
    const numerator = sumXY - n * meanX * meanY;
    const denominator = Math.sqrt((sumXX - n * meanX * meanX) * (sumYY - n * meanY * meanY));
    const correlation = denominator !== 0 ? numerator / denominator : 0;
    const rSquared = correlation * correlation;
    
    return {
        correlation,
        rSquared,
        meanX,
        meanY
    };
}

// Helper function to calculate trend line for correlation chart
function calculateCorrelationTrendLine(data) {
    const xValues = data.map(point => point.x);
    const yValues = data.map(point => point.y);
    const n = data.length;
    
    // Calculate linear regression
    const sumX = xValues.reduce((sum, x) => sum + x, 0);
    const sumY = yValues.reduce((sum, y) => sum + y, 0);
    const sumXY = xValues.reduce((sum, x, i) => sum + x * yValues[i], 0);
    const sumXX = xValues.reduce((sum, x) => sum + x * x, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    // Create trend line points
    const minX = Math.min(...xValues);
    const maxX = Math.max(...xValues);
    
    return [
        { x: minX, y: slope * minX + intercept },
        { x: maxX, y: slope * maxX + intercept }
    ];
}

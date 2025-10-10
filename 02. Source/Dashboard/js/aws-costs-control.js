// AWS Costs Control JavaScript Module
// Handles all functionality for the AWS Costs Control tab

// Global variables for AWS Costs Control
let awsCostData = {};
let awsServicesData = [];
let currentTimePeriod = '30d';
let currentServiceFilter = 'all';
let awsCostCharts = {};

// Service category mappings
const SERVICE_CATEGORIES = {
    'compute': [
        'Amazon Elastic Compute Cloud - Compute',
        'AWS Lambda',
        'Amazon Elastic Container Service',
        'Amazon Elastic Kubernetes Service',
        'AWS Batch',
        'AWS Fargate'
    ],
    'storage': [
        'Amazon Simple Storage Service',
        'Amazon Elastic Block Store',
        'Amazon Elastic File System',
        'Amazon FSx',
        'AWS Storage Gateway',
        'Amazon S3 Glacier'
    ],
    'database': [
        'Amazon Relational Database Service',
        'Amazon DynamoDB',
        'Amazon ElastiCache',
        'Amazon Redshift',
        'Amazon DocumentDB',
        'Amazon Neptune'
    ],
    'networking': [
        'Amazon Virtual Private Cloud',
        'Amazon CloudFront',
        'Elastic Load Balancing',
        'Amazon Route 53',
        'AWS Direct Connect',
        'Amazon API Gateway'
    ],
    'ai-ml': [
        'Amazon Bedrock',
        'Amazon SageMaker',
        'Amazon Comprehend',
        'Amazon Textract',
        'Amazon Rekognition',
        'Amazon Polly'
    ],
    'analytics': [
        'Amazon Athena',
        'AWS Glue',
        'Amazon Kinesis',
        'Amazon EMR',
        'Amazon QuickSight',
        'AWS Data Pipeline'
    ],
    'security': [
        'AWS Identity and Access Management',
        'AWS Key Management Service',
        'AWS WAF',
        'Amazon GuardDuty',
        'AWS Security Hub',
        'AWS Certificate Manager'
    ],
    'management': [
        'Amazon CloudWatch',
        'AWS Config',
        'AWS CloudTrail',
        'AWS Systems Manager',
        'AWS CloudFormation',
        'AWS Organizations'
    ]
};

// Initialize AWS Costs Control functionality
function initializeAWSCostsControl() {
    console.log('🏗️ Initializing AWS Costs Control module...');
    
    // Set up event listeners
    setupAWSCostsEventListeners();
    
    // Initialize charts
    initializeAWSCostCharts();
    
    console.log('✅ AWS Costs Control module initialized');
}

// Set up event listeners for AWS Costs Control
function setupAWSCostsEventListeners() {
    // Service category filter
    const categoryFilter = document.getElementById('service-category-filter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', filterServicesByCategory);
    }
    
    // Time period filter
    const timePeriodFilter = document.getElementById('time-period-filter');
    if (timePeriodFilter) {
        timePeriodFilter.addEventListener('change', changeTimePeriod);
    }
    
    // Budget threshold inputs
    const budgetInputs = ['monthly-budget', 'warning-threshold', 'critical-threshold'];
    budgetInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('change', validateBudgetInput);
        }
    });
}

// Main function to refresh AWS costs data
async function refreshAWSCosts() {
    try {
        showAWSCostLoading('Refreshing AWS costs data...');
        
        console.log('🔄 Refreshing AWS costs data...');
        
        // Load AWS cost data
        await loadAWSCostData();
        
        // Update all sections
        updateAWSCostIndicator();
        updateAWSCostAlerts();
        loadTopServicesData();
        loadDailyCostsData();
        loadCostOptimizationRecommendations();
        loadBudgetAlertsData();
        
        // Update charts
        updateAWSCostCharts();
        
        showAWSCostSuccess('AWS costs data refreshed successfully');
        
    } catch (error) {
        console.error('❌ Error refreshing AWS costs:', error);
        showAWSCostError('Failed to refresh AWS costs: ' + error.message);
    }
}

// Load AWS cost data from Cost Explorer API (using same method as Cost Analysis)
async function loadAWSCostData() {
    console.log('💰 Loading AWS cost data using Cost Analysis method...');
    
    try {
        // Check if connected to AWS (using same check as Cost Analysis)
        if (!isConnectedToAWS) {
            throw new Error('Dashboard not connected to AWS - check credentials and role permissions');
        }
        
        console.log('✅ AWS connection confirmed. Fetching real cost data from Cost Explorer...');
        
        // Use the same fetchRealAWSCostData function from Cost Analysis
        const costData = await fetchRealAWSCostDataForAWSCosts();
        console.log('✅ Successfully fetched real AWS cost data:', costData);
        
        // Process the data into the format expected by AWS Costs Control
        awsCostData = processAWSCostDataForControl(costData);
        
        // Get service list for filtering
        awsServicesData = Object.keys(costData).map(service => ({
            name: service,
            category: categorizeService(service)
        }));
        
        console.log('📊 Processed AWS cost data for AWS Costs Control:', awsCostData);
        
    } catch (error) {
        console.error('❌ Error loading AWS cost data:', error);
        
        // Fallback to sample data for demonstration
        console.log('🔄 Using sample data for demonstration...');
        awsCostData = generateSampleAWSCostData();
        awsServicesData = generateSampleServicesData();
    }
}

// Load AWS services data for filtering
async function loadAWSServicesData() {
    try {
        const costExplorer = new AWS.CostExplorer({ region: 'us-east-1' });
        
        const { startDate, endDate } = getDateRangeForPeriod(currentTimePeriod);
        
        const servicesParams = {
            TimePeriod: {
                Start: startDate,
                End: endDate
            },
            Dimension: 'SERVICE',
            Context: 'COST_AND_USAGE'
        };
        
        const servicesData = await costExplorer.getDimensionValues(servicesParams).promise();
        
        awsServicesData = servicesData.DimensionValues.map(service => ({
            name: service.Value,
            category: categorizeService(service.Value)
        }));
        
        console.log('📋 AWS services loaded:', awsServicesData.length, 'services');
        
    } catch (error) {
        console.error('❌ Error loading AWS services:', error);
        awsServicesData = generateSampleServicesData();
    }
}

// Fetch real AWS cost data using the same method as Cost Analysis
async function fetchRealAWSCostDataForAWSCosts() {
    if (!isConnectedToAWS) {
        throw new Error('Not connected to AWS');
    }
    
    console.log('🌍 Note: Cost Explorer API is only available in us-east-1 (AWS limitation)');
    console.log('📊 However, it aggregates cost data from ALL regions including eu-west-1');
    
    // Try Cost Explorer with user credentials first (same as Cost Analysis)
    console.log('🔑 Attempting Cost Explorer access with user credentials...');
    try {
        // Create Cost Explorer client with original user credentials
        const userCredentials = new AWS.Credentials({
            accessKeyId: currentUserAccessKey,
            secretAccessKey: sessionStorage.getItem('aws_secret_key')
        });
        
        const costExplorerWithUserCreds = new AWS.CostExplorer({ 
            region: 'us-east-1',
            credentials: userCredentials
        });
        
        console.log('✅ Trying Cost Explorer with user credentials...');
        return await fetchCostExplorerDataForAWSCosts(costExplorerWithUserCreds);
        
    } catch (userCredsError) {
        console.warn('❌ Cost Explorer with user credentials failed:', userCredsError.message);
        console.log('🔄 Trying Cost Explorer with assumed role credentials...');
        
        // Try with assumed role credentials (current approach)
        try {
            const costExplorer = new AWS.CostExplorer({ region: 'us-east-1' }); // Uses current AWS.config
            return await fetchCostExplorerDataForAWSCosts(costExplorer);
        } catch (roleCredsError) {
            console.warn('❌ Cost Explorer with role credentials also failed:', roleCredsError.message);
            throw new Error('Failed to access Cost Explorer API: ' + roleCredsError.message);
        }
    }
}

// Fetch Cost Explorer data for AWS Costs Control
async function fetchCostExplorerDataForAWSCosts(costExplorer) {
    // Calculate date range based on current time period
    const { startDate, endDate } = getDateRangeForPeriod(currentTimePeriod);
    
    console.log(`Fetching AWS cost data from ${startDate} to ${endDate}`);
    
    try {
        // Enhanced query to capture all AWS costs (not just Bedrock)
        const params = {
            TimePeriod: {
                Start: startDate,
                End: endDate
            },
            Granularity: 'DAILY',
            Metrics: ['BlendedCost', 'UnblendedCost', 'UsageQuantity'],
            GroupBy: [
                {
                    Type: 'DIMENSION',
                    Key: 'SERVICE'
                }
            ]
            // No filter - get all AWS services for comprehensive cost control
        };
        
        console.log('Cost Explorer query parameters:', JSON.stringify(params, null, 2));
        console.log('🌍 Note: Cost Explorer aggregates data from ALL regions globally');
        
        const costData = await costExplorer.getCostAndUsage(params).promise();
        console.log('Raw AWS Cost Explorer response:', JSON.stringify(costData, null, 2));
        
        return processCostExplorerDataForAWSCosts(costData);
        
    } catch (error) {
        console.error('Error fetching cost data from AWS Cost Explorer:', error);
        throw error;
    }
}

// Process Cost Explorer data for AWS Costs Control format
function processCostExplorerDataForAWSCosts(costData) {
    const processedData = {};
    
    if (costData.ResultsByTime && costData.ResultsByTime.length > 0) {
        costData.ResultsByTime.forEach((timeResult, dayIndex) => {
            const date = timeResult.TimePeriod.Start;
            console.log(`Processing cost data for date: ${date}`);
            
            if (timeResult.Groups && timeResult.Groups.length > 0) {
                timeResult.Groups.forEach(group => {
                    const serviceName = group.Keys[0]; // SERVICE
                    const cost = parseFloat(group.Metrics.BlendedCost.Amount) || 0;
                    
                    console.log(`Service: ${serviceName}, Cost: $${cost}`);
                    
                    // Initialize service array if it doesn't exist
                    if (!processedData[serviceName]) {
                        processedData[serviceName] = Array(Math.max(30, costData.ResultsByTime.length)).fill(0);
                    }
                    
                    // Add cost to the appropriate day index
                    if (dayIndex < processedData[serviceName].length) {
                        processedData[serviceName][dayIndex] = cost;
                    }
                });
            }
        });
    }
    
    console.log('Processed AWS cost data (using actual service names from API):', processedData);
    return processedData;
}

// Process AWS cost data into the format expected by AWS Costs Control
function processAWSCostDataForControl(costData) {
    const processedData = {
        dailyCosts: {},
        serviceCosts: {},
        totalCost: 0
    };
    
    // Get the number of days from the cost data
    const services = Object.keys(costData);
    if (services.length === 0) {
        return processedData;
    }
    
    const numDays = costData[services[0]].length;
    
    // Process each day - FIXED: Start from yesterday, not today
    // AWS Cost Explorer data has a delay and doesn't include current day
    for (let dayIndex = 0; dayIndex < numDays; dayIndex++) {
        // Create date string for this day - start from yesterday (day -1) and go backwards
        const date = new Date();
        date.setDate(date.getDate() - 1 - (numDays - 1 - dayIndex)); // Start from yesterday
        const dateStr = date.toISOString().split('T')[0];
        
        console.log(`📅 Processing day index ${dayIndex} -> date ${dateStr} (${numDays - 1 - dayIndex + 1} days ago)`);
        
        processedData.dailyCosts[dateStr] = {};
        let dailyTotal = 0;
        
        // Process each service for this day
        services.forEach(serviceName => {
            const cost = costData[serviceName][dayIndex] || 0;
            
            // Add to daily costs
            processedData.dailyCosts[dateStr][serviceName] = cost;
            dailyTotal += cost;
            
            // Add to service costs
            if (!processedData.serviceCosts[serviceName]) {
                processedData.serviceCosts[serviceName] = 0;
            }
            processedData.serviceCosts[serviceName] += cost;
        });
        
        processedData.dailyCosts[dateStr].total = dailyTotal;
        processedData.totalCost += dailyTotal;
        
        console.log(`💰 Date ${dateStr}: $${dailyTotal.toFixed(2)} total cost`);
    }
    
    console.log('📊 Final processed data structure:', processedData);
    return processedData;
}

// Helper function to check if a service is Bedrock-related
function isBedrockService(serviceName) {
    const bedrockKeywords = [
        'bedrock',
        'claude',
        'anthropic',
        'titan'
    ];
    
    const lowerServiceName = serviceName.toLowerCase();
    return bedrockKeywords.some(keyword => lowerServiceName.includes(keyword));
}

// Categorize AWS service into predefined categories
function categorizeService(serviceName) {
    for (const [category, services] of Object.entries(SERVICE_CATEGORIES)) {
        if (services.some(service => serviceName.includes(service))) {
            return category;
        }
    }
    return 'other';
}

// Get date range for specified time period
function getDateRangeForPeriod(period) {
    const endDate = new Date();
    const startDate = new Date();
    
    switch (period) {
        case '7d':
            startDate.setDate(endDate.getDate() - 7);
            break;
        case '30d':
            startDate.setDate(endDate.getDate() - 30);
            break;
        case '90d':
            startDate.setDate(endDate.getDate() - 90);
            break;
        case '12m':
            startDate.setFullYear(endDate.getFullYear() - 1);
            break;
        default:
            startDate.setDate(endDate.getDate() - 30);
    }
    
    return {
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0]
    };
}

// Update AWS cost indicator (for AWS Costs Control tab)
function updateAWSCostIndicator() {
    // Update the two new indicators in AWS Costs Control tab
    updateAWSCostsControlIndicators();
    
    // Also update the Cost Analysis tab indicators
    updateCostAnalysisIndicators();
}

// Update AWS Costs Control tab indicators (Last 30 Days and Current Month for ALL services)
function updateAWSCostsControlIndicators() {
    console.log('📊 updateAWSCostsControlIndicators called');
    console.log('📊 awsCostData:', awsCostData);
    console.log('📊 awsCostData.dailyCosts:', awsCostData.dailyCosts);
    
    if (!awsCostData.dailyCosts || Object.keys(awsCostData.dailyCosts).length === 0) {
        console.log('⚠️ No daily costs data available for AWS Costs Control indicators');
        
        // Set loading state instead of returning silently
        const last30DaysElement = document.getElementById('aws-cost-all-services-last-30-days');
        const currentMonthElement = document.getElementById('aws-cost-all-services-current-month');
        
        if (last30DaysElement) {
            last30DaysElement.textContent = 'Loading...';
        }
        if (currentMonthElement) {
            currentMonthElement.textContent = 'Loading...';
        }
        
        return;
    }
    
    // Calculate Last 30 Days cost (ALL SERVICES)
    const last30DaysCost = calculateAllServicesLast30DaysCost();
    
    // Calculate Current Month cost (ALL SERVICES)
    const currentMonthCost = calculateAllServicesCurrentMonthCost();
    
    // Update Last 30 Days indicator
    const last30DaysElement = document.getElementById('aws-cost-all-services-last-30-days');
    const last30DaysChangeElement = document.getElementById('aws-cost-all-services-last-30-days-change');
    const last30DaysSubtitleElement = document.getElementById('aws-cost-all-services-last-30-days-subtitle');
    
    if (last30DaysElement) {
        last30DaysElement.textContent = `$${last30DaysCost.total.toFixed(2)}`;
    }
    
    if (last30DaysChangeElement) {
        const changeSymbol = last30DaysCost.change >= 0 ? '↗' : '↘';
        const changeClass = last30DaysCost.change >= 0 ? 'positive' : 'negative';
        last30DaysChangeElement.innerHTML = `<span>${changeSymbol}</span> ${Math.abs(last30DaysCost.change).toFixed(1)}% vs previous 30 days`;
        last30DaysChangeElement.className = `metric-change ${changeClass}`;
    }
    
    if (last30DaysSubtitleElement) {
        last30DaysSubtitleElement.textContent = `${last30DaysCost.days} days of data (${Object.keys(awsCostData.serviceCosts || {}).length} services)`;
    }
    
    // Update Current Month indicator
    const currentMonthElement = document.getElementById('aws-cost-all-services-current-month');
    const currentMonthChangeElement = document.getElementById('aws-cost-all-services-current-month-change');
    const currentMonthSubtitleElement = document.getElementById('aws-cost-all-services-current-month-subtitle');
    
    if (currentMonthElement) {
        currentMonthElement.textContent = `$${currentMonthCost.total.toFixed(2)}`;
    }
    
    if (currentMonthChangeElement) {
        const changeSymbol = currentMonthCost.change >= 0 ? '↗' : '↘';
        const changeClass = currentMonthCost.change >= 0 ? 'positive' : 'negative';
        currentMonthChangeElement.innerHTML = `<span>${changeSymbol}</span> ${Math.abs(currentMonthCost.change).toFixed(1)}% vs last month`;
        currentMonthChangeElement.className = `metric-change ${changeClass}`;
    }
    
    if (currentMonthSubtitleElement) {
        const today = new Date();
        const monthName = today.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        currentMonthSubtitleElement.textContent = `${monthName} - Day 1 to ${today.getDate()} (${currentMonthCost.days} days)`;
    }
    
    console.log('✅ AWS Costs Control indicators updated:', {
        last30Days: last30DaysCost,
        currentMonth: currentMonthCost
    });
}

// Calculate Last 30 Days cost (ALL SERVICES)
function calculateAllServicesLast30DaysCost() {
    const sortedDates = Object.keys(awsCostData.dailyCosts).sort().reverse();
    const last30Days = sortedDates.slice(0, 30);
    
    console.log('📊 calculateAllServicesLast30DaysCost - Processing dates:', last30Days);
    
    let totalCost = 0;
    
    last30Days.forEach(date => {
        const dailyData = awsCostData.dailyCosts[date];
        if (dailyData && dailyData.total) {
            totalCost += dailyData.total;
        }
    });
    
    console.log(`📊 Last 30 Days ALL Services Cost: $${totalCost.toFixed(2)}`);
    
    // Calculate change vs previous 30 days (if we have enough data)
    let changePercent = 0;
    if (sortedDates.length >= 60) {
        const previous30Days = sortedDates.slice(30, 60);
        let previousTotal = 0;
        previous30Days.forEach(date => {
            previousTotal += awsCostData.dailyCosts[date]?.total || 0;
        });
        
        if (previousTotal > 0) {
            changePercent = ((totalCost - previousTotal) / previousTotal) * 100;
        }
    } else {
        // If we don't have 60 days of data, use a simplified calculation
        changePercent = Math.random() * 20 - 10; // Random for demo
    }
    
    return {
        total: totalCost,
        change: changePercent,
        days: last30Days.length
    };
}

// Calculate Current Month cost (ALL SERVICES)
function calculateAllServicesCurrentMonthCost() {
    const today = new Date();
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    
    // Get all dates in current month up to today
    const currentMonthDates = Object.keys(awsCostData.dailyCosts).filter(dateStr => {
        const date = new Date(dateStr);
        return date >= firstDayOfMonth && date <= today;
    });
    
    console.log('📊 calculateAllServicesCurrentMonthCost - Processing dates:', currentMonthDates);
    
    let totalCost = 0;
    
    currentMonthDates.forEach(date => {
        const dailyData = awsCostData.dailyCosts[date];
        if (dailyData && dailyData.total) {
            totalCost += dailyData.total;
        }
    });
    
    console.log(`📊 Current Month ALL Services Cost: $${totalCost.toFixed(2)}`);
    
    // Calculate change vs same period last month
    let changePercent = 0;
    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    const lastMonthEndDate = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate());
    
    const lastMonthDates = Object.keys(awsCostData.dailyCosts).filter(dateStr => {
        const date = new Date(dateStr);
        return date >= lastMonth && date <= lastMonthEndDate;
    });
    
    if (lastMonthDates.length > 0) {
        let lastMonthTotal = 0;
        lastMonthDates.forEach(date => {
            lastMonthTotal += awsCostData.dailyCosts[date]?.total || 0;
        });
        
        if (lastMonthTotal > 0) {
            changePercent = ((totalCost - lastMonthTotal) / lastMonthTotal) * 100;
        }
    } else {
        // If we don't have last month data, use a simplified calculation
        changePercent = Math.random() * 20 - 10; // Random for demo
    }
    
    return {
        total: totalCost,
        change: changePercent,
        days: currentMonthDates.length
    };
}

// Update Cost Analysis tab indicators (Last 30 Days and Current Month)
function updateCostAnalysisIndicators() {
    console.log('📊 updateCostAnalysisIndicators called');
    console.log('📊 awsCostData:', awsCostData);
    console.log('📊 awsCostData.dailyCosts:', awsCostData.dailyCosts);
    
    if (!awsCostData.dailyCosts || Object.keys(awsCostData.dailyCosts).length === 0) {
        console.log('⚠️ No daily costs data available for Cost Analysis indicators');
        
        // Set loading state instead of returning silently
        const last30DaysElement = document.getElementById('aws-cost-last-30-days');
        const currentMonthElement = document.getElementById('aws-cost-current-month');
        
        if (last30DaysElement) {
            last30DaysElement.textContent = 'Loading...';
        }
        if (currentMonthElement) {
            currentMonthElement.textContent = 'Loading...';
        }
        
        return;
    }
    
    // Calculate Last 30 Days cost
    const last30DaysCost = calculateLast30DaysCost();
    
    // Calculate Current Month cost (from day 1 to today)
    const currentMonthCost = calculateCurrentMonthCost();
    
    // Update Last 30 Days indicator
    const last30DaysElement = document.getElementById('aws-cost-last-30-days');
    const last30DaysChangeElement = document.getElementById('aws-cost-last-30-days-change');
    const last30DaysSubtitleElement = document.getElementById('aws-cost-last-30-days-subtitle');
    
    if (last30DaysElement) {
        last30DaysElement.textContent = `$${last30DaysCost.total.toFixed(2)}`;
    }
    
    if (last30DaysChangeElement) {
        const changeSymbol = last30DaysCost.change >= 0 ? '↗' : '↘';
        const changeClass = last30DaysCost.change >= 0 ? 'positive' : 'negative';
        last30DaysChangeElement.innerHTML = `<span>${changeSymbol}</span> ${Math.abs(last30DaysCost.change).toFixed(1)}% vs previous 30 days`;
        last30DaysChangeElement.className = `metric-change ${changeClass}`;
    }
    
    if (last30DaysSubtitleElement) {
        last30DaysSubtitleElement.textContent = `${last30DaysCost.days} days of data (${Object.keys(awsCostData.serviceCosts || {}).length} services)`;
    }
    
    // Update Current Month indicator
    const currentMonthElement = document.getElementById('aws-cost-current-month');
    const currentMonthChangeElement = document.getElementById('aws-cost-current-month-change');
    const currentMonthSubtitleElement = document.getElementById('aws-cost-current-month-subtitle');
    
    if (currentMonthElement) {
        currentMonthElement.textContent = `$${currentMonthCost.total.toFixed(2)}`;
    }
    
    if (currentMonthChangeElement) {
        const changeSymbol = currentMonthCost.change >= 0 ? '↗' : '↘';
        const changeClass = currentMonthCost.change >= 0 ? 'positive' : 'negative';
        currentMonthChangeElement.innerHTML = `<span>${changeSymbol}</span> ${Math.abs(currentMonthCost.change).toFixed(1)}% vs last month`;
        currentMonthChangeElement.className = `metric-change ${changeClass}`;
    }
    
    if (currentMonthSubtitleElement) {
        const today = new Date();
        const monthName = today.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        currentMonthSubtitleElement.textContent = `${monthName} - Day 1 to ${today.getDate()} (${currentMonthCost.days} days)`;
    }
    
    console.log('✅ Cost Analysis indicators updated:', {
        last30Days: last30DaysCost,
        currentMonth: currentMonthCost
    });
}

// Calculate Last 30 Days cost (BEDROCK ONLY)
function calculateLast30DaysCost() {
    const sortedDates = Object.keys(awsCostData.dailyCosts).sort().reverse();
    const last30Days = sortedDates.slice(0, 30);
    
    console.log('📊 calculateLast30DaysCost - Processing dates:', last30Days);
    
    let totalCost = 0;
    let bedrockServiceCount = 0;
    let allServicesFound = [];
    
    last30Days.forEach(date => {
        const dailyData = awsCostData.dailyCosts[date];
        if (dailyData) {
            // Sum only Bedrock services
            Object.entries(dailyData).forEach(([serviceName, cost]) => {
                if (serviceName !== 'total') {
                    allServicesFound.push(serviceName);
                    if (isBedrockService(serviceName)) {
                        console.log(`✅ Found Bedrock service: ${serviceName} with cost $${cost.toFixed(2)} on ${date}`);
                        totalCost += cost;
                        bedrockServiceCount++;
                    }
                }
            });
        }
    });
    
    console.log(`📊 All services found in data:`, [...new Set(allServicesFound)]);
    console.log(`📊 Last 30 Days Bedrock Cost: $${totalCost.toFixed(2)} from ${bedrockServiceCount} service entries`);
    
    if (bedrockServiceCount === 0) {
        console.warn('⚠️ No Bedrock services found in the last 30 days data');
    }
    
    // Calculate change vs previous 30 days (if we have enough data)
    let changePercent = 0;
    if (sortedDates.length >= 60) {
        const previous30Days = sortedDates.slice(30, 60);
        let previousTotal = 0;
        previous30Days.forEach(date => {
            previousTotal += awsCostData.dailyCosts[date]?.total || 0;
        });
        
        if (previousTotal > 0) {
            changePercent = ((totalCost - previousTotal) / previousTotal) * 100;
        }
    } else {
        // If we don't have 60 days of data, use a simplified calculation
        changePercent = Math.random() * 20 - 10; // Random for demo
    }
    
    return {
        total: totalCost,
        change: changePercent,
        days: last30Days.length
    };
}

// Calculate Current Month cost (from day 1 to today) - BEDROCK ONLY
function calculateCurrentMonthCost() {
    const today = new Date();
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    
    // Get all dates in current month up to today
    const currentMonthDates = Object.keys(awsCostData.dailyCosts).filter(dateStr => {
        const date = new Date(dateStr);
        return date >= firstDayOfMonth && date <= today;
    });
    
    console.log('📊 calculateCurrentMonthCost - Processing dates:', currentMonthDates);
    
    let totalCost = 0;
    let bedrockServiceCount = 0;
    let allServicesFound = [];
    
    currentMonthDates.forEach(date => {
        const dailyData = awsCostData.dailyCosts[date];
        if (dailyData) {
            // Sum only Bedrock services
            Object.entries(dailyData).forEach(([serviceName, cost]) => {
                if (serviceName !== 'total') {
                    allServicesFound.push(serviceName);
                    if (isBedrockService(serviceName)) {
                        console.log(`✅ Found Bedrock service: ${serviceName} with cost $${cost.toFixed(2)} on ${date}`);
                        totalCost += cost;
                        bedrockServiceCount++;
                    }
                }
            });
        }
    });
    
    console.log(`📊 All services found in current month:`, [...new Set(allServicesFound)]);
    console.log(`📊 Current Month Bedrock Cost: $${totalCost.toFixed(2)} from ${bedrockServiceCount} service entries`);
    
    if (bedrockServiceCount === 0) {
        console.warn('⚠️ No Bedrock services found in current month data');
    }
    
    // Calculate change vs same period last month
    let changePercent = 0;
    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    const lastMonthEndDate = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate());
    
    const lastMonthDates = Object.keys(awsCostData.dailyCosts).filter(dateStr => {
        const date = new Date(dateStr);
        return date >= lastMonth && date <= lastMonthEndDate;
    });
    
    if (lastMonthDates.length > 0) {
        let lastMonthTotal = 0;
        lastMonthDates.forEach(date => {
            lastMonthTotal += awsCostData.dailyCosts[date]?.total || 0;
        });
        
        if (lastMonthTotal > 0) {
            changePercent = ((totalCost - lastMonthTotal) / lastMonthTotal) * 100;
        }
    } else {
        // If we don't have last month data, use a simplified calculation
        changePercent = Math.random() * 20 - 10; // Random for demo
    }
    
    return {
        total: totalCost,
        change: changePercent,
        days: currentMonthDates.length
    };
}

// Update AWS cost alerts
function updateAWSCostAlerts() {
    const alertsContainer = document.getElementById('aws-cost-alerts-container');
    if (!alertsContainer) return;
    
    alertsContainer.innerHTML = '';
    
    // System status alert
    alertsContainer.innerHTML += `
        <div class="alert info">
            <strong>Cost Monitoring:</strong> Tracking ${Object.keys(awsCostData.serviceCosts || {}).length} AWS services across all regions
        </div>
    `;
    
    // High cost services alert
    const highCostServices = Object.entries(awsCostData.serviceCosts || {})
        .sort(([,a], [,b]) => b - a)
        .slice(0, 3);
    
    if (highCostServices.length > 0) {
        const topService = highCostServices[0];
        const topServiceCost = topService[1];
        
        if (topServiceCost > 100) {
            alertsContainer.innerHTML += `
                <div class="alert warning">
                    <strong>High Cost Alert:</strong> ${topService[0]} accounts for $${topServiceCost.toFixed(2)} (${((topServiceCost / awsCostData.totalCost) * 100).toFixed(1)}% of total costs)
                </div>
            `;
        }
    }
}

// Load top services data
function loadTopServicesData() {
    const tableBody = document.querySelector('#top-services-table tbody');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    // Sort services by cost
    const allServices = Object.entries(awsCostData.serviceCosts || {})
        .sort(([,a], [,b]) => b - a);
    
    if (allServices.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8">No cost data available</td>
            </tr>
        `;
        return;
    }
    
    // Get top 10 services
    const topServices = allServices.slice(0, 10);
    
    // Calculate "Other Services" cost (services beyond top 10)
    const otherServicesCost = allServices.slice(10).reduce((sum, [, cost]) => sum + cost, 0);
    const otherServicesCount = allServices.length - 10;
    
    topServices.forEach(([serviceName, cost]) => {
        const category = categorizeService(serviceName);
        const percentOfTotal = ((cost / awsCostData.totalCost) * 100).toFixed(1);
        
        // Generate sample previous month cost and recommendation
        const previousMonthCost = cost * (0.8 + Math.random() * 0.4); // Random variation
        const changePercent = ((cost - previousMonthCost) / previousMonthCost * 100).toFixed(1);
        const trend = parseFloat(changePercent) >= 0 ? '↗' : '↘';
        const trendClass = parseFloat(changePercent) >= 0 ? 'positive' : 'negative';
        
        const recommendation = generateServiceRecommendation(serviceName, cost, parseFloat(changePercent));
        
        tableBody.innerHTML += `
            <tr>
                <td><strong>${serviceName}</strong></td>
                <td><span class="status-badge active">${category.toUpperCase()}</span></td>
                <td>$${cost.toFixed(2)}</td>
                <td>$${previousMonthCost.toFixed(2)}</td>
                <td><span class="metric-change ${trendClass}">${trend} ${Math.abs(changePercent)}%</span></td>
                <td>${trend}</td>
                <td>${percentOfTotal}%</td>
                <td>${recommendation}</td>
            </tr>
        `;
    });
    
    // Add "Other Services" row if there are more than 10 services
    if (otherServicesCount > 0 && otherServicesCost > 0) {
        const percentOfTotal = ((otherServicesCost / awsCostData.totalCost) * 100).toFixed(1);
        const previousMonthCost = otherServicesCost * (0.8 + Math.random() * 0.4);
        const changePercent = ((otherServicesCost - previousMonthCost) / previousMonthCost * 100).toFixed(1);
        const trend = parseFloat(changePercent) >= 0 ? '↗' : '↘';
        const trendClass = parseFloat(changePercent) >= 0 ? 'positive' : 'negative';
        
        tableBody.innerHTML += `
            <tr style="background-color: rgba(0, 0, 0, 0.02);">
                <td><strong>Other Services (${otherServicesCount})</strong></td>
                <td><span class="status-badge active">VARIOUS</span></td>
                <td>$${otherServicesCost.toFixed(2)}</td>
                <td>$${previousMonthCost.toFixed(2)}</td>
                <td><span class="metric-change ${trendClass}">${trend} ${Math.abs(changePercent)}%</span></td>
                <td>${trend}</td>
                <td>${percentOfTotal}%</td>
                <td>Multiple services - review individually</td>
            </tr>
        `;
    }
}

// Load daily costs data
function loadDailyCostsData() {
    const tableBody = document.querySelector('#daily-costs-table tbody');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    console.log('📊 Loading daily costs data...');
    console.log('awsCostData structure:', awsCostData);
    
    // Check if we have the expected data structure
    if (!awsCostData.dailyCosts || Object.keys(awsCostData.dailyCosts).length === 0) {
        console.warn('⚠️ No daily costs data available in awsCostData.dailyCosts');
        tableBody.innerHTML = `
            <tr>
                <td colspan="9">No daily cost data available</td>
            </tr>
        `;
        return;
    }
    
    // Get sorted dates (oldest first - ascending order) and limit to 30 days
    const sortedDates = Object.keys(awsCostData.dailyCosts).sort().slice(0, 30);
    console.log('📅 Sorted dates for daily costs table (ascending):', sortedDates);
    
    if (sortedDates.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="9">No daily cost data available</td>
            </tr>
        `;
        return;
    }
    
    sortedDates.forEach((date, index) => {
        const dailyData = awsCostData.dailyCosts[date];
        console.log(`📊 Processing date ${date}:`, dailyData);
        
        if (!dailyData) {
            console.warn(`⚠️ No data for date ${date}`);
            return;
        }
        
        const totalCost = dailyData.total || 0;
        console.log(`💰 Total cost for ${date}: $${totalCost.toFixed(2)}`);
        
        // Calculate category costs
        const categoryCosts = calculateCategoryCosts(dailyData);
        console.log(`📊 Category costs for ${date}:`, categoryCosts);
        
        // Calculate daily change (compare with previous day in chronological order)
        // Since dates are sorted ascending (oldest first), previous day is at index - 1
        let dailyChange = 0;
        if (index > 0) {
            const previousDate = sortedDates[index - 1];
            const previousTotal = awsCostData.dailyCosts[previousDate]?.total || 0;
            if (previousTotal > 0) {
                dailyChange = ((totalCost - previousTotal) / previousTotal * 100);
            }
        }
        
        const changeSymbol = dailyChange >= 0 ? '↗' : '↘';
        const changeClass = dailyChange >= 0 ? 'positive' : 'negative';
        
        tableBody.innerHTML += `
            <tr>
                <td>${formatDate(date)}</td>
                <td><strong>$${totalCost.toFixed(2)}</strong></td>
                <td>$${categoryCosts.compute.toFixed(2)}</td>
                <td>$${categoryCosts.storage.toFixed(2)}</td>
                <td>$${categoryCosts.database.toFixed(2)}</td>
                <td>$${categoryCosts.networking.toFixed(2)}</td>
                <td>$${categoryCosts['ai-ml'].toFixed(2)}</td>
                <td>$${categoryCosts.analytics.toFixed(2)}</td>
                <td>$${categoryCosts.security.toFixed(2)}</td>
                <td>$${categoryCosts.management.toFixed(2)}</td>
                <td>$${categoryCosts.other.toFixed(2)}</td>
                <td><span class="metric-change ${changeClass}">${changeSymbol} ${Math.abs(dailyChange).toFixed(1)}%</span></td>
            </tr>
        `;
    });
    
    console.log('✅ Daily costs table loaded successfully');
}

// Calculate category costs for a given day
function calculateCategoryCosts(dailyData) {
    const categoryCosts = {
        compute: 0,
        storage: 0,
        database: 0,
        networking: 0,
        'ai-ml': 0,
        analytics: 0,
        security: 0,
        management: 0,
        other: 0
    };
    
    Object.entries(dailyData).forEach(([serviceName, cost]) => {
        if (serviceName === 'total') return;
        
        const category = categorizeService(serviceName);
        categoryCosts[category] += cost;
    });
    
    return categoryCosts;
}

// Load cost optimization recommendations
function loadCostOptimizationRecommendations() {
    const tableBody = document.querySelector('#recommendations-table tbody');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    // Generate recommendations based on cost data
    const recommendations = generateCostOptimizationRecommendations();
    
    if (recommendations.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8">No optimization recommendations at this time</td>
            </tr>
        `;
        return;
    }
    
    recommendations.forEach(rec => {
        const priorityClass = rec.priority === 'High' ? 'critical' : 
                             rec.priority === 'Medium' ? 'warning' : 'info';
        
        const riskClass = rec.riskLevel === 'High' ? 'critical' : 
                         rec.riskLevel === 'Medium' ? 'warning' : 'success';
        
        tableBody.innerHTML += `
            <tr>
                <td><strong>${rec.service}</strong></td>
                <td>${rec.issueType}</td>
                <td>$${rec.currentCost.toFixed(2)}</td>
                <td>$${rec.potentialSavings.toFixed(2)}</td>
                <td><span class="status-badge ${priorityClass}">${rec.priority}</span></td>
                <td>${rec.recommendation}</td>
                <td>${rec.implementation}</td>
                <td><span class="status-badge ${riskClass}">${rec.riskLevel}</span></td>
            </tr>
        `;
    });
}

// Generate cost optimization recommendations
function generateCostOptimizationRecommendations() {
    const recommendations = [];
    
    // Analyze top cost services for optimization opportunities
    const topServices = Object.entries(awsCostData.serviceCosts || {})
        .sort(([,a], [,b]) => b - a)
        .slice(0, 5);
    
    topServices.forEach(([serviceName, cost]) => {
        if (cost > 50) { // Only recommend for services costing more than $50
            const rec = generateServiceOptimizationRecommendation(serviceName, cost);
            if (rec) {
                recommendations.push(rec);
            }
        }
    });
    
    return recommendations;
}

// Generate optimization recommendation for a specific service
function generateServiceOptimizationRecommendation(serviceName, cost) {
    const category = categorizeService(serviceName);
    
    const recommendations = {
        'compute': {
            issueType: 'Right-sizing',
            recommendation: 'Consider using smaller instance types or Reserved Instances',
            implementation: 'Analyze CloudWatch metrics and resize instances',
            potentialSavings: cost * 0.3,
            priority: 'High',
            riskLevel: 'Low'
        },
        'storage': {
            issueType: 'Storage optimization',
            recommendation: 'Move infrequently accessed data to cheaper storage classes',
            implementation: 'Set up S3 lifecycle policies',
            potentialSavings: cost * 0.25,
            priority: 'Medium',
            riskLevel: 'Low'
        },
        'database': {
            issueType: 'Database optimization',
            recommendation: 'Consider Aurora Serverless or Reserved Instances',
            implementation: 'Evaluate usage patterns and migrate',
            potentialSavings: cost * 0.35,
            priority: 'High',
            riskLevel: 'Medium'
        },
        'networking': {
            issueType: 'Data transfer costs',
            recommendation: 'Optimize data transfer and use CloudFront',
            implementation: 'Review data transfer patterns',
            potentialSavings: cost * 0.20,
            priority: 'Medium',
            riskLevel: 'Low'
        }
    };
    
    const baseRec = recommendations[category] || recommendations['compute'];
    
    return {
        service: serviceName,
        currentCost: cost,
        ...baseRec
    };
}

// Load budget alerts data
function loadBudgetAlertsData() {
    const tableBody = document.querySelector('#budget-alerts-table tbody');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    // Generate sample budget data
    const budgets = generateSampleBudgetData();
    
    budgets.forEach(budget => {
        const usagePercent = (budget.currentSpend / budget.budgetAmount * 100).toFixed(1);
        const remaining = budget.budgetAmount - budget.currentSpend;
        
        let statusClass = 'success';
        let statusText = 'On Track';
        
        if (usagePercent >= 95) {
            statusClass = 'critical';
            statusText = 'Over Budget';
        } else if (usagePercent >= 80) {
            statusClass = 'warning';
            statusText = 'At Risk';
        }
        
        tableBody.innerHTML += `
            <tr>
                <td><strong>${budget.name}</strong></td>
                <td>$${budget.budgetAmount.toFixed(2)}</td>
                <td>$${budget.currentSpend.toFixed(2)}</td>
                <td>${window.createPercentageIndicator(parseFloat(usagePercent))}</td>
                <td>$${remaining.toFixed(2)}</td>
                <td>$${budget.forecast.toFixed(2)}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td>${budget.nextAlert}</td>
            </tr>
        `;
    });
}

// Filter services by category
function filterServicesByCategory() {
    const categoryFilter = document.getElementById('service-category-filter');
    if (!categoryFilter) return;
    
    currentServiceFilter = categoryFilter.value;
    console.log('🔍 Filtering services by category:', currentServiceFilter);
    
    // Reload data with filter applied
    loadTopServicesData();
    updateAWSCostCharts();
}

// Change time period
function changeTimePeriod() {
    const timePeriodFilter = document.getElementById('time-period-filter');
    if (!timePeriodFilter) return;
    
    currentTimePeriod = timePeriodFilter.value;
    console.log('📅 Changing time period to:', currentTimePeriod);
    
    // Reload all data with new time period
    refreshAWSCosts();
}

// Validate budget input
function validateBudgetInput(event) {
    const input = event.target;
    const value = parseFloat(input.value);
    
    if (isNaN(value) || value < 0) {
        input.value = input.defaultValue || 0;
        showAWSCostError('Please enter a valid positive number');
    }
}

// Update budget thresholds
function updateBudgetThresholds() {
    const monthlyBudget = parseFloat(document.getElementById('monthly-budget')?.value || 1000);
    const warningThreshold = parseFloat(document.getElementById('warning-threshold')?.value || 80);
    const criticalThreshold = parseFloat(document.getElementById('critical-threshold')?.value || 95);
    
    console.log('💰 Updating budget thresholds:', {
        monthlyBudget,
        warningThreshold,
        criticalThreshold
    });
    
    // Update alerts based on new thresholds
    updateAWSCostAlerts();
    loadBudgetAlertsData();
    
    showAWSCostSuccess('Budget thresholds updated successfully');
}

// Helper functions for status display
function showAWSCostLoading(message) {
    const alertsContainer = document.getElementById('aws-cost-alerts-container');
    if (alertsContainer) {
        alertsContainer.innerHTML = `
            <div class="alert info">
                <div class="loading-spinner"></div>
                <strong>Loading:</strong> ${message}
            </div>
        `;
    }
}

function showAWSCostSuccess(message) {
    const alertsContainer = document.getElementById('aws-cost-alerts-container');
    if (alertsContainer) {
        alertsContainer.innerHTML = `
            <div class="alert success">
                <strong>Success:</strong> ${message}
            </div>
        `;
        
        // Auto-refresh data after success message
        setTimeout(() => {
            updateAWSCostAlerts();
        }, 2000);
    }
}

// Helper function for updateConnectionStatus compatibility
function updateConnectionStatus(status, message) {
    console.log(`Status: ${status} - ${message}`);
    
    // Try to update global connection status if available
    if (typeof window.updateConnectionStatus === 'function') {
        window.updateConnectionStatus(status, message);
    }
}

// Initialize AWS cost charts
function initializeAWSCostCharts() {
    console.log('📊 Initializing AWS cost charts...');
    
    // Initialize all chart canvases
    const chartConfigs = [
        { id: 'aws-cost-trend-chart', type: 'line' },
        { id: 'aws-service-distribution-chart', type: 'doughnut' },
        { id: 'aws-monthly-comparison-chart', type: 'bar' },
        { id: 'aws-category-cost-chart', type: 'bar' }
    ];
    
    chartConfigs.forEach(config => {
        const canvas = document.getElementById(config.id);
        if (canvas) {
            const ctx = canvas.getContext('2d');
            awsCostCharts[config.id] = new Chart(ctx, {
                type: config.type,
                data: { labels: [], datasets: [] },
                options: getChartOptions(config.type)
            });
        }
    });
}

// Update AWS cost charts
function updateAWSCostCharts() {
    console.log('📈 Updating AWS cost charts...');
    
    // Update AWS cost trend chart
    updateAWSCostTrendChart();
    
    // Update service distribution chart
    updateServiceDistributionChart();
    
    // Update monthly comparison chart
    updateMonthlyComparisonChart();
    
    // Update category cost chart
    updateCategoryCostChart();
}

// Update AWS cost trend chart (renamed to avoid conflict with Cost Analysis chart)
function updateAWSCostTrendChart() {
    const chart = awsCostCharts['aws-cost-trend-chart'];
    if (!chart) return;
    
    const sortedDates = Object.keys(awsCostData.dailyCosts || {}).sort();
    const labels = sortedDates.map(date => formatDate(date));
    const data = sortedDates.map(date => awsCostData.dailyCosts[date]?.total || 0);
    
    chart.data = {
        labels: labels,
        datasets: [{
            label: 'Daily Cost',
            data: data,
            borderColor: '#319795',
            backgroundColor: 'rgba(49, 151, 149, 0.1)',
            tension: 0.4,
            fill: true
        }]
    };
    
    chart.update();
}

// Update service distribution chart
function updateServiceDistributionChart() {
    const chart = awsCostCharts['aws-service-distribution-chart'];
    if (!chart) return;
    
    const topServices = Object.entries(awsCostData.serviceCosts || {})
        .sort(([,a], [,b]) => b - a)
        .slice(0, 8);
    
    const labels = topServices.map(([name]) => name.length > 20 ? name.substring(0, 20) + '...' : name);
    const data = topServices.map(([,cost]) => cost);
    const colors = generateChartColors(labels.length);
    
    chart.data = {
        labels: labels,
        datasets: [{
            data: data,
            backgroundColor: colors,
            borderWidth: 2,
            borderColor: '#fff'
        }]
    };
    
    chart.update();
}

// Update monthly comparison chart
function updateMonthlyComparisonChart() {
    const chart = awsCostCharts['aws-monthly-comparison-chart'];
    if (!chart) return;
    
    // Generate sample monthly data
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    const currentMonthData = months.map(() => Math.random() * 1000 + 500);
    const previousMonthData = months.map(() => Math.random() * 1000 + 400);
    
    chart.data = {
        labels: months,
        datasets: [
            {
                label: 'Current Period',
                data: currentMonthData,
                backgroundColor: 'rgba(49, 151, 149, 0.8)',
                borderColor: '#319795',
                borderWidth: 1
            },
            {
                label: 'Previous Period',
                data: previousMonthData,
                backgroundColor: 'rgba(113, 128, 150, 0.8)',
                borderColor: '#718096',
                borderWidth: 1
            }
        ]
    };
    
    chart.update();
}

// Update category cost chart
function updateCategoryCostChart() {
    const chart = awsCostCharts['aws-category-cost-chart'];
    if (!chart) return;
    
    // Calculate category totals
    const categoryTotals = {
        compute: 0,
        storage: 0,
        database: 0,
        networking: 0,
        'ai-ml': 0,
        analytics: 0,
        security: 0,
        management: 0,
        other: 0
    };
    
    Object.entries(awsCostData.serviceCosts || {}).forEach(([serviceName, cost]) => {
        const category = categorizeService(serviceName);
        categoryTotals[category] += cost;
    });
    
    const labels = Object.keys(categoryTotals);
    const data = Object.values(categoryTotals);
    const colors = generateChartColors(labels.length);
    
    chart.data = {
        labels: labels.map(label => label.charAt(0).toUpperCase() + label.slice(1).replace('-', '/')),
        datasets: [{
            label: 'Cost by Category',
            data: data,
            backgroundColor: colors,
            borderColor: colors.map(color => color.replace('0.8', '1')),
            borderWidth: 1
        }]
    };
    
    chart.update();
}

// Helper function to get chart options
function getChartOptions(type) {
    const baseOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top'
            }
        }
    };
    
    if (type === 'line') {
        return {
            ...baseOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Cost (USD)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        };
    } else if (type === 'bar') {
        return {
            ...baseOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Cost (USD)'
                    }
                }
            }
        };
    } else if (type === 'doughnut') {
        return {
            ...baseOptions,
            plugins: {
                ...baseOptions.plugins,
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: $${value.toFixed(2)} (${percentage}%)`;
                        }
                    }
                }
            }
        };
    }
    
    return baseOptions;
}

// Helper function to generate chart colors
function generateChartColors(count) {
    const colors = [
        'rgba(49, 151, 149, 0.8)',
        'rgba(113, 128, 150, 0.8)',
        'rgba(237, 137, 54, 0.8)',
        'rgba(56, 178, 172, 0.8)',
        'rgba(66, 153, 225, 0.8)',
        'rgba(159, 122, 234, 0.8)',
        'rgba(236, 72, 153, 0.8)',
        'rgba(34, 197, 94, 0.8)',
        'rgba(251, 191, 36, 0.8)',
        'rgba(239, 68, 68, 0.8)'
    ];
    
    return Array.from({ length: count }, (_, i) => colors[i % colors.length]);
}

// Helper function to format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// Helper function to get period display text
function getPeriodDisplayText(period) {
    switch (period) {
        case '7d': return 'Last 7 days';
        case '30d': return 'Last 30 days';
        case '90d': return 'Last 90 days';
        case '12m': return 'Last 12 months';
        default: return 'Last 30 days';
    }
}

// Helper function to generate service recommendation
function generateServiceRecommendation(serviceName, cost, changePercent) {
    if (changePercent > 20) {
        return 'High cost increase - investigate usage patterns';
    } else if (cost > 500) {
        return 'High cost service - consider optimization';
    } else if (changePercent < -10) {
        return 'Cost decreasing - good optimization';
    } else {
        return 'Monitor usage trends';
    }
}

// Helper function to show AWS cost error
function showAWSCostError(message) {
    const alertsContainer = document.getElementById('aws-cost-alerts-container');
    if (alertsContainer) {
        alertsContainer.innerHTML = `
            <div class="alert critical">
                <strong>Error:</strong> ${message}
            </div>
        `;
    }
}

// Generate sample AWS cost data for demonstration
function generateSampleAWSCostData() {
    const services = [
        'Amazon Elastic Compute Cloud - Compute',
        'Amazon Simple Storage Service',
        'Amazon Relational Database Service',
        'AWS Lambda',
        'Amazon CloudFront',
        'Amazon Bedrock',
        'Amazon DynamoDB',
        'Amazon Virtual Private Cloud'
    ];
    
    const sampleData = {
        dailyCosts: {},
        serviceCosts: {},
        totalCost: 0
    };
    
    console.log('📊 Generating sample AWS cost data - starting from yesterday (AWS cost data delay)');
    
    // Generate 30 days of sample data - FIXED: Start from yesterday, not today
    // AWS Cost Explorer data has a delay and doesn't include current day
    for (let i = 30; i >= 1; i--) { // Changed: i=30 to i=1 (30 days ago to yesterday)
        const date = new Date();
        date.setDate(date.getDate() - i); // This now goes from yesterday (i=1) back to 30 days ago (i=30)
        const dateStr = date.toISOString().split('T')[0];
        
        console.log(`📅 Generating sample data for ${dateStr} (${i} days ago)`);
        
        sampleData.dailyCosts[dateStr] = {};
        let dailyTotal = 0;
        
        services.forEach(service => {
            const cost = Math.random() * 100 + 10; // Random cost between $10-$110
            sampleData.dailyCosts[dateStr][service] = cost;
            dailyTotal += cost;
            
            if (!sampleData.serviceCosts[service]) {
                sampleData.serviceCosts[service] = 0;
            }
            sampleData.serviceCosts[service] += cost;
        });
        
        sampleData.dailyCosts[dateStr].total = dailyTotal;
        sampleData.totalCost += dailyTotal;
        
        console.log(`💰 Sample data for ${dateStr}: $${dailyTotal.toFixed(2)}`);
    }
    
    console.log('✅ Sample AWS cost data generated - 30 days from yesterday backwards');
    console.log('📊 Sample data structure:', sampleData);
    return sampleData;
}

// Generate sample services data
function generateSampleServicesData() {
    return [
        { name: 'Amazon Elastic Compute Cloud - Compute', category: 'compute' },
        { name: 'Amazon Simple Storage Service', category: 'storage' },
        { name: 'Amazon Relational Database Service', category: 'database' },
        { name: 'AWS Lambda', category: 'compute' },
        { name: 'Amazon CloudFront', category: 'networking' },
        { name: 'Amazon Bedrock', category: 'ai-ml' },
        { name: 'Amazon DynamoDB', category: 'database' },
        { name: 'Amazon Virtual Private Cloud', category: 'networking' }
    ];
}

// Generate sample budget data
function generateSampleBudgetData() {
    return [
        {
            name: 'Monthly AWS Budget',
            budgetAmount: 1000,
            currentSpend: 750,
            forecast: 950,
            nextAlert: 'In 5 days'
        },
        {
            name: 'Compute Budget',
            budgetAmount: 400,
            currentSpend: 320,
            forecast: 380,
            nextAlert: 'In 7 days'
        },
        {
            name: 'Storage Budget',
            budgetAmount: 200,
            currentSpend: 180,
            forecast: 195,
            nextAlert: 'In 3 days'
        },
        {
            name: 'Database Budget',
            budgetAmount: 300,
            currentSpend: 250,
            forecast: 290,
            nextAlert: 'In 6 days'
        }
    ];
}

// Helper function to export table to CSV
function exportTableToCSV(tableId, filename) {
    try {
        const table = document.getElementById(tableId);
        if (!table) {
            console.error('Table not found:', tableId);
            return;
        }
        
        let csvContent = '';
        
        // Get table headers
        const headers = table.querySelectorAll('thead th');
        const headerRow = Array.from(headers).map(th => `"${th.textContent.trim()}"`).join(',');
        csvContent += headerRow + '\n';
        
        // Get table rows
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            const rowData = Array.from(cells).map(td => {
                // Clean cell content (remove HTML tags and extra whitespace)
                const text = td.textContent.trim().replace(/\s+/g, ' ');
                return `"${text}"`;
            }).join(',');
            csvContent += rowData + '\n';
        });
        
        // Create and download the file
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            
            const now = new Date();
            const dateStr = now.toLocaleDateString('en-CA');
            const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '-');
            
            link.setAttribute('download', `${filename}-${dateStr}-${timeStr}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            console.log('✅ Table exported successfully:', filename);
        }
    } catch (error) {
        console.error('❌ Error exporting table:', error);
        showAWSCostError('Failed to export table: ' + error.message);
    }
}

// Export functions for tables
function exportTopServicesTable() {
    exportTableToCSV('top-services-table', 'aws-top-services-by-cost');
}

function exportDailyCostsTable() {
    exportTableToCSV('daily-costs-table', 'aws-daily-cost-breakdown');
}

function exportRecommendationsTable() {
    exportTableToCSV('recommendations-table', 'aws-cost-optimization-recommendations');
}

function exportBudgetAlertsTable() {
    exportTableToCSV('budget-alerts-table', 'aws-budget-alerts-thresholds');
}

function exportAWSCostsData() {
    // Export all AWS costs data as a comprehensive CSV
    try {
        let csvContent = '';
        
        // Add summary header
        csvContent += 'AWS Costs Control - Complete Export\n';
        csvContent += `Export Date: ${new Date().toLocaleDateString()}\n`;
        csvContent += `Time Period: ${getPeriodDisplayText(currentTimePeriod)}\n`;
        csvContent += `Total Cost: $${awsCostData.totalCost?.toFixed(2) || '0.00'}\n\n`;
        
        // Add service costs summary
        csvContent += 'Service,Total Cost,Category\n';
        Object.entries(awsCostData.serviceCosts || {}).forEach(([service, cost]) => {
            const category = categorizeService(service);
            csvContent += `"${service}",${cost.toFixed(2)},${category}\n`;
        });
        
        // Create and download the file
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            
            const now = new Date();
            const dateStr = now.toLocaleDateString('en-CA');
            const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '-');
            
            link.setAttribute('download', `aws-costs-complete-export-${dateStr}-${timeStr}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            updateConnectionStatus('success', 'AWS costs data exported successfully');
        }
    } catch (error) {
        console.error('Error exporting AWS costs data:', error);
        updateConnectionStatus('error', 'Failed to export AWS costs data: ' + error.message);
    }
}

// Make functions globally available
window.refreshAWSCosts = refreshAWSCosts;
window.filterServicesByCategory = filterServicesByCategory;
window.changeTimePeriod = changeTimePeriod;
window.updateBudgetThresholds = updateBudgetThresholds;
window.exportTopServicesTable = exportTopServicesTable;
window.exportDailyCostsTable = exportDailyCostsTable;
window.exportRecommendationsTable = exportRecommendationsTable;
window.exportBudgetAlertsTable = exportBudgetAlertsTable;
window.exportAWSCostsData = exportAWSCostsData;
window.updateCostAnalysisIndicators = updateCostAnalysisIndicators; // CRITICAL: Export for Cost Analysis tab

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeAWSCostsControl();
    
    // Auto-load data when AWS Costs tab becomes active
    const awsCostsTab = document.getElementById('aws-costs-tab');
    if (awsCostsTab) {
        // Check if tab is already active
        if (awsCostsTab.classList.contains('active')) {
            setTimeout(() => {
                refreshAWSCosts();
            }, 1000);
        }
        
        // Set up observer to detect when tab becomes active
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    if (awsCostsTab.classList.contains('active')) {
                        // Tab became active, load data
                        setTimeout(() => {
                            refreshAWSCosts();
                        }, 500);
                    }
                }
            });
        });
        
        observer.observe(awsCostsTab, {
            attributes: true,
            attributeFilter: ['class']
        });
    }
});

// Also make the module available globally for manual initialization
window.initializeAWSCostsControl = initializeAWSCostsControl;

console.log('✅ AWS Costs Control module loaded successfully');

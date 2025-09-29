// Centralized AWS Data Service for Bedrock Usage Dashboard
// This service acts as a cache layer and single source of truth for all AWS data

class BedrockDataService {
    constructor() {
        // Data cache
        this.cache = {
            users: {
                data: [],
                lastUpdated: null,
                isLoading: false
            },
            userMetrics: {
                data: {},
                lastUpdated: null,
                isLoading: false
            },
            teamMetrics: {
                data: {},
                lastUpdated: null,
                isLoading: false
            },
            costData: {
                data: {},
                lastUpdated: null,
                isLoading: false
            },
            quotaConfig: {
                data: null,
                lastUpdated: null,
                isLoading: false
            }
        };
        
        // Event listeners for data updates
        this.listeners = {
            users: [],
            userMetrics: [],
            teamMetrics: [],
            costData: [],
            quotaConfig: []
        };
        
        // Cache expiry times (in milliseconds) - TEMPORARILY SET TO 0 FOR DEBUGGING
        this.cacheExpiry = {
            users: 0,        // Force refresh every time
            userMetrics: 0,  // Force refresh every time
            teamMetrics: 0,  // Force refresh every time
            costData: 10 * 60 * 1000,    // 10 minutes
            quotaConfig: 30 * 60 * 1000  // 30 minutes
        };
        
        console.log('🏗️ BedrockDataService initialized');
    }
    
    // Event system for reactive updates
    subscribe(dataType, callback) {
        if (this.listeners[dataType]) {
            this.listeners[dataType].push(callback);
            console.log(`📡 Subscribed to ${dataType} updates`);
        }
    }
    
    unsubscribe(dataType, callback) {
        if (this.listeners[dataType]) {
            const index = this.listeners[dataType].indexOf(callback);
            if (index > -1) {
                this.listeners[dataType].splice(index, 1);
            }
        }
    }
    
    notifyListeners(dataType, data) {
        if (this.listeners[dataType]) {
            this.listeners[dataType].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${dataType} listener:`, error);
                }
            });
        }
    }
    
    // Check if cached data is still valid
    isCacheValid(dataType) {
        const cacheEntry = this.cache[dataType];
        if (!cacheEntry.lastUpdated) return false;
        
        const now = Date.now();
        const expiry = this.cacheExpiry[dataType];
        return (now - cacheEntry.lastUpdated) < expiry;
    }
    
    // Generic method to get data with caching
    async getData(dataType, fetchFunction, forceRefresh = false) {
        const cacheEntry = this.cache[dataType];
        
        // Return cached data if valid and not forcing refresh
        if (!forceRefresh && this.isCacheValid(dataType) && cacheEntry.data) {
            console.log(`📦 Returning cached ${dataType} data`);
            return cacheEntry.data;
        }
        
        // Prevent multiple simultaneous requests
        if (cacheEntry.isLoading) {
            console.log(`⏳ ${dataType} already loading, waiting...`);
            return new Promise((resolve) => {
                const checkLoading = () => {
                    if (!cacheEntry.isLoading) {
                        resolve(cacheEntry.data);
                    } else {
                        setTimeout(checkLoading, 100);
                    }
                };
                checkLoading();
            });
        }
        
        // Fetch fresh data
        cacheEntry.isLoading = true;
        console.log(`🔄 Fetching fresh ${dataType} data...`);
        
        try {
            const data = await fetchFunction();
            cacheEntry.data = data;
            cacheEntry.lastUpdated = Date.now();
            cacheEntry.isLoading = false;
            
            // Notify all subscribers
            this.notifyListeners(dataType, data);
            
            console.log(`✅ ${dataType} data updated and cached`);
            return data;
            
        } catch (error) {
            cacheEntry.isLoading = false;
            console.error(`❌ Error fetching ${dataType} data:`, error);
            throw error;
        }
    }
    
    // Specific data fetching methods
    async getUsers(forceRefresh = false) {
        return this.getData('users', async () => {
            if (!isConnectedToAWS) {
                throw new Error('Not connected to AWS');
            }
            
            const iam = new AWS.IAM();
            const allUsers = [];
            const usersByTeam = {};
            const userTags = {};
            
            // Initialize teams
            ALL_TEAMS.forEach(team => {
                usersByTeam[team] = [];
            });
            
            // Fetch users for each team
            for (const team of ALL_TEAMS) {
                try {
                    const groupResponse = await iam.getGroup({ GroupName: team }).promise();
                    
                    for (const user of groupResponse.Users) {
                        const username = user.UserName;
                        
                        usersByTeam[team].push(username);
                        
                        if (!allUsers.includes(username)) {
                            allUsers.push(username);
                        }
                        
                        // Fetch user tags
                        try {
                            const tagsResponse = await iam.listUserTags({ UserName: username }).promise();
                            const tags = {};
                            
                            tagsResponse.Tags.forEach(tag => {
                                tags[tag.Key] = tag.Value;
                            });
                            
                            userTags[username] = tags;
                        } catch (tagError) {
                            console.error(`Error fetching tags for user ${username}:`, tagError);
                            userTags[username] = {};
                        }
                    }
                } catch (groupError) {
                    console.error(`Error fetching users for team ${team}:`, groupError);
                }
            }
            
            return { allUsers, usersByTeam, userTags };
        }, forceRefresh);
    }
    
    async getUserMetrics(forceRefresh = false) {
        return this.getData('userMetrics', async () => {
            if (!isConnectedToAWS) {
                throw new Error('Not connected to AWS');
            }
            
            const users = await this.getUsers();
            const userMetrics = {};
            
            console.log('🗄️ DynamoDB-centric approach: Fetching user metrics from bedrock_user_daily_usage table');
            
            // Fetch metrics for each user from DynamoDB
            for (const username of users.allUsers) {
                try {
                    const monthlyResult = await this.fetchDynamoDBUserMetrics(username, 'monthly');
                    const dailyResult = await this.fetchDynamoDBUserMetrics(username, 'daily');
                    
                    userMetrics[username] = {
                        monthly: monthlyResult || 0,
                        daily: dailyResult || Array(10).fill(0)
                    };
                    
                    console.log(`📊 DynamoDB: ${username} - Monthly: ${monthlyResult}, Daily: [${dailyResult.slice(0, 3).join(', ')}...]`);
                    
                } catch (error) {
                    console.error(`Error fetching DynamoDB metrics for user ${username}:`, error);
                    userMetrics[username] = {
                        monthly: 0,
                        daily: Array(10).fill(0)
                    };
                }
            }
            
            return userMetrics;
        }, forceRefresh);
    }
    
    async getTeamMetrics(forceRefresh = false) {
        return this.getData('teamMetrics', async () => {
            const users = await this.getUsers();
            const userMetrics = await this.getUserMetrics();
            const teamMetrics = {};
            
            // Calculate team metrics by aggregating user metrics
            for (const team of ALL_TEAMS) {
                const teamUsers = users.usersByTeam[team] || [];
                
                teamMetrics[team] = {
                    monthly: 0,
                    daily: Array(10).fill(0)
                };
                
                for (const username of teamUsers) {
                    if (userMetrics[username]) {
                        teamMetrics[team].monthly += userMetrics[username].monthly;
                        
                        for (let i = 0; i < 10; i++) {
                            teamMetrics[team].daily[i] += userMetrics[username].daily[i] || 0;
                        }
                    }
                }
            }
            
            return teamMetrics;
        }, forceRefresh);
    }
    
    async getCostData(forceRefresh = false) {
        return this.getData('costData', async () => {
            if (!isConnectedToAWS) {
                throw new Error('Not connected to AWS');
            }
            
            console.log('🔍 Fetching REAL cost data from AWS Cost Explorer - NO FALLBACK');
            
            // Try Cost Explorer with user credentials first
            try {
                const userCredentials = new AWS.Credentials({
                    accessKeyId: currentUserAccessKey,
                    secretAccessKey: sessionStorage.getItem('aws_secret_key')
                });
                
                const costExplorer = new AWS.CostExplorer({ 
                    region: 'us-east-1',
                    credentials: userCredentials
                });
                
                console.log('✅ Attempting Cost Explorer with user credentials...');
                return await this.fetchCostExplorerData(costExplorer);
                
            } catch (userCredsError) {
                console.warn('❌ Cost Explorer with user credentials failed:', userCredsError.message);
                console.log('🔄 Trying Cost Explorer with assumed role credentials...');
                
                try {
                    const costExplorer = new AWS.CostExplorer({ region: 'us-east-1' });
                    const result = await this.fetchCostExplorerData(costExplorer);
                    console.log('✅ Successfully fetched real cost data with role credentials');
                    return result;
                } catch (roleCredsError) {
                    console.error('❌ Cost Explorer with role credentials also failed:', roleCredsError.message);
                    console.error('💥 NO FALLBACK - Cost data fetch completely failed');
                    
                    // Return empty cost data structure instead of fallback
                    const emptyCostData = {};
                    BEDROCK_SERVICES.forEach(service => {
                        emptyCostData[service] = Array(10).fill(0);
                    });
                    
                    console.log('📊 Returning empty cost data structure (all zeros)');
                    return emptyCostData;
                }
            }
        }, forceRefresh);
    }
    
    async getQuotaConfig(forceRefresh = false) {
        return this.getData('quotaConfig', async () => {
            try {
                const cacheBuster = new Date().getTime();
                let response;
                
                // Try Lambda function directory first
                try {
                    response = await fetch(`individual_blocking_system/lambda_functions/quota_config.json?v=${cacheBuster}`);
                    if (response.ok) {
                        return await response.json();
                    }
                } catch (lambdaError) {
                    console.log('Lambda directory quota_config.json not accessible, trying root directory...');
                }
                
                // Try root directory as fallback
                try {
                    response = await fetch(`quota_config.json?v=${cacheBuster}`);
                    if (response.ok) {
                        return await response.json();
                    }
                } catch (rootError) {
                    console.log('Root directory quota_config.json not accessible either');
                }
                
                throw new Error('quota_config.json not found');
                
            } catch (error) {
                console.error('Error loading quota configuration, using fallback:', error);
                return DEFAULT_QUOTA_CONFIG;
            }
        }, forceRefresh);
    }
    
    // NEW: DynamoDB query methods for the DynamoDB-centric approach
    async fetchDynamoDBUserMetrics(username, type) {
        if (!isConnectedToAWS) {
            throw new Error('Not connected to AWS');
        }
        
        const dynamodb = new AWS.DynamoDB.DocumentClient();
        
        try {
            if (type === 'monthly') {
                return await this.fetchMonthlyUsageFromDynamoDB(dynamodb, username);
            } else if (type === 'daily') {
                return await this.fetchDailyUsageFromDynamoDB(dynamodb, username);
            }
        } catch (error) {
            console.error(`Error fetching DynamoDB ${type} metrics for ${username}:`, error);
            return type === 'monthly' ? 0 : Array(10).fill(0);
        }
    }
    
    async fetchMonthlyUsageFromDynamoDB(dynamodb, username) {
        // Get current month's data from DynamoDB
        const utcNow = new Date();
        const cetNow = new Date(utcNow.getTime() + (2 * 60 * 60 * 1000)); // UTC+2 (CET)
        
        // CRITICAL FIX: Use tomorrow instead of today to ensure we capture all of today's data
        const firstOfMonth = new Date(cetNow.getFullYear(), cetNow.getMonth(), 1, 0, 0, 0, 0);
        const tomorrow = new Date(cetNow.getFullYear(), cetNow.getMonth(), cetNow.getDate() + 1, 0, 0, 0, 0);
        
        let totalMonthlyUsage = 0;
        let daysProcessed = 0;
        
        console.log(`📅 FIXED Monthly calculation for ${username}:`);
        console.log(`📅 From: ${firstOfMonth.toISOString().split('T')[0]} (${firstOfMonth.toISOString()})`);
        console.log(`📅 To: ${tomorrow.toISOString().split('T')[0]} (${tomorrow.toISOString()})`);
        console.log(`📅 Current CET time: ${cetNow.toISOString()}`);
        
        // FIXED: Use a proper loop with normalized dates - now includes tomorrow to ensure today is captured
        const currentDate = new Date(firstOfMonth);
        while (currentDate <= tomorrow) {
            const dateStr = currentDate.toISOString().split('T')[0]; // YYYY-MM-DD format
            
            try {
                const params = {
                    TableName: 'bedrock_user_daily_usage',
                    Key: {
                        'user_id': username,
                        'date': dateStr
                    }
                };
                
                const result = await dynamodb.get(params).promise();
                
                if (result.Item && result.Item.request_count) {
                    totalMonthlyUsage += result.Item.request_count;
                    console.log(`📅 ${dateStr}: +${result.Item.request_count} requests (running total: ${totalMonthlyUsage})`);
                } else {
                    console.log(`📅 ${dateStr}: 0 requests (no data)`);
                }
                
                daysProcessed++;
            } catch (error) {
                console.error(`Error fetching DynamoDB data for ${username} on ${dateStr}:`, error);
                // Continue with other days
            }
            
            // Move to next day (add exactly 24 hours to avoid DST issues)
            currentDate.setDate(currentDate.getDate() + 1);
        }
        
        console.log(`📊 DynamoDB Monthly: ${username} = ${totalMonthlyUsage} requests (${daysProcessed} days processed including TODAY)`);
        
        // VERIFICATION: Double-check that today was included
        const todayStr = new Date(cetNow.getFullYear(), cetNow.getMonth(), cetNow.getDate()).toISOString().split('T')[0];
        console.log(`🔍 VERIFICATION: Today's date ${todayStr} should be included in the ${daysProcessed} days processed`);
        
        return totalMonthlyUsage;
    }
    
    async fetchDailyUsageFromDynamoDB(dynamodb, username) {
        // Get last 10 days of data from DynamoDB
        const dailyData = Array(10).fill(0);
        
        const utcNow = new Date();
        const cetNow = new Date(utcNow.getTime() + (2 * 60 * 60 * 1000)); // UTC+2 (CET)
        
        // Query each of the last 10 days
        for (let daysAgo = 0; daysAgo < 10; daysAgo++) {
            const targetDate = new Date(cetNow);
            targetDate.setDate(targetDate.getDate() - daysAgo);
            const dateStr = targetDate.toISOString().split('T')[0]; // YYYY-MM-DD format
            
            try {
                const params = {
                    TableName: 'bedrock_user_daily_usage',
                    Key: {
                        'user_id': username,
                        'date': dateStr
                    }
                };
                
                const result = await dynamodb.get(params).promise();
                
                // Calculate array index (today = 8, yesterday = 7, etc.)
                let index;
                if (daysAgo === 0) {
                    index = 8; // Today
                } else if (daysAgo === 1) {
                    index = 7; // Yesterday
                } else {
                    index = 8 - daysAgo;
                }
                
                if (index >= 0 && index < 10 && result.Item && result.Item.request_count) {
                    dailyData[index] = result.Item.request_count;
                }
                
                console.log(`📅 DynamoDB: ${dateStr} (${daysAgo} days ago) -> index ${index}: ${result.Item?.request_count || 0} requests`);
                
            } catch (error) {
                console.error(`Error fetching DynamoDB data for ${username} on ${dateStr}:`, error);
                // Keep the default 0 value for this day
            }
        }
        
        console.log(`📊 DynamoDB Daily: ${username} = [${dailyData.slice(0, 3).join(', ')}...]`);
        return dailyData;
    }

    // Helper methods (moved from dashboard.js)
    async fetchCloudWatchMetrics(metricName, dimension, startTime, endTime, namespace = 'UserMetrics', dimensionName = 'User') {
        if (!isConnectedToAWS) {
            throw new Error('Not connected to AWS');
        }
        
        const cloudwatch = new AWS.CloudWatch();
        
        const params = {
            MetricName: metricName,
            Namespace: namespace,
            Dimensions: [
                {
                    Name: dimensionName,
                    Value: dimension
                }
            ],
            StartTime: startTime,
            EndTime: endTime,
            Period: 3600,
            Statistics: ['Sum']
        };
        
        try {
            const data = await cloudwatch.getMetricStatistics(params).promise();
            
            let total = 0;
            let datapoints = data.Datapoints || [];
            
            if (datapoints.length > 0) {
                // FIXED: Deduplicate metrics before calculating total
                const deduplicatedDatapoints = this.deduplicateMetrics(datapoints);
                
                deduplicatedDatapoints.forEach(datapoint => {
                    total += datapoint.Sum || 0;
                });
                
                console.log(`📊 ${dimension}: Original ${datapoints.length} datapoints -> ${deduplicatedDatapoints.length} deduplicated -> Total: ${total}`);
                datapoints = deduplicatedDatapoints;
            }
            
            return { total, datapoints };
        } catch (error) {
            console.error(`Error fetching metrics for ${dimension}:`, error);
            return { total: 0, datapoints: [] };
        }
    }
    
    async getDailyMetricData(username, startTime, endTime) {
        try {
            // FIXED: Use precise daily queries for each day instead of complex array logic
            const dailyData = Array(10).fill(0);
            
            const utcNow = new Date();
            const cetNow = new Date(utcNow.getTime() + (2 * 60 * 60 * 1000)); // Add 2 hours for CET
            
            console.log(`🕐 DAILY CET TIMEZONE: Fetching daily data for ${username}`);
            
            // Query each day individually to avoid timezone confusion
            for (let daysAgo = 0; daysAgo < 10; daysAgo++) {
                const targetDate = new Date(cetNow);
                targetDate.setDate(targetDate.getDate() - daysAgo);
                
                // Start of target day in CET, converted to UTC
                const startOfDayCET = new Date(targetDate.getFullYear(), targetDate.getMonth(), targetDate.getDate());
                const startOfDayUTC = new Date(startOfDayCET.getTime() - (2 * 60 * 60 * 1000));
                
                // Start of next day in CET, converted to UTC
                const startOfNextDayCET = new Date(targetDate.getFullYear(), targetDate.getMonth(), targetDate.getDate() + 1);
                const startOfNextDayUTC = new Date(startOfNextDayCET.getTime() - (2 * 60 * 60 * 1000));
                
                try {
                    const dayResult = await this.fetchCloudWatchMetrics('BedrockUsage', username, startOfDayUTC, startOfNextDayUTC, 'UserMetrics');
                    
                    // Calculate array index (today = 8, yesterday = 7, etc.)
                    let index;
                    if (daysAgo === 0) {
                        index = 8; // Today
                    } else if (daysAgo === 1) {
                        index = 7; // Yesterday
                    } else {
                        index = 8 - daysAgo;
                    }
                    
                    if (index >= 0 && index < 10) {
                        dailyData[index] = dayResult.total || 0;
                        console.log(`📅 ${startOfDayCET.toISOString().split('T')[0]} (${daysAgo} days ago) -> index ${index}: ${dayResult.total} requests`);
                    }
                } catch (dayError) {
                    console.error(`Error fetching data for ${daysAgo} days ago:`, dayError);
                    // Keep the default 0 value for this day
                }
            }
            
            console.log(`📊 Final daily data for ${username}:`, dailyData);
            console.log(`📊 Today's requests (index 8): ${dailyData[8]}`);
            
            return { dailyData };
        } catch (error) {
            console.error(`Error fetching daily metrics for ${username}:`, error);
            return { dailyData: Array(10).fill(0) };
        }
    }
    
    // NEW: Deduplicate CloudWatch metrics by timestamp, preferring "Count" unit over "None"
    deduplicateMetrics(datapoints) {
        const metricMap = new Map();
        
        datapoints.forEach(datapoint => {
            const timestamp = datapoint.Timestamp;
            const existing = metricMap.get(timestamp);
            
            if (!existing) {
                // First occurrence of this timestamp
                metricMap.set(timestamp, datapoint);
            } else {
                // Duplicate timestamp - prefer "Count" unit over "None"
                if (datapoint.Unit === 'Count' && existing.Unit !== 'Count') {
                    console.log(`🔄 Replacing duplicate metric at ${timestamp}: ${existing.Unit} -> ${datapoint.Unit} (${existing.Sum} -> ${datapoint.Sum})`);
                    metricMap.set(timestamp, datapoint);
                } else if (existing.Unit === 'Count' && datapoint.Unit !== 'Count') {
                    console.log(`⚠️ Ignoring duplicate metric at ${timestamp}: keeping ${existing.Unit} (${existing.Sum}) over ${datapoint.Unit} (${datapoint.Sum})`);
                } else {
                    // Both have same unit or both are "None" - keep the higher value
                    if (datapoint.Sum > existing.Sum) {
                        console.log(`🔄 Replacing duplicate metric at ${timestamp}: keeping higher value ${datapoint.Sum} over ${existing.Sum}`);
                        metricMap.set(timestamp, datapoint);
                    }
                }
            }
        });
        
        const deduplicated = Array.from(metricMap.values());
        console.log(`🧹 Deduplicated ${datapoints.length} datapoints to ${deduplicated.length}`);
        return deduplicated;
    }
    
    async fetchCostExplorerData(costExplorer) {
        // Fetch from yesterday (day-1) back to 10 days ago (day-10)
        // Cost Explorer end date is exclusive, so we need to add 1 day to include yesterday
        const endDate = new Date();
        // endDate stays as today to include yesterday's data (Cost Explorer end date is exclusive)
        
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 10); // 10 days ago (8th Sep)
        
        const startDateStr = startDate.toISOString().split('T')[0];
        const endDateStr = endDate.toISOString().split('T')[0];
        
        console.log(`📅 Fetching cost data from ${startDateStr} to ${endDateStr} (8 Sep to 17 Sep inclusive)`);
        console.log(`📅 End date is exclusive in Cost Explorer, so using today's date to include yesterday's data`);
        console.log(`📅 This should give us 10 days of data including yesterday (17 Sep)`);
        
        // Step 1: Get all services with costs to discover Bedrock services dynamically
        console.log('🔍 Step 1: Discovering all Bedrock services dynamically...');
        const discoveryParams = {
            TimePeriod: {
                Start: startDateStr,
                End: endDateStr
            },
            Granularity: 'DAILY',
            Metrics: ['BlendedCost'],
            GroupBy: [
                {
                    Type: 'DIMENSION',
                    Key: 'SERVICE'
                }
            ]
        };
        
        const discoveryData = await costExplorer.getCostAndUsage(discoveryParams).promise();
        
        // Find all services that contain "Bedrock" in their name
        const bedrockServices = new Set();
        if (discoveryData.ResultsByTime && discoveryData.ResultsByTime.length > 0) {
            discoveryData.ResultsByTime.forEach(timeResult => {
                if (timeResult.Groups && timeResult.Groups.length > 0) {
                    timeResult.Groups.forEach(group => {
                        const serviceName = group.Keys[0];
                        const cost = parseFloat(group.Metrics.BlendedCost.Amount) || 0;
                        
                        // Check if service name contains "Bedrock" (case insensitive)
                        if (serviceName.toLowerCase().includes('bedrock') && cost > 0) {
                            bedrockServices.add(serviceName);
                        }
                    });
                }
            });
        }
        
        console.log(`✅ Discovered ${bedrockServices.size} Bedrock services:`, Array.from(bedrockServices));
        
        if (bedrockServices.size === 0) {
            console.log('⚠️ No Bedrock services found with costs in the specified date range');
            // Return empty structure
            const emptyData = {};
            BEDROCK_SERVICES.forEach(service => {
                emptyData[service] = Array(10).fill(0);
            });
            return emptyData;
        }
        
        // Step 2: Fetch detailed cost data for discovered Bedrock services
        console.log('📊 Step 2: Fetching detailed cost data for discovered Bedrock services...');
        const detailedParams = {
            TimePeriod: {
                Start: startDateStr,
                End: endDateStr
            },
            Granularity: 'DAILY',
            Metrics: ['BlendedCost', 'UnblendedCost', 'UsageQuantity'],
            GroupBy: [
                {
                    Type: 'DIMENSION',
                    Key: 'SERVICE'
                },
                {
                    Type: 'DIMENSION',
                    Key: 'REGION'
                }
            ],
            Filter: {
                Or: Array.from(bedrockServices).map(serviceName => ({
                    Dimensions: {
                        Key: 'SERVICE',
                        Values: [serviceName],
                        MatchOptions: ['EQUALS']
                    }
                }))
            }
        };
        
        const costData = await costExplorer.getCostAndUsage(detailedParams).promise();
        return this.processCostExplorerData(costData, bedrockServices);
    }
    
    processCostExplorerData(costData, discoveredServices) {
        const processedData = {};
        
        // Initialize with discovered services instead of hardcoded BEDROCK_SERVICES
        if (discoveredServices && discoveredServices.size > 0) {
            // Use actual discovered service names
            discoveredServices.forEach(serviceName => {
                processedData[serviceName] = Array(10).fill(0);
            });
        } else {
            // Fallback to hardcoded services if no discovery data
            BEDROCK_SERVICES.forEach(service => {
                processedData[service] = Array(10).fill(0);
            });
        }
        
        if (costData.ResultsByTime && costData.ResultsByTime.length > 0) {
            console.log(`📊 Processing ${costData.ResultsByTime.length} days of cost data from Cost Explorer`);
            
            costData.ResultsByTime.forEach((timeResult, dayIndex) => {
                const dateStr = timeResult.TimePeriod.Start;
                console.log(`📅 Processing cost data for date: ${dateStr} (dayIndex: ${dayIndex})`);
                
                if (timeResult.Groups && timeResult.Groups.length > 0) {
                    timeResult.Groups.forEach(group => {
                        const serviceName = group.Keys[0];
                        const regionName = group.Keys[1];
                        const cost = parseFloat(group.Metrics.BlendedCost.Amount) || 0;
                        
                        console.log(`💰 ${dateStr}: ${serviceName} (${regionName}) = $${cost}`);
                        
                        // Use the actual service name from AWS (no more hardcoded mapping)
                        // This ensures we capture all Bedrock services dynamically
                        if (processedData[serviceName] !== undefined) {
                            processedData[serviceName][dayIndex] += cost;
                            console.log(`✅ Mapped to column ${dayIndex} for service ${serviceName}: $${cost}`);
                        } else {
                            console.log(`⚠️ Service ${serviceName} not found in processed data structure`);
                        }
                    });
                }
            });
            
            console.log('📊 Final processed cost data:', processedData);
        }
        
        return processedData;
    }
    
    generateFallbackCostData() {
        const processedData = {};
        const now = new Date();
        
        BEDROCK_SERVICES.forEach(service => {
            processedData[service] = [];
            
            for (let i = 9; i >= 0; i--) {
                const date = new Date(now);
                date.setDate(date.getDate() - i);
                
                let baseCost = 0;
                switch (service) {
                    case 'Amazon Bedrock':
                        baseCost = Math.random() * 5 + 2;
                        break;
                    case 'Claude 3.7 Sonnet (Bedrock Edition)':
                        baseCost = Math.random() * 25 + 15;
                        break;
                    case 'Claude 3 Sonnet (Bedrock Edition)':
                        baseCost = Math.random() * 15 + 8;
                        break;
                    case 'Claude 3 Haiku (Bedrock Edition)':
                        baseCost = Math.random() * 8 + 3;
                        break;
                    case 'Claude 3 Opus (Bedrock Edition)':
                        baseCost = Math.random() * 35 + 20;
                        break;
                    case 'Amazon Titan Text (Bedrock Edition)':
                        baseCost = Math.random() * 6 + 2;
                        break;
                }
                
                const dayOfWeek = date.getDay();
                if (dayOfWeek === 0 || dayOfWeek === 6) {
                    baseCost *= 0.6;
                }
                
                baseCost *= (0.8 + Math.random() * 0.4);
                processedData[service].push(parseFloat(baseCost.toFixed(2)));
            }
        });
        
        return processedData;
    }
    
    // Utility methods
    async refreshAllData() {
        console.log('🔄 Refreshing all cached data...');
        
        try {
            await Promise.all([
                this.getUsers(true),
                this.getUserMetrics(true),
                this.getTeamMetrics(true),
                this.getCostData(true),
                this.getQuotaConfig(true)
            ]);
            
            console.log('✅ All data refreshed successfully');
            return true;
        } catch (error) {
            console.error('❌ Error refreshing data:', error);
            throw error;
        }
    }
    
    clearCache() {
        Object.keys(this.cache).forEach(key => {
            this.cache[key] = {
                data: key === 'users' ? [] : (key === 'quotaConfig' ? null : {}),
                lastUpdated: null,
                isLoading: false
            };
        });
        console.log('🗑️ Cache cleared');
    }
    
    getCacheStatus() {
        const status = {};
        Object.keys(this.cache).forEach(key => {
            const cacheEntry = this.cache[key];
            status[key] = {
                hasData: !!cacheEntry.data && (Array.isArray(cacheEntry.data) ? cacheEntry.data.length > 0 : Object.keys(cacheEntry.data).length > 0),
                lastUpdated: cacheEntry.lastUpdated,
                isValid: this.isCacheValid(key),
                isLoading: cacheEntry.isLoading
            };
        });
        return status;
    }
}

// Create global instance - REDIRECT TO MYSQL SERVICE
// window.dataService = new BedrockDataService(); // OLD DynamoDB service

// Wait for MySQL service to be available, then redirect
if (window.mysqlDataService) {
    window.dataService = window.mysqlDataService;
    console.log('🏗️ Data Service REDIRECTED to MySQL - Real-time individual request logging');
    console.log('🔧 Dashboard now uses MySQL instead of DynamoDB');
} else {
    // Wait for MySQL service to load
    const checkMySQLService = () => {
        if (window.mysqlDataService) {
            window.dataService = window.mysqlDataService;
            console.log('🏗️ Data Service REDIRECTED to MySQL - Real-time individual request logging');
            console.log('🔧 Dashboard now uses MySQL instead of DynamoDB');
        } else {
            setTimeout(checkMySQLService, 100);
        }
    };
    checkMySQLService();
}

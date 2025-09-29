// MySQL-based Data Service for Bedrock Usage Dashboard
// This service connects to the new RDS MySQL database for real-time individual request logging

class BedrockMySQLDataService {
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
            userMetricsCost: {
                data: {},
                lastUpdated: null,
                isLoading: false
            },
            teamMetricsCost: {
                data: {},
                lastUpdated: null,
                isLoading: false
            },
            hourlyMetrics: {
                data: {},
                lastUpdated: null,
                isLoading: false
            },
            realtimeUsage: {
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
            userMetricsCost: [],
            teamMetricsCost: [],
            hourlyMetrics: [],
            realtimeUsage: [],
            quotaConfig: []
        };
        
        // Cache expiry times (in milliseconds)
        this.cacheExpiry = {
            users: 5 * 60 * 1000,        // 5 minutes
            userMetrics: 2 * 60 * 1000,  // 2 minutes
            teamMetrics: 2 * 60 * 1000,  // 2 minutes
            userMetricsCost: 2 * 60 * 1000,  // 2 minutes
            teamMetricsCost: 2 * 60 * 1000,  // 2 minutes
            hourlyMetrics: 1 * 60 * 1000, // 1 minute
            realtimeUsage: 30 * 1000,    // 30 seconds
            quotaConfig: 30 * 60 * 1000  // 30 minutes
        };
        
        // MySQL connection configuration
        this.dbConfig = {
            host: 'bedrock-usage-mysql.czuimyk2qu10.eu-west-1.rds.amazonaws.com',
            port: 3306,
            database: 'bedrock_usage_control',
            // Connection will be established via Lambda function calls
        };
        
        console.log('🏗️ BedrockMySQLDataService initialized with RDS MySQL backend');
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
        console.log(`🔄 Fetching fresh ${dataType} data from MySQL...`);
        
        try {
            const data = await fetchFunction();
            cacheEntry.data = data;
            cacheEntry.lastUpdated = Date.now();
            cacheEntry.isLoading = false;
            
            // Notify all subscribers
            this.notifyListeners(dataType, data);
            
            console.log(`✅ ${dataType} data updated and cached from MySQL`);
            return data;
            
        } catch (error) {
            cacheEntry.isLoading = false;
            console.error(`❌ Error fetching ${dataType} data from MySQL:`, error);
            throw error;
        }
    }
    
    // MySQL query execution via Lambda function
    async executeQuery(query, params = []) {
        try {
            const lambda = new AWS.Lambda({ region: 'eu-west-1' });
            
            const payload = {
                action: 'query',
                query: query,
                params: params
            };
            
            const lambdaParams = {
                FunctionName: 'bedrock-mysql-query-executor',
                Payload: JSON.stringify(payload)
            };
            
            console.log(`🔍 Executing MySQL query via Lambda:`, query.substring(0, 100) + '...');
            console.log(`📝 Query parameters being sent:`, params);
            console.log(`📦 Full payload being sent to Lambda:`, payload);
            
            const result = await lambda.invoke(lambdaParams).promise();
            const response = JSON.parse(result.Payload);
            
            console.log(`📥 Lambda response:`, response);
            
            if (response.errorMessage) {
                throw new Error(response.errorMessage);
            }
            
            return response.data || [];
            
        } catch (error) {
            console.error('❌ Error executing MySQL query:', error);
            throw error;
        }
    }
    
    // Helper function to get current CET timezone offset
    getCETOffset() {
        const now = new Date();
        const cetOffset = now.getTimezoneOffset() === -60 ? '+01:00' : '+02:00'; // CET/CEST
        console.log(`🕐 Current CET offset: ${cetOffset}`);
        return cetOffset;
    }
    
    // Helper function to convert UTC timestamp to CET for display
    convertUTCtoCET(utcTimestamp) {
        if (!utcTimestamp) return null;
        
        const utcDate = new Date(utcTimestamp + 'Z'); // Ensure UTC interpretation
        const cetOffset = this.getCETOffset();
        
        // Convert to CET
        const offsetHours = cetOffset === '+01:00' ? 1 : 2;
        const cetDate = new Date(utcDate.getTime() + (offsetHours * 60 * 60 * 1000));
        
        return cetDate;
    }
    
    // Specific data fetching methods for MySQL
    async getUsers(forceRefresh = false) {
        return this.getData('users', async () => {
            if (!isConnectedToAWS) {
                throw new Error('Not connected to AWS');
            }
            
            console.log('🗄️ Fetching users from RDS MySQL database - DYNAMIC team discovery from database');
            
            // STEP 1: Get all teams dynamically from database
            const teamsQuery = `
                SELECT DISTINCT team 
                FROM bedrock_usage.user_limits 
                WHERE team IS NOT NULL AND team != '' 
                ORDER BY team
            `;
            
            const teamsResult = await this.executeQuery(teamsQuery);
            const dynamicTeams = teamsResult.map(row => row.team);
            
            console.log('🎯 DYNAMIC TEAMS discovered from database:', dynamicTeams);
            console.log('📊 Total teams found:', dynamicTeams.length);
            
            // STEP 2: Get users from user_limits table for correct person and team information
            const usersQuery = `
                SELECT DISTINCT 
                    ul.user_id,
                    ul.team,
                    ul.person,
                    COUNT(br.id) as total_requests,
                    MAX(br.request_timestamp) as last_request
                FROM bedrock_usage.user_limits ul
                LEFT JOIN bedrock_usage.bedrock_requests br ON ul.user_id = br.user_id
                GROUP BY ul.user_id, ul.team, ul.person
                ORDER BY last_request DESC
            `;
            
            try {
                const usersResult = await this.executeQuery(usersQuery);
                
                const allUsers = [];
                const usersByTeam = {};
                const userTags = {}; // We'll keep this empty since tags aren't in MySQL
                
                // Initialize teams DYNAMICALLY from database
                dynamicTeams.forEach(team => {
                    usersByTeam[team] = [];
                });
                
                // Process users from MySQL - now using users table data
                const userPersonMap = {}; // Store person info for each user
                usersResult.forEach(row => {
                    const username = row.user_id;
                    const team = row.team || 'Unknown';
                    const person = row.person || 'Unknown';
                    
                    console.log(`👤 FIXED: User ${username} -> Person: ${person}, Team: ${team} (from user_limits table)`);
                    
                    // Store person info for this user
                    userPersonMap[username] = person;
                    
                    if (!allUsers.includes(username)) {
                        allUsers.push(username);
                    }
                    
                    // Add to team if team exists in dynamicTeams
                    if (dynamicTeams.includes(team)) {
                        if (!usersByTeam[team].includes(username)) {
                            usersByTeam[team].push(username);
                        }
                    } else {
                        // Add to Unknown team or create it if needed
                        if (!usersByTeam['Unknown']) {
                            usersByTeam['Unknown'] = [];
                        }
                        if (!usersByTeam['Unknown'].includes(username)) {
                            usersByTeam['Unknown'].push(username);
                        }
                    }
                    
                    // Store person and team info in userTags for compatibility
                    userTags[username] = {
                        Person: person,
                        team: team
                    };
                });
                
                console.log(`📊 DYNAMIC: Found ${allUsers.length} users in MySQL database using user_limits table`);
                console.log(`👥 Users by team:`, Object.keys(usersByTeam).map(team => `${team}: ${usersByTeam[team].length}`).join(', '));
                console.log(`🎯 DYNAMIC TEAMS: Successfully discovered ${dynamicTeams.length} teams from database`);
                
                return { allUsers, usersByTeam, userTags, userPersonMap, dynamicTeams };
                
            } catch (error) {
                console.error('Error fetching users from MySQL:', error);
                // Fallback to empty data structure with dynamic teams
                const usersByTeam = {};
                dynamicTeams.forEach(team => {
                    usersByTeam[team] = [];
                });
                return { allUsers: [], usersByTeam, userTags: {}, dynamicTeams };
            }
        }, forceRefresh);
    }
    
    async getUserMetrics(forceRefresh = false) {
        return this.getData('userMetrics', async () => {
            if (!isConnectedToAWS) {
                throw new Error('Not connected to AWS');
            }
            
            const users = await this.getUsers();
            const userMetrics = {};
            
            console.log('🗄️ MySQL-centric approach: Fetching user metrics from bedrock_requests table (HOY hasta HOY-10)');
            
            // Get current CET timezone offset
            const cetOffset = this.getCETOffset();
            
            // Get current month and daily data from MySQL (timestamps now stored in CET)
            // NOTE: Removed input_tokens, output_tokens, cost_usd as they don't exist in current schema
            // FIXED: Use CET date instead of MySQL CURDATE() for monthly calculations
            const monthlyQuery = `
                SELECT 
                    user_id,
                    COUNT(*) as monthly_requests
                FROM bedrock_usage.bedrock_requests 
                WHERE user_id = ? 
                AND YEAR(request_timestamp) = YEAR(?)
                AND MONTH(request_timestamp) = MONTH(?)
                GROUP BY user_id
            `;
            
            // DASHBOARD TABS: User/Team/Consumption Details - Desde HOY hasta HOY-10 (11 días incluyendo hoy)
            // Use browser's current date/time directly - use LOCAL date, not UTC
            const browserNow = new Date();
            const todayStr = browserNow.toLocaleDateString('en-CA'); // Returns YYYY-MM-DD in local timezone
            const startDate = new Date(browserNow);
            startDate.setDate(startDate.getDate() - 10);
            const startDateStr = startDate.toLocaleDateString('en-CA'); // Returns YYYY-MM-DD in local timezone
            
            const dailyQuery = `
                SELECT 
                    DATE(request_timestamp) as request_date,
                    COUNT(*) as daily_requests
                FROM bedrock_usage.bedrock_requests 
                WHERE user_id = ? 
                AND DATE(request_timestamp) >= ?
                AND DATE(request_timestamp) <= ?
                GROUP BY DATE(request_timestamp)
                ORDER BY request_date ASC
            `;
            
            // Fetch metrics for each user from MySQL
            for (const username of users.allUsers) {
                try {
                    console.log(`🔍 Fetching metrics for user: ${username}`);
                    
                    // Get monthly data with browser date parameters
                    console.log(`📅 Monthly query for ${username}:`, monthlyQuery);
                    console.log(`📅 Monthly query parameters: [${username}, ${todayStr}, ${todayStr}]`);
                    const monthlyResult = await this.executeQuery(monthlyQuery, [username, todayStr, todayStr]);
                    console.log(`📊 Monthly result for ${username}:`, monthlyResult);
                    console.log(`🔍 Monthly result details:`, monthlyResult.length > 0 ? monthlyResult[0] : 'No data');
                    const monthlyRequests = monthlyResult.length > 0 ? parseInt(monthlyResult[0].monthly_requests) || 0 : 0;
                    
                    // Get daily data with browser date parameters
                    console.log(`📅 Daily query for ${username}:`, dailyQuery);
                    console.log(`📅 Query parameters: [${username}, ${startDateStr}, ${todayStr}]`);
                    const dailyResult = await this.executeQuery(dailyQuery, [username, startDateStr, todayStr]);
                    console.log(`📊 Daily result for ${username}:`, dailyResult);
                    console.log(`🔍 Daily result details:`, dailyResult.map(row => ({
                        date: row.request_date,
                        requests: row.daily_requests,
                        type: typeof row.request_date
                    })));
                    
                    // Debug: Show what dates are actually in the MySQL result
                    console.log(`🔍 Available dates in MySQL result:`, dailyResult.map(row => {
                        let dateStr = row.request_date;
                        if (dateStr instanceof Date) {
                            dateStr = dateStr.toLocaleDateString('en-CA');
                        } else if (typeof dateStr === 'string') {
                            dateStr = dateStr.split(' ')[0];
                        }
                        return `${dateStr} (${row.daily_requests} requests)`;
                    }));
                    
                    const dailyData = Array(11).fill(0);
                    
                    // Map daily results to array (last 11 days)
                    // Create a map of dates for easier lookup
                    const dateMap = {};
                    dailyResult.forEach(row => {
                        let rowDateStr = row.request_date;
                        if (rowDateStr instanceof Date) {
                            rowDateStr = rowDateStr.toLocaleDateString('en-CA');
                        } else if (typeof rowDateStr === 'string') {
                            rowDateStr = rowDateStr.split(' ')[0]; // Remove time part if present
                        }
                        dateMap[rowDateStr] = parseInt(row.daily_requests) || 0;
                    });
                    
                    // Fill the daily array with data for the last 11 days (including today)
                    // FIXED: Use MySQL CURDATE() to ensure date synchronization
                    // Array structure: [day-10, day-9, day-8, day-7, day-6, day-5, day-4, day-3, day-2, day-1, today]
                    //                  [   0,     1,     2,     3,     4,     5,     6,     7,     8,     9,    10]
                    
                    // Use browser's current date for calculations
                    const today = new Date(todayStr + 'T00:00:00');
                    
                    console.log(`🕐 Browser Today String: ${todayStr}`);
                    console.log(`🕐 Browser Today Date Object: ${today.toISOString().split('T')[0]}`);
                    console.log(`🕐 Using browser date for calculations`);
                    
                    for (let i = 0; i < 11; i++) {
                        const targetDate = new Date(today);
                        targetDate.setDate(targetDate.getDate() - (10 - i)); // Start from day-10, end at today (day 0)
                        const dateStr = targetDate.toLocaleDateString('en-CA');
                        
                        dailyData[i] = dateMap[dateStr] || 0;
                        console.log(`📅 FIXED Day ${i} (${dateStr}): ${dailyData[i]} requests - ${i === 10 ? 'TODAY' : 'Day -' + (10 - i)}`);
                        console.log(`📅 CRITICAL: Index ${i} should contain data for ${dateStr} - Found: ${dailyData[i]} requests`);
                        
                        // Special debug for the problematic first chart point (11 Sep)
                        if (i === 1) {
                            console.log(`🚨 CRITICAL DEBUG: Index 1 (day-9, 11 Sep) = ${dailyData[i]} requests`);
                            console.log(`🚨 Date string being looked up: ${dateStr}`);
                            console.log(`🚨 Available dates in dateMap:`, Object.keys(dateMap));
                            console.log(`🚨 Full dateMap:`, dateMap);
                        }
                    }
                    
                    // Debug: Show the final daily array
                    console.log(`📊 Final daily array for ${username}:`, dailyData);
                    
                    userMetrics[username] = {
                        monthly: monthlyRequests,
                        daily: dailyData,
                        monthlyTokens: 0, // Not available in current schema
                        monthlyCost: 0    // Not available in current schema
                    };
                    
                    console.log(`📊 MySQL: ${username} - Monthly: ${monthlyRequests} requests, Daily: [${dailyData.slice(0, 3).join(', ')}...]`);
                    
                } catch (error) {
                    console.error(`Error fetching MySQL metrics for user ${username}:`, error);
                    userMetrics[username] = {
                        monthly: 0,
                        daily: Array(11).fill(0),
                        monthlyTokens: 0, // Not available in current schema
                        monthlyCost: 0    // Not available in current schema
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
            
            console.log('🏢 TEAM METRICS: Starting team aggregation from fixed user metrics...');
            
            // Use dynamic teams from database instead of hardcoded ALL_TEAMS
            const dynamicTeams = users.dynamicTeams || [];
            console.log('🎯 DYNAMIC TEAMS for team metrics calculation:', dynamicTeams);
            
            // Calculate team metrics by aggregating user metrics
            for (const team of dynamicTeams) {
                const teamUsers = users.usersByTeam[team] || [];
                console.log(`🏢 Processing team ${team} with users:`, teamUsers);
                
                teamMetrics[team] = {
                    monthly: 0,
                    daily: Array(11).fill(0),
                    monthlyTokens: 0,
                    monthlyCost: 0
                };
                
                for (const username of teamUsers) {
                    if (userMetrics[username]) {
                        console.log(`👤 Adding user ${username} data to team ${team}:`);
                        console.log(`   - User daily data:`, userMetrics[username].daily);
                        
                        teamMetrics[team].monthly += userMetrics[username].monthly;
                        teamMetrics[team].monthlyTokens += userMetrics[username].monthlyTokens || 0;
                        teamMetrics[team].monthlyCost += userMetrics[username].monthlyCost || 0;
                        
                        for (let i = 0; i < 11; i++) {
                            const userValue = userMetrics[username].daily[i] || 0;
                            teamMetrics[team].daily[i] += userValue;
                            
                            // Special debug for index 1 (11 Sep issue)
                            if (i === 1 && userValue > 0) {
                                console.log(`🚨 TEAM AGGREGATION: User ${username} contributing ${userValue} requests to team ${team} for index 1 (11 Sep)`);
                            }
                        }
                        
                        console.log(`   - Team ${team} daily data after adding ${username}:`, teamMetrics[team].daily);
                    } else {
                        console.log(`⚠️ No user metrics found for ${username} in team ${team}`);
                    }
                }
                
                console.log(`📊 FINAL team ${team} daily data:`, teamMetrics[team].daily);
                console.log(`🔍 Team ${team} index 1 (11 Sep) total: ${teamMetrics[team].daily[1]} requests`);
            }
            
            return teamMetrics;
        }, forceRefresh);
    }
    
    // NEW: Get hourly metrics for detailed analytics
    async getHourlyMetrics(forceRefresh = false) {
        return this.getData('hourlyMetrics', async () => {
            if (!isConnectedToAWS) {
                throw new Error('Not connected to AWS');
            }
            
            console.log('🕐 Fetching hourly metrics from MySQL for detailed analytics (UTC to CET conversion)');
            
            // Get current CET timezone offset
            const cetOffset = this.getCETOffset();
            
            const hourlyQuery = `
                SELECT 
                    user_id,
                    team,
                    DATE(CONVERT_TZ(request_timestamp, '+00:00', '${cetOffset}')) as request_date,
                    HOUR(CONVERT_TZ(request_timestamp, '+00:00', '${cetOffset}')) as request_hour,
                    model_id,
                    COUNT(*) as hourly_requests
                FROM bedrock_usage.bedrock_requests 
                WHERE request_timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY user_id, team, DATE(CONVERT_TZ(request_timestamp, '+00:00', '${cetOffset}')), HOUR(CONVERT_TZ(request_timestamp, '+00:00', '${cetOffset}')), model_id
                ORDER BY request_timestamp DESC
            `;
            
            try {
                const hourlyResult = await this.executeQuery(hourlyQuery);
                
                // Organize data by user and hour
                const hourlyMetrics = {};
                
                hourlyResult.forEach(row => {
                    const userId = row.user_id;
                    const hour = `${row.request_date} ${String(row.request_hour).padStart(2, '0')}:00`;
                    
                    if (!hourlyMetrics[userId]) {
                        hourlyMetrics[userId] = {};
                    }
                    
                    if (!hourlyMetrics[userId][hour]) {
                        hourlyMetrics[userId][hour] = {
                            requests: 0,
                            inputTokens: 0,
                            outputTokens: 0,
                            cost: 0,
                            models: {}
                        };
                    }
                    
                    hourlyMetrics[userId][hour].requests += row.hourly_requests;
                    hourlyMetrics[userId][hour].inputTokens += 0; // Not available in current schema
                    hourlyMetrics[userId][hour].outputTokens += 0; // Not available in current schema
                    hourlyMetrics[userId][hour].cost += 0; // Not available in current schema
                    
                    if (!hourlyMetrics[userId][hour].models[row.model_id]) {
                        hourlyMetrics[userId][hour].models[row.model_id] = 0;
                    }
                    hourlyMetrics[userId][hour].models[row.model_id] += row.hourly_requests;
                });
                
                console.log(`📊 Fetched hourly metrics for ${Object.keys(hourlyMetrics).length} users`);
                return hourlyMetrics;
                
            } catch (error) {
                console.error('Error fetching hourly metrics:', error);
                return {};
            }
        }, forceRefresh);
    }
    
    // NEW: Get real-time usage status for blocking decisions
    async getRealtimeUsage(forceRefresh = false) {
        return this.getData('realtimeUsage', async () => {
            if (!isConnectedToAWS) {
                throw new Error('Not connected to AWS');
            }
            
            console.log('⚡ Fetching real-time usage status from MySQL (UTC to CET conversion)');
            
            // Get current CET timezone offset
            const cetOffset = this.getCETOffset();
            
            const realtimeQuery = `
                SELECT 
                    user_id,
                    is_blocked,
                    blocked_reason,
                    blocked_at,
                    blocked_until,
                    last_request_at,
                    last_reset_at,
                    created_at,
                    updated_at
                FROM bedrock_usage.user_blocking_status
                ORDER BY updated_at DESC
            `;
            
            try {
                const realtimeResult = await this.executeQuery(realtimeQuery);
                
                const realtimeUsage = {};
                
                realtimeResult.forEach(row => {
                    realtimeUsage[row.user_id] = {
                        isBlocked: row.is_blocked === 'Y',
                        blockReason: row.blocked_reason,
                        blockedAt: row.blocked_at,
                        blockedUntil: row.blocked_until,
                        lastRequest: row.last_request_at,
                        lastReset: row.last_reset_at,
                        lastUpdated: row.updated_at
                    };
                });
                
                console.log(`⚡ Fetched real-time status for ${Object.keys(realtimeUsage).length} users`);
                return realtimeUsage;
                
            } catch (error) {
                console.error('Error fetching real-time usage:', error);
                return {};
            }
        }, forceRefresh);
    }
    
    async getQuotaConfig(forceRefresh = false) {
        return this.getData('quotaConfig', async () => {
            try {
                // NEW: First try to get limits from database
                console.log('💾 Attempting to fetch user limits from database...');
                const userLimitsFromDB = await this.getUserLimitsFromDatabase();
                
                if (userLimitsFromDB && Object.keys(userLimitsFromDB.users).length > 0) {
                    console.log('✅ Successfully loaded user limits from database');
                    return userLimitsFromDB;
                }
                
                // Fallback to JSON file if database fails
                console.log('⚠️ Database limits not available, falling back to quota_config.json file...');
                
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
    
    // NEW: Get user limits from database
    async getUserLimitsFromDatabase() {
        try {
            if (!isConnectedToAWS) {
                throw new Error('Not connected to AWS');
            }
            
            console.log('💾 Fetching user limits from user_limits table in database...');
            
            const limitsQuery = `
                SELECT 
                    user_id,
                    team,
                    person,
                    daily_request_limit,
                    monthly_request_limit,
                    created_at,
                    updated_at
                FROM bedrock_usage.user_limits
                ORDER BY user_id
            `;
            
            const limitsResult = await this.executeQuery(limitsQuery);
            
            if (!limitsResult || limitsResult.length === 0) {
                console.log('⚠️ No user limits found in database');
                return null;
            }
            
            // Convert database results to quota_config.json format
            const quotaConfig = {
                users: {},
                teams: {
                    "team_darwin_group": {
                        "monthly_limit": 25000,
                        "warning_threshold": 60,
                        "critical_threshold": 85
                    },
                    "team_sap_group": {
                        "monthly_limit": 25000,
                        "warning_threshold": 60,
                        "critical_threshold": 85
                    },
                    "team_mulesoft_group": {
                        "monthly_limit": 25000,
                        "warning_threshold": 60,
                        "critical_threshold": 85
                    },
                    "team_yo_leo_gas_group": {
                        "monthly_limit": 25000,
                        "warning_threshold": 60,
                        "critical_threshold": 85
                    },
                    "team_lcorp_group": {
                        "monthly_limit": 25000,
                        "warning_threshold": 60,
                        "critical_threshold": 85
                    }
                }
            };
            
            // Process each user from database
            limitsResult.forEach(row => {
                quotaConfig.users[row.user_id] = {
                    daily_limit: row.daily_request_limit || 350,
                    monthly_limit: row.monthly_request_limit || 5000,
                    team: row.team || 'unknown',
                    warning_threshold: 60,
                    critical_threshold: 85
                };
            });
            
            console.log(`💾 Successfully loaded ${limitsResult.length} user limits from database`);
            console.log('📊 Sample user limits from database:', Object.keys(quotaConfig.users).slice(0, 3).map(userId => ({
                userId,
                daily_limit: quotaConfig.users[userId].daily_limit,
                monthly_limit: quotaConfig.users[userId].monthly_limit
            })));
            
            return quotaConfig;
            
        } catch (error) {
            console.error('❌ Error fetching user limits from database:', error);
            return null;
        }
    }
    
    // NEW: Get user metrics for Cost Analysis (HOY-1 hasta HOY-11)
    async getUserMetricsForCostAnalysis(forceRefresh = false) {
        return this.getData('userMetricsCost', async () => {
            if (!isConnectedToAWS) {
                throw new Error('Not connected to AWS');
            }
            
            const users = await this.getUsers();
            const userMetrics = {};
            
            console.log('💰 MySQL Cost Analysis: Fetching user metrics from bedrock_requests table (HOY-1 hasta HOY-11)');
            
            // Get current CET timezone offset
            const cetOffset = this.getCETOffset();
            
            // COST ANALYSIS TAB: Desde HOY-1 hasta HOY-11 (11 días excluyendo hoy, desde ayer)
            // Use browser's current date/time directly - use LOCAL date, not UTC
            const browserNow = new Date();
            const todayStr = browserNow.toLocaleDateString('en-CA'); // Returns YYYY-MM-DD in local timezone
            const startDate = new Date(browserNow);
            startDate.setDate(startDate.getDate() - 11);
            const startDateStr = startDate.toLocaleDateString('en-CA'); // Returns YYYY-MM-DD in local timezone
            
            const dailyQueryCost = `
                SELECT 
                    DATE(request_timestamp) as request_date,
                    COUNT(*) as daily_requests
                FROM bedrock_usage.bedrock_requests 
                WHERE user_id = ? 
                AND DATE(request_timestamp) >= ?
                AND DATE(request_timestamp) < ?
                GROUP BY DATE(request_timestamp)
                ORDER BY request_date ASC
            `;
            
            // Fetch metrics for each user from MySQL
            for (const username of users.allUsers) {
                try {
                    console.log(`💰 Fetching COST ANALYSIS metrics for user: ${username}`);
                    
                    // Get daily data for cost analysis (excluding today) with browser date parameters
                    console.log(`📅 Cost Analysis daily query for ${username}:`, dailyQueryCost);
                    console.log(`📅 Cost Analysis query parameters: [${username}, ${startDateStr}, ${todayStr}]`);
                    const dailyResult = await this.executeQuery(dailyQueryCost, [username, startDateStr, todayStr]);
                    console.log(`📊 Cost Analysis daily result for ${username}:`, dailyResult);
                    
                    const dailyData = Array(11).fill(0);
                    
                    // Map daily results to array (last 11 days excluding today)
                    const dateMap = {};
                    dailyResult.forEach(row => {
                        let rowDateStr = row.request_date;
                        if (rowDateStr instanceof Date) {
                            rowDateStr = rowDateStr.toLocaleDateString('en-CA');
                        } else if (typeof rowDateStr === 'string') {
                            rowDateStr = rowDateStr.split(' ')[0];
                        }
                        dateMap[rowDateStr] = parseInt(row.daily_requests) || 0;
                    });
                    
                    // Fill the daily array with data for the last 11 days (excluding today)
                    // Query returns data from HOY-11 to HOY-1 (yesterday)
                    const today = new Date();
                    for (let i = 0; i < 11; i++) {
                        const targetDate = new Date(today);
                        targetDate.setDate(targetDate.getDate() - (11 - i)); // Start from day-11, end at day-1 (yesterday)
                        const dateStr = targetDate.toLocaleDateString('en-CA');
                        
                        dailyData[i] = dateMap[dateStr] || 0;
                        console.log(`💰 Cost Day ${i} (${dateStr}): ${dailyData[i]} requests - Day -${11 - i}`);
                    }
                    
                    userMetrics[username] = {
                        daily: dailyData
                    };
                    
                    console.log(`💰 Cost Analysis MySQL: ${username} - Daily: [${dailyData.slice(0, 3).join(', ')}...]`);
                    
                } catch (error) {
                    console.error(`Error fetching Cost Analysis MySQL metrics for user ${username}:`, error);
                    userMetrics[username] = {
                        daily: Array(11).fill(0)
                    };
                }
            }
            
            return userMetrics;
        }, forceRefresh);
    }
    
    // NEW: Get team metrics for Cost Analysis (HOY-1 hasta HOY-11)
    async getTeamMetricsForCostAnalysis(forceRefresh = false) {
        return this.getData('teamMetricsCost', async () => {
            const users = await this.getUsers();
            const userMetrics = await this.getUserMetricsForCostAnalysis();
            const teamMetrics = {};
            
            console.log('💰 Calculating team metrics for Cost Analysis (HOY-1 hasta HOY-11)');
            
            // Use dynamic teams from database instead of hardcoded ALL_TEAMS
            const dynamicTeams = users.dynamicTeams || [];
            console.log('🎯 DYNAMIC TEAMS for cost analysis team metrics:', dynamicTeams);
            
            // Calculate team metrics by aggregating user metrics
            for (const team of dynamicTeams) {
                const teamUsers = users.usersByTeam[team] || [];
                
                teamMetrics[team] = {
                    daily: Array(11).fill(0)
                };
                
                for (const username of teamUsers) {
                    if (userMetrics[username]) {
                        for (let i = 0; i < 11; i++) {
                            teamMetrics[team].daily[i] += userMetrics[username].daily[i] || 0;
                        }
                    }
                }
            }
            
            return teamMetrics;
        }, forceRefresh);
    }
    
    // NEW: Get model usage breakdown
    async getModelUsageBreakdown(userId = null, timeRange = '24h') {
        console.log(`📊 Fetching model usage breakdown for ${userId || 'all users'} (${timeRange})`);
        
        let timeCondition = '';
        switch (timeRange) {
            case '1h':
                timeCondition = 'request_timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)';
                break;
            case '24h':
                timeCondition = 'request_timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)';
                break;
            case '7d':
                timeCondition = 'request_timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)';
                break;
            case '10d':
                timeCondition = 'request_timestamp >= DATE_SUB(NOW(), INTERVAL 10 DAY)';
                break;
            case '30d':
                timeCondition = 'request_timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)';
                break;
            default:
                timeCondition = 'request_timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)';
        }
        
        const modelQuery = `
            SELECT 
                model_id,
                COUNT(*) as request_count,
                AVG(processing_time_ms) as avg_processing_time
            FROM bedrock_usage.bedrock_requests 
            WHERE ${timeCondition}
            ${userId ? 'AND user_id = ?' : ''}
            GROUP BY model_id
            ORDER BY request_count DESC
        `;
        
        try {
            const params = userId ? [userId] : [];
            const modelResult = await this.executeQuery(modelQuery, params);
            
            console.log(`📊 Model usage breakdown: ${modelResult.length} models found`);
            return modelResult;
            
        } catch (error) {
            console.error('Error fetching model usage breakdown:', error);
            return [];
        }
    }
    
    // Utility methods
    async refreshAllData() {
        console.log('🔄 Refreshing all cached MySQL data...');
        
        try {
            await Promise.all([
                this.getUsers(true),
                this.getUserMetrics(true),
                this.getTeamMetrics(true),
                this.getHourlyMetrics(true),
                this.getRealtimeUsage(true),
                this.getQuotaConfig(true)
            ]);
            
            console.log('✅ All MySQL data refreshed successfully');
            return true;
        } catch (error) {
            console.error('❌ Error refreshing MySQL data:', error);
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
        console.log('🗑️ MySQL cache cleared');
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

// Create global instance
window.mysqlDataService = new BedrockMySQLDataService();

console.log('🏗️ MySQL Data Service loaded and ready - Real-time individual request logging');
console.log('🔧 Connected to RDS MySQL for enhanced analytics and hourly usage tracking');

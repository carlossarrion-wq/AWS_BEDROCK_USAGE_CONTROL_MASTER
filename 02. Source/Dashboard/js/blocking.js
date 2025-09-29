// Blocking Management Functions for AWS Bedrock Usage Dashboard

// Blocking management functions - Real Lambda integration
async function loadBlockingData() {
    if (!isConnectedToAWS) {
        showBlockingError('Not connected to AWS. Please refresh the page and login again.');
        return;
    }
    
    try {
        console.log('Loading blocking management data...');
        showBlockingLoadingIndicators();
        
        // CRITICAL FIX: Load real-time usage data to populate the realtimeUsage cache
        console.log('🔄 Loading real-time usage data for blocking timestamps...');
        await window.mysqlDataService.getRealtimeUsage(true);
        console.log('✅ Real-time usage data loaded and cached');
        
        // Load real blocking data from Lambda functions
        await loadUserBlockingStatus();
        await loadBlockingOperationsHistory();
        
        console.log('Blocking data loaded successfully');
        
    } catch (error) {
        console.error('Error loading blocking data:', error);
        showBlockingError('Failed to load blocking management data: ' + error.message);
    }
}

async function loadUserBlockingStatus() {
    // Populate user select dropdown
    const userSelect = document.getElementById('user-select');
    userSelect.innerHTML = '<option value="">Select User...</option>';
    
    // Use real user data from user_limits table
    const sortedUsers = [...allUsers].sort();
    
    for (const username of sortedUsers) {
            // FIXED: Get person and team from user_limits table instead of userTags
            let personTag = "Unknown";
            let userTeam = "Unknown";
            
            try {
                if (window.mysqlDataService) {
                    const userInfoQuery = `
                        SELECT person, team 
                        FROM bedrock_usage.user_limits 
                        WHERE user_id = ?
                    `;
                    const userInfoResult = await window.mysqlDataService.executeQuery(userInfoQuery, [username]);
                    if (userInfoResult.length > 0) {
                        personTag = userInfoResult[0].person || "Unknown";
                        userTeam = userInfoResult[0].team || "Unknown";
                        console.log(`👤 FIXED: User ${username} -> Person: ${personTag}, Team: ${userTeam} (from user_limits table)`);
                    } else {
                        console.log(`⚠️ No user_limits record found for user ${username}, using fallback`);
                        // Fallback to getUserPersonTag if available
                        personTag = getUserPersonTag(username) || "Unknown";
                        for (const team in usersByTeam) {
                            if (usersByTeam[team].includes(username)) {
                                userTeam = team;
                                break;
                            }
                        }
                    }
                } else {
                    // Fallback to old method if MySQL service not available
                    personTag = getUserPersonTag(username) || "Unknown";
                    for (const team in usersByTeam) {
                        if (usersByTeam[team].includes(username)) {
                            userTeam = team;
                            break;
                        }
                    }
                }
            } catch (error) {
                console.error(`Error fetching user info for ${username}:`, error);
                // Fallback to old method
                personTag = getUserPersonTag(username) || "Unknown";
                for (const team in usersByTeam) {
                    if (usersByTeam[team].includes(username)) {
                        userTeam = team;
                        break;
                    }
                }
            }
        
        // Add to select dropdown
        userSelect.innerHTML += `<option value="${username}">${username} - ${personTag}</option>`;
    }
    
    // Use the pagination function from dashboard.js instead of rendering all users
    if (window.loadUserBlockingDataWithPagination) {
        console.log('📊 FIXED: Using pagination function for user blocking table');
        await window.loadUserBlockingDataWithPagination();
    } else {
        console.error('❌ Pagination function not available, showing error message');
        const statusTableBody = document.querySelector('#user-blocking-status-table tbody');
        statusTableBody.innerHTML = `
            <tr>
                <td colspan="10">Error: Pagination function not available</td>
            </tr>
        `;
    }
}

async function loadBlockingOperationsHistory() {
    try {
        // Get all operations history from MySQL database (first time only)
        if (allOperations.length === 0) {
            if (!window.mysqlDataService) {
                throw new Error('MySQL data service not available');
            }
            
            // Query the blocking_audit_log table
            const query = `
                SELECT 
                    bal.id,
                    bal.user_id,
                    bal.operation_type,
                    bal.operation_reason,
                    bal.performed_by,
                    bal.operation_timestamp,
                    bal.previous_status,
                    bal.new_status,
                    bal.blocked_until,
                    bal.daily_requests_at_operation,
                    bal.daily_limit_at_operation,
                    bal.usage_percentage,
                    bal.iam_policy_updated,
                    bal.email_sent,
                    bal.error_message,
                    ul.person
                FROM bedrock_usage.blocking_audit_log bal
                LEFT JOIN bedrock_usage.user_limits ul ON bal.user_id = ul.user_id
                ORDER BY bal.operation_timestamp DESC
                LIMIT 100
            `;
            
            const operations = await window.mysqlDataService.executeQuery(query);
            
            // Transform database results to match expected format
            allOperations = operations.map(op => ({
                id: op.id,
                user_id: op.user_id,
                operation: op.operation_type,
                reason: op.operation_reason,
                performed_by: op.performed_by || 'System',
                timestamp: op.operation_timestamp,
                status: op.error_message ? 'FAILED' : 'SUCCESS',
                previous_status: op.previous_status,
                new_status: op.new_status,
                blocked_until: op.blocked_until,
                daily_requests: op.daily_requests_at_operation,
                daily_limit: op.daily_limit_at_operation,
                usage_percentage: op.usage_percentage,
                iam_updated: op.iam_policy_updated === 'Y',
                email_sent: op.email_sent === 'Y',
                error_message: op.error_message,
                person: op.person || 'Unknown'
            }));
            
            operationsTotalCount = allOperations.length;
        }
        
        // Display current page
        displayOperationsPage();
        
    } catch (error) {
        console.error('Error loading operations history:', error);
        const operationsTableBody = document.querySelector('#blocking-operations-table tbody');
        operationsTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="error-message">
                    Error loading operations history: ${error.message}
                </td>
            </tr>
        `;
        updateOperationsPaginationInfo();
    }
}

// Display current page of operations
function displayOperationsPage() {
    const operationsTableBody = document.querySelector('#blocking-operations-table tbody');
    operationsTableBody.innerHTML = '';
    
    if (allOperations.length === 0) {
        operationsTableBody.innerHTML = `
            <tr>
                <td colspan="6">No operations history found</td>
            </tr>
        `;
        updateOperationsPaginationInfo();
        return;
    }
    
    // Calculate pagination
    const startIndex = (operationsCurrentPage - 1) * PAGINATION_CONFIG.operationsPageSize;
    const endIndex = Math.min(startIndex + PAGINATION_CONFIG.operationsPageSize, allOperations.length);
    const pageOperations = allOperations.slice(startIndex, endIndex);
    
    // Display operations for current page
    pageOperations.forEach(op => {
        const timestamp = formatDateTime(op.timestamp, true);
        const statusBadge = op.status === 'SUCCESS' ? 
            '<span class="status-badge active">Success</span>' : 
            '<span class="status-badge blocked">Failed</span>';
        
        // Use person field from database or fallback to getUserPersonTag
        const personTag = op.person || getUserPersonTag(op.user_id) || 'Unknown';
        
        operationsTableBody.innerHTML += `
            <tr>
                <td>${timestamp}</td>
                <td>${op.user_id || 'Unknown'}</td>
                <td>${personTag}</td>
                <td>${op.operation || 'Unknown'}</td>
                <td>${op.reason || 'No reason provided'}</td>
                <td>${op.performed_by || 'System'}</td>
            </tr>
        `;
    });
    
    // Update pagination info and buttons
    updateOperationsPaginationInfo();
}

// Update pagination information and button states
function updateOperationsPaginationInfo() {
    const totalPages = Math.ceil(operationsTotalCount / PAGINATION_CONFIG.operationsPageSize);
    const startIndex = (operationsCurrentPage - 1) * PAGINATION_CONFIG.operationsPageSize + 1;
    const endIndex = Math.min(operationsCurrentPage * PAGINATION_CONFIG.operationsPageSize, operationsTotalCount);
    
    // Update info text
    document.getElementById('operations-info').textContent = 
        `Showing ${startIndex}-${endIndex} of ${operationsTotalCount} operations`;
    
    // Update page info
    document.getElementById('operations-page-info').textContent = 
        `Page ${operationsCurrentPage} of ${totalPages}`;
    
    // Update button states
    const prevBtn = document.getElementById('prev-operations-btn');
    const nextBtn = document.getElementById('next-operations-btn');
    
    prevBtn.disabled = operationsCurrentPage <= 1;
    nextBtn.disabled = operationsCurrentPage >= totalPages;
    
    // Update button styles
    if (prevBtn.disabled) {
        prevBtn.style.opacity = '0.5';
        prevBtn.style.cursor = 'not-allowed';
    } else {
        prevBtn.style.opacity = '1';
        prevBtn.style.cursor = 'pointer';
    }
    
    if (nextBtn.disabled) {
        nextBtn.style.opacity = '0.5';
        nextBtn.style.cursor = 'not-allowed';
    } else {
        nextBtn.style.opacity = '1';
        nextBtn.style.cursor = 'pointer';
    }
}

// Load previous page of operations
function loadPreviousOperations() {
    if (operationsCurrentPage > 1) {
        operationsCurrentPage--;
        displayOperationsPage();
    }
}

// Load next page of operations
function loadNextOperations() {
    const totalPages = Math.ceil(operationsTotalCount / PAGINATION_CONFIG.operationsPageSize);
    if (operationsCurrentPage < totalPages) {
        operationsCurrentPage++;
        displayOperationsPage();
    }
}

function showBlockingLoadingIndicators() {
    document.querySelector('#user-blocking-status-table tbody').innerHTML = 
        '<tr><td colspan="10"><div class="loading-spinner"></div>Loading user status...</td></tr>';
    document.querySelector('#blocking-operations-table tbody').innerHTML = 
        '<tr><td colspan="6"><div class="loading-spinner"></div>Loading operations history from database...</td></tr>';
}

function showBlockingError(message) {
    const statusTable = document.querySelector('#user-blocking-status-table tbody');
    const historyTable = document.querySelector('#blocking-operations-table tbody');
    
    statusTable.innerHTML = `<tr><td colspan="10" class="error-message">${message}</td></tr>`;
    historyTable.innerHTML = `<tr><td colspan="6" class="error-message">${message}</td></tr>`;
}

// Real blocking functions using MySQL database directly
async function performManualBlock() {
    const userSelect = document.getElementById('user-select');
    const blockDuration = document.getElementById('block-duration');
    const blockReason = document.getElementById('block-reason');
    
    const username = userSelect.value;
    const duration = blockDuration.value;
    const reason = blockReason.value;
    
    if (!username) {
        updateConnectionStatus('error', 'Please select a user to block');
        return;
    }
    
    if (!reason) {
        updateConnectionStatus('error', 'Please provide a reason for blocking');
        return;
    }
    
    try {
        // Calculate expiration date
        const expiresAt = calculateExpirationDate(duration);
        if (duration === 'custom' && !expiresAt) {
            updateConnectionStatus('error', 'Please select a custom date and time');
            return;
        }
        
        // Use MySQL database to perform blocking
        if (window.mysqlDataService) {
            // Get current usage data for audit log - FIXED: Use same data source as Daily Usage tab
            const fullDailyData = userMetrics[username]?.daily || Array(11).fill(0);
            const dailyUsage = fullDailyData[10] || 0; // Index 10 is today (same as Daily Usage tab)
            
            // FIXED: Get daily limit from database instead of quota_config.json
            let dailyLimit = 350; // Default fallback
            try {
                if (window.mysqlDataService) {
                    const limitsQuery = `
                        SELECT daily_request_limit 
                        FROM bedrock_usage.user_limits 
                        WHERE user_id = ?
                    `;
                    const limitsResult = await window.mysqlDataService.executeQuery(limitsQuery, [username]);
                    if (limitsResult.length > 0) {
                        dailyLimit = limitsResult[0].daily_request_limit || 350;
                    }
                }
                } catch (error) {
                    console.error(`Error fetching daily limit for audit log for user ${username}:`, error);
                    // FIXED: Use default limit only, no fallback to quota config
                    dailyLimit = 350;
                }
            
            const usagePercentage = dailyLimit > 0 ? Math.round((dailyUsage / dailyLimit) * 100) : 0;
            
            // Get CET timestamp for blocking operations - FIXED: Store CET values directly in database
            const cetTimestamp = getCurrentCETTimestamp();
            
            // Convert expiration date to CET format if it's not indefinite
            let blockUntilCET = null;
            if (expiresAt !== 'Indefinite') {
                // Convert the expiration date to CET format for database storage
                const expirationDate = new Date(expiresAt);
                blockUntilCET = convertDateToCETString(expirationDate);
            }
            
            // Insert or update user blocking status with requests_at_blocking - FIXED: Store CET timestamps directly
            const blockQuery = `
                INSERT INTO bedrock_usage.user_blocking_status 
                (user_id, is_blocked, blocked_reason, blocked_at, blocked_until, requests_at_blocking, created_at, updated_at)
                VALUES (?, 'Y', ?, ?, ?, ?, ?, ?)
                ON DUPLICATE KEY UPDATE
                is_blocked = 'Y',
                blocked_reason = VALUES(blocked_reason),
                blocked_at = VALUES(blocked_at),
                blocked_until = VALUES(blocked_until),
                requests_at_blocking = VALUES(requests_at_blocking),
                updated_at = VALUES(updated_at)
            `;
            
            await window.mysqlDataService.executeQuery(blockQuery, [username, reason, cetTimestamp, blockUntilCET, dailyUsage, cetTimestamp, cetTimestamp]);
            
            // Insert audit log entry with CET timestamp and usage data - FIXED: Store CET timestamps directly
            const auditQuery = `
                INSERT INTO bedrock_usage.blocking_audit_log 
                (user_id, operation_type, operation_reason, performed_by, new_status, operation_timestamp, 
                 daily_requests_at_operation, daily_limit_at_operation, usage_percentage, 
                 iam_policy_updated, email_sent, created_at)
                VALUES (?, 'ADMIN_BLOCK', ?, 'dashboard_admin', 'Y', ?, ?, ?, ?, 'Y', 'Y', ?)
            `;
            
            await window.mysqlDataService.executeQuery(auditQuery, [
                username, reason, cetTimestamp, dailyUsage, dailyLimit, usagePercentage, cetTimestamp
            ]);
            
            // Set Administrative Safe flag for manual blocks
            const adminSafeQuery = `
                INSERT INTO bedrock_usage.user_limits (user_id, administrative_safe, created_at, updated_at)
                VALUES (?, 'Y', NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                administrative_safe = 'Y',
                updated_at = NOW()
            `;
            
            await window.mysqlDataService.executeQuery(adminSafeQuery, [username]);
            
            // Get user team for Lambda payload
            let userTeam = "Unknown";
            for (const team in usersByTeam) {
                if (usersByTeam[team].includes(username)) {
                    userTeam = team;
                    break;
                }
            }
            
            // Call IAM policy management Lambda function
            try {
                const lambda = new AWS.Lambda({ region: 'eu-west-1' });
                const policyPayload = {
                    action: 'block',
                    user_id: username,
                    reason: reason,
                    performed_by: 'dashboard_admin',
                    usage_record: {
                        request_count: dailyUsage,
                        daily_limit: dailyLimit,
                        team: userTeam,
                        date: new Date().toISOString().split('T')[0]
                    }
                };
                
                const policyResponse = await lambda.invoke({
                    FunctionName: 'bedrock-realtime-usage-controller',
                    InvocationType: 'RequestResponse',
                    Payload: JSON.stringify(policyPayload)
                }).promise();
                
                const policyResult = JSON.parse(policyResponse.Payload);
                if (policyResult.statusCode !== 200) {
                    console.error('Failed to update IAM policy for blocking:', policyResult);
                } else {
                    console.log('Successfully updated IAM policy for blocking');
                }
            } catch (error) {
                console.error('Error calling IAM policy management:', error);
            }
            
            // Call email service Lambda function
            try {
                const emailResponse = await fetch('/api/lambda/bedrock-email-service', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        user_id: username,
                        action: 'block',
                        reason: reason,
                        blocked_until: blockUntilCET,
                        performed_by: 'dashboard_admin'
                    })
                });
                
                if (!emailResponse.ok) {
                    console.error('Failed to send blocking email notification');
                }
            } catch (error) {
                console.error('Error calling email service:', error);
            }
            
            updateConnectionStatus('success', `User ${username} has been blocked successfully`);
            // Clear form
            userSelect.value = '';
            blockReason.value = '';
            // Force complete refresh of blocking data
            await loadBlockingData();
        } else {
            updateConnectionStatus('error', 'Database connection not available');
        }
    } catch (error) {
        console.error('Error blocking user:', error);
        updateConnectionStatus('error', `Error blocking user: ${error.message}`);
    }
}

async function blockUser(username) {
    const reason = prompt(`Enter reason for blocking ${username}:`);
    if (!reason) return;
    
    try {
        // Use MySQL database to perform blocking
        if (window.mysqlDataService) {
            // Get duration from the upper controls - always read the value first
            const blockDuration = document.getElementById('block-duration');
            let duration = '1day'; // Default fallback
            
            if (blockDuration && blockDuration.value) {
                // Always use the control value if it exists, regardless of disabled state
                duration = blockDuration.value;
                console.log(`🔧 Using duration from upper controls: ${duration}`);
            } else {
                // If no value in controls, ask user for duration
                const userChoice = prompt(`Select blocking duration for ${username}:\n1 = 1 day\n30 = 30 days\n90 = 90 days\nindefinite = Indefinite\n\nEnter choice:`, '1');
                if (!userChoice) return;
                
                switch(userChoice.toLowerCase()) {
                    case '1':
                        duration = '1day';
                        break;
                    case '30':
                        duration = '30days';
                        break;
                    case '90':
                        duration = '90days';
                        break;
                    case 'indefinite':
                        duration = 'indefinite';
                        break;
                    default:
                        duration = '1day';
                        break;
                }
                console.log(`🔧 Using duration from prompt: ${duration}`);
            }
            
            // Calculate expiration date using the same logic as other blocking functions
            const expiresAt = calculateExpirationDate(duration);
            if (duration === 'custom' && !expiresAt) {
                alert('Custom duration not supported from table buttons. Please use the manual blocking form above.');
                return;
            }
            
            const currentCETString = getCurrentCETTimestamp();
            
            // Convert expiration date to CET format if it's not indefinite
            let blockUntilCET = null;
            if (expiresAt !== 'Indefinite') {
                const expirationDate = new Date(expiresAt);
                blockUntilCET = convertDateToCETString(expirationDate);
            }
            
            // Insert or update user blocking status with CET timestamps
            const blockQuery = `
                INSERT INTO bedrock_usage.user_blocking_status 
                (user_id, is_blocked, blocked_reason, blocked_at, blocked_until, created_at, updated_at)
                VALUES (?, 'Y', ?, ?, ?, ?, ?)
                ON DUPLICATE KEY UPDATE
                is_blocked = 'Y',
                blocked_reason = VALUES(blocked_reason),
                blocked_at = VALUES(blocked_at),
                blocked_until = VALUES(blocked_until),
                updated_at = VALUES(updated_at)
            `;
            
            await window.mysqlDataService.executeQuery(blockQuery, [username, reason, currentCETString, blockUntilCET, currentCETString, currentCETString]);
            
            // Insert audit log entry with CET timestamp
            const auditQuery = `
                INSERT INTO bedrock_usage.blocking_audit_log 
                (user_id, operation_type, operation_reason, performed_by, new_status, operation_timestamp, created_at)
                VALUES (?, 'ADMIN_BLOCK', ?, 'dashboard_admin', 'Y', ?, ?)
            `;
            
            await window.mysqlDataService.executeQuery(auditQuery, [username, reason, currentCETString, currentCETString]);
            
            alert(`User ${username} has been blocked successfully`);
            // Force complete refresh of blocking data
            await loadBlockingData();
        } else {
            alert('Database connection not available');
        }
    } catch (error) {
        console.error('Error blocking user:', error);
        alert(`Error blocking user: ${error.message}`);
    }
}

async function unblockUser(username) {
    try {
        // Use MySQL database to perform unblocking
        if (window.mysqlDataService) {
            // Get current usage data for audit log - FIXED: Use same data source as Daily Usage tab
            const fullDailyData = userMetrics[username]?.daily || Array(11).fill(0);
            const dailyUsage = fullDailyData[10] || 0; // Index 10 is today (same as Daily Usage tab)
            
            // FIXED: Get daily limit from database instead of quota_config.json
            let dailyLimit = 350; // Default fallback
            try {
                if (window.mysqlDataService) {
                    const limitsQuery = `
                        SELECT daily_request_limit 
                        FROM bedrock_usage.user_limits 
                        WHERE user_id = ?
                    `;
                    const limitsResult = await window.mysqlDataService.executeQuery(limitsQuery, [username]);
                    if (limitsResult.length > 0) {
                        dailyLimit = limitsResult[0].daily_request_limit || 350;
                    }
                }
            } catch (error) {
                console.error(`Error fetching daily limit for unblock audit log for user ${username}:`, error);
                // FIXED: Use default limit only, no fallback to quota config
                dailyLimit = 350;
            }
            
            const usagePercentage = dailyLimit > 0 ? Math.round((dailyUsage / dailyLimit) * 100) : 0;
            
            // Update user blocking status with CET timestamp
            const currentCETString = getCurrentCETTimestamp();
            const unblockQuery = `
                UPDATE bedrock_usage.user_blocking_status 
                SET is_blocked = 'N',
                    blocked_reason = 'Manual unblock',
                    blocked_at = NULL,
                    blocked_until = NULL,
                    last_reset_at = ?
                WHERE user_id = ?
            `;
            
            await window.mysqlDataService.executeQuery(unblockQuery, [currentCETString, username]);
            
            // Get CET timestamp for audit log
            const cetTimestamp = getCurrentCETTimestamp();
            
            // Insert audit log entry with CET timestamp and usage data
            const auditQuery = `
                INSERT INTO bedrock_usage.blocking_audit_log 
                (user_id, operation_type, operation_reason, performed_by, new_status, operation_timestamp, 
                 daily_requests_at_operation, daily_limit_at_operation, usage_percentage, 
                 iam_policy_updated, email_sent, created_at)
                VALUES (?, 'ADMIN_UNBLOCK', 'Manual unblock', 'dashboard_admin', 'N', ?, ?, ?, ?, 'Y', 'Y', ?)
            `;
            
            await window.mysqlDataService.executeQuery(auditQuery, [
                username, cetTimestamp, dailyUsage, dailyLimit, usagePercentage, cetTimestamp
            ]);
            
            // Set Administrative Safe flag for manual unblocks
            const adminSafeQuery = `
                INSERT INTO bedrock_usage.user_limits (user_id, administrative_safe, created_at, updated_at)
                VALUES (?, 'Y', NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                administrative_safe = 'Y',
                updated_at = NOW()
            `;
            
            await window.mysqlDataService.executeQuery(adminSafeQuery, [username]);
            
                // Call new merged Lambda function for IAM policy management
                try {
                    const lambda = new AWS.Lambda({ region: 'eu-west-1' });
                    const policyPayload = {
                        action: 'unblock',
                        user_id: username,
                        reason: 'Manual unblock',
                        performed_by: 'dashboard_admin'
                    };
                    
                    const policyResponse = await lambda.invoke({
                        FunctionName: 'bedrock-realtime-usage-controller',
                        InvocationType: 'RequestResponse',
                        Payload: JSON.stringify(policyPayload)
                    }).promise();
                    
                    const policyResult = JSON.parse(policyResponse.Payload);
                    if (policyResult.statusCode !== 200) {
                        console.error('Failed to update IAM policy for unblocking:', policyResult);
                    } else {
                        console.log('Successfully updated IAM policy for unblocking');
                    }
                } catch (error) {
                    console.error('Error calling IAM policy management:', error);
                }
            
            // Call email service Lambda function
            try {
                const emailResponse = await fetch('/api/lambda/bedrock-email-service', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        user_id: username,
                        action: 'unblock',
                        reason: 'Manual unblock',
                        performed_by: 'dashboard_admin'
                    })
                });
                
                if (!emailResponse.ok) {
                    console.error('Failed to send unblocking email notification');
                }
            } catch (error) {
                console.error('Error calling email service:', error);
            }
            
            alert(`User ${username} has been unblocked successfully`);
            // Force complete refresh of blocking data
            await loadBlockingData();
        } else {
            alert('Database connection not available');
        }
    } catch (error) {
        console.error('Error unblocking user:', error);
        alert(`Error unblocking user: ${error.message}`);
    }
}

async function getUserStatus(username) {
    try {
        // Get status from MySQL database instead of Lambda
        if (window.mysqlDataService) {
            const statusQuery = `
                SELECT ubs.is_blocked, ubs.blocked_reason, ubs.blocked_at, ubs.blocked_until,
                       ul.daily_request_limit, ul.administrative_safe
                FROM bedrock_usage.user_blocking_status ubs
                LEFT JOIN bedrock_usage.user_limits ul ON ubs.user_id = ul.user_id
                WHERE ubs.user_id = ?
            `;
            
            const result = await window.mysqlDataService.executeQuery(statusQuery, [username]);
            if (result.length > 0) {
                const data = result[0];
                const status = data.is_blocked === 'Y' ? 'BLOCKED' : 'ACTIVE';
                const adminProtected = data.administrative_safe === 'Y' ? ' (Admin Protected)' : '';
                const message = `User: ${username}\nStatus: ${status}${adminProtected}\nDaily Limit: ${data.daily_request_limit || 'Not set'}\nReason: ${data.blocked_reason || 'N/A'}`;
                alert(message);
            } else {
                alert(`User: ${username}\nStatus: ACTIVE\nNo blocking record found`);
            }
        } else {
            alert('Database connection not available');
        }
    } catch (error) {
        console.error('Error getting user status:', error);
        alert(`Error getting user status: ${error.message}`);
    }
}

// Update user blocking status for all users
async function updateUserBlockingStatus() {
    if (!isConnectedToAWS) {
        console.log('Not connected to AWS, skipping blocking status update');
        return;
    }
    
    try {
        console.log('Updating blocking status and admin protection for all users...');
        
        // Clear existing status
        userBlockingStatus = {};
        userAdminProtection = {};
        
        // Get blocking status and admin protection for each user
        for (const username of allUsers) {
            try {
                // Get blocking status from MySQL database
                if (window.mysqlDataService) {
                    const statusQuery = `
                        SELECT is_blocked
                        FROM bedrock_usage.user_blocking_status 
                        WHERE user_id = ?
                    `;
                    
                    const result = await window.mysqlDataService.executeQuery(statusQuery, [username]);
                    if (result.length > 0) {
                        userBlockingStatus[username] = result[0].is_blocked === 'Y';
                    } else {
                        userBlockingStatus[username] = false;
                    }
                } else {
                    userBlockingStatus[username] = false;
                }
                
                // Check for administrative protection by querying MySQL database
                try {
                    if (window.mysqlDataService) {
                        const adminQuery = `
                            SELECT administrative_safe 
                            FROM bedrock_usage.user_limits 
                            WHERE user_id = ?
                        `;
                        
                        const result = await window.mysqlDataService.executeQuery(adminQuery, [username]);
                        if (result.length > 0 && result[0].administrative_safe === 'Y') {
                            userAdminProtection[username] = true;
                            console.log(`User ${username} has administrative protection`);
                        } else {
                            userAdminProtection[username] = false;
                        }
                    } else {
                        userAdminProtection[username] = false;
                    }
                } catch (error) {
                    console.error(`Error checking admin protection for user ${username}:`, error);
                    userAdminProtection[username] = false;
                }
                
            } catch (error) {
                console.error(`Error getting blocking status for user ${username}:`, error);
                // Default to not blocked if there's an error
                userBlockingStatus[username] = false;
                userAdminProtection[username] = false;
            }
        }
        
        console.log('Updated blocking status:', userBlockingStatus);
        console.log('Updated admin protection:', userAdminProtection);
        
    } catch (error) {
        console.error('Error updating user blocking status:', error);
    }
}

// Format datetime in CET timezone
function formatDateTime(isoString, includeSeconds = false) {
    if (!isoString || isoString === 'Indefinite' || isoString === null) {
        return 'Indefinite';
    }
    
    try {
        // Create date from ISO string (this will be in UTC)
        const utcDate = new Date(isoString);
        
        // Check if date is valid
        if (isNaN(utcDate.getTime())) {
            return 'Indefinite';
        }
        
        // Use Intl.DateTimeFormat with formatToParts for proper timezone conversion
        const formatter = new Intl.DateTimeFormat('en-GB', {
            timeZone: 'Europe/Madrid',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        
        const parts = formatter.formatToParts(utcDate);
        const partsObj = {};
        parts.forEach(part => {
            partsObj[part.type] = part.value;
        });
        
        const day = partsObj.day;
        const month = partsObj.month;
        const fullYear = partsObj.year;
        const year = includeSeconds ? fullYear : fullYear.slice(-2);
        const hours = partsObj.hour;
        const minutes = partsObj.minute;
        const seconds = partsObj.second;
        
        if (includeSeconds) {
            return `${day}/${month}/${year}, ${hours}:${minutes}:${seconds}`;
        } else {
            return `${day}/${month}/${year} - ${hours}:${minutes}`;
        }
    } catch (error) {
        console.error('Error formatting date:', error);
        return 'Indefinite';
    }
}

// Handle duration change for custom datetime
function handleDurationChange() {
    const durationSelect = document.getElementById('block-duration');
    const customDatetime = document.getElementById('custom-datetime');
    
    if (durationSelect.value === 'custom') {
        customDatetime.style.display = 'block';
        // Set minimum datetime to current time
        const now = new Date();
        const localISOTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
        customDatetime.min = localISOTime;
        customDatetime.value = localISOTime;
        
        // Update the option text to show selected datetime
        customDatetime.addEventListener('change', function() {
            const selectedDate = new Date(this.value);
            const formattedDate = formatDateTime(selectedDate.toISOString());
            durationSelect.options[durationSelect.selectedIndex].text = formattedDate;
        });
    } else {
        customDatetime.style.display = 'none';
        // Reset custom option text
        const customOption = durationSelect.querySelector('option[value="custom"]');
        if (customOption) {
            customOption.text = 'Custom';
        }
    }
}

// Calculate expiration date based on duration
function calculateExpirationDate(duration) {
    const now = new Date();
    
    switch (duration) {
        case '1day':
            return new Date(now.getTime() + 24 * 60 * 60 * 1000).toISOString();
        case '30days':
            return new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString();
        case '90days':
            return new Date(now.getTime() + 90 * 24 * 60 * 60 * 1000).toISOString();
        case 'custom':
            const customDatetime = document.getElementById('custom-datetime');
            if (!customDatetime.value) {
                return null;
            }
            return new Date(customDatetime.value).toISOString();
        case 'indefinite':
        default:
            return 'Indefinite';
    }
}

// Dynamic action function
async function performDynamicAction() {
    const userSelect = document.getElementById('user-select');
    const blockDuration = document.getElementById('block-duration');
    const blockReason = document.getElementById('block-reason');
    const dynamicBtn = document.getElementById('dynamic-action-btn');
    
    const username = userSelect.value;
    const duration = blockDuration.value;
    const reason = blockReason.value;
    
    if (!username) {
        alert('Please select a user');
        return;
    }
    
    const isBlocked = userBlockingStatus[username] || false;
    
    if (isBlocked) {
        // Unblock user using MySQL database
        try {
            if (window.mysqlDataService) {
                // Update user blocking status with CET timestamp
                const currentCETString = getCurrentCETTimestamp();
                const unblockQuery = `
                    UPDATE bedrock_usage.user_blocking_status 
                    SET is_blocked = 'N',
                        blocked_reason = 'Manual unblock',
                        blocked_at = NULL,
                        blocked_until = NULL,
                        last_reset_at = ?,
                        updated_at = ?
                    WHERE user_id = ?
                `;
                
                await window.mysqlDataService.executeQuery(unblockQuery, [currentCETString, currentCETString, username]);
                
                // Get current usage data for audit log - FIXED: Use same data source as Daily Usage tab
                const fullDailyData = userMetrics[username]?.daily || Array(11).fill(0);
                const dailyUsage = fullDailyData[10] || 0; // Index 10 is today (same as Daily Usage tab)
                
                // FIXED: Get daily limit from database instead of quota_config.json
                let dailyLimit = 350; // Default fallback
                try {
                    if (window.mysqlDataService) {
                        const limitsQuery = `
                            SELECT daily_request_limit 
                            FROM bedrock_usage.user_limits 
                            WHERE user_id = ?
                        `;
                        const limitsResult = await window.mysqlDataService.executeQuery(limitsQuery, [username]);
                        if (limitsResult.length > 0) {
                            dailyLimit = limitsResult[0].daily_request_limit || 350;
                        }
                    }
                } catch (error) {
                    console.error(`Error fetching daily limit for dynamic action audit log for user ${username}:`, error);
                    // FIXED: Use default limit only, no fallback to quota config
                    dailyLimit = 350;
                }
                
                const usagePercentage = dailyLimit > 0 ? Math.round((dailyUsage / dailyLimit) * 100) : 0;
                
                // Get CET timestamp for audit log
                const cetTimestamp = getCurrentCETTimestamp();
                
                // Insert audit log entry with CET timestamp and usage data
                const auditQuery = `
                    INSERT INTO bedrock_usage.blocking_audit_log 
                    (user_id, operation_type, operation_reason, performed_by, new_status, operation_timestamp, 
                     daily_requests_at_operation, daily_limit_at_operation, usage_percentage, 
                     iam_policy_updated, email_sent, created_at)
                    VALUES (?, 'ADMIN_UNBLOCK', ?, 'dashboard_admin', 'N', ?, ?, ?, ?, 'Y', 'Y', ?)
                `;
                
                await window.mysqlDataService.executeQuery(auditQuery, [
                    username, reason || 'Manual unblock', cetTimestamp, dailyUsage, dailyLimit, usagePercentage, cetTimestamp
                ]);
                
                // Set Administrative Safe flag for manual unblocks
                const adminSafeQuery = `
                    INSERT INTO bedrock_usage.user_limits (user_id, administrative_safe, created_at, updated_at)
                    VALUES (?, 'Y', NOW(), NOW())
                    ON DUPLICATE KEY UPDATE
                    administrative_safe = 'Y',
                    updated_at = NOW()
                `;
                
                await window.mysqlDataService.executeQuery(adminSafeQuery, [username]);
                
                // Call new merged Lambda function for IAM policy management
                try {
                    const lambda = new AWS.Lambda({ region: 'eu-west-1' });
                    const policyPayload = {
                        action: 'unblock',
                        user_id: username,
                        reason: reason || 'Manual unblock',
                        performed_by: 'dashboard_admin'
                    };
                    
                    const policyResponse = await lambda.invoke({
                        FunctionName: 'bedrock-realtime-usage-controller',
                        InvocationType: 'RequestResponse',
                        Payload: JSON.stringify(policyPayload)
                    }).promise();
                    
                    const policyResult = JSON.parse(policyResponse.Payload);
                    if (policyResult.statusCode !== 200) {
                        console.error('Failed to update IAM policy for unblocking:', policyResult);
                    } else {
                        console.log('Successfully updated IAM policy for unblocking');
                    }
                } catch (error) {
                    console.error('Error calling IAM policy management:', error);
                }
                
                // Call email service Lambda function
                try {
                    const emailResponse = await fetch('/api/lambda/bedrock-email-service', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            user_id: username,
                            action: 'unblock',
                            reason: reason || 'Manual unblock',
                            performed_by: 'dashboard_admin'
                        })
                    });
                    
                    if (!emailResponse.ok) {
                        console.error('Failed to send unblocking email notification');
                    }
                } catch (error) {
                    console.error('Error calling email service:', error);
                }
                
                alert(`User ${username} has been unblocked successfully`);
                // Clear form
                userSelect.value = '';
                blockReason.value = '';
                // Update button state
                updateDynamicButton();
                // Force complete refresh of blocking data
                await loadBlockingData();
            } else {
                alert('Database connection not available');
            }
        } catch (error) {
            console.error('Error unblocking user:', error);
            alert(`Error unblocking user: ${error.message}`);
        }
    } else {
        // Block user
        if (!reason) {
            alert('Please provide a reason for blocking');
            return;
        }
        
        // Calculate expiration date
        const expiresAt = calculateExpirationDate(duration);
        if (duration === 'custom' && !expiresAt) {
            alert('Please select a custom date and time');
            return;
        }
        
        try {
            // Use MySQL database to perform blocking
            if (window.mysqlDataService) {
                // Insert or update user blocking status with CET timestamps
                const currentCETString = getCurrentCETTimestamp();
                
                // Convert expiration date to CET format if it's not indefinite
                let blockUntilCET = null;
                if (expiresAt !== 'Indefinite') {
                    const expirationDate = new Date(expiresAt);
                    blockUntilCET = convertDateToCETString(expirationDate);
                }
                
                const blockQuery = `
                    INSERT INTO bedrock_usage.user_blocking_status 
                    (user_id, is_blocked, blocked_reason, blocked_at, blocked_until, created_at)
                    VALUES (?, 'Y', ?, ?, ?, ?)
                    ON DUPLICATE KEY UPDATE
                    is_blocked = 'Y',
                    blocked_reason = VALUES(blocked_reason),
                    blocked_at = VALUES(blocked_at),
                    blocked_until = VALUES(blocked_until)
                `;
                
                await window.mysqlDataService.executeQuery(blockQuery, [username, reason, currentCETString, blockUntilCET, currentCETString]);
                
                // Get current usage data for audit log - FIXED: Use same data source as Daily Usage tab
                const fullDailyData = userMetrics[username]?.daily || Array(11).fill(0);
                const dailyUsage = fullDailyData[10] || 0; // Index 10 is today (same as Daily Usage tab)
                
                // FIXED: Get daily limit from database instead of quota_config.json
                let dailyLimit = 350; // Default fallback
                try {
                    if (window.mysqlDataService) {
                        const limitsQuery = `
                            SELECT daily_request_limit 
                            FROM bedrock_usage.user_limits 
                            WHERE user_id = ?
                        `;
                        const limitsResult = await window.mysqlDataService.executeQuery(limitsQuery, [username]);
                        if (limitsResult.length > 0) {
                            dailyLimit = limitsResult[0].daily_request_limit || 350;
                        }
                    }
                } catch (error) {
                    console.error(`Error fetching daily limit for block audit log for user ${username}:`, error);
                    // FIXED: Use default limit only, no fallback to quota config
                    dailyLimit = 350;
                }
                
                const usagePercentage = dailyLimit > 0 ? Math.round((dailyUsage / dailyLimit) * 100) : 0;
                
                // Get CET timestamp for audit log
                const cetTimestamp = getCurrentCETTimestamp();
                
                // Insert audit log entry with CET timestamp and usage data
                const auditQuery = `
                    INSERT INTO bedrock_usage.blocking_audit_log 
                    (user_id, operation_type, operation_reason, performed_by, new_status, operation_timestamp, 
                     daily_requests_at_operation, daily_limit_at_operation, usage_percentage, 
                     iam_policy_updated, email_sent, created_at)
                    VALUES (?, 'ADMIN_BLOCK', ?, 'dashboard_admin', 'Y', ?, ?, ?, ?, 'Y', 'Y', ?)
                `;
                
                await window.mysqlDataService.executeQuery(auditQuery, [
                    username, reason, cetTimestamp, dailyUsage, dailyLimit, usagePercentage, cetTimestamp
                ]);
                
                // Set Administrative Safe flag for manual blocks
                const adminSafeQuery = `
                    INSERT INTO bedrock_usage.user_limits (user_id, administrative_safe, created_at, updated_at)
                    VALUES (?, 'Y', NOW(), NOW())
                    ON DUPLICATE KEY UPDATE
                    administrative_safe = 'Y',
                    updated_at = NOW()
                `;
                
                await window.mysqlDataService.executeQuery(adminSafeQuery, [username]);
                
                // Get user team for Lambda payload
                let userTeam = "Unknown";
                for (const team in usersByTeam) {
                    if (usersByTeam[team].includes(username)) {
                        userTeam = team;
                        break;
                    }
                }
                
                // Call new merged Lambda function for IAM policy management
                try {
                    const lambda = new AWS.Lambda({ region: 'eu-west-1' });
                    const policyPayload = {
                        action: 'block',
                        user_id: username,
                        reason: reason,
                        performed_by: 'dashboard_admin',
                        usage_record: {
                            request_count: dailyUsage,
                            daily_limit: dailyLimit,
                            team: userTeam,
                            date: new Date().toISOString().split('T')[0]
                        }
                    };
                    
                    const policyResponse = await lambda.invoke({
                        FunctionName: 'bedrock-realtime-usage-controller',
                        InvocationType: 'RequestResponse',
                        Payload: JSON.stringify(policyPayload)
                    }).promise();
                    
                    const policyResult = JSON.parse(policyResponse.Payload);
                    if (policyResult.statusCode !== 200) {
                        console.error('Failed to update IAM policy for blocking:', policyResult);
                    } else {
                        console.log('Successfully updated IAM policy for blocking');
                    }
                } catch (error) {
                    console.error('Error calling IAM policy management:', error);
                }
                
                // Call email service Lambda function
                try {
                    const emailResponse = await fetch('/api/lambda/bedrock-email-service', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            user_id: username,
                            action: 'block',
                            reason: reason,
                            blocked_until: blockUntilCET,
                            performed_by: 'dashboard_admin'
                        })
                    });
                    
                    if (!emailResponse.ok) {
                        console.error('Failed to send blocking email notification');
                    }
                } catch (error) {
                    console.error('Error calling email service:', error);
                }
                
                alert(`User ${username} has been blocked successfully`);
                // Clear form
                userSelect.value = '';
                blockReason.value = '';
                blockDuration.value = '1day';
                document.getElementById('custom-datetime').style.display = 'none';
                // Reset custom option text
                const customOption = blockDuration.querySelector('option[value="custom"]');
                if (customOption) {
                    customOption.text = 'Custom';
                }
                // Update button state
                updateDynamicButton();
                // Force complete refresh of blocking data
                await loadBlockingData();
            } else {
                alert('Database connection not available');
            }
        } catch (error) {
            console.error('Error blocking user:', error);
            alert(`Error blocking user: ${error.message}`);
        }
    }
}

// Update dynamic button and duration control based on selected user
function updateDynamicButton() {
    const userSelect = document.getElementById('user-select');
    const dynamicBtn = document.getElementById('dynamic-action-btn');
    const blockDuration = document.getElementById('block-duration');
    const customDatetime = document.getElementById('custom-datetime');
    const selectedUser = userSelect.value;
    
    if (!selectedUser) {
        // No user selected - gray state
        dynamicBtn.className = 'btn btn-select-user';
        dynamicBtn.textContent = 'Select user';
        dynamicBtn.disabled = true;
        // Disable duration control when no user selected
        blockDuration.disabled = true;
        customDatetime.style.display = 'none';
    } else {
        const isBlocked = userBlockingStatus[selectedUser] || false;
        
        if (isBlocked) {
            // User is blocked - green unblock button
            dynamicBtn.className = 'btn btn-unblock-user';
            dynamicBtn.textContent = 'Unblock User';
            dynamicBtn.disabled = false;
            // Disable duration control for blocked users
            blockDuration.disabled = true;
            customDatetime.style.display = 'none';
        } else {
            // User is active - pink block button
            dynamicBtn.className = 'btn btn-block-user';
            dynamicBtn.textContent = 'Block User';
            dynamicBtn.disabled = false;
            // Enable duration control for active users
            blockDuration.disabled = false;
            // Show custom datetime if custom is selected
            if (blockDuration.value === 'custom') {
                customDatetime.style.display = 'block';
            }
        }
    }
}

// Initialize controls on page load
function initializeBlockingControls() {
    const blockDuration = document.getElementById('block-duration');
    const customDatetime = document.getElementById('custom-datetime');
    
    // Set default value to "1day" and disable control
    blockDuration.value = '1day';
    blockDuration.disabled = true;
    customDatetime.style.display = 'none';
}

// Helper function to get current CET timestamp for database operations
function getCurrentCETTimestamp() {
    const now = new Date();
    // Convert to CET (Europe/Madrid timezone) and format for MySQL
    const cetTime = new Intl.DateTimeFormat('sv-SE', {
        timeZone: 'Europe/Madrid',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    }).format(now);
    
    return cetTime.replace('T', ' '); // MySQL datetime format: YYYY-MM-DD HH:MM:SS
}

// Helper function to convert a Date object to CET string for database storage
function convertDateToCETString(date) {
    // Convert the date to CET timezone and format for MySQL
    const cetTime = new Intl.DateTimeFormat('sv-SE', {
        timeZone: 'Europe/Madrid',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    }).format(date);
    
    return cetTime.replace('T', ' '); // MySQL datetime format: YYYY-MM-DD HH:MM:SS
}

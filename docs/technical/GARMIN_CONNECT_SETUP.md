# Garmin Connect Developer Configuration Guide

## Overview

This guide walks you through setting up Garmin Connect API access for the Athlete Performance Predictor platform. Garmin Connect provides access to workout data, biometric readings, and device information from Garmin fitness devices.

## Prerequisites

- Garmin Connect account (regular user account)
- Valid email address
- Understanding of OAuth2 authentication flow

## Step 1: Create Garmin Developer Account

### 1.1 Visit the Developer Portal
- Go to [Garmin Developer Portal](https://developer.garmin.com/)
- Click "Sign In" or "Create Account"

### 1.2 Create Developer Account
- If you don't have a developer account, click "Create Account"
- Use your existing Garmin Connect credentials or create new ones
- Complete the developer profile information
- Accept the terms of service

## Step 2: Register Your Application

### 2.1 Create New Application
- In the developer portal, click "My Apps" → "Create App"
- Fill in the application details:
  - **App Name**: `Athlete Performance Predictor` (or your preferred name)
  - **Description**: `Multi-source fitness data analysis platform`
  - **Category**: Select "Health & Fitness"
  - **Platform**: Web Application

### 2.2 Configure OAuth2 Settings
- **Redirect URI**: `http://localhost:8000/auth/garmin/callback`
  - For production: Use your actual domain
  - For development: Localhost is acceptable
- **Scopes**: Select the following permissions:
  - `activity` - Access to workout and activity data
  - `profile` - Basic user profile information
  - `health` - Health and biometric data

### 2.3 Save Application
- Click "Create App" to save your configuration
- Note down your **Client ID** and **Client Secret**

## Step 3: Configure Environment Variables

### 3.1 Update Environment File
Add the following variables to your `.env` file:

```bash
# Garmin Connect API Configuration
GARMIN_CLIENT_ID=your_actual_client_id_here
GARMIN_CLIENT_SECRET=your_actual_client_secret_here
GARMIN_REDIRECT_URI=http://localhost:8000/auth/garmin/callback
```

### 3.2 Security Notes
- Never commit your `.env` file to version control
- Keep your client secret secure
- Rotate credentials if compromised

## Step 4: OAuth2 Authentication Flow

### 4.1 Generate Authorization URL
The connector will generate an authorization URL when needed:

```python
from src.connectors.garmin import GarminConnectConnector

config = {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret", 
    "redirect_uri": "http://localhost:8000/auth/garmin/callback"
}

connector = GarminConnectConnector("garmin_connect", config)
auth_url = await connector.get_oauth_url()
print(f"Visit this URL to authorize: {auth_url}")
```

### 4.2 User Authorization
1. User visits the authorization URL
2. Logs into Garmin Connect
3. Grants permissions to your application
4. Garmin redirects to your callback URL with an authorization code

### 4.3 Exchange Code for Tokens
```python
# Handle the callback and exchange code for tokens
authorization_code = "code_from_callback_url"
success = await connector.exchange_code_for_tokens(authorization_code)

if success:
    # Tokens are now stored in connector.config
    access_token = connector.config["access_token"]
    refresh_token = connector.config["refresh_token"]
```

## Step 5: Data Access

### 5.1 Supported Data Types
The connector supports the following data:

**Workouts:**
- Running, cycling, swimming, strength training, yoga, walking, hiking
- Duration, distance, calories, heart rate, elevation gain
- GPS tracks and detailed activity metrics

**Biometrics:**
- Daily steps, calories burned
- Heart rate (average and max)
- Sleep duration
- Weight and body composition
- Activity summaries

### 5.2 Fetching Data
```python
from datetime import date, timedelta

# Fetch workouts for the last 7 days
end_date = date.today()
start_date = end_date - timedelta(days=7)

workouts = await connector.fetch_workouts(start_date, end_date)
biometrics = await connector.fetch_biometrics(start_date, end_date)
```

## Step 6: Rate Limiting and Best Practices

### 6.1 Rate Limits
- Garmin Connect has conservative rate limits
- Minimum 1 second between requests
- Respect rate limit headers in responses

### 6.2 Error Handling
The connector handles common errors:
- Authentication failures
- Rate limit exceeded
- API errors
- Network timeouts

### 6.3 Token Management
- Access tokens expire (typically 1 hour)
- Refresh tokens are long-lived
- Automatic token refresh on expiration
- Store tokens securely

## Step 7: Testing Your Setup

### 7.1 Test Authentication
```python
# Test if your configuration works
authenticated = await connector.authenticate()
print(f"Authentication successful: {authenticated}")
```

### 7.2 Test Data Fetching
```python
# Test with a small date range
test_date = date.today()
workouts = await connector.fetch_workouts(test_date, test_date)
print(f"Found {len(workouts)} workouts today")
```

### 7.3 Verify Data Quality
- Check that workout data is properly transformed
- Verify biometric readings are accurate
- Ensure sport types are correctly mapped

## Troubleshooting

### Common Issues

**Authentication Failed:**
- Verify client ID and secret
- Check redirect URI matches exactly
- Ensure scopes are properly configured

**Rate Limit Errors:**
- Increase delay between requests
- Implement exponential backoff
- Check rate limit headers

**Data Not Found:**
- Verify user has activities in the date range
- Check if user granted necessary permissions
- Ensure Garmin device is synced

**Token Refresh Issues:**
- Verify refresh token is valid
- Check client credentials
- Re-authenticate if necessary

### Getting Help

- [Garmin Developer Documentation](https://developer.garmin.com/)
- [Garmin Connect API Reference](https://developer.garmin.com/connect/api/)
- [OAuth2 Implementation Guide](https://oauth.net/2/)

## Security Considerations

### 1. Token Storage
- Store tokens securely (encrypted database, secure environment variables)
- Never log tokens in plain text
- Implement token rotation

### 2. User Privacy
- Only request necessary scopes
- Implement data retention policies
- Respect user data deletion requests

### 3. API Security
- Use HTTPS for all API calls
- Validate all user inputs
- Implement proper error handling

## Next Steps

Once your Garmin Connect connector is configured:

1. **Integrate with Data Pipeline**: Add to your data ingestion workflow
2. **Test with Real Data**: Verify data quality and completeness
3. **Monitor Performance**: Track API usage and error rates
4. **Scale Up**: Add more users and data sources
5. **Production Deployment**: Update redirect URIs and security settings

## Support

For technical support with this connector:
- Check the troubleshooting section above
- Review Garmin's official documentation
- Open an issue in the project repository
- Contact the development team

---

*Last updated: [Current Date]*
*Version: 1.0*

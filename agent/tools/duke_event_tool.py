import requests
from datetime import datetime, timedelta

def search_campus_events(user_query: str = None) -> str:
    """
    Retrieve Duke campus events for the next 50 days and filter by optional keywords.

    Parameters:
        user_query: Optional user query keywords to search within event title and description.

    Returns:
        Formatted string of events, or a message if no matching events are found.
    """
    url = "https://calendar.duke.edu/events/index.json?&future_days=50&local=true&feed_type=simple"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Extract events from response
        if isinstance(data, dict) and "events" in data:
            events = data["events"]
        elif isinstance(data, list):
            events = data
        else:
            return "Error: Unable to parse event data format."
        
        # Filter events by query terms
        filtered_events = []
        for event in events:
            if not isinstance(event, dict):
                # Skip non-dictionary entries
                continue
            summary = event.get('summary', '')
            description = event.get('description', '')
            # Filter by query if provided (case-insensitive)
            if user_query:
                if user_query.lower() in summary.lower() or user_query.lower() in description.lower():
                    filtered_events.append(event)
            else:
                filtered_events.append(event)
        
        if not filtered_events:
            return "No matching events found."
        
        # Format event details
        event_details = []
        for event in filtered_events:
            # Get event title
            summary = event.get('summary', 'Untitled')
            
            # Get start timestamp - make sure we're checking for the exact key
            time_info = "Time: Not specified"
            
            # Debugging: print all keys to see actual timestamp field names
            # print(f"Event keys: {list(event.keys())}")
            
            # Try different possible timestamp keys
            for start_key in ['start-timestamp', 'startTimestamp', 'start_timestamp', 'start']:
                if start_key in event:
                    start_ts = event[start_key]
                    try:
                        start_dt = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
                        # Convert to Eastern Time (approximate)
                        start_dt = start_dt - timedelta(hours=4)
                        date_str = start_dt.strftime("%Y-%m-%d")
                        start_time = start_dt.strftime("%H:%M")
                        
                        # Look for end timestamp
                        end_time = None
                        for end_key in ['end-timestamp', 'endTimestamp', 'end_timestamp', 'end']:
                            if end_key in event:
                                end_ts = event[end_key]
                                try:
                                    end_dt = datetime.fromisoformat(end_ts.replace("Z", "+00:00"))
                                    end_dt = end_dt - timedelta(hours=4)
                                    end_time = end_dt.strftime("%H:%M")
                                    break
                                except:
                                    pass
                        
                        if end_time:
                            time_info = f"Date: {date_str}, Time: {start_time} - {end_time}"
                        else:
                            time_info = f"Date: {date_str}, Time: {start_time}"
                            
                        break
                    except Exception as e:
                        # If datetime parsing fails, try a simpler approach
                        time_info = f"Date/Time: {start_ts}"
            
            # Get location information
            location_data = event.get('location', {})
            if isinstance(location_data, dict):
                location = location_data.get('address', 'No location information')
            else:
                location = location_data if location_data else "No location information"
            
            # Get the link - try different fields
            event_url = None
            for link_key in ['url', 'link', 'event-url', 'eventUrl']:
                if link_key in event and event[link_key]:
                    event_url = event[link_key]
                    break
                    
            # If we have a URL, include it in the output
            url_text = f"Link: {event_url}" if event_url else "No link available"
            
            # Combine event information
            event_details.append(f"Event: {summary}\n{time_info}\nLocation: {location}\n{url_text}")
        
        return "\n\n".join(event_details)
    
    except Exception as e:
        return f"Error retrieving campus events: {str(e)}"

if __name__ == "__main__":
    
    query = "Spring"
    result = search_campus_events(query)
    print("search: ", query)
    print(result)

import vertexai
from vertexai.generative_models import (
    FunctionDeclaration,
    GenerationConfig,
    GenerativeModel,
    Part,
    Tool
)
import requests
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import uuid

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
load_dotenv()

# Initialize Vertex AI
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "footbackapi")
LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Define your API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.football1.io.vn/api")
API_KEY = os.getenv("API_KEY", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOi8vYXBpLmZvb3RiYWxsMS5pby52bi9hcGkvbG9naW4iLCJpYXQiOjE3NDU4OTM2NzMsImV4cCI6MTc0Njc2MDA3MywibmJmIjoxNzQ1ODkzNjczLCJqdGkiOiJ1MkNDR1o1dXhaNFFqVGJIIiwic3ViIjoiMSIsInBydiI6IjIzYmQ1Yzg5NDlmNjAwYWRiMzllNzAxYzQwMDg3MmRiN2E1OTc2ZjcifQ.-E-gTJQzUqRYgjMKajdJ43B3Dkap-KXjE2idlz7TmuY")

# Define function declarations
get_competition = FunctionDeclaration(
    name="get_competition",
    description="Lấy thông tin chi tiết về giải đấu",
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Tên giải đấu (ví dụ: Premier League, La Liga, Champions League)",
                "enum": ["Premier League", "La Liga", "Champions League", "Bundesliga", "Serie A"]
            }
        },
        "required": ["name"]
    }
)

get_fixture = FunctionDeclaration(
    name="get_fixture",
    description="Lấy thông tin trận đấu",
    parameters={
        "type": "object",
        "properties": {
            "home_team": {
                "type": "string",
                "description": "Tên đội chủ nhà"
            },
            "away_team": {
                "type": "string",
                "description": "Tên đội khách"
            },
            "date": {
                "type": "string",
                "description": "Ngày thi đấu (định dạng YYYY-MM-DD), không bắt buộc"
            }
        },
        "required": ["home_team", "away_team"]
    }
)

get_team = FunctionDeclaration(
    name="get_team",
    description="Lấy thông tin về đội bóng",
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Tên đội bóng (ví dụ: Manchester United, Real Madrid, Barcelona)"
            }
        },
        "required": ["name"]
    }
)

get_news = FunctionDeclaration(
    name="get_news",
    description="Lấy tin tức mới nhất về bóng đá",
    parameters={
        "type": "object",
        "properties": {
            "team_id": {
                "type": "string",
                "description": "ID của đội bóng (không bắt buộc)"
            },
            "limit": {
                "type": "integer",
                "description": "Số lượng tin tức muốn lấy"
            }
        }
    }
)

get_standing = FunctionDeclaration(
    name="get_standing",
    description="Lấy bảng xếp hạng của giải đấu",
    parameters={
        "type": "object",
        "properties": {
            "competition_name": {
                "type": "string",
                "description": "Tên giải đấu (ví dụ: Premier League, La Liga, Champions League)",
                "enum": ["Premier League", "La Liga", "Champions League", "Bundesliga", "Serie A"]
            },
            "team_name": {
                "type": "string",
                "description": "Tên đội bóng cần xem thông tin (không bắt buộc)"
            }
        },
        "required": ["competition_name"]
    }
)

get_upcoming_fixtures = FunctionDeclaration(
    name="get_upcoming_fixtures",
    description="Lấy thông tin các trận đấu sắp diễn ra của một đội bóng trong một giải đấu, hoặc tất cả trận đấu của một giải đấu",
    parameters={
        "type": "object",
        "properties": {
            "team_name": {
                "type": "string",
                "description": "Tên đội bóng (ví dụ: Manchester United, Real Madrid, Barcelona) - không bắt buộc"
            },
            "competition_name": {
                "type": "string",
                "description": "Tên giải đấu (ví dụ: Premier League, La Liga, Champions League)",
                "enum": ["Premier League", "La Liga", "Champions League", "Bundesliga", "Serie A"]
            },
            "limit": {
                "type": "integer",
                "description": "Số lượng trận đấu muốn lấy (mặc định: 5)"
            },
            "include_recent": {
                "type": "boolean",
                "description": "Có lấy cả các trận đấu gần đây không"
            }
        },
        "required": ["competition_name"]
    }
)

# Create tool with all functions
football_tool = Tool(
    function_declarations=[
        get_competition,
        get_fixture,
        get_team,
        get_news,
        get_standing,
        get_upcoming_fixtures
    ]
)

# Define API call functions
def get_competition_from_api(content):
    url = f"{API_BASE_URL}/competitions"
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    params = {"name": content['name']}
    print(url)
    print(params)
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # Check for successful response
        if not data.get('success'):
            return {"error": "API returned unsuccessful response"}

        # Extract competitions from the nested structure
        competitions = data.get('data', {}).get('competitions', [])

        # Find matching competition
        matching_competition = next((comp for comp in competitions
                                   if comp.get('name', '').lower() == content['name'].lower()), None)

        if matching_competition:
            comp_id = matching_competition['id']
            detail_url = f"{API_BASE_URL}/competitions/{comp_id}"
            detail_response = requests.get(detail_url, headers=headers)
            detail_response.raise_for_status()
            return detail_response.json()
        return {"message": "Không tìm thấy giải đấu", "data": None}
    except Exception as e:
        print(f"Error querying competition: {e}")
        return {"error": f"Không thể lấy thông tin giải đấu: {str(e)}"}

def get_fixture_from_api(content):
    url = f"{API_BASE_URL}/fixtures"
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    home_team_id = get_team_id_by_name(content['home_team'], headers)
    away_team_id = get_team_id_by_name(content['away_team'], headers)
    if not home_team_id or not away_team_id:
        return {"error": "Không tìm thấy thông tin đội bóng"}
    params = {
        "home_team_id": home_team_id,
        "away_team_id": away_team_id
    }
    if content.get('date'):
        params['date'] = content['date']
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        fixtures = response.json()
        if fixtures and fixtures.get('data') and len(fixtures['data']) > 0:
            fixture_id = fixtures['data'][0]['id']
            detail_url = f"{API_BASE_URL}/fixtures/{fixture_id}"
            detail_response = requests.get(detail_url, headers=headers)
            detail_response.raise_for_status()
            return detail_response.json()
        return {"error": "Không tìm thấy trận đấu"}
    except Exception as e:
        print(f"Error querying fixture: {e}")
        return {"error": f"Không thể tìm trận đấu: {str(e)}"}

def get_team_id_by_name(team_name, headers):
    try:
        search_url = f"{API_BASE_URL}/teams"
        params = {"name": team_name}
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        print(result)
        if result and result.get('data'):
            for team in result['data']:
                if team['name'].lower() == team_name.lower():
                    return team['id']
            if len(result['data']) > 0:
                return result['data'][0]['id']
        return None
    except Exception as e:
        print(f"Error finding team ID: {e}")
        return None

def get_team_from_api(content):
    url = f"{API_BASE_URL}/teams"
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    params = {"name": content['name']}
    print(url)
    print(params)
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()

        # Check if we have a successful response with teams data
        if result and result.get('success') and result.get('data', {}).get('teams'):
            teams = result['data']['teams']
            if len(teams) > 0:
                # Try to find exact match by name (case insensitive)
                team = next((t for t in teams if t['name'].lower() == content['name'].lower()), teams[0])
                team_id = team['id']

                # Get detailed team info
                detail_url = f"{API_BASE_URL}/teams/{team_id}"
                detail_response = requests.get(detail_url, headers=headers)
                detail_response.raise_for_status()
                return detail_response.json()
        return {"error": "Không tìm thấy đội bóng"}
    except Exception as e:
        print(f"Error querying team: {e}")
        return {"error": f"Không thể tìm đội bóng: {str(e)}"}

def get_news_from_api(content):
    url = f"{API_BASE_URL}/news"
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    params = {}
    if content.get("team_id"):
        params["team_id"] = content.get("team_id")
    if content.get("limit"):
        params["limit"] = content.get("limit", 5)
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error querying news: {e}")
        return {"error": f"Không thể lấy tin tức: {str(e)}"}

def get_standing_from_api(content):
    url = f"{API_BASE_URL}/standings"
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}

    params = {}
    if "competition_name" in content:
        params["name"] = content["competition_name"]
    if "team_name" in content and content["team_name"].strip():
        params["teamName"] = content["team_name"]

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()

        if not result.get("success"):
            return {"error": "API returned unsuccessful response"}

        return result
    except Exception as e:
        print(f"Error querying standings: {e}")
        return {"error": f"Không thể lấy bảng xếp hạng: {str(e)}"}

def get_upcoming_fixtures_from_api(content):
    url = f"{API_BASE_URL}/fixtures/upcoming/ai"
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}

    params = {}
    if "competition_name" in content:
        params["competition_name"] = content["competition_name"]
    if "team_name" in content and content["team_name"].strip():
        params["team_name"] = content["team_name"]
    if "limit" in content:
        params["limit"] = content["limit"]
    # Add parameter for including recent matches
    if "include_recent" in content and content["include_recent"]:
        params["include_recent"] = "true"

    print(f"API call to {url} with params: {params}")
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()

        if not result.get("success"):
            return {"error": "API returned unsuccessful response"}

        return result
    except Exception as e:
        print(f"Error querying upcoming fixtures: {e}")
        return {"error": f"Không thể lấy lịch thi đấu sắp tới: {str(e)}"}

# Function handler to map function names to API calls
function_handler = {
    "get_competition": get_competition_from_api,
    "get_fixture": get_fixture_from_api,
    "get_team": get_team_from_api,
    "get_news": get_news_from_api,
    "get_standing": get_standing_from_api,
    "get_upcoming_fixtures": get_upcoming_fixtures_from_api
}

# Initialize Gemini model
gemini_model = GenerativeModel(
    "gemini-2.0-flash",
    generation_config=GenerationConfig(temperature=0),
    tools=[football_tool]
)

# Initialize chat session
chat = gemini_model.start_chat()

# Function to process chat and function calls
def send_chat_message(prompt):
    prompt += """
    Tóm tắt ngắn gọn và dễ hiểu. Chỉ sử dụng thông tin từ API trả về.
    """
    response = chat.send_message(prompt)
    function_calling_in_process = True
    while function_calling_in_process:
        function_call = response.candidates[0].content.parts[0].function_call
        if function_call.name in function_handler.keys():
            function_name = function_call.name
            params = {key: value for key, value in function_call.args.items()}
            api_response = function_handler[function_name](params)
            response = chat.send_message(
                Part.from_function_response(
                    name=function_name,
                    response={"content": str(api_response)}
                )
            )
        else:
            function_calling_in_process = False
    return response.text

# API endpoint to handle queries
@app.route('/query', methods=['POST'])
def handle_query():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' in request body"}), 400

        query = data['query']
        if not isinstance(query, str) or not query.strip():
            return jsonify({"error": "Query must be a non-empty string"}), 400

        # Preprocess query for common patterns
        lower_query = query.lower()

        # Handle standings-related queries
        if any(term in lower_query for term in ["bảng xếp hạng", "bxh", "standing"]):
            # Identify league name from query
            leagues = {
                "premier league": "Premier League",
                "ngoại hạng anh": "Premier League",
                "la liga": "la liga",
                "bundesliga": "Bundesliga",
                "serie a": "Serie A",
                "champions league": "Champions League"
            }

            # Try to extract team name if present
            team_indicators = ["của", "team", "đội", "clb"]
            team_name = None

            # Check if query contains both league and team information
            for league_key, league_name in leagues.items():
                if league_key in lower_query:
                    # Found a league, now check if there's a team mentioned
                    for indicator in team_indicators:
                        if indicator in lower_query:
                            # Extract potential team name that follows the indicator
                            parts = lower_query.split(indicator)
                            if len(parts) > 1:
                                # Simple extraction, might need refinement
                                team_candidate = parts[1].strip()
                                if team_candidate:
                                    team_name = team_candidate
                                    break

        response_text = send_chat_message(query)
        return jsonify({
            "query": query,
            "response": response_text,
            "request_id": str(uuid.uuid4())
        }), 200
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

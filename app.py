import os
import logging
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Flask app setup
app = Flask(__name__)

# Bluesky API configuration
API_URL = "https://bsky.social/xrpc"
USERNAME = os.getenv("BLUESKY_USERNAME")
PASSWORD = os.getenv("BLUESKY_APP_PASSWORD")

# Authentication token
access_token = None


def get_access_token():
    """Authenticate with Bluesky and retrieve an access token."""
    global access_token
    try:
        logging.info("Attempting to log into Bluesky...")
        response = requests.post(
            f"{API_URL}/com.atproto.server.createSession",
            json={"identifier": USERNAME, "password": PASSWORD},
        )
        response.raise_for_status()
        data = response.json()
        access_token = data.get("accessJwt")
        if not access_token:
            raise ValueError("Access token not retrieved.")
        logging.info("Login successful. Access token retrieved.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during Bluesky authentication: {e}")
        raise Exception("Authentication failed. Check your username and password.")


def resolve_did(handle):
    """Resolve a Bluesky handle to its DID."""
    global access_token
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        logging.info(f"Resolving DID for handle: {handle}")
        response = requests.get(
            f"{API_URL}/com.atproto.identity.resolveHandle",
            headers=headers,
            params={"handle": handle},
        )
        response.raise_for_status()
        data = response.json()
        did = data.get("did")
        if did:
            logging.info(f"Resolved DID for {handle}: {did}")
            return did
        else:
            logging.error(f"Failed to resolve DID for handle: {handle}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error resolving DID for handle {handle}: {e}")
        return None


def fetch_username_from_did(api_url, access_token, did):
    """Fetch the username (handle) associated with a DID using the Bluesky API."""
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(f"{api_url}/app.bsky.actor.getProfile", headers=headers, params={"actor": did})
        response.raise_for_status()
        handle = response.json().get("handle")
        logging.info(f"Resolved handle for DID {did}: {handle}")
        return handle
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching username for DID {did}: {e}")
        return None


def generate_chart(colors, title, xlabel, ylabel, dates, counts, chart_image_path):
    """General function to generate a styled bar chart."""
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 6))
    plt.bar(dates, counts, width=0.5, align="center", color=colors)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title, fontsize=12, color="#ff69b4")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(chart_image_path)
    plt.close()
    logging.info(f"Chart saved to {chart_image_path}")


def generate_likes_chart(handle, like_timestamps, post_link):
    """Generate and save a likes chart."""
    from collections import Counter
    from datetime import datetime

    logging.info("Generating likes chart...")
    dates = [datetime.fromisoformat(ts.split("T")[0]) for ts in like_timestamps]
    date_counts = Counter(dates)
    sorted_dates = sorted(date_counts.keys())
    counts = [date_counts[date] for date in sorted_dates]

    chart_image_path = "static/likes_chart.png"
    colors = ["#ff69b4" for _ in sorted_dates]
    generate_chart(
        colors,
        f"Likes Over Time for @{handle}\nPost: {post_link}",
        "Date",
        "Number of Likes",
        sorted_dates,
        counts,
        chart_image_path,
    )
    return chart_image_path


def generate_reposts_chart(handle, reposts):
    """Generate and save a reposts chart."""
    from collections import Counter
    from datetime import datetime

    logging.info("Generating reposts chart...")
    repost_timestamps = [repost["indexedAt"] for repost in reposts if "indexedAt" in repost]
    dates = [datetime.fromisoformat(ts.split("T")[0]) for ts in repost_timestamps]
    date_counts = Counter(dates)
    sorted_dates = sorted(date_counts.keys())
    counts = [date_counts[date] for date in sorted_dates]

    chart_image_path = "static/reposts_chart.png"
    colors = ["#ff85c0" for _ in sorted_dates]
    generate_chart(
        colors,
        f"Reposts Over Time for @{handle}",
        "Date",
        "Number of Reposts",
        sorted_dates,
        counts,
        chart_image_path,
    )
    return chart_image_path


@app.route("/")
def home():
    """Render the home page."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bluesky Data Visualizer</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #ff69b4, #ff85c0, #ff99cc);
                color: white;
                text-align: center;
            }
            h1 {
                font-size: 3em;
                margin-top: 20px;
                text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
            }
            form {
                margin: 20px auto;
                padding: 15px;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
                max-width: 400px;
            }
            label {
                font-size: 1.2em;
                display: block;
                margin-bottom: 10px.
            input {
                width: 90%;
                padding: 10px;
                margin-bottom: 20px;
                border: none;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                font-size: 1em;
            }
            button {
                background-color: #ff69b4;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 1em;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }
            button:hover {
                background-color: #ff85c0;
            }
            #result img {
                margin-top: 20px;
                max-width: 100%;
                border: 3px solid #ff85c0;
                border-radius: 10px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            }
        </style>
    </head>
    <body>
        <h1>Bluesky Data Visualizer</h1>
        <form id="chart-form" method="post" action="/generate">
            <label for="link">Enter a Bluesky post link:</label>
            <input type="text" id="link" name="link" placeholder="https://bsky.app/profile/..." required>
            <button type="submit">Generate Charts</button>
        </form>
        <div id="result">
            <!-- Graph or chart will appear here -->
        </div>
        <script>
            const form = document.getElementById("chart-form");
            form.addEventListener("submit", async (event) => {
                event.preventDefault();
                const link = document.getElementById("link").value;
                const response = await fetch("/generate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ link }),
                });
                const data = await response.json();
                if (data.likes_chart || data.reposts_chart) {
                    const resultDiv = document.getElementById("result");
                    resultDiv.innerHTML = `
                        ${data.likes_chart ? `<img src="/${data.likes_chart}" alt="Likes Chart">` : ''}
                        ${data.reposts_chart ? `<img src="/${data.reposts_chart}" alt="Reposts Chart">` : ''}
                    `;
                } else {
                    alert("Error: " + data.error);
                }
            });
        </script>
    </body>
    </html>
    """


@app.route("/generate", methods=["POST"])
def generate_charts():
    """Generate both likes and reposts charts from a single Bluesky link."""
    global access_token
    try:
        if not access_token:
            get_access_token()

        data = request.json
        if not data or "link" not in data:
            logging.error("No link provided in the request.")
            return jsonify({"error": "No link provided"}), 400

        link = data["link"].strip()
        logging.info(f"Received link: {link}")

        # Match links with DID in the profile section
        did_in_profile_match = re.match(r"https?://bsky\.app/profile/(did:[^/]+)/post/([^/]+)", link)

        # Match regular web links
        web_match = re.match(r"https?://bsky\.app/profile/([^/]+)/post/([^/]+)", link)

        if did_in_profile_match:
            did, post_id = did_in_profile_match.groups()
            handle = fetch_username_from_did(API_URL, access_token, did)
        elif web_match:
            handle, post_id = web_match.groups()
            did = resolve_did(handle)
        else:
            return jsonify({"error": "Invalid link format."}), 400

        at_uri = f"at://{did}/app.bsky.feed.post/{post_id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        # Fetch reposts
        reposts_response = requests.get(
            f"{API_URL}/app.bsky.feed.getRepostedBy", headers=headers, params={"uri": at_uri}
        )
        reposts = reposts_response.json().get("repostedBy", []) if reposts_response.status_code == 200 else []

        # Fetch likes
        likes_response = requests.get(
            f"{API_URL}/app.bsky.feed.getLikes", headers=headers, params={"uri": at_uri}
        )
        likes = likes_response.json().get("likes", []) if likes_response.status_code == 200 else []

        # Generate charts
        post_link = f"https://bsky.app/profile/{handle}/post/{post_id}"
        likes_timestamps = [like["indexedAt"] for like in likes if "indexedAt" in like]
        likes_chart_path = generate_likes_chart(handle, likes_timestamps, post_link) if likes else None
        reposts_chart_path = generate_reposts_chart(handle, reposts) if reposts else None

        response = {}
        if likes_chart_path:
            response["likes_chart"] = likes_chart_path
        if reposts_chart_path:
            response["reposts_chart"] = reposts_chart_path

        return jsonify(response)
    except Exception as e:
        logging.error(f"Error generating charts: {e}")
        return jsonify({"error": f"Error generating charts: {str(e)}"}), 500


if __name__ == "__main__":
    get_access_token()
    app.run(host="0.0.0.0", port=8000, debug=False)
